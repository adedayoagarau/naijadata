#!/usr/bin/env python3
"""
Intelligent Budget Analyzer - Hybrid Rule-Based + LLM Pipeline

Architecture:
1. Rule-based scoring (FREE) - Analyze ALL items with risk_scorer
2. Pattern detection (FREE) - Find clusters, duplicates, networks
3. LLM enrichment (CHEAP) - Only on high-risk items for deep analysis
4. Knowledge base (FREE) - Learn patterns, build intelligence

Cost-effective: Only uses LLM on ~5-10% of flagged items
"""

import os
import json
import asyncio
import aiohttp
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict, field
import re

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Import the existing risk scorer
from risk_scorer import UniversalRiskScorer, format_amount

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"  # Cost-effective

# Paths
BASE_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = BASE_DIR / "extracted"
FINDINGS_DIR = BASE_DIR / "findings"
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_base"


@dataclass
class IntelligenceReport:
    """Comprehensive intelligence report for a finding"""
    item_id: str
    budget_code: str
    description: str
    amount: float
    mda: str
    year: int

    # Rule-based analysis
    risk_score: int
    severity: str
    risk_factors: List[Dict]

    # Pattern analysis
    pattern_flags: List[str] = field(default_factory=list)
    related_items: List[str] = field(default_factory=list)
    network_connections: List[Dict] = field(default_factory=list)

    # LLM enrichment (filled later)
    llm_analysis: Optional[str] = None
    investigation_leads: List[str] = field(default_factory=list)
    comparable_cases: List[str] = field(default_factory=list)
    whistleblower_questions: List[str] = field(default_factory=list)
    foia_requests: List[str] = field(default_factory=list)

    # Metadata
    analyzed_at: str = ""
    enriched_by_llm: bool = False


