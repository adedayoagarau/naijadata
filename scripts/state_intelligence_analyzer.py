#!/usr/bin/env python3
"""
State Budget Intelligence Analyzer
Analyzes all 36 Nigerian state budgets using metadata from state_budget_db.py
Applies rule-based scoring + LLM enrichment for state-level anomalies
"""

import os
import json
import asyncio
import aiohttp
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Import state database
from state_budget_db import STATES, FEDERAL, get_pending_2026

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

BASE_DIR = Path(__file__).parent.parent
FINDINGS_DIR = BASE_DIR / "findings"


def parse_amount(amount_str: str) -> float:
    """Parse Nigerian amount string to float"""
    if not amount_str or amount_str in ['TBD', 'PENDING', 'Part of Federal ₦58.18T']:
        return 0

    # Remove currency symbol and commas
    clean = amount_str.replace('₦', '').replace(',', '').strip()

    # Handle trillion/billion/million
    multiplier = 1
    if 'trillion' in clean.lower():
        multiplier = 1_000_000_000_000
        clean = re.sub(r'\s*trillion.*', '', clean, flags=re.IGNORECASE)
    elif 'billion' in clean.lower():
        multiplier = 1_000_000_000
        clean = re.sub(r'\s*billion.*', '', clean, flags=re.IGNORECASE)
    elif 'million' in clean.lower():
        multiplier = 1_000_000
        clean = re.sub(r'\s*million.*', '', clean, flags=re.IGNORECASE)

    try:
        return float(clean) * multiplier
    except:
        return 0


def parse_percentage(pct_str: str) -> float:
    """Parse percentage string"""
    if not pct_str:
        return 0
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', str(pct_str))
    if match:
        return float(match.group(1))
    return 0


@dataclass
class StateAnalysis:
    """Analysis result for a state"""
    state: str
    region: str

    # Budget data
    budget_2025: float
    budget_2026: float
    status_2026: str

    # Derived metrics
    yoy_change_pct: float
    capital_ratio: float
    education_pct: float

    # Risk assessment
    risk_score: int
    risk_level: str
    risk_factors: List[Dict] = field(default_factory=list)

    # LLM enrichment
    llm_analysis: Optional[str] = None
    red_flags: List[str] = field(default_factory=list)
    investigation_leads: List[str] = field(default_factory=list)

    # Metadata
    enriched_by_llm: bool = False


class StateRiskScorer:
    """Scores states based on budget anomalies"""

    # Thresholds
    EDUCATION_MIN_PCT = 15  # UN recommendation
    CAPITAL_MIN_PCT = 40    # Healthy infrastructure investment
    YOY_SUSPICIOUS_PCT = 100  # >100% increase is suspicious

    # High-risk states (historically problematic)
    HIGH_RISK_STATES = [
        'rivers',  # Political crisis
        'imo',     # Low education spending
        'akwa_ibom',  # Very low education (2.27%)
    ]

    def score_state(self, state_key: str, state_data: Dict) -> StateAnalysis:
        """Score a single state"""
        risk_score = 0
        risk_factors = []

        name = state_data.get('name', state_key)
        region = state_data.get('region', 'Unknown')

        # Parse budget amounts
        b2025 = parse_amount(state_data.get('2025', {}).get('total', '0'))
        b2026 = parse_amount(state_data.get('2026', {}).get('total', '0'))
        status_2026 = state_data.get('2026', {}).get('status', 'UNKNOWN')

        # Calculate YoY change
        yoy_change = 0
        if b2025 > 0 and b2026 > 0:
            yoy_change = ((b2026 - b2025) / b2025) * 100

        # Parse capital ratio
        capital_str = state_data.get('2026', {}).get('capital', '') or state_data.get('2025', {}).get('capital', '')
        capital_ratio = parse_percentage(capital_str)

        # Parse education percentage
        edu_str = state_data.get('2026', {}).get('education', '') or state_data.get('2025', {}).get('education', '')
        education_pct = parse_percentage(edu_str)

        # RISK FACTOR 1: No 2026 budget
        if status_2026 in ['PENDING', 'NOT YET PRESENTED', 'UNKNOWN']:
            risk_score += 25
            risk_factors.append({
                'factor': 'NO_2026_BUDGET',
                'points': 25,
                'detail': f'2026 budget not yet presented or pending'
            })

        # RISK FACTOR 2: Extreme YoY increase
        if yoy_change > 150:
            risk_score += 30
            risk_factors.append({
                'factor': 'EXTREME_YOY_INCREASE',
                'points': 30,
                'detail': f'{yoy_change:.1f}% budget increase (very suspicious)'
            })
        elif yoy_change > 100:
            risk_score += 20
            risk_factors.append({
                'factor': 'HIGH_YOY_INCREASE',
                'points': 20,
                'detail': f'{yoy_change:.1f}% budget increase (suspicious)'
            })
        elif yoy_change > 50:
            risk_score += 10
            risk_factors.append({
                'factor': 'NOTABLE_YOY_INCREASE',
                'points': 10,
                'detail': f'{yoy_change:.1f}% budget increase'
            })

        # RISK FACTOR 3: Low education spending
        if education_pct > 0 and education_pct < 10:
            risk_score += 25
            risk_factors.append({
                'factor': 'CRITICAL_LOW_EDUCATION',
                'points': 25,
                'detail': f'Education at {education_pct:.1f}% (critically below 15% UN threshold)'
            })
        elif education_pct > 0 and education_pct < self.EDUCATION_MIN_PCT:
            risk_score += 15
            risk_factors.append({
                'factor': 'LOW_EDUCATION_SPENDING',
                'points': 15,
                'detail': f'Education at {education_pct:.1f}% (below 15% UN threshold)'
            })

        # RISK FACTOR 4: Low capital investment
        if capital_ratio > 0 and capital_ratio < 30:
            risk_score += 20
            risk_factors.append({
                'factor': 'LOW_CAPITAL_INVESTMENT',
                'points': 20,
                'detail': f'Capital expenditure only {capital_ratio:.1f}% (low infrastructure investment)'
            })

        # RISK FACTOR 5: Known high-risk state
        if state_key in self.HIGH_RISK_STATES:
            risk_score += 15
            risk_factors.append({
                'factor': 'HIGH_RISK_STATE',
                'points': 15,
                'detail': f'State has history of budget/governance issues'
            })

        # RISK FACTOR 6: Political notes
        note = state_data.get('2026', {}).get('note', '') or state_data.get('2025', {}).get('note', '')
        if note and any(word in note.lower() for word in ['political', 'crisis', 'special administration']):
            risk_score += 20
            risk_factors.append({
                'factor': 'POLITICAL_INSTABILITY',
                'points': 20,
                'detail': f'Political issues noted: {note[:100]}'
            })

        # Cap at 100
        risk_score = min(100, risk_score)

        # Determine severity
        if risk_score >= 60:
            risk_level = 'CRITICAL'
        elif risk_score >= 40:
            risk_level = 'HIGH'
        elif risk_score >= 20:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        return StateAnalysis(
            state=name,
            region=region,
            budget_2025=b2025,
            budget_2026=b2026,
            status_2026=status_2026,
            yoy_change_pct=yoy_change,
            capital_ratio=capital_ratio,
            education_pct=education_pct,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors
        )

    def score_all_states(self) -> List[StateAnalysis]:
        """Score all states"""
        results = []
        for state_key, state_data in STATES.items():
            analysis = self.score_state(state_key, state_data)
            results.append(analysis)
        return sorted(results, key=lambda x: -x.risk_score)


