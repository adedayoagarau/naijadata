#!/usr/bin/env python3
"""
Flatten nested budget data and run risk scorer
"""

import json
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
from risk_scorer import UniversalRiskScorer, format_amount, _generate_recommendation

def flatten_budget_data(data):
    """Convert nested MDA structure to flat items list"""
    items = []

    # Handle single budget vs list of budgets
    budgets = data if isinstance(data, list) else [data]

    for budget in budgets:
        source = budget.get('source', 'federal')
        year = budget.get('year', 2026)

        for mda in budget.get('mdas', []):
            mda_name = mda.get('name', 'Unknown MDA')
            mda_code = mda.get('code', '')

            for item in mda.get('line_items', []):
                items.append({
                    'mda': mda_name,
                    'mda_code': mda_code,
                    'budget_code': item.get('code', ''),
                    'description': item.get('description', ''),
                    'amount': item.get('amount', 0),
                    'year': year,
                    'source': source,
                    'type': 'capital' if str(item.get('code', '')).startswith('23') else 'recurrent'
                })

    return items

def main():
    # Load all available budget data
    data_paths = [
        Path('/home/user/naijadata/extracted/sample_budget_data.json'),
        Path('/home/user/naijadata/data/master_budget_data.json'),
        Path('/home/user/naijadata/extracted/master_budget_data.json'),
    ]

    all_items = []

    for path in data_paths:
        if path.exists():
            print(f"Loading {path}...")
            with open(path) as f:
                data = json.load(f)
            items = flatten_budget_data(data)
            all_items.extend(items)
            print(f"  Found {len(items)} items")

    if not all_items:
        print("No budget data found!")
        return

    print(f"\nTotal items to score: {len(all_items)}")

    # Score all items
    print("\nRunning risk scorer...")
    scorer = UniversalRiskScorer()
    scored_items = scorer.score_all(all_items)

    # Group by severity
    by_severity = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
    for item in scored_items:
        by_severity[item['severity']].append(item)

    # Stats
    total_amount = sum(i.get('amount', 0) for i in scored_items)
    critical_amount = sum(i.get('amount', 0) for i in by_severity['CRITICAL'])
    high_amount = sum(i.get('amount', 0) for i in by_severity['HIGH'])

    print(f"\n{'='*60}")
    print("RISK SCORING COMPLETE")
    print(f"{'='*60}")
    print(f"\nTotal Items: {len(scored_items)}")
    print(f"Total Amount: {format_amount(total_amount)}")
    print(f"\nBy Severity:")
    print(f"  CRITICAL: {len(by_severity['CRITICAL'])} items ({format_amount(critical_amount)})")
    print(f"  HIGH:     {len(by_severity['HIGH'])} items ({format_amount(high_amount)})")
    print(f"  MEDIUM:   {len(by_severity['MEDIUM'])} items")
    print(f"  LOW:      {len(by_severity['LOW'])} items")

    # Output directory
    output_dir = Path('/home/user/naijadata/findings')
    output_dir.mkdir(parents=True, exist_ok=True)

    # High priority items for webapp
    high_priority = by_severity['CRITICAL'] + by_severity['HIGH']
    high_priority.sort(key=lambda x: (-x.get('risk_score', 0), -x.get('amount', 0)))

    # Generate webapp findings
    findings = []
    for i, item in enumerate(high_priority[:500]):
        findings.append({
            'id': str(i + 1),
            'type': item['risk_factors'][0]['factor'] if item.get('risk_factors') else 'GENERAL_RISK',
            'entity': item.get('mda', 'Unknown MDA'),
            'description': item.get('description', '')[:200],
            'amount': item.get('amount', 0),
            'severity': item['severity'],
            'risk_score': item['risk_score'],
            'year': item.get('year', 2026),
            'state': item.get('source', '').title() if item.get('source') != 'federal' else None,
            'budget_code': item.get('budget_code', ''),
            'risk_factors': [f['factor'] for f in item.get('risk_factors', [])],
            'recommendation': _generate_recommendation(item)
        })

    # Save webapp_findings.json
    webapp_output = {
        'generated_at': __import__('datetime').datetime.now().isoformat(),
        'total_scored': len(scored_items),
        'total_amount': total_amount,
        'critical_count': len(by_severity['CRITICAL']),
        'high_count': len(by_severity['HIGH']),
        'findings': findings
    }

    with open(output_dir / 'webapp_findings.json', 'w') as f:
        json.dump(webapp_output, f, indent=2)

    print(f"\nSaved {len(findings)} findings to {output_dir / 'webapp_findings.json'}")

    # Also save all scored items
    with open(output_dir / 'all_scored.json', 'w') as f:
        json.dump({'items': scored_items}, f)

    print(f"Saved all {len(scored_items)} scored items to {output_dir / 'all_scored.json'}")

if __name__ == '__main__':
    main()
