#!/usr/bin/env python3
"""
Budget Data Organizer

Takes the master extraction and organizes it into a proper folder structure:

data/
├── federal/
│   ├── 2019/
│   │   ├── budget_items.json
│   │   └── summary.json
│   ├── 2021/
│   ├── 2022/
│   ├── 2024/
│   ├── 2025/
│   └── 2026/
├── states/
│   ├── lagos/
│   │   └── 2025/
│   ├── kano/
│   └── ...
├── contractors/
│   └── all_contractors.json
├── aggregations/
│   ├── by_mda.json
│   ├── by_sector.json
│   ├── by_budget_code.json
│   └── totals_by_year.json
└── master/
    ├── all_items.json
    └── manifest.json
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional
from datetime import datetime


def extract_contractor(description: str) -> Optional[str]:
    """Extract contractor/vendor name from description"""
    if not description:
        return None

    patterns = [
        r'\bby\s+([A-Z][A-Za-z\s&]+(?:Ltd|Limited|PLC|Nigeria|Nig\.?|& Sons|& Co\.?|Company))',
        r'\bfrom\s+([A-Z][A-Za-z\s&]+(?:Ltd|Limited|PLC|Nigeria|Nig\.?|& Sons|& Co\.?|Company))',
        r'\bto\s+([A-Z][A-Za-z\s&]+(?:Ltd|Limited|PLC|Nigeria|Nig\.?|& Sons|& Co\.?|Company))',
        r'\bthrough\s+([A-Z][A-Za-z\s&]+(?:Ltd|Limited|PLC|Nigeria|Nig\.?|& Sons|& Co\.?|Company))',
        r'\b([A-Z][A-Za-z\s&]+(?:Ltd|Limited|PLC|& Sons|& Co\.?))\b',
        r'(?:contract(?:ed)?|awarded?)\s+(?:to\s+)?([A-Z][A-Za-z\s&]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            contractor = match.group(1).strip()
            # Clean up
            contractor = re.sub(r'\s+', ' ', contractor)
            if len(contractor) > 5 and len(contractor) < 100:
                return contractor

    return None


def extract_location(description: str) -> Optional[str]:
    """Extract location from description"""
    if not description:
        return None

    # Nigerian states
    states = [
        'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue',
        'Borno', 'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'FCT',
        'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi',
        'Kwara', 'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo',
        'Plateau', 'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara', 'Abuja'
    ]

    for state in states:
        if state.lower() in description.lower():
            return state

    # Look for "in [Location]" patterns
    match = re.search(r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', description)
    if match:
        return match.group(1)

    return None


def extract_quantity(description: str, amount: float) -> Dict:
    """Extract quantity and calculate unit cost"""
    if not description:
        return {}

    # Patterns like "50 units", "20 vehicles", "10 boreholes"
    patterns = [
        r'(\d+)\s*(?:nos?\.?|units?|pieces?|sets?)',
        r'(\d+)\s*(?:vehicles?|cars?|trucks?|motorcycles?|hilux|land\s*cruisers?)',
        r'(\d+)\s*(?:boreholes?|wells?)',
        r'(\d+)\s*(?:laptops?|computers?|desktops?)',
        r'(\d+)\s*(?:buildings?|blocks?|classrooms?|offices?)',
        r'(?:purchase|procurement|supply)\s+of\s+(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            quantity = int(match.group(1))
            if quantity > 0 and amount > 0:
                return {
                    'quantity': quantity,
                    'unit_cost': amount / quantity
                }

    return {}


def categorize_sector(mda: str, description: str) -> str:
    """Categorize into sector based on MDA and description"""
    mda_lower = (mda or '').lower()
    desc_lower = (description or '').lower()

    if any(x in mda_lower for x in ['education', 'university', 'polytechnic', 'school']):
        return 'education'
    if any(x in mda_lower for x in ['health', 'hospital', 'medical']):
        return 'health'
    if any(x in mda_lower for x in ['defence', 'army', 'navy', 'air force', 'military']):
        return 'defence'
    if any(x in mda_lower for x in ['police', 'security', 'intelligence', 'nscdc']):
        return 'security'
    if any(x in mda_lower for x in ['works', 'road', 'infrastructure', 'housing']):
        return 'infrastructure'
    if any(x in mda_lower for x in ['agric', 'water', 'rural']):
        return 'agriculture'
    if any(x in mda_lower for x in ['power', 'energy', 'petroleum']):
        return 'energy'
    if any(x in mda_lower for x in ['transport', 'aviation', 'railway', 'maritime']):
        return 'transport'
    if any(x in mda_lower for x in ['finance', 'budget', 'revenue']):
        return 'finance'
    if any(x in mda_lower for x in ['justice', 'judiciary', 'court']):
        return 'justice'
    if any(x in mda_lower for x in ['national assembly', 'senate', 'house of rep']):
        return 'legislature'
    if any(x in mda_lower for x in ['presidency', 'state house', 'cabinet']):
        return 'executive'

    return 'other'


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


def organize_data(input_path: Path, output_dir: Path):
    """Main function to organize budget data"""

    print("=" * 60)
    print("BUDGET DATA ORGANIZER")
    print("=" * 60)

    # Load master data
    print(f"\nLoading {input_path}...")
    with open(input_path) as f:
        data = json.load(f)

    items = data.get('items', data.get('line_items', data if isinstance(data, list) else []))
    print(f"Loaded {len(items):,} items")

    # Create output structure
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'federal').mkdir(exist_ok=True)
    (output_dir / 'states').mkdir(exist_ok=True)
    (output_dir / 'contractors').mkdir(exist_ok=True)
    (output_dir / 'aggregations').mkdir(exist_ok=True)
    (output_dir / 'master').mkdir(exist_ok=True)

    # Organize by year and level
    by_year_level = defaultdict(lambda: defaultdict(list))
    by_mda = defaultdict(lambda: {'items': [], 'total': 0})
    by_sector = defaultdict(lambda: {'items': [], 'total': 0})
    by_budget_code = defaultdict(lambda: {'items': [], 'total': 0})
    contractors = defaultdict(lambda: {
        'total_allocated': 0,
        'project_count': 0,
        'years': set(),
        'mdas': set(),
        'projects': []
    })

    totals_by_year = defaultdict(lambda: {'total': 0, 'item_count': 0})

    # Process each item
    print("\nProcessing items...")
    for i, item in enumerate(items):
        if i % 50000 == 0:
            print(f"  Processed {i:,} items...")

        year = item.get('year', 2026)
        level = item.get('level', 'federal')
        state = item.get('state')
        mda = item.get('mda', 'Unknown')
        description = item.get('description', '')
        amount = item.get('amount', 0)
        budget_code = item.get('budget_code', '')

        # Enrich item
        item['sector'] = categorize_sector(mda, description)
        item['contractor'] = extract_contractor(description)
        item['location'] = extract_location(description)

        quantity_info = extract_quantity(description, amount)
        if quantity_info:
            item['quantity'] = quantity_info.get('quantity')
            item['unit_cost'] = quantity_info.get('unit_cost')

        # Organize by year/level
        if level == 'federal':
            by_year_level['federal'][year].append(item)
        else:
            state_key = (state or 'unknown').lower().replace(' ', '_')
            by_year_level[f'states/{state_key}'][year].append(item)

        # Aggregate by MDA
        by_mda[mda]['items'].append({
            'year': year,
            'description': description[:200],
            'amount': amount,
            'budget_code': budget_code
        })
        by_mda[mda]['total'] += amount

        # Aggregate by sector
        sector = item['sector']
        by_sector[sector]['total'] += amount

        # Aggregate by budget code prefix
        if budget_code:
            code_prefix = budget_code[:4] if len(budget_code) >= 4 else budget_code
            by_budget_code[code_prefix]['total'] += amount
            by_budget_code[code_prefix]['items'].append({
                'mda': mda,
                'description': description[:100],
                'amount': amount
            })

        # Track contractors
        contractor = item.get('contractor')
        if contractor:
            contractors[contractor]['total_allocated'] += amount
            contractors[contractor]['project_count'] += 1
            contractors[contractor]['years'].add(year)
            contractors[contractor]['mdas'].add(mda)
            contractors[contractor]['projects'].append({
                'year': year,
                'mda': mda,
                'description': description[:200],
                'amount': amount
            })

        # Totals by year
        totals_by_year[year]['total'] += amount
        totals_by_year[year]['item_count'] += 1

    # Save organized data
    print("\nSaving organized data...")

    # 1. By year and level
    for path_key, years_data in by_year_level.items():
        for year, year_items in years_data.items():
            year_dir = output_dir / path_key / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)

            # Save items
            with open(year_dir / 'budget_items.json', 'w') as f:
                json.dump({
                    'year': year,
                    'item_count': len(year_items),
                    'total': sum(i.get('amount', 0) for i in year_items),
                    'items': year_items
                }, f, indent=2, default=str)

            # Save summary
            mda_totals = defaultdict(float)
            for item in year_items:
                mda_totals[item.get('mda', 'Unknown')] += item.get('amount', 0)

            with open(year_dir / 'summary.json', 'w') as f:
                json.dump({
                    'year': year,
                    'item_count': len(year_items),
                    'total': sum(i.get('amount', 0) for i in year_items),
                    'total_formatted': format_amount(sum(i.get('amount', 0) for i in year_items)),
                    'by_mda': dict(sorted(mda_totals.items(), key=lambda x: -x[1])[:20])
                }, f, indent=2)

    # 2. Contractors
    contractor_list = []
    for name, info in contractors.items():
        contractor_list.append({
            'name': name,
            'total_allocated': info['total_allocated'],
            'total_formatted': format_amount(info['total_allocated']),
            'project_count': info['project_count'],
            'years_active': sorted(list(info['years'])),
            'mdas_worked_with': list(info['mdas'])[:10],
            'sample_projects': info['projects'][:5]
        })

    contractor_list.sort(key=lambda x: -x['total_allocated'])

    with open(output_dir / 'contractors' / 'all_contractors.json', 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_contractors': len(contractor_list),
            'total_allocated': sum(c['total_allocated'] for c in contractor_list),
            'contractors': contractor_list
        }, f, indent=2)

    print(f"  Found {len(contractor_list):,} contractors")

    # 3. Aggregations
    # By MDA
    mda_summary = []
    for mda, info in by_mda.items():
        mda_summary.append({
            'mda': mda,
            'total': info['total'],
            'total_formatted': format_amount(info['total']),
            'item_count': len(info['items'])
        })
    mda_summary.sort(key=lambda x: -x['total'])

    with open(output_dir / 'aggregations' / 'by_mda.json', 'w') as f:
        json.dump({
            'total_mdas': len(mda_summary),
            'mdas': mda_summary
        }, f, indent=2)

    # By Sector
    sector_summary = []
    for sector, info in by_sector.items():
        sector_summary.append({
            'sector': sector,
            'total': info['total'],
            'total_formatted': format_amount(info['total'])
        })
    sector_summary.sort(key=lambda x: -x['total'])

    with open(output_dir / 'aggregations' / 'by_sector.json', 'w') as f:
        json.dump({'sectors': sector_summary}, f, indent=2)

    # By Budget Code
    code_summary = []
    for code, info in by_budget_code.items():
        code_summary.append({
            'budget_code_prefix': code,
            'total': info['total'],
            'total_formatted': format_amount(info['total']),
            'item_count': len(info['items'])
        })
    code_summary.sort(key=lambda x: -x['total'])

    with open(output_dir / 'aggregations' / 'by_budget_code.json', 'w') as f:
        json.dump({'budget_codes': code_summary[:100]}, f, indent=2)

    # Totals by year
    year_summary = []
    for year, info in sorted(totals_by_year.items()):
        year_summary.append({
            'year': year,
            'total': info['total'],
            'total_formatted': format_amount(info['total']),
            'item_count': info['item_count']
        })

    with open(output_dir / 'aggregations' / 'totals_by_year.json', 'w') as f:
        json.dump({'years': year_summary}, f, indent=2)

    # 4. Master copy with enriched data
    with open(output_dir / 'master' / 'all_items.json', 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_items': len(items),
            'total_amount': sum(i.get('amount', 0) for i in items),
            'years': sorted(list(totals_by_year.keys())),
            'items': items
        }, f, indent=2, default=str)

    # Save manifest
    with open(output_dir / 'master' / 'manifest.json', 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'source_file': str(input_path),
            'total_items': len(items),
            'total_amount': sum(i.get('amount', 0) for i in items),
            'total_formatted': format_amount(sum(i.get('amount', 0) for i in items)),
            'years_covered': sorted(list(totals_by_year.keys())),
            'contractors_found': len(contractor_list),
            'top_contractors': [c['name'] for c in contractor_list[:10]],
            'folder_structure': {
                'federal/': 'Federal budget by year',
                'states/': 'State budgets by state and year',
                'contractors/': 'All contractors with allocations',
                'aggregations/': 'Summary data by MDA, sector, budget code',
                'master/': 'Complete dataset with all items'
            }
        }, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("ORGANIZATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}")
    print(f"Total items: {len(items):,}")
    print(f"Total amount: {format_amount(sum(i.get('amount', 0) for i in items))}")
    print(f"Contractors found: {len(contractor_list):,}")
    print(f"MDAs: {len(mda_summary):,}")
    print(f"Years: {sorted(list(totals_by_year.keys()))}")

    print("\nTop 10 Contractors by Allocation:")
    for c in contractor_list[:10]:
        print(f"  {c['name']}: {c['total_formatted']} ({c['project_count']} projects)")

    print(f"\nFolder structure created at: {output_dir}/")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Organize budget data into structured folders')
    parser.add_argument('--input', '-i', type=Path,
                       default=Path('extracted/master_budget_data.json'),
                       help='Input master data file')
    parser.add_argument('--output', '-o', type=Path,
                       default=Path('data'),
                       help='Output directory')

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        exit(1)

    organize_data(args.input, args.output)