class StateLLMEnricher:
    """Enriches state analysis with LLM intelligence"""

    SYSTEM_PROMPT = """You are an expert on Nigerian state governance and fiscal policy.
You analyze state budgets for signs of mismanagement, corruption risks, and governance issues.

Key context:
- Nigeria has 36 states + FCT
- UN recommends 15-20% education spending
- Healthy capital:recurrent ratio is around 60:40
- Large YoY budget increases often indicate padding or unrealistic projections
- Some states have history of governance issues (Rivers political crisis, etc.)

Provide specific, actionable intelligence."""

    USER_PROMPT_TEMPLATE = """Analyze this Nigerian state's budget situation:

STATE: {state}
REGION: {region}

BUDGET DATA:
- 2025 Budget: ₦{budget_2025:,.0f}
- 2026 Budget: ₦{budget_2026:,.0f}
- 2026 Status: {status_2026}
- Year-over-Year Change: {yoy_change:.1f}%
- Capital Ratio: {capital_ratio:.1f}%
- Education Spending: {education_pct:.1f}%

RULE-BASED FLAGS:
{risk_factors}

Provide analysis in JSON format:
{{
    "analysis": "<2-3 sentences on key concerns for this state>",
    "red_flags": ["<specific red flag 1>", "<specific red flag 2>"],
    "investigation_leads": ["<what to investigate>", "<what documents to request>"],
    "comparison": "<how this compares to similar states in the region>",
    "score_adjustment": <-10 to +10 based on your analysis>
}}

Return ONLY valid JSON."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.tokens_used = 0

    async def enrich_state(self, session: aiohttp.ClientSession, analysis: StateAnalysis) -> StateAnalysis:
        """Enrich a single state analysis"""
        risk_factors_str = "\n".join([
            f"- {f['factor']}: {f.get('detail', '')}"
            for f in analysis.risk_factors
        ]) or "None detected"

        prompt = self.USER_PROMPT_TEMPLATE.format(
            state=analysis.state,
            region=analysis.region,
            budget_2025=analysis.budget_2025,
            budget_2026=analysis.budget_2026,
            status_2026=analysis.status_2026,
            yoy_change=analysis.yoy_change_pct,
            capital_ratio=analysis.capital_ratio,
            education_pct=analysis.education_pct,
            risk_factors=risk_factors_str
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800,
            "response_format": {"type": "json_object"}
        }

        try:
            async with session.post(OPENAI_API_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    self.tokens_used += result.get('usage', {}).get('total_tokens', 0)
                    content = result['choices'][0]['message']['content']
                    data = json.loads(content)

                    analysis.llm_analysis = data.get('analysis', '')
                    analysis.red_flags = data.get('red_flags', [])
                    analysis.investigation_leads = data.get('investigation_leads', [])
                    analysis.enriched_by_llm = True

                    # Adjust score
                    adjustment = data.get('score_adjustment', 0)
                    analysis.risk_score = min(100, max(0, analysis.risk_score + adjustment))

                elif response.status == 429:
                    await asyncio.sleep(30)
                    return await self.enrich_state(session, analysis)
        except Exception as e:
            print(f"  Error enriching {analysis.state}: {e}")

        return analysis

    async def enrich_all(self, analyses: List[StateAnalysis], top_n: int = 20) -> List[StateAnalysis]:
        """Enrich top N states with LLM"""
        # Only enrich high-risk states
        to_enrich = [a for a in analyses if a.risk_score >= 20][:top_n]

        print(f"\nEnriching {len(to_enrich)} states with LLM...")

        connector = aiohttp.TCPConnector(limit=3)
        async with aiohttp.ClientSession(connector=connector) as session:
            for i, analysis in enumerate(to_enrich):
                print(f"  [{i+1}/{len(to_enrich)}] {analysis.state}...", end=" ")
                await self.enrich_state(session, analysis)
                print("✓")
                await asyncio.sleep(0.5)

        print(f"  Total tokens: {self.tokens_used:,}")
        return analyses


async def main():
    print("=" * 60)
    print("NIGERIAN STATE BUDGET INTELLIGENCE ANALYZER")
    print("=" * 60)
    print(f"Analyzing all 36 states + FCT")
    print()

    # Phase 1: Rule-based scoring
    print("PHASE 1: Rule-Based Risk Scoring")
    print("-" * 40)
    scorer = StateRiskScorer()
    analyses = scorer.score_all_states()

    # Summary
    by_risk = defaultdict(list)
    for a in analyses:
        by_risk[a.risk_level].append(a)

    print(f"  CRITICAL: {len(by_risk['CRITICAL'])} states")
    print(f"  HIGH: {len(by_risk['HIGH'])} states")
    print(f"  MEDIUM: {len(by_risk['MEDIUM'])} states")
    print(f"  LOW: {len(by_risk['LOW'])} states")

    # Phase 2: LLM enrichment
    if OPENAI_API_KEY:
        print(f"\nPHASE 2: LLM Deep Analysis")
        print("-" * 40)
        enricher = StateLLMEnricher()
        analyses = await enricher.enrich_all(analyses, top_n=25)

    # Save results
    FINDINGS_DIR.mkdir(exist_ok=True)

    results = {
        'generated_at': datetime.now().isoformat(),
        'total_states': len(analyses),
        'by_risk_level': {
            'CRITICAL': len(by_risk['CRITICAL']),
            'HIGH': len(by_risk['HIGH']),
            'MEDIUM': len(by_risk['MEDIUM']),
            'LOW': len(by_risk['LOW'])
        },
        'states': [asdict(a) for a in analyses]
    }

    with open(FINDINGS_DIR / 'state_intelligence_latest.json', 'w') as f:
        json.dump(results, f, indent=2)

    with open(FINDINGS_DIR / 'state_high_risk.json', 'w') as f:
        high_risk = [a for a in analyses if a.risk_level in ['CRITICAL', 'HIGH']]
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'count': len(high_risk),
            'states': [asdict(a) for a in high_risk]
        }, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("STATE INTELLIGENCE REPORT")
    print(f"{'='*60}")

    print("\n🔴 CRITICAL RISK STATES:")
    for a in by_risk['CRITICAL']:
        print(f"  • {a.state} ({a.region}) - Score: {a.risk_score}")
        for f in a.risk_factors[:2]:
            print(f"    └ {f['factor']}: {f['detail'][:50]}")
        if a.llm_analysis:
            print(f"    └ LLM: {a.llm_analysis[:80]}...")

    print("\n🟠 HIGH RISK STATES:")
    for a in by_risk['HIGH'][:5]:
        print(f"  • {a.state} ({a.region}) - Score: {a.risk_score}")
        for f in a.risk_factors[:1]:
            print(f"    └ {f['factor']}")

    print(f"\n📁 Results saved to:")
    print(f"   {FINDINGS_DIR}/state_intelligence_latest.json")
    print(f"   {FINDINGS_DIR}/state_high_risk.json")

    # Regional analysis
    print(f"\n{'='*60}")
    print("REGIONAL SUMMARY")
    print(f"{'='*60}")

    by_region = defaultdict(list)
    for a in analyses:
        by_region[a.region].append(a)

    for region in sorted(by_region.keys()):
        states = by_region[region]
        total_2026 = sum(s.budget_2026 for s in states)
        avg_risk = sum(s.risk_score for s in states) / len(states)
        critical = len([s for s in states if s.risk_level == 'CRITICAL'])
        print(f"\n{region}:")
        print(f"  Total 2026 Budget: ₦{total_2026/1e12:.2f}T")
        print(f"  Avg Risk Score: {avg_risk:.1f}")
        print(f"  Critical States: {critical}")


if __name__ == "__main__":
    asyncio.run(main())
