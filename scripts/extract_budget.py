#!/usr/bin/env python3
"""
Extract budget data from Nigerian government PDFs.

This script uses pdfplumber to extract tables and text from budget PDFs,
then structures the data into JSON format for the Decide9ja tool.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict, field

import pdfplumber
import pandas as pd
from tqdm import tqdm


@dataclass
class LineItem:
    """A single budget line item."""
    code: str
    description: str
    amount: float
    category: str = ""  # e.g., "travel", "medical", "personnel"


@dataclass
class MDA:
    """Ministry, Department, or Agency budget."""
    code: str
    name: str
    total: float = 0
    personnel: float = 0
    overhead: float = 0
    capital: float = 0
    line_items: list = field(default_factory=list)


@dataclass
class BudgetData:
    """Complete budget data structure."""
    source: str  # "federal" or state name
    year: int
    document_type: str
    total_budget: float = 0
    recurrent: float = 0
    capital: float = 0
    mdas: list = field(default_factory=list)
    raw_tables: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# Budget code patterns for key categories
BUDGET_CODE_PATTERNS = {
    "international_travel": r"22020801",
    "local_travel": r"22020803",
    "sitting_allowances": r"22020802",
    "drugs_medical": r"22020901",
    "vehicle_purchase": r"23010105",
    "personnel": r"2101\d+",
    "overhead": r"2202\d+",
}

# MDA name patterns to identify key ministries
MDA_PATTERNS = {
    "legislature": [
        r"house\s+of\s+(assembly|representatives)",
        r"national\s+assembly",
        r"senate",
        r"legislature",
    ],
    "health": [
        r"ministry\s+of\s+health",
        r"health\s+ministry",
        r"primary\s+health",
    ],
    "education": [
        r"ministry\s+of\s+education",
        r"education\s+ministry",
        r"universal\s+basic\s+education",
    ],
    "executive": [
        r"office\s+of\s+the\s+governor",
        r"governor.s\s+office",
        r"presidency",
        r"state\s+house",
    ],
}


def parse_amount(text: str) -> float:
    """Parse Nigerian currency amounts from text."""
    if not text or not isinstance(text, str):
        return 0.0

    # Remove currency symbols, commas, and whitespace
    cleaned = re.sub(r'[₦N,\s]', '', text)

    # Handle "billion" and "million" suffixes
    if 'B' in cleaned.upper() or 'BILLION' in cleaned.upper():
        cleaned = re.sub(r'[BbIiLlOoNn]', '', cleaned)
        try:
            return float(cleaned) * 1_000_000_000
        except ValueError:
            return 0.0
    elif 'M' in cleaned.upper() or 'MILLION' in cleaned.upper():
        cleaned = re.sub(r'[MmIiLlOoNn]', '', cleaned)
        try:
            return float(cleaned) * 1_000_000
        except ValueError:
            return 0.0

    # Try to parse as regular number
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def identify_mda_category(name: str) -> str:
    """Identify which category an MDA belongs to."""
    name_lower = name.lower()
    for category, patterns in MDA_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, name_lower):
                return category
    return "other"


def extract_tables_from_pdf(pdf_path: Path) -> list:
    """Extract all tables from a PDF file."""
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"  Processing {total_pages} pages...")

        for i, page in enumerate(tqdm(pdf.pages, desc="  Pages")):
            page_tables = page.extract_tables()
            for table in page_tables:
                if table and len(table) > 1:  # Skip empty tables
                    tables.append({
                        "page": i + 1,
                        "data": table
                    })

    return tables


def extract_text_from_pdf(pdf_path: Path, max_pages: int = 50) -> str:
    """Extract text content from PDF for analysis."""
    text = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages]):
            page_text = page.extract_text()
            if page_text:
                text.append(f"--- Page {i+1} ---\n{page_text}")

    return "\n\n".join(text)


def find_budget_tables(tables: list) -> dict:
    """Analyze tables to identify budget-related content."""
    results = {
        "summary_tables": [],
        "mda_tables": [],
        "line_item_tables": [],
        "other_tables": []
    }

    for table_info in tables:
        table = table_info["data"]
        if not table:
            continue

        # Convert to strings and check content
        flat_text = " ".join([
            str(cell) for row in table for cell in row if cell
        ]).lower()

        # Classify table based on content
        if any(x in flat_text for x in ["total budget", "appropriation", "revenue", "expenditure"]):
            results["summary_tables"].append(table_info)
        elif any(x in flat_text for x in ["ministry", "department", "agency", "mda"]):
            results["mda_tables"].append(table_info)
        elif re.search(r'\d{8,10}', flat_text):  # Budget codes are usually 8-10 digits
            results["line_item_tables"].append(table_info)
        else:
            results["other_tables"].append(table_info)

    return results


def extract_mda_from_table(table: list) -> list:
    """Extract MDA data from a budget table."""
    mdas = []

    # Try to identify header row
    header_row = None
    for i, row in enumerate(table[:5]):  # Check first 5 rows
        row_text = " ".join([str(c) for c in row if c]).lower()
        if any(x in row_text for x in ["code", "description", "amount", "total"]):
            header_row = i
            break

    if header_row is None:
        header_row = 0

    # Find column indices
    headers = [str(c).lower() if c else "" for c in table[header_row]]
    code_col = next((i for i, h in enumerate(headers) if "code" in h), 0)
    name_col = next((i for i, h in enumerate(headers) if any(x in h for x in ["description", "name", "mda"])), 1)
    amount_col = next((i for i, h in enumerate(headers) if any(x in h for x in ["amount", "total", "allocation"])), -1)

    # Process data rows
    for row in table[header_row + 1:]:
        if not row or len(row) <= max(code_col, name_col):
            continue

        code = str(row[code_col]) if row[code_col] else ""
        name = str(row[name_col]) if row[name_col] else ""
        amount = parse_amount(str(row[amount_col])) if amount_col >= 0 and row[amount_col] else 0

        if name and (code or amount > 0):
            mda = MDA(
                code=code,
                name=name,
                total=amount
            )
            mda_dict = asdict(mda)
            mda_dict["category"] = identify_mda_category(name)
            mdas.append(mda_dict)

    return mdas


def analyze_budget_pdf(pdf_path: Path) -> BudgetData:
    """Main function to analyze a budget PDF and extract structured data."""
    print(f"\n📄 Analyzing: {pdf_path.name}")

    # Initialize budget data
    budget = BudgetData(
        source="federal" if "federal" in str(pdf_path).lower() else "state",
        year=extract_year_from_path(pdf_path),
        document_type="appropriation_bill"
    )

    # Extract tables
    print("  Extracting tables...")
    tables = extract_tables_from_pdf(pdf_path)
    print(f"  Found {len(tables)} tables")

    # Classify tables
    classified = find_budget_tables(tables)
    print(f"  Summary: {len(classified['summary_tables'])}, MDA: {len(classified['mda_tables'])}, Line items: {len(classified['line_item_tables'])}")

    # Extract MDAs
    all_mdas = []
    for table_info in classified["mda_tables"] + classified["line_item_tables"]:
        mdas = extract_mda_from_table(table_info["data"])
        all_mdas.extend(mdas)

    budget.mdas = all_mdas
    budget.metadata["total_tables"] = len(tables)
    budget.metadata["pages_processed"] = tables[-1]["page"] if tables else 0

    # Store raw tables for debugging
    budget.raw_tables = [t["data"][:5] for t in tables[:10]]  # First 5 rows of first 10 tables

    return budget


def extract_year_from_path(pdf_path: Path) -> int:
    """Extract fiscal year from file path or name."""
    # Try to find 4-digit year in path
    match = re.search(r'20[1-2][0-9]', str(pdf_path))
    if match:
        return int(match.group())
    return 0


def extract_sample_content(pdf_path: Path, num_pages: int = 5) -> dict:
    """Extract sample content from PDF for inspection."""
    result = {
        "filename": pdf_path.name,
        "pages": [],
        "sample_tables": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        result["total_pages"] = len(pdf.pages)

        # Get sample pages
        for i, page in enumerate(pdf.pages[:num_pages]):
            page_data = {
                "page_number": i + 1,
                "text_preview": (page.extract_text() or "")[:1000],
                "num_tables": len(page.extract_tables())
            }
            result["pages"].append(page_data)

            # Get sample tables from this page
            for table in page.extract_tables()[:2]:
                if table:
                    result["sample_tables"].append({
                        "page": i + 1,
                        "rows": len(table),
                        "cols": len(table[0]) if table else 0,
                        "preview": table[:5]  # First 5 rows
                    })

    return result


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python extract_budget.py <pdf_path> [--sample]")
        print("\nOptions:")
        print("  --sample    Only extract sample content for inspection")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    sample_only = "--sample" in sys.argv

    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    output_dir = Path(__file__).parent.parent / "extracted"
    output_dir.mkdir(exist_ok=True)

    if sample_only:
        print("🔍 Extracting sample content for inspection...")
        result = extract_sample_content(pdf_path)
        output_file = output_dir / f"{pdf_path.stem}_sample.json"
    else:
        print("📊 Extracting full budget data...")
        result = analyze_budget_pdf(pdf_path)
        result = asdict(result)
        output_file = output_dir / f"{pdf_path.stem}_extracted.json"

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n✅ Output saved to: {output_file}")

    # Print summary
    if not sample_only and "mdas" in result:
        print(f"\n📋 Extraction Summary:")
        print(f"   MDAs found: {len(result['mdas'])}")
        print(f"   Tables processed: {result['metadata'].get('total_tables', 0)}")

        # Show key MDAs
        key_categories = ["legislature", "health", "education"]
        for category in key_categories:
            matches = [m for m in result['mdas'] if m.get('category') == category]
            if matches:
                print(f"\n   {category.title()}:")
                for m in matches[:3]:
                    print(f"      - {m['name'][:50]}: ₦{m['total']:,.0f}")


if __name__ == "__main__":
    main()
