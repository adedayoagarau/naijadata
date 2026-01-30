#!/usr/bin/env python3
"""
Batch Budget Extractor

Processes ALL budget PDFs in the data directory:
- Federal budgets (2019-2026)
- State budgets (36 states)
- Any other budget documents

Creates a unified database for the forensic auditor.

Usage:
    python3 batch_extract.py                    # Process all PDFs
    python3 batch_extract.py --federal-only     # Only federal budgets
    python3 batch_extract.py --year 2026        # Specific year
    python3 batch_extract.py --state lagos      # Specific state
"""

import json
import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime

try:
    import pdfplumber
    from tqdm import tqdm
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip3 install pdfplumber tqdm")
    sys.exit(1)


@dataclass
class BudgetLineItem:
    """A single budget line item"""
    budget_code: str
    description: str
    amount: float
    mda: str
    mda_code: str
    category: str
    page: int
    source_file: str
    year: int
    level: str  # federal or state
    state: Optional[str] = None


def parse_amount(text: str) -> float:
    """Parse Nigerian budget amounts."""
    if not text:
        return 0.0
    cleaned = re.sub(r'[₦N,\s]', '', str(text))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def detect_year_from_path(path: Path) -> int:
    """Extract year from file path or name."""
    # Try path components
    for part in path.parts:
        if part.isdigit() and 2015 <= int(part) <= 2030:
            return int(part)

    # Try filename
    match = re.search(r'(20[12]\d)', path.name)
    if match:
        return int(match.group(1))

    return 2026  # Default


def detect_state_from_path(path: Path) -> Optional[str]:
    """Extract state name from file path."""
    states = [
        'abia', 'adamawa', 'akwa ibom', 'anambra', 'bauchi', 'bayelsa',
        'benue', 'borno', 'cross river', 'delta', 'ebonyi', 'edo',
        'ekiti', 'enugu', 'gombe', 'imo', 'jigawa', 'kaduna', 'kano',
        'katsina', 'kebbi', 'kogi', 'kwara', 'lagos', 'nasarawa', 'niger',
        'ogun', 'ondo', 'osun', 'oyo', 'plateau', 'rivers', 'sokoto',
        'taraba', 'yobe', 'zamfara', 'fct'
    ]

    path_lower = str(path).lower()
    for state in states:
        if state in path_lower:
            return state.title()

    return None


def extract_line_items_from_page(
    page_text: str,
    page_num: int,
    current_mda: Dict,
    source_file: str,
    year: int,
    level: str,
    state: Optional[str]
) -> List[BudgetLineItem]:
    """Extract budget line items from a single page."""
    items = []

    patterns = [
        r'(\d{8})\s+([A-Z][A-Z\s\-/&\(\)\.\']+?)\s+([\d,]+(?:\.\d{2})?)\s*$',
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
                        page=page_num + 1,
                        source_file=source_file,
                        year=year,
                        level=level,
                        state=state
                    ))
                break

    return items


def detect_mda_header(text: str) -> Optional[Dict]:
    """Detect MDA headers."""
    patterns = [
        r'^(0\d{3})\s+([A-Z][A-Z\s\-/&]+?)(?:\s*$|\s+\d)',
        r'(0\d{3})\s+([A-Z][A-Z\s\-/&]{5,50})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            code = match.group(1)
            name = match.group(2).strip()
            if len(name) > 3 and not name.isdigit():
                return {'code': code, 'name': name}

    return None


def process_pdf(
    pdf_path: Path,
    max_pages: Optional[int] = None
) -> Tuple[List[BudgetLineItem], Dict]:
    """Process a single PDF and extract all line items."""

    year = detect_year_from_path(pdf_path)
    state = detect_state_from_path(pdf_path)
    level = 'state' if state else 'federal'

    items = []
    mda_totals = defaultdict(lambda: {
        'name': '', 'code': '', 'personnel': 0, 'overhead': 0,
        'capital': 0, 'item_count': 0
    })

    current_mda = {'code': '', 'name': 'PREAMBLE'}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages) if max_pages is None else min(max_pages, len(pdf.pages))

            for page_num in range(total_pages):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""

                mda_header = detect_mda_header(text)
                if mda_header:
                    current_mda = mda_header

                page_items = extract_line_items_from_page(
                    text, page_num, current_mda, pdf_path.name,
                    year, level, state
                )

                for item in page_items:
                    items.append(item)
                    mda_key = item.mda_code or item.mda
                    mda_totals[mda_key]['name'] = item.mda
                    mda_totals[mda_key]['code'] = item.mda_code
                    mda_totals[mda_key][item.category] += item.amount
                    mda_totals[mda_key]['item_count'] += 1

    except Exception as e:
        print(f"  Error processing {pdf_path.name}: {e}")
        return [], {}

    return items, dict(mda_totals)