class PatternDetector:
    """Detects patterns across budget items without using LLM"""

    def __init__(self):
        self.amount_clusters = defaultdict(list)  # Same amounts
        self.description_hashes = defaultdict(list)  # Similar descriptions
        self.mda_totals = defaultdict(float)
        self.code_totals = defaultdict(float)
        self.contractor_mentions = defaultdict(list)
        self.location_mentions = defaultdict(list)

    def analyze_patterns(self, items: List[Dict]) -> Dict:
        """Analyze patterns across all items"""
        print("  Detecting patterns...")

        # Build indices
        for i, item in enumerate(items):
            amount = item.get('amount', 0)
            desc = item.get('description', '').lower()
            mda = item.get('mda', '')
            code = item.get('budget_code', '')

            # Track exact amount duplicates
            if amount > 100_000_000:  # >₦100M
                amount_key = int(amount)
                self.amount_clusters[amount_key].append(i)

            # Track similar descriptions (hash first 30 chars)
            if len(desc) > 10:
                desc_hash = hashlib.md5(desc[:30].encode()).hexdigest()[:8]
                self.description_hashes[desc_hash].append(i)

            # Track MDA totals
            self.mda_totals[mda] += amount
            self.code_totals[code[:4] if code else 'unknown'] += amount

            # Extract contractor names
            contractors = self._extract_contractors(desc)
            for contractor in contractors:
                self.contractor_mentions[contractor].append(i)

            # Extract locations
            locations = self._extract_locations(desc)
            for loc in locations:
                self.location_mentions[loc].append(i)

        # Find patterns
        patterns = {
            'duplicate_amounts': self._find_duplicate_amounts(items),
            'similar_descriptions': self._find_similar_descriptions(items),
            'contractor_networks': self._find_contractor_networks(items),
            'geographic_clusters': self._find_geographic_clusters(items),
            'mda_anomalies': self._find_mda_anomalies(items),
            'splitting_patterns': self._find_splitting_patterns(items),
        }

        return patterns

    def _extract_contractors(self, description: str) -> List[str]:
        """Extract potential contractor/vendor names from description"""
        contractors = []

        # Common patterns
        patterns = [
            r'(?:by|from|to|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Ltd|Limited|PLC|Nig|Nigeria|Company|Enterprise|Ventures))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Construction|Engineering|Services|Consulting|Solutions))',
            r'(?:contract(?:or)?|vendor|supplier):\s*([^,\n]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            contractors.extend(matches)

        return list(set(contractors))

    def _extract_locations(self, description: str) -> List[str]:
        """Extract Nigerian locations from description"""
        # Nigerian states and major cities
        locations = [
            'lagos', 'kano', 'abuja', 'ibadan', 'port harcourt', 'kaduna',
            'benin', 'maiduguri', 'zaria', 'aba', 'jos', 'ilorin', 'oyo',
            'enugu', 'abeokuta', 'sokoto', 'onitsha', 'warri', 'calabar',
            'katsina', 'akure', 'bauchi', 'ebonyi', 'yola', 'gombe'
        ]

        found = []
        desc_lower = description.lower()
        for loc in locations:
            if loc in desc_lower:
                found.append(loc.title())

        return found

    def _find_duplicate_amounts(self, items: List[Dict]) -> List[Dict]:
        """Find items with identical amounts (potential copy-paste budgeting)"""
        duplicates = []

        for amount, indices in self.amount_clusters.items():
            if len(indices) >= 3:  # 3+ items with same amount
                duplicates.append({
                    'amount': amount,
                    'count': len(indices),
                    'items': [items[i].get('description', '')[:50] for i in indices[:5]],
                    'flag': 'DUPLICATE_AMOUNT',
                    'concern': f'{len(indices)} items with identical amount ₦{amount:,.0f}'
                })

        return sorted(duplicates, key=lambda x: x['count'], reverse=True)[:20]

    def _find_similar_descriptions(self, items: List[Dict]) -> List[Dict]:
        """Find items with very similar descriptions"""
        similar = []

        for desc_hash, indices in self.description_hashes.items():
            if len(indices) >= 5:  # 5+ items with similar descriptions
                sample = items[indices[0]]
                similar.append({
                    'description_prefix': sample.get('description', '')[:50],
                    'count': len(indices),
                    'total_amount': sum(items[i].get('amount', 0) for i in indices),
                    'flag': 'SIMILAR_DESCRIPTIONS',
                    'concern': 'Multiple items with near-identical descriptions'
                })

        return sorted(similar, key=lambda x: x['total_amount'], reverse=True)[:20]

    def _find_contractor_networks(self, items: List[Dict]) -> List[Dict]:
        """Find contractors appearing multiple times"""
        networks = []

        for contractor, indices in self.contractor_mentions.items():
            if len(indices) >= 2:
                total = sum(items[i].get('amount', 0) for i in indices)
                networks.append({
                    'contractor': contractor,
                    'contract_count': len(indices),
                    'total_value': total,
                    'mdas': list(set(items[i].get('mda', '') for i in indices)),
                    'flag': 'CONTRACTOR_NETWORK',
                    'concern': f'Contractor appears in {len(indices)} budget items'
                })

        return sorted(networks, key=lambda x: x['total_value'], reverse=True)[:20]

    def _find_geographic_clusters(self, items: List[Dict]) -> List[Dict]:
        """Find geographic concentration of spending"""
        clusters = []

        for location, indices in self.location_mentions.items():
            if len(indices) >= 3:
                total = sum(items[i].get('amount', 0) for i in indices)
                clusters.append({
                    'location': location,
                    'project_count': len(indices),
                    'total_amount': total,
                    'flag': 'GEOGRAPHIC_CLUSTER',
                    'concern': f'High concentration of projects in {location}'
                })

        return sorted(clusters, key=lambda x: x['total_amount'], reverse=True)[:20]

    def _find_mda_anomalies(self, items: List[Dict]) -> List[Dict]:
        """Find MDAs with unusual spending patterns"""
        anomalies = []

        # Calculate average
        total = sum(self.mda_totals.values())
        avg = total / len(self.mda_totals) if self.mda_totals else 0

        for mda, amount in self.mda_totals.items():
            if amount > avg * 5:  # 5x above average
                anomalies.append({
                    'mda': mda,
                    'total_amount': amount,
                    'multiple_of_average': amount / avg if avg else 0,
                    'flag': 'MDA_OUTLIER',
                    'concern': f'MDA total is {amount/avg:.1f}x the average'
                })

        return sorted(anomalies, key=lambda x: x['total_amount'], reverse=True)[:20]

    def _find_splitting_patterns(self, items: List[Dict]) -> List[Dict]:
        """Find potential contract splitting (amounts just below thresholds)"""
        # Common Nigerian procurement thresholds
        thresholds = [
            (50_000_000, 'Bureau of Public Procurement threshold'),
            (100_000_000, 'Ministerial Tenders Board threshold'),
            (500_000_000, 'Federal Executive Council threshold'),
        ]

        splitting = []

        for threshold, name in thresholds:
            # Find amounts between 90-99% of threshold
            lower = threshold * 0.90
            upper = threshold * 0.99

            suspicious = [
                item for item in items
                if lower <= item.get('amount', 0) <= upper
            ]

            if len(suspicious) >= 10:
                splitting.append({
                    'threshold': threshold,
                    'threshold_name': name,
                    'count': len(suspicious),
                    'flag': 'CONTRACT_SPLITTING',
                    'concern': f'{len(suspicious)} items just below {name}'
                })

        return splitting


class LLMEnricher:
    """Enriches high-risk items with LLM analysis"""

    SYSTEM_PROMPT = """You are a forensic budget analyst specializing in Nigerian government corruption.
You're given a high-risk budget item that has already been flagged by rule-based analysis.

Your job is to:
1. Provide deeper analysis of WHY this is suspicious
2. Suggest specific investigation leads
3. Generate FOIA-style questions to ask the agency
4. Identify what a whistleblower might know
5. Compare to known corruption cases in Nigeria

Be specific, actionable, and cite Nigerian context (EFCC cases, audit reports, known patterns)."""

    USER_PROMPT_TEMPLATE = """Analyze this HIGH-RISK Nigerian budget item:

ITEM DETAILS:
- Description: {description}
- Amount: ₦{amount:,.2f}
- MDA: {mda}
- Budget Code: {budget_code}
- Year: {year}

RULE-BASED FLAGS:
{risk_factors}

PATTERN FLAGS:
{pattern_flags}

Provide analysis in this JSON format:
{{
    "deep_analysis": "<2-3 sentences on why this is suspicious in Nigerian context>",
    "investigation_leads": ["<specific lead 1>", "<specific lead 2>", "<specific lead 3>"],
    "whistleblower_questions": ["<what would an insider know?>", "<what documents exist?>"],
    "foia_requests": ["<specific document to request>", "<specific question to ask>"],
    "comparable_cases": ["<similar EFCC case or audit finding>"],
    "red_flag_score_adjustment": <-10 to +10 based on your analysis>
}}

Return ONLY valid JSON."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.calls_made = 0
        self.tokens_used = 0

    async def enrich_batch(self, session: aiohttp.ClientSession, items: List[Dict]) -> List[Dict]:
        """Enrich a batch of items with LLM analysis"""
        enriched = []

        for item in items:
            try:
                result = await self._analyze_single(session, item)
                if result:
                    item['llm_analysis'] = result.get('deep_analysis', '')
                    item['investigation_leads'] = result.get('investigation_leads', [])
                    item['whistleblower_questions'] = result.get('whistleblower_questions', [])
                    item['foia_requests'] = result.get('foia_requests', [])
                    item['comparable_cases'] = result.get('comparable_cases', [])
                    item['enriched_by_llm'] = True

                    # Adjust score if LLM suggests
                    adjustment = result.get('red_flag_score_adjustment', 0)
                    item['risk_score'] = min(100, max(0, item.get('risk_score', 0) + adjustment))

                enriched.append(item)
                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"    Error enriching item: {e}")
                enriched.append(item)

        return enriched

    async def _analyze_single(self, session: aiohttp.ClientSession, item: Dict) -> Optional[Dict]:
        """Analyze a single item"""
        risk_factors_str = "\n".join([
            f"- {f['factor']}: {f.get('detail', '')}"
            for f in item.get('risk_factors', [])
        ])

        pattern_flags_str = "\n".join([
            f"- {f}" for f in item.get('pattern_flags', [])
        ]) or "None detected"

        prompt = self.USER_PROMPT_TEMPLATE.format(
            description=item.get('description', 'N/A'),
            amount=item.get('amount', 0),
            mda=item.get('mda', 'N/A'),
            budget_code=item.get('budget_code', 'N/A'),
            year=item.get('year', 2026),
            risk_factors=risk_factors_str,
            pattern_flags=pattern_flags_str
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
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }

        try:
            async with session.post(OPENAI_API_URL, headers=headers, json=payload) as response:
                self.calls_made += 1

                if response.status == 200:
                    result = await response.json()
                    self.tokens_used += result.get('usage', {}).get('total_tokens', 0)
                    content = result['choices'][0]['message']['content']
                    return json.loads(content)
                elif response.status == 429:
                    await asyncio.sleep(30)
                    return await self._analyze_single(session, item)
                else:
                    return None
        except Exception as e:
            print(f"    API error: {e}")
            return None


class KnowledgeBase:
    """Stores and learns from findings"""

    def __init__(self):
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        self.patterns_file = KNOWLEDGE_DIR / "learned_patterns.json"
        self.contractors_file = KNOWLEDGE_DIR / "suspicious_contractors.json"
        self.mdas_file = KNOWLEDGE_DIR / "mda_risk_profiles.json"

        self.patterns = self._load_json(self.patterns_file, {'patterns': []})
        self.contractors = self._load_json(self.contractors_file, {'contractors': {}})
        self.mda_profiles = self._load_json(self.mdas_file, {'mdas': {}})

    def _load_json(self, path: Path, default: Dict) -> Dict:
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default

    def _save_json(self, path: Path, data: Dict):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def update_from_findings(self, findings: List[Dict]):
        """Update knowledge base from new findings"""
        print("  Updating knowledge base...")

        for finding in findings:
            mda = finding.get('mda', '')

            # Update MDA risk profile
            if mda:
                if mda not in self.mda_profiles['mdas']:
                    self.mda_profiles['mdas'][mda] = {
                        'total_flagged': 0,
                        'total_amount_flagged': 0,
                        'common_issues': [],
                        'years_flagged': []
                    }

                profile = self.mda_profiles['mdas'][mda]
                profile['total_flagged'] += 1
                profile['total_amount_flagged'] += finding.get('amount', 0)

                for factor in finding.get('risk_factors', []):
                    if factor['factor'] not in profile['common_issues']:
                        profile['common_issues'].append(factor['factor'])

                year = finding.get('year')
                if year and year not in profile['years_flagged']:
                    profile['years_flagged'].append(year)

        # Save updated knowledge
        self._save_json(self.mdas_file, self.mda_profiles)

        print(f"    Updated {len(self.mda_profiles['mdas'])} MDA profiles")

    def get_mda_history(self, mda: str) -> Optional[Dict]:
        """Get historical risk profile for an MDA"""
        return self.mda_profiles['mdas'].get(mda)

    def export_intelligence_report(self) -> Dict:
        """Export comprehensive intelligence report"""
        return {
            'generated_at': datetime.now().isoformat(),
            'mda_risk_profiles': self.mda_profiles,
            'known_patterns': self.patterns,
            'suspicious_contractors': self.contractors
        }


class IntelligentAnalyzer:
    """Main orchestrator for hybrid analysis pipeline"""

    def __init__(self):
        self.risk_scorer = UniversalRiskScorer()
        self.pattern_detector = PatternDetector()
        self.llm_enricher = LLMEnricher() if OPENAI_API_KEY else None
        self.knowledge_base = KnowledgeBase()

        # Stats
        self.total_items = 0
        self.critical_items = 0
        self.high_items = 0
        self.llm_enriched = 0

    async def analyze(self, items: List[Dict], enrich_top_n: int = 500) -> Dict:
        """
        Run the full analysis pipeline:
        1. Rule-based scoring (all items)
        2. Pattern detection (all items)
        3. LLM enrichment (top N high-risk only)
        4. Knowledge base update
        """
        self.total_items = len(items)

        print(f"\n{'='*60}")
        print("INTELLIGENT BUDGET ANALYZER")
        print(f"{'='*60}")
        print(f"Total items: {self.total_items:,}")
        print(f"LLM enrichment: Top {enrich_top_n} high-risk items")
        print(f"{'='*60}\n")

        # PHASE 1: Rule-based scoring (FREE)
        print("PHASE 1: Rule-Based Risk Scoring")
        print("-" * 40)
        scored_items = self.risk_scorer.score_all(items)

        # Categorize by severity
        by_severity = defaultdict(list)
        for item in scored_items:
            by_severity[item['severity']].append(item)

        self.critical_items = len(by_severity['CRITICAL'])
        self.high_items = len(by_severity['HIGH'])

        print(f"  CRITICAL: {self.critical_items:,} items")
        print(f"  HIGH: {self.high_items:,} items")
        print(f"  MEDIUM: {len(by_severity['MEDIUM']):,} items")
        print(f"  LOW: {len(by_severity['LOW']):,} items")

        # PHASE 2: Pattern detection (FREE)
        print(f"\nPHASE 2: Pattern Detection")
        print("-" * 40)
        patterns = self.pattern_detector.analyze_patterns(scored_items)

        print(f"  Duplicate amounts: {len(patterns['duplicate_amounts'])} patterns")
        print(f"  Similar descriptions: {len(patterns['similar_descriptions'])} patterns")
        print(f"  Contractor networks: {len(patterns['contractor_networks'])} detected")
        print(f"  Geographic clusters: {len(patterns['geographic_clusters'])} found")
        print(f"  Splitting patterns: {len(patterns['splitting_patterns'])} suspected")

        # Add pattern flags to items
        self._add_pattern_flags(scored_items, patterns)

        # PHASE 3: LLM enrichment (SELECTIVE - costs money)
        high_risk = by_severity['CRITICAL'] + by_severity['HIGH']
        high_risk.sort(key=lambda x: (-x['risk_score'], -x.get('amount', 0)))
        top_items = high_risk[:enrich_top_n]

        if self.llm_enricher and top_items:
            print(f"\nPHASE 3: LLM Deep Analysis (Top {len(top_items)} items)")
            print("-" * 40)

            connector = aiohttp.TCPConnector(limit=3)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Process in batches
                batch_size = 10
                for i in range(0, len(top_items), batch_size):
                    batch = top_items[i:i+batch_size]
                    print(f"  Processing batch {i//batch_size + 1}/{(len(top_items)-1)//batch_size + 1}...", end=" ")

                    enriched = await self.llm_enricher.enrich_batch(session, batch)
                    self.llm_enriched += len([e for e in enriched if e.get('enriched_by_llm')])

                    print(f"✓ ({self.llm_enricher.tokens_used:,} tokens)")

            print(f"\n  Items enriched: {self.llm_enriched}")
            print(f"  Total API calls: {self.llm_enricher.calls_made}")
            print(f"  Total tokens: {self.llm_enricher.tokens_used:,}")
            est_cost = (self.llm_enricher.tokens_used / 1_000_000) * 0.60  # Rough estimate
            print(f"  Estimated cost: ${est_cost:.2f}")
        else:
            print(f"\nPHASE 3: LLM Enrichment SKIPPED (no API key or no items)")

        # PHASE 4: Knowledge base update (FREE)
        print(f"\nPHASE 4: Knowledge Base Update")
        print("-" * 40)
        self.knowledge_base.update_from_findings(high_risk)

        # Compile results
        results = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_items_analyzed': self.total_items,
                'critical_count': self.critical_items,
                'high_count': self.high_items,
                'llm_enriched_count': self.llm_enriched,
                'model_used': MODEL if self.llm_enricher else 'none',
            },
            'summary': {
                'total_amount': sum(i.get('amount', 0) for i in scored_items),
                'critical_amount': sum(i.get('amount', 0) for i in by_severity['CRITICAL']),
                'high_amount': sum(i.get('amount', 0) for i in by_severity['HIGH']),
            },
            'patterns': patterns,
            'top_findings': top_items[:100],  # Top 100 for quick review
            'all_critical': by_severity['CRITICAL'],
            'all_high': by_severity['HIGH'],
            'knowledge_base': self.knowledge_base.export_intelligence_report(),
        }

        return results

    def _add_pattern_flags(self, items: List[Dict], patterns: Dict):
        """Add pattern flags to individual items"""
        # Create lookup by description hash
        desc_hashes = {}
        for item in items:
            desc = item.get('description', '').lower()
            if len(desc) > 10:
                h = hashlib.md5(desc[:30].encode()).hexdigest()[:8]
                desc_hashes[id(item)] = h

        # Flag items involved in patterns
        for item in items:
            flags = []
            amount = item.get('amount', 0)

            # Check duplicate amounts
            for dup in patterns['duplicate_amounts']:
                if int(amount) == dup['amount']:
                    flags.append(f"DUPLICATE_AMOUNT: {dup['count']} items with same amount")

            # Check contractor networks
            desc = item.get('description', '').lower()
            for network in patterns['contractor_networks']:
                if network['contractor'].lower() in desc:
                    flags.append(f"CONTRACTOR_NETWORK: {network['contractor']} ({network['contract_count']} contracts)")

            item['pattern_flags'] = flags


def save_results(results: Dict, output_dir: Path):
    """Save all results to files"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Main report
    with open(output_dir / f'intelligent_analysis_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Latest symlink-style
    with open(output_dir / 'intelligent_analysis_latest.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Separate files for easy access
    with open(output_dir / 'top_findings.json', 'w') as f:
        json.dump({
            'generated_at': results['metadata']['generated_at'],
            'findings': results['top_findings']
        }, f, indent=2, default=str)

    with open(output_dir / 'patterns_detected.json', 'w') as f:
        json.dump(results['patterns'], f, indent=2, default=str)

    # Webapp-ready format
    webapp_findings = []
    for item in results['top_findings']:
        webapp_findings.append({
            'id': hashlib.md5(f"{item.get('description','')}{item.get('amount',0)}".encode()).hexdigest()[:12],
            'type': item['risk_factors'][0]['factor'] if item.get('risk_factors') else 'GENERAL',
            'severity': item['severity'],
            'risk_score': item['risk_score'],
            'mda': item.get('mda', 'Unknown'),
            'description': item.get('description', '')[:200],
            'amount': item.get('amount', 0),
            'year': item.get('year', 2026),
            'risk_factors': item.get('risk_factors', []),
            'pattern_flags': item.get('pattern_flags', []),
            'llm_analysis': item.get('llm_analysis'),
            'investigation_leads': item.get('investigation_leads', []),
            'foia_requests': item.get('foia_requests', []),
        })

    with open(output_dir / 'webapp_intelligence.json', 'w') as f:
        json.dump({
            'generated_at': results['metadata']['generated_at'],
            'total_analyzed': results['metadata']['total_items_analyzed'],
            'critical_count': results['metadata']['critical_count'],
            'high_count': results['metadata']['high_count'],
            'findings': webapp_findings
        }, f, indent=2)

    print(f"\n📁 Results saved to {output_dir}/")
    print(f"   - intelligent_analysis_{timestamp}.json (full)")
    print(f"   - intelligent_analysis_latest.json")
    print(f"   - top_findings.json")
    print(f"   - patterns_detected.json")
    print(f"   - webapp_intelligence.json")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='Intelligent Budget Analyzer')
    parser.add_argument('--input', '-i', type=Path,
                       default=EXTRACTED_DIR / 'master_budget_data.json',
                       help='Input budget data file')
    parser.add_argument('--output', '-o', type=Path,
                       default=FINDINGS_DIR,
                       help='Output directory')
    parser.add_argument('--enrich-top', type=int, default=500,
                       help='Number of high-risk items to enrich with LLM (default: 500)')
    parser.add_argument('--no-llm', action='store_true',
                       help='Skip LLM enrichment entirely (free analysis only)')

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.input}...")
    with open(args.input) as f:
        data = json.load(f)

    items = data.get('items', data if isinstance(data, list) else [])
    print(f"Loaded {len(items):,} items")

    # Run analysis
    analyzer = IntelligentAnalyzer()

    if args.no_llm:
        analyzer.llm_enricher = None

    results = await analyzer.analyze(items, enrich_top_n=args.enrich_top)

    # Save results
    save_results(results, args.output)

    # Print summary
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Total items: {results['metadata']['total_items_analyzed']:,}")
    print(f"Critical findings: {results['metadata']['critical_count']:,}")
    print(f"High findings: {results['metadata']['high_count']:,}")
    print(f"LLM-enriched: {results['metadata']['llm_enriched_count']:,}")
    print(f"\nTotal amount analyzed: {format_amount(results['summary']['total_amount'])}")
    print(f"Critical amount flagged: {format_amount(results['summary']['critical_amount'])}")
    print(f"High amount flagged: {format_amount(results['summary']['high_amount'])}")


if __name__ == "__main__":
    asyncio.run(main())
