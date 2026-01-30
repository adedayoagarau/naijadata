#!/usr/bin/env python3
"""
Universal Budget Risk Scorer

Philosophy: In Nigeria's context, EVERY budget item is potentially suspicious.
Instead of binary anomaly detection, we assign risk scores to ALL items.

Risk factors stack additively:
- Round number: +10-25 points
- High amount: +5-20 points
- Vague description: +15 points
- Security agency non-security spending: +30 points
- YoY spike (if data available): +10-40 points
- Known problematic budget code: +20 points
- Election year + capital project: +15 points
- etc.

Output: Every single budget item with a risk score 0-100
"""

import json
import re
import math
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional
from datetime import datetime


class UniversalRiskScorer:
    """Scores every budget item for corruption risk"""

    def __init__(self):
        # Security agencies that shouldn't do certain things
        self.security_agencies = [
            'national intelligence agency', 'nia', 'dia', 'dss', 'state security',
            'defence intelligence', 'nscdc', 'civil defence', 'immigration',
            'customs', 'efcc', 'icpc', 'ndlea', 'police', 'army', 'navy',
            'air force', 'military', 'armed forces', 'office of the nsa'
        ]

        # Non-security activities
        self.non_security_activities = [
            'hospital', 'school', 'university', 'education', 'health',
            'agriculture', 'farm', 'borehole', 'water supply', 'market',
            'shopping', 'hotel', 'guest house', 'recreation', 'entertainment'
        ]

        # Vague/suspicious description keywords
        self.vague_keywords = [
            'miscellaneous', 'sundry', 'other', 'general', 'various',
            'contingency', 'emergency', 'unforeseen', 'as and when required'
        ]

        # High-risk budget code prefixes
        self.high_risk_codes = {
            '2301': 10,   # Capital purchases - often inflated
            '2302': 10,   # Construction - high padding risk
            '2303': 15,   # Rehabilitation - duplicate/ghost projects
            '2210': 10,   # Training - often phantom
            '2211': 20,   # Consulting - major fraud area
        }

        # Known high-risk MDAs (historically problematic)
        self.high_risk_mdas = [
            'national assembly', 'nnpc', 'nnpcl', 'petroleum',
            'solid minerals', 'power', 'works', 'nddc', 'niger delta',
            'universal basic education', 'ubec', 'nimasa'
        ]

        # Election years (higher capital spending, often wasteful)
        self.election_years = [2019, 2023, 2027]

    def score_item(self, item: Dict, historical_data: Optional[Dict] = None) -> Dict:
        """
        Score a single budget item.
        Returns the item with added risk_score and risk_factors.
        """
        risk_score = 0
        risk_factors = []

        amount = item.get('amount', 0)
        description = (item.get('description') or '').lower()
        mda = (item.get('mda') or '').lower()
        budget_code = item.get('budget_code', '')
        year = item.get('year', 2026)
        item_type = (item.get('type') or '').lower()

        # 1. AMOUNT-BASED RISKS
        if amount > 0:
            # Large amounts = more scrutiny needed
            if amount >= 100_000_000_000:  # ≥₦100B
                risk_score += 20
                risk_factors.append({
                    'factor': 'VERY_LARGE_AMOUNT',
                    'points': 20,
                    'detail': f'Amount exceeds ₦100B'
                })
            elif amount >= 10_000_000_000:  # ≥₦10B
                risk_score += 15
                risk_factors.append({
                    'factor': 'LARGE_AMOUNT',
                    'points': 15,
                    'detail': f'Amount exceeds ₦10B'
                })
            elif amount >= 1_000_000_000:  # ≥₦1B
                risk_score += 10
                risk_factors.append({
                    'factor': 'SIGNIFICANT_AMOUNT',
                    'points': 10,
                    'detail': f'Amount exceeds ₦1B'
                })

            # Round number detection (more suspicious at higher amounts)
            if self._is_suspiciously_round(amount):
                points = 15 if amount >= 1_000_000_000 else 10
                risk_score += points
                risk_factors.append({
                    'factor': 'ROUND_NUMBER',
                    'points': points,
                    'detail': f'Exact round amount suggests estimation, not actual costing'
                })

        # 2. DESCRIPTION-BASED RISKS
        if description:
            # Vague descriptions
            for keyword in self.vague_keywords:
                if keyword in description:
                    risk_score += 15
                    risk_factors.append({
                        'factor': 'VAGUE_DESCRIPTION',
                        'points': 15,
                        'detail': f'Contains vague term: "{keyword}"'
                    })
                    break

            # Very short descriptions (hiding details)
            if len(description) < 20 and amount > 100_000_000:
                risk_score += 10
                risk_factors.append({
                    'factor': 'SHORT_DESCRIPTION',
                    'points': 10,
                    'detail': 'Minimal description for large amount'
                })

            # Security agency doing non-security things
            is_security = any(agency in mda for agency in self.security_agencies)
            if is_security:
                for activity in self.non_security_activities:
                    if activity in description:
                        risk_score += 30
                        risk_factors.append({
                            'factor': 'MANDATE_VIOLATION',
                            'points': 30,
                            'detail': f'Security agency allocated for "{activity}"'
                        })
                        break

        # 3. BUDGET CODE RISKS
        if budget_code:
            code_prefix = budget_code[:4]
            if code_prefix in self.high_risk_codes:
                points = self.high_risk_codes[code_prefix]
                risk_score += points
                risk_factors.append({
                    'factor': 'HIGH_RISK_CODE',
                    'points': points,
                    'detail': f'Budget code {code_prefix} historically prone to abuse'
                })

        # 4. MDA RISKS
        for risky_mda in self.high_risk_mdas:
            if risky_mda in mda:
                risk_score += 15
                risk_factors.append({
                    'factor': 'HIGH_RISK_MDA',
                    'points': 15,
                    'detail': f'MDA has history of audit issues'
                })
                break

        # 5. TIMING RISKS
        if year in self.election_years:
            if 'capital' in item_type or any(x in description for x in ['construction', 'project', 'procurement']):
                risk_score += 15
                risk_factors.append({
                    'factor': 'ELECTION_YEAR_CAPITAL',
                    'points': 15,
                    'detail': f'{year} is election year - capital projects often rushed/inflated'
                })

        # 6. HISTORICAL COMPARISON (if available)
        if historical_data:
            prev_amount = historical_data.get('previous_amount', 0)
            if prev_amount > 0 and amount > 0:
                change_pct = ((amount - prev_amount) / prev_amount) * 100

                if change_pct > 200:
                    risk_score += 25
                    risk_factors.append({
                        'factor': 'EXTREME_YOY_INCREASE',
                        'points': 25,
                        'detail': f'{change_pct:.0f}% increase from previous year'
                    })
                elif change_pct > 100:
                    risk_score += 15
                    risk_factors.append({
                        'factor': 'HIGH_YOY_INCREASE',
                        'points': 15,
                        'detail': f'{change_pct:.0f}% increase from previous year'
                    })
                elif change_pct > 50:
                    risk_score += 10
                    risk_factors.append({
                        'factor': 'NOTABLE_YOY_INCREASE',
                        'points': 10,
                        'detail': f'{change_pct:.0f}% increase (above inflation)'
                    })

        # Cap at 100
        risk_score = min(100, risk_score)

        # Determine severity
        if risk_score >= 60:
            severity = 'CRITICAL'
        elif risk_score >= 40:
            severity = 'HIGH'
        elif risk_score >= 20:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        # Return enriched item
        return {
            **item,
            'risk_score': risk_score,
            'severity': severity,
            'risk_factors': risk_factors,
            'risk_factor_count': len(risk_factors)
        }

    def _is_suspiciously_round(self, amount: float) -> bool:
        """Check if amount is suspiciously round"""
        if amount < 100_000_000:  # Below ₦100M, round numbers are common
            return False

        # Check for exact billions
        if amount >= 1_000_000_000:
            billions = amount / 1_000_000_000
            if billions == int(billions):
                return True

        # Check for exact hundred millions
        hundred_millions = amount / 100_000_000
        if hundred_millions == int(hundred_millions):
            return True

        # Check for amounts ending in many zeros
        amount_str = str(int(amount))
        trailing_zeros = len(amount_str) - len(amount_str.rstrip('0'))
        if trailing_zeros >= 7:  # 10 million or more in trailing zeros
            return True

        return False

    def score_all(self, items: List[Dict]) -> List[Dict]:
        """Score all items"""
        # Build historical lookup for YoY comparison
        historical = defaultdict(dict)
        for item in items:
            key = (item.get('mda', ''), item.get('budget_code', ''), item.get('description', '')[:50])
            year = item.get('year', 2026)
            historical[key][year] = item.get('amount', 0)

        # Score each item
        scored_items = []
        for item in items:
            key = (item.get('mda', ''), item.get('budget_code', ''), item.get('description', '')[:50])
            year = item.get('year', 2026)

            # Find previous year data
            hist_data = None
            prev_year = year - 1
            if prev_year in historical[key]:
                hist_data = {'previous_amount': historical[key][prev_year]}

            scored_item = self.score_item(item, hist_data)
            scored_items.append(scored_item)

        return scored_items


