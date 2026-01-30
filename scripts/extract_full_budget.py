#!/usr/bin/env python3
"""
Full Budget Extractor for Forensic Analysis

Extracts ALL budget line items from the entire PDF for comprehensive analysis.
This creates the data needed for the Budget Forensic Auditor.

Usage:
    python3 extract_full_budget.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from collections import defaultdict

import pdfplumber
from tqdm import tqdm


@dataclass
class BudgetLineItem:
    """A single budget line item"""
    budget_code: str
    description: str
    amount: float
    mda: str
    mda_code: str
    category: str  # personnel, overhead, capital
    page: int


def parse_amount(text: str) -> float:
    """Parse Nigerian budget amounts."""
    if not text:
        return 0.0
    cleaned = re.sub(r'[₦N,\s]', '', str(text))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def detect_mda_header(text: str) -> Optional[Dict]:
    """
    Detect MDA headers in the format:
    CODE  NAME
    e.g., "0112  NATIONAL ASSEMBLY"
    """
    # Pattern for MDA header
    patterns = [
        r'^(0\d{3})\s+([A-Z][A-Z\s\-/&]+?)(?:\s*$|\s+\d)',
        r'(0\d{3})\s+([A-Z][A-Z\s\-/&]{5,50})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            code = match.group(1)
            name = match.group(2).strip()
            # Filter out false positives
            if len(name) > 3 and not name.isdigit():
                return {'code': code, 'name': name}

    return None


def extract_line_items_from_page(page_text: str, page_num: int, current_mda: Dict) -> List[BudgetLineItem]:
    """Extract budget line items from a single page."""
    items = []

    # Pattern for budget line items: 8-digit code, description, amount
    # Examples:
    # 22020101  LOCAL TRAVEL - TRAINING  1,500,000.00
    # 23010105  MOTOR VEHICLES  25,000,000

    patterns = [
        # Standard format: CODE DESCRIPTION AMOUNT
        r'(\d{8})\s+([A-Z][A-Z\s\-/&\(\)\.\']+?)\s+([\d,]+(?:\.\d{2})?)\s*$',
        # With extra whitespace
        r'(\d{8})\s{2,}([A-Z][A-Z\s\-/&\(\)\.\']+?)\s{2,}([\d,]+(?:\.\d{2})?)',
    ]

    for line in page_text.split('\n'):
        line = line.strip()
        if not line:
            continue

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                code = match.group(1)
                desc = match.group(2).strip()
                amount = parse_amount(match.group(3))

                if amount > 0 and len(desc) > 3:
                    # Determine category from code
                    if code.startswith('21'):
                        category = 'personnel'
                    elif code.startswith('22'):
                        category = 'overhead'
                    elif code.startswith('23'):
                        category = 'capital'
                    else:
                        category = 'other'

                    items.append(BudgetLineItem(
                        budget_code=code,
                        description=desc,
                        amount=amount,
                        mda=current_mda.get('name', 'UNKNOWN'),
                        mda_code=current_mda.get('code', ''),
                        category=category,
                        page=page_num + 1
                    ))
                break

    return items


def extract_full_budget(pdf_path: Path, max_pages: Optional[int] = None) -> Dict:
    """
    Extract all budget line items from the entire PDF.

    Args:
        pdf_path: Path to the budget PDF
        max_pages: Optional limit on pages to process (for testing)

    Returns:
        Dictionary with all extracted data
    """
    print(f"\n{'='*60}")
    print("FULL BUDGET EXTRACTION")
    print(f"File: {pdf_path.name}")
    print(f"{'='*60}\n")

    all_items: List[BudgetLineItem] = []
    mda_totals: Dict[str, Dict] = defaultdict(lambda: {
        'name': '',
        'code': '',
        'personnel': 0,
        'overhead': 0,
        'capital': 0,
        'item_count': 0
    })

    current_mda = {'code': '', 'name': 'PREAMBLE'}

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages) if max_pages is None else min(max_pages, len(pdf.pages))
        print(f"Processing {total_pages} pages...\n")

        for page_num in tqdm(range(total_pages), desc="Extracting"):
            page = pdf.pages[page_num]
            text = page.extract_text() or ""

            # Check for MDA header
            mda_header = detect_mda_header(text)
            if mda_header:
                current_mda = mda_header

            # Extract line items
            items = extract_line_items_from_page(text, page_num, current_mda)

            for item in items:
                all_items.append(item)

                # Update MDA totals
                mda_key = item.mda_code or item.mda
                mda_totals[mda_key]['name'] = item.mda
                mda_totals[mda_key]['code'] = item.mda_code
                mda_totals[mda_key][item.category] += item.amount
                mda_totals[mda_key]['item_count'] += 1

    # Calculate totals
    total_amount = sum(item.amount for item in all_items)
    total_personnel = sum(m['personnel'] for m in mda_totals.values())
    total_overhead = sum(m['overhead'] for m in mda_totals.values())
    total_capital = sum(m['capital'] for m in mda_totals.values())

    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Line Items: {len(all_items):,}")
    print(f"Total MDAs Found: {len(mda_totals)}")
    print(f"Total Amount: ₦{total_amount/1e12:.2f}T")
    print(f"  Personnel: ₦{total_personnel/1e12:.2f}T")
    print(f"  Overhead:  ₦{total_overhead/1e12:.2f}T")
    print(f"  Capital:   ₦{total_capital/1e12:.2f}T")

    # Show top MDAs by spending
    print(f"\nTop 10 MDAs by Total Spending:")
    sorted_mdas = sorted(mda_totals.items(),
                        key=lambda x: x[1]['personnel'] + x[1]['overhead'] + x[1]['capital'],
                        reverse=True)[:10]
    for mda_key, mda_data in sorted_mdas:
        total = mda_data['personnel'] + mda_data['overhead'] + mda_data['capital']
        print(f"  {mda_data['name'][:40]:<40} ₦{total/1e9:,.1f}B ({mda_data['item_count']} items)")

    # Prepare output
    output = {
        'source': pdf_path.name,
        'extraction_date': str(Path(pdf_path).stat().st_mtime),
        'total_pages_processed': total_pages,
        'summary': {
            'total_line_items': len(all_items),
            'total_mdas': len(mda_totals),
            'total_amount': total_amount,
            'total_personnel': total_personnel,
            'total_overhead': total_overhead,
            'total_capital': total_capital
        },
        'mda_summary': {k: dict(v) for k, v in mda_totals.items()},
        'items': [asdict(item) for item in all_items]
    }

    return output


def save_output(output: Dict, pdf_path: Path, output_dir: Path):
    """Save extracted data to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full output
    full_path = output_dir / f"{pdf_path.stem}_full_extract.json"
    with open(full_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nFull extraction saved to: {full_path}")

    # Items only (for auditor)
    items_path = output_dir / f"{pdf_path.stem}_line_items.json"
    items_output = {
        'source': output['source'],
        'total': len(output['items']),
        'items': output['items']
    }
    with open(items_path, 'w') as f:
        json.dump(items_output, f, indent=2)
    print(f"Line items saved to: {items_path}")

    # MDA summary
    summary_path = output_dir / f"{pdf_path.stem}_mda_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(output['mda_summary'], f, indent=2)
    print(f"MDA summary saved to: {summary_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_full_budget.py <pdf_path> [max_pages]")
        print("\nExample:")
        print("  python3 extract_full_budget.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf")
        print("  python3 extract_full_budget.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf 100")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    output = extract_full_budget(pdf_path, max_pages)
    save_output(output, pdf_path, Path("extracted"))