def find_all_pdfs(base_path: Path, federal_only: bool = False) -> List[Path]:
    """Find all budget PDFs in the data directory."""
    pdfs = []

    # Federal budgets
    federal_path = base_path / "raw_pdfs" / "federal"
    if federal_path.exists():
        pdfs.extend(federal_path.rglob("*.pdf"))

    # State budgets (if not federal only)
    if not federal_only:
        state_path = base_path / "raw_pdfs" / "states"
        if state_path.exists():
            pdfs.extend(state_path.rglob("*.pdf"))

    # Any other PDFs in raw_pdfs
    raw_pdfs_path = base_path / "raw_pdfs"
    if raw_pdfs_path.exists():
        for pdf in raw_pdfs_path.glob("*.pdf"):
            if pdf not in pdfs:
                pdfs.append(pdf)

    return sorted(pdfs)


def batch_extract(
    base_path: Path,
    output_dir: Path,
    federal_only: bool = False,
    year_filter: Optional[int] = None,
    state_filter: Optional[str] = None,
    max_pages_per_pdf: Optional[int] = None
):
    """
    Batch extract all budget PDFs.
    """
    print(f"\n{'='*60}")
    print("BATCH BUDGET EXTRACTION")
    print(f"{'='*60}\n")

    # Find all PDFs
    pdfs = find_all_pdfs(base_path, federal_only)

    if year_filter:
        pdfs = [p for p in pdfs if str(year_filter) in str(p)]

    if state_filter:
        pdfs = [p for p in pdfs if state_filter.lower() in str(p).lower()]

    print(f"Found {len(pdfs)} PDF files to process\n")

    if not pdfs:
        print("No PDFs found. Check your raw_pdfs directory structure:")
        print("  raw_pdfs/federal/2019/")
        print("  raw_pdfs/federal/2020/")
        print("  raw_pdfs/states/lagos/")
        print("  etc.")
        return

    # Process each PDF
    all_items = []
    all_mda_totals = {}
    processed_files = []

    for pdf_path in tqdm(pdfs, desc="Processing PDFs"):
        print(f"\n  Processing: {pdf_path.name}")
        items, mda_totals = process_pdf(pdf_path, max_pages_per_pdf)

        if items:
            all_items.extend(items)
            year = detect_year_from_path(pdf_path)
            state = detect_state_from_path(pdf_path)
            key = f"{year}_{state or 'federal'}"
            all_mda_totals[key] = mda_totals
            processed_files.append({
                'file': pdf_path.name,
                'year': year,
                'level': 'state' if state else 'federal',
                'state': state,
                'items_extracted': len(items)
            })
            print(f"    Extracted {len(items)} line items")

    # Summary
    print(f"\n{'='*60}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"Files processed: {len(processed_files)}")
    print(f"Total line items: {len(all_items):,}")
    print(f"Total amount: ₦{sum(i.amount for i in all_items)/1e12:.2f}T")

    # By year
    by_year = defaultdict(list)
    for item in all_items:
        by_year[item.year].append(item)

    print("\nBy Year:")
    for year in sorted(by_year.keys()):
        items = by_year[year]
        total = sum(i.amount for i in items)
        print(f"  {year}: {len(items):,} items, ₦{total/1e12:.2f}T")

    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    # All items (for auditor)
    master_output = {
        'extraction_date': datetime.now().isoformat(),
        'files_processed': len(processed_files),
        'total_items': len(all_items),
        'years_covered': sorted(by_year.keys()),
        'items': [asdict(item) for item in all_items]
    }

    master_path = output_dir / "master_budget_data.json"
    with open(master_path, 'w') as f:
        json.dump(master_output, f, indent=2)
    print(f"\nMaster data saved to: {master_path}")

    # Per-year files
    for year, items in by_year.items():
        year_output = {
            'year': year,
            'total_items': len(items),
            'items': [asdict(item) for item in items]
        }
        year_path = output_dir / f"budget_{year}.json"
        with open(year_path, 'w') as f:
            json.dump(year_output, f, indent=2)

    # Processing manifest
    manifest = {
        'extraction_date': datetime.now().isoformat(),
        'files': processed_files,
        'summary': {
            'total_files': len(processed_files),
            'total_items': len(all_items),
            'years': list(sorted(by_year.keys())),
            'by_year': {str(y): len(items) for y, items in by_year.items()}
        }
    }

    manifest_path = output_dir / "extraction_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to: {manifest_path}")

    return master_output


def main():
    parser = argparse.ArgumentParser(description='Batch Budget Extractor')
    parser.add_argument('--base-path', type=Path, default=Path('.'),
                       help='Base path for naijadata project')
    parser.add_argument('--output', '-o', type=Path, default=Path('./extracted'),
                       help='Output directory')
    parser.add_argument('--federal-only', action='store_true',
                       help='Only process federal budgets')
    parser.add_argument('--year', '-y', type=int,
                       help='Filter to specific year')
    parser.add_argument('--state', '-s', type=str,
                       help='Filter to specific state')
    parser.add_argument('--max-pages', type=int,
                       help='Max pages per PDF (for testing)')

    args = parser.parse_args()

    batch_extract(
        base_path=args.base_path,
        output_dir=args.output,
        federal_only=args.federal_only,
        year_filter=args.year,
        state_filter=args.state,
        max_pages_per_pdf=args.max_pages
    )


if __name__ == "__main__":
    main()