def format_amount(amount: float) -> str:
    """Format amount in human-readable form"""
    if amount >= 1_000_000_000_000:
        return f"₦{amount/1_000_000_000_000:.2f}T"
    elif amount >= 1_000_000_000:
        return f"₦{amount/1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"₦{amount/1_000_000:.2f}M"
    else:
        return f"₦{amount:,.0f}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Universal Budget Risk Scorer')
    parser.add_argument('--input', '-i', type=Path, required=True,
                       help='Input budget data file')
    parser.add_argument('--output', '-o', type=Path, default=Path('data/risk_scored'),
                       help='Output directory')

    args = parser.parse_args()

    print("=" * 60)
    print("UNIVERSAL BUDGET RISK SCORER")
    print("=" * 60)
    print("\nPhilosophy: Every item is potentially suspicious.")
    print("No thresholds. No filters. Just risk scores.\n")

    # Load data
    print(f"Loading {args.input}...")
    with open(args.input) as f:
        data = json.load(f)

    items = data.get('items', data.get('line_items', data if isinstance(data, list) else []))
    print(f"Loaded {len(items):,} items")

    # Score all items
    print("\nScoring all items...")
    scorer = UniversalRiskScorer()
    scored_items = scorer.score_all(items)

    # Statistics
    by_severity = defaultdict(list)
    for item in scored_items:
        by_severity[item['severity']].append(item)

    total_amount = sum(i.get('amount', 0) for i in scored_items)
    critical_amount = sum(i.get('amount', 0) for i in by_severity['CRITICAL'])
    high_amount = sum(i.get('amount', 0) for i in by_severity['HIGH'])

    print(f"\n{'='*60}")
    print("RISK SCORING COMPLETE")
    print(f"{'='*60}")
    print(f"\nTotal Items: {len(scored_items):,}")
    print(f"Total Amount: {format_amount(total_amount)}")
    print(f"\nBy Severity:")
    print(f"  CRITICAL (60-100): {len(by_severity['CRITICAL']):,} items ({format_amount(critical_amount)})")
    print(f"  HIGH (40-59):      {len(by_severity['HIGH']):,} items ({format_amount(high_amount)})")
    print(f"  MEDIUM (20-39):    {len(by_severity['MEDIUM']):,} items")
    print(f"  LOW (0-19):        {len(by_severity['LOW']):,} items")

    # Top risk factors
    factor_counts = defaultdict(int)
    for item in scored_items:
        for factor in item.get('risk_factors', []):
            factor_counts[factor['factor']] += 1

    print(f"\nMost Common Risk Factors:")
    for factor, count in sorted(factor_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {factor}: {count:,}")

    # Save output
    args.output.mkdir(parents=True, exist_ok=True)

    # Full scored dataset
    with open(args.output / 'all_items_scored.json', 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_items': len(scored_items),
            'total_amount': total_amount,
            'by_severity': {
                'CRITICAL': len(by_severity['CRITICAL']),
                'HIGH': len(by_severity['HIGH']),
                'MEDIUM': len(by_severity['MEDIUM']),
                'LOW': len(by_severity['LOW'])
            },
            'items': scored_items
        }, f)

    # Critical items only (for quick review)
    with open(args.output / 'critical_items.json', 'w') as f:
        critical_sorted = sorted(by_severity['CRITICAL'], key=lambda x: -x.get('amount', 0))
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_items': len(critical_sorted),
            'total_amount': critical_amount,
            'items': critical_sorted
        }, f, indent=2)

    # High priority (CRITICAL + HIGH)
    high_priority = by_severity['CRITICAL'] + by_severity['HIGH']
    high_priority.sort(key=lambda x: (-x.get('risk_score', 0), -x.get('amount', 0)))

    with open(args.output / 'high_priority.json', 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_items': len(high_priority),
            'total_amount': critical_amount + high_amount,
            'items': high_priority[:1000]  # Top 1000 for webapp
        }, f, indent=2)

    # Summary for webapp
    top_findings = []
    for item in high_priority[:500]:
        top_findings.append({
            'id': f"{item.get('year', 2026)}-{hash(item.get('description', ''))%100000}",
            'type': item['risk_factors'][0]['factor'] if item.get('risk_factors') else 'GENERAL_RISK',
            'entity': item.get('mda', 'Unknown MDA'),
            'description': item.get('description', '')[:200],
            'amount': item.get('amount', 0),
            'severity': item['severity'],
            'risk_score': item['risk_score'],
            'year': item.get('year', 2026),
            'budget_code': item.get('budget_code', ''),
            'risk_factors': item.get('risk_factors', []),
            'recommendation': _generate_recommendation(item)
        })

    with open(args.output / 'webapp_findings.json', 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_scored': len(scored_items),
            'total_amount': total_amount,
            'critical_count': len(by_severity['CRITICAL']),
            'high_count': len(by_severity['HIGH']),
            'findings': top_findings
        }, f, indent=2)

    print(f"\nOutput saved to: {args.output}/")
    print(f"  - all_items_scored.json ({len(scored_items):,} items)")
    print(f"  - critical_items.json ({len(by_severity['CRITICAL']):,} items)")
    print(f"  - high_priority.json (top 1000)")
    print(f"  - webapp_findings.json (for frontend)")


def _generate_recommendation(item: Dict) -> str:
    """Generate recommendation based on risk factors"""
    factors = [f['factor'] for f in item.get('risk_factors', [])]

    if 'MANDATE_VIOLATION' in factors:
        return "Review against agency's statutory mandate. Consider reallocation."
    if 'EXTREME_YOY_INCREASE' in factors:
        return "Request detailed justification for increase. Compare with sector benchmarks."
    if 'ROUND_NUMBER' in factors:
        return "Request itemized breakdown with unit costs and quantities."
    if 'VAGUE_DESCRIPTION' in factors:
        return "Demand specific project details, location, and deliverables."
    if 'HIGH_RISK_MDA' in factors:
        return "Flag for enhanced monitoring. Cross-reference with audit reports."
    if 'ELECTION_YEAR_CAPITAL' in factors:
        return "Verify project completion timeline extends beyond election."

    return "Review for value-for-money and proper procurement process."


if __name__ == "__main__":
    main()
