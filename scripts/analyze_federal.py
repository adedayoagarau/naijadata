#!/usr/bin/env python3
"""
Nigerian Federal Budget Analyzer
Extracts legislature vs health spending for accountability analysis

Usage:
    python3 analyze_federal.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field, asdict

import pdfplumber
from tqdm import tqdm

# Target MDAs and their codes
TARGET_MDAS = {
    "0112": "National Assembly",
    "0113": "National Judicial Council",  # Judiciary
    "0251": "Federal Ministry of Health",
    "0253": "Federal Ministry of Education",
}

# Key budget codes to track
BUDGET_CODES = {
    # Travel
    "22020101": "Local Travel - Training",
    "22020102": "Local Travel - Others",
    "22020103": "International Travel - Training",
    "22020104": "International Travel - Others",
    # Medical
    "22020901": "Drugs/Medical Supplies",
    "22020902": "Medical Expenses - Local",
    "22020903": "Medical Expenses - Abroad",
    # Vehicles
    "23010105": "Motor Vehicles Purchase",
    "23010119": "Motor Vehicle Purchase - Executive",
    # Sitting allowances
    "21020127": "Sitting Allowances",
    "22021002": "Honorarium/Sitting Allowance",
    # Miscellaneous
    "22021001": "Refreshment & Meals",
    "22021010": "Miscellaneous Expenses",
}


@dataclass
class LineItem:
    code: str
    description: str
    amount: float
    mda_code: str = ""
    mda_name: str = ""
    page: int = 0


@dataclass
class MDABudget:
    code: str
    name: str
    personnel: float = 0
    overhead: float = 0
    capital: float = 0
    total: float = 0
    line_items: list = field(default_factory=list)
    travel_total: float = 0
    medical_total: float = 0
    vehicles_total: float = 0


def parse_amount(text: str) -> float:
    """Parse Nigerian budget amounts."""
    if not text:
        return 0.0
    # Remove currency symbols, commas, spaces
    cleaned = re.sub(r'[₦N,\s]', '', str(text))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_mda_summary(pdf_path: Path) -> dict:
    """Extract MDA summary from first few pages."""
    mdas = {}

    with pdfplumber.open(pdf_path) as pdf:
        # Summary is on first 2-3 pages
        for page_num in range(min(3, len(pdf.pages))):
            page = pdf.pages[page_num]
            text = page.extract_text() or ""

            # Parse each line for MDA data
            for line in text.split('\n'):
                # Look for lines with MDA codes (4 digits starting with 0)
                match = re.search(r'(\d+)\s+(0\d{3})\s+(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', line)
                if match:
                    code = match.group(2)
                    name = match.group(3).strip()
                    personnel = parse_amount(match.group(4))
                    overhead = parse_amount(match.group(5))
                    capital = parse_amount(match.group(6))

                    mdas[code] = MDABudget(
                        code=code,
                        name=name,
                        personnel=personnel,
                        overhead=overhead,
                        capital=capital,
                        total=personnel + overhead + capital
                    )

    return mdas


def find_mda_pages(pdf_path: Path) -> dict:
    """Scan PDF to find page ranges for each target MDA."""
    mda_pages = {}
    current_mda = None

    with pdfplumber.open(pdf_path) as pdf:
        print(f"Scanning {len(pdf.pages)} pages for target MDAs...")

        for i, page in enumerate(tqdm(pdf.pages[:500], desc="Scanning")):  # First 500 pages
            text = page.extract_text() or ""

            # Look for MDA headers
            for code, name in TARGET_MDAS.items():
                if code in text and name.upper() in text.upper():
                    if code not in mda_pages:
                        mda_pages[code] = {"name": name, "start": i, "end": i}
                    mda_pages[code]["end"] = i

    return mda_pages


def extract_line_items(pdf_path: Path, start_page: int, end_page: int, mda_code: str, mda_name: str) -> list:
    """Extract budget line items from a page range."""
    items = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page, min(end_page + 10, len(pdf.pages))):
            page = pdf.pages[page_num]
            text = page.extract_text() or ""

            # Stop if we hit a new MDA section
            if page_num > start_page:
                new_mda = re.search(r'\b0\d{3}\b.*(?:MINISTRY|ASSEMBLY|COUNCIL|COMMISSION)', text)
                if new_mda and mda_code not in text[:200]:
                    break

            # Extract line items with budget codes
            for line in text.split('\n'):
                # Match pattern: CODE DESCRIPTION AMOUNT
                match = re.match(r'(\d{8})\s+(.+?)\s+([\d,]+(?:\.\d{2})?)\s*$', line.strip())
                if match:
                    code = match.group(1)
                    desc = match.group(2).strip()
                    amount = parse_amount(match.group(3))

                    if amount > 0:
                        items.append(LineItem(
                            code=code,
                            description=desc,
                            amount=amount,
                            mda_code=mda_code,
                            mda_name=mda_name,
                            page=page_num + 1
                        ))

    return items


def categorize_spending(items: list) -> dict:
    """Categorize line items by spending type."""
    categories = {
        "travel": {"items": [], "total": 0},
        "medical": {"items": [], "total": 0},
        "vehicles": {"items": [], "total": 0},
        "sitting_allowances": {"items": [], "total": 0},
        "miscellaneous": {"items": [], "total": 0},
        "other": {"items": [], "total": 0},
    }

    for item in items:
        code = item.code
        added = False

        if code.startswith("220201"):  # Travel
            categories["travel"]["items"].append(item)
            categories["travel"]["total"] += item.amount
            added = True
        elif code.startswith("220209"):  # Medical
            categories["medical"]["items"].append(item)
            categories["medical"]["total"] += item.amount
            added = True
        elif code in ["23010105", "23010119"]:  # Vehicles
            categories["vehicles"]["items"].append(item)
            categories["vehicles"]["total"] += item.amount
            added = True
        elif code in ["21020127", "22021002"]:  # Sitting allowances
            categories["sitting_allowances"]["items"].append(item)
            categories["sitting_allowances"]["total"] += item.amount
            added = True
        elif code == "22021010":  # Miscellaneous
            categories["miscellaneous"]["items"].append(item)
            categories["miscellaneous"]["total"] += item.amount
            added = True

        if not added:
            categories["other"]["items"].append(item)
            categories["other"]["total"] += item.amount

    return categories


def format_naira(n: float) -> str:
    """Format as readable naira."""
    if n >= 1e12:
        return f"₦{n/1e12:.2f}T"
    if n >= 1e9:
        return f"₦{n/1e9:.2f}B"
    if n >= 1e6:
        return f"₦{n/1e6:.2f}M"
    return f"₦{n:,.0f}"


def analyze_federal_budget(pdf_path: Path):
    """Main analysis function."""
    print(f"\n{'='*60}")
    print("FEDERAL BUDGET ACCOUNTABILITY ANALYSIS")
    print(f"File: {pdf_path.name}")
    print(f"{'='*60}\n")

    # Step 1: Extract MDA summary
    print("Step 1: Extracting MDA summary...")
    mdas = extract_mda_summary(pdf_path)
    print(f"Found {len(mdas)} MDAs in summary\n")

    # Show key MDAs
    print("KEY MDA ALLOCATIONS:")
    print("-" * 50)
    for code in ["0112", "0251", "0253"]:  # NASS, Health, Education
        if code in mdas:
            m = mdas[code]
            print(f"{m.name[:40]:<40} {format_naira(m.total):>15}")
    print()

    # Step 2: Find target MDA pages
    print("Step 2: Locating target MDAs in document...")
    mda_pages = find_mda_pages(pdf_path)

    for code, info in mda_pages.items():
        print(f"  {info['name']}: pages {info['start']+1}-{info['end']+1}")
    print()

    # Step 3: Extract line items for each target MDA
    print("Step 3: Extracting line items...")
    all_items = []
    mda_categories = {}

    for code, info in mda_pages.items():
        print(f"\n  Extracting {info['name']}...")
        items = extract_line_items(pdf_path, info['start'], info['end'], code, info['name'])
        all_items.extend(items)

        categories = categorize_spending(items)
        mda_categories[code] = {
            "name": info["name"],
            "categories": categories,
            "total_items": len(items)
        }

        print(f"    Found {len(items)} line items")
        print(f"    Travel: {format_naira(categories['travel']['total'])}")
        print(f"    Medical: {format_naira(categories['medical']['total'])}")
        print(f"    Vehicles: {format_naira(categories['vehicles']['total'])}")

    # Step 4: Generate report
    print(f"\n{'='*60}")
    print("ACCOUNTABILITY FINDINGS")
    print(f"{'='*60}\n")

    # National Assembly spotlight
    if "0112" in mda_categories:
        nass = mda_categories["0112"]
        nass_cats = nass["categories"]

        print("NATIONAL ASSEMBLY:")
        print("-" * 40)
        print(f"  Travel Budget:     {format_naira(nass_cats['travel']['total'])}")
        print(f"  Sitting Allowances: {format_naira(nass_cats['sitting_allowances']['total'])}")
        print(f"  Vehicles:          {format_naira(nass_cats['vehicles']['total'])}")
        print(f"  Miscellaneous:     {format_naira(nass_cats['miscellaneous']['total'])}")

        # Top travel items
        travel_items = sorted(nass_cats['travel']['items'], key=lambda x: x.amount, reverse=True)
        if travel_items:
            print(f"\n  Top Travel Line Items:")
            for item in travel_items[:5]:
                print(f"    {item.description[:40]:<40} {format_naira(item.amount):>12}")

    # Health Ministry spotlight
    if "0251" in mda_categories:
        health = mda_categories["0251"]
        health_cats = health["categories"]

        print(f"\nMINISTRY OF HEALTH:")
        print("-" * 40)
        print(f"  Medical/Drugs:     {format_naira(health_cats['medical']['total'])}")
        print(f"  Travel Budget:     {format_naira(health_cats['travel']['total'])}")

    # Comparison
    if "0112" in mda_categories and "0251" in mda_categories:
        nass_travel = mda_categories["0112"]["categories"]["travel"]["total"]
        health_drugs = mda_categories["0251"]["categories"]["medical"]["total"]

        if health_drugs > 0:
            ratio = nass_travel / health_drugs
            print(f"\n{'='*60}")
            print("ACCOUNTABILITY RATIO:")
            print(f"  NASS Travel / Health Drugs = {ratio:.1f}x")
            if ratio > 1:
                print(f"  [!] Legislature spends {format_naira(nass_travel - health_drugs)} MORE on travel")
                print(f"      than Health spends on drugs!")
            print(f"{'='*60}")

    # Save results
    output = {
        "source": pdf_path.name,
        "mda_summary": {k: asdict(v) for k, v in mdas.items()},
        "detailed_analysis": {},
        "line_items_count": len(all_items)
    }

    for code, data in mda_categories.items():
        output["detailed_analysis"][code] = {
            "name": data["name"],
            "travel_total": data["categories"]["travel"]["total"],
            "medical_total": data["categories"]["medical"]["total"],
            "vehicles_total": data["categories"]["vehicles"]["total"],
            "top_travel_items": [
                {"desc": i.description, "amount": i.amount, "code": i.code}
                for i in sorted(data["categories"]["travel"]["items"],
                              key=lambda x: x.amount, reverse=True)[:10]
            ]
        }

    output_path = Path("extracted") / f"{pdf_path.stem}_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nDetailed results saved to: {output_path}")

    return output


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_federal.py <pdf_path>")
        print("\nExample:")
        print("  python3 analyze_federal.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    analyze_federal_budget(pdf_path)
