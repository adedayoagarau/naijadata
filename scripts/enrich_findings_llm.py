#!/usr/bin/env python3
"""
LLM Enrichment for Corruption Findings
Adds deep analysis, investigation leads, and actionable intelligence
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

BASE_DIR = Path(__file__).parent.parent
FINDINGS_DIR = BASE_DIR / "findings"


SYSTEM_PROMPT = """You are a forensic accountant specializing in Nigerian government corruption.
You analyze budget line items that have been flagged by automated detection systems.

Your expertise includes:
1. Nigerian government budget structure (MDAs, budget codes, appropriation processes)
2. Common corruption schemes (ghost workers, contract inflation, mandate violations, splitting)
3. EFCC/ICPC investigation methods and precedents
4. Public procurement regulations (PPA 2007)
5. FOI request strategies

For each finding, provide:
1. Deeper analysis of WHY this is suspicious in Nigerian context
2. Specific investigation leads (what to look for, who to interview)
3. FOIA requests to make (specific documents to demand)
4. Potential criminal violations (if applicable)
5. What a whistleblower might reveal

Be specific, actionable, and cite Nigerian legal/regulatory context."""


USER_PROMPT_TEMPLATE = """Analyze this flagged Nigerian budget item:

DETECTION TYPE: {finding_type}
SEVERITY: {severity}
RISK SCORE: {risk_score}/100

BUDGET DETAILS:
- MDA: {mda}
- Budget Code: {budget_code}
- Description: {description}
- Amount: ₦{amount:,.0f}
- Year: {year}
- Level: {level}

AUTOMATED EXPLANATION: {explanation}

Provide deep forensic analysis in JSON format:
{{
    "corruption_type": "<specific corruption scheme this likely represents>",
    "nigerian_context": "<why this is suspicious in Nigeria specifically>",
    "modus_operandi": "<how this type of fraud typically works>",
    "investigation_leads": [
        "<specific lead 1>",
        "<specific lead 2>",
        "<specific lead 3>"
    ],
    "foia_requests": [
        "<specific document/record to request>",
        "<specific question to ask agency>"
    ],
    "potential_violations": [
        "<specific law/regulation potentially violated>"
    ],
    "whistleblower_indicators": "<what an insider would know about this>",
    "estimated_loss": "<estimated actual vs legitimate cost>",
    "urgency": "<HIGH/MEDIUM/LOW - how urgent to investigate>",
    "comparable_cases": "<similar EFCC cases or audit findings>"
}}

Return ONLY valid JSON."""


async def enrich_finding(session: aiohttp.ClientSession, finding: Dict) -> Dict:
    """Enrich a single finding with LLM analysis"""
    prompt = USER_PROMPT_TEMPLATE.format(
        finding_type=finding.get('finding_type', 'UNKNOWN'),
        severity=finding.get('severity', 'UNKNOWN'),
        risk_score=finding.get('risk_score', 0),
        mda=finding.get('mda', 'Unknown'),
        budget_code=finding.get('budget_code', 'Unknown'),
        description=finding.get('description', 'Unknown'),
        amount=finding.get('amount', 0),
        year=finding.get('year', 2026),
        level=finding.get('level', 'federal'),
        explanation=finding.get('explanation', '')
    )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
        "response_format": {"type": "json_object"}
    }

    try:
        async with session.post(OPENAI_API_URL, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                tokens = result.get('usage', {}).get('total_tokens', 0)
                content = result['choices'][0]['message']['content']
                analysis = json.loads(content)

                finding['llm_analysis'] = analysis
                finding['enriched'] = True
                return finding, tokens
            elif response.status == 429:
                await asyncio.sleep(30)
                return await enrich_finding(session, finding)
            else:
                return finding, 0
    except Exception as e:
        print(f"  Error: {e}")
        return finding, 0


async def enrich_top_findings(findings: List[Dict], top_n: int = 100) -> Dict:
    """Enrich top N findings with LLM"""
    print(f"\nEnriching top {top_n} findings with LLM intelligence...")

    # Get unique findings by type (avoid enriching too many similar items)
    by_type = {}
    for f in findings:
        typ = f.get('finding_type', 'UNKNOWN')
        if typ not in by_type:
            by_type[typ] = []
        if len(by_type[typ]) < 20:  # Max 20 per type
            by_type[typ].append(f)

    to_enrich = []
    for typ, items in by_type.items():
        to_enrich.extend(items)
    to_enrich = to_enrich[:top_n]

    print(f"  Selected {len(to_enrich)} findings across {len(by_type)} types")

    enriched = []
    total_tokens = 0

    connector = aiohttp.TCPConnector(limit=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, finding in enumerate(to_enrich):
            print(f"  [{i+1}/{len(to_enrich)}] {finding['finding_type']}...", end=" ", flush=True)
            result, tokens = await enrich_finding(session, finding)
            enriched.append(result)
            total_tokens += tokens
            print(f"✓ ({tokens} tokens)")
            await asyncio.sleep(0.5)

    print(f"\n  Total tokens used: {total_tokens:,}")
    est_cost = (total_tokens / 1_000_000) * 0.60
    print(f"  Estimated cost: ${est_cost:.2f}")

    return {
        'enriched_findings': enriched,
        'total_tokens': total_tokens,
        'estimated_cost': est_cost
    }


async def main():
    print("=" * 60)
    print("LLM ENRICHMENT FOR CORRUPTION FINDINGS")
    print("=" * 60)

    # Load existing findings
    findings_file = FINDINGS_DIR / 'corruption_findings_latest.json'
    if not findings_file.exists():
        print("No findings file found. Run corruption_detector.py first.")
        return

    with open(findings_file) as f:
        data = json.load(f)

    findings = data.get('findings', [])
    print(f"Loaded {len(findings):,} findings")

    # Enrich top findings
    result = await enrich_top_findings(findings, top_n=50)

    # Save enriched findings
    output = {
        'generated_at': datetime.now().isoformat(),
        'model': MODEL,
        'total_enriched': len(result['enriched_findings']),
        'total_tokens': result['total_tokens'],
        'estimated_cost': result['estimated_cost'],
        'findings': result['enriched_findings']
    }

    with open(FINDINGS_DIR / 'enriched_corruption_findings.json', 'w') as f:
        json.dump(output, f, indent=2)

    # Print sample
    print(f"\n{'='*60}")
    print("SAMPLE ENRICHED FINDINGS")
    print(f"{'='*60}")

    for f in result['enriched_findings'][:3]:
        if f.get('llm_analysis'):
            a = f['llm_analysis']
            print(f"\n[{f['finding_type']}] {f['description'][:50]}...")
            print(f"Amount: ₦{f['amount']:,.0f}")
            print(f"\n🔍 Corruption Type: {a.get('corruption_type', 'N/A')}")
            print(f"📋 Nigerian Context: {a.get('nigerian_context', 'N/A')[:100]}...")
            print(f"\n🚨 Investigation Leads:")
            for lead in a.get('investigation_leads', [])[:3]:
                print(f"   • {lead}")
            print(f"\n📄 FOIA Requests:")
            for req in a.get('foia_requests', [])[:2]:
                print(f"   • {req}")
            print(f"\n⚖️ Potential Violations: {a.get('potential_violations', [])}")
            print("-" * 60)

    print(f"\n📁 Saved to: {FINDINGS_DIR}/enriched_corruption_findings.json")


if __name__ == "__main__":
    asyncio.run(main())
