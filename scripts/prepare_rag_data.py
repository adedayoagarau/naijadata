#!/usr/bin/env python3
"""
Prepare budget data for RAG (Retrieval Augmented Generation)

This script:
1. Loads extracted budget JSON files
2. Chunks them into searchable documents
3. Creates embeddings-ready format
4. Outputs documents for vector store indexing
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class BudgetDocument:
    """A document chunk for RAG indexing."""
    id: str
    content: str
    metadata: dict

def format_naira(n: float) -> str:
    """Format as readable naira."""
    if n >= 1e12: return f"₦{n/1e12:.2f} trillion"
    if n >= 1e9: return f"₦{n/1e9:.2f} billion"
    if n >= 1e6: return f"₦{n/1e6:.2f} million"
    return f"₦{n:,.0f}"

def create_mda_summary_doc(mda: dict, year: int, source: str) -> BudgetDocument:
    """Create a summary document for an MDA."""
    name = mda.get("name", "Unknown MDA")
    code = mda.get("code", "")
    total = mda.get("total", 0)
    personnel = mda.get("personnel", 0)
    overhead = mda.get("overhead", 0)
    capital = mda.get("capital", 0)

    content = f"""
{name} ({code}) - {year} Federal Budget

Total Allocation: {format_naira(total)}
- Personnel Cost: {format_naira(personnel)}
- Overhead Cost: {format_naira(overhead)}
- Capital Expenditure: {format_naira(capital)}

Source: {source}
Year: {year}
Budget Type: Federal Government of Nigeria Appropriation Bill
""".strip()

    return BudgetDocument(
        id=f"{year}-{code}-summary",
        content=content,
        metadata={
            "type": "mda_summary",
            "year": year,
            "mda_code": code,
            "mda_name": name,
            "total": total,
            "source": source
        }
    )

def create_line_item_doc(item: dict, mda_name: str, mda_code: str, year: int) -> BudgetDocument:
    """Create a document for a budget line item."""
    code = item.get("code", "")
    desc = item.get("description", item.get("desc", ""))
    amount = item.get("amount", 0)

    content = f"""
Budget Line Item: {desc}
Budget Code: {code}
Amount: {format_naira(amount)}
MDA: {mda_name}
Year: {year}

This line item with code {code} under {mda_name} has an allocation of {format_naira(amount)} in the {year} budget.
""".strip()

    return BudgetDocument(
        id=f"{year}-{mda_code}-{code}",
        content=content,
        metadata={
            "type": "line_item",
            "year": year,
            "mda_code": mda_code,
            "mda_name": mda_name,
            "budget_code": code,
            "description": desc,
            "amount": amount
        }
    )

def create_anomaly_doc(anomaly: dict, year: int) -> BudgetDocument:
    """Create a document for a budget anomaly/red flag."""
    mda = anomaly.get("mda", "Unknown")
    item = anomaly.get("item", "")
    amount = anomaly.get("amount", 0)
    reason = anomaly.get("reason", "")
    severity = anomaly.get("severity", "MEDIUM")

    content = f"""
BUDGET RED FLAG - {severity} SEVERITY

MDA: {mda}
Suspicious Item: {item}
Amount: {format_naira(amount)}
Why Flagged: {reason}
Year: {year}

This is a potential budget anomaly. {mda} has allocated {format_naira(amount)} for "{item}".
This was flagged because: {reason}

Severity Level: {severity}
""".strip()

    return BudgetDocument(
        id=f"{year}-anomaly-{hash(mda + item) % 100000}",
        content=content,
        metadata={
            "type": "anomaly",
            "year": year,
            "mda_name": mda,
            "item": item,
            "amount": amount,
            "reason": reason,
            "severity": severity
        }
    )

def create_comparison_doc(comparison: dict) -> BudgetDocument:
    """Create a document for a notable comparison."""
    content = f"""
BUDGET COMPARISON: {comparison['title']}

{comparison['item1_name']}: {format_naira(comparison['item1_amount'])}
{comparison['item2_name']}: {format_naira(comparison['item2_amount'])}

Ratio: {comparison['item1_name']} is {comparison['ratio']:.1f}x MORE than {comparison['item2_name']}

Analysis: {comparison['analysis']}

What {format_naira(comparison['item1_amount'])} could build instead:
- {comparison.get('impact_schools', 0):,} primary schools
- {comparison.get('impact_health_centers', 0):,} health centers
- {comparison.get('impact_boreholes', 0):,} boreholes
""".strip()

    return BudgetDocument(
        id=f"comparison-{hash(comparison['title']) % 100000}",
        content=content,
        metadata={
            "type": "comparison",
            "year": comparison.get("year", 2026),
            "item1": comparison['item1_name'],
            "item2": comparison['item2_name'],
            "ratio": comparison['ratio']
        }
    )

def load_and_process_analysis(filepath: Path, year: int) -> list:
    """Load analysis JSON and create documents."""
    docs = []

    with open(filepath) as f:
        data = json.load(f)

    source = data.get("source", filepath.name)

    # Process MDA summaries
    mda_summary = data.get("mda_summary", {})
    for code, mda in mda_summary.items():
        if isinstance(mda, dict):
            mda["code"] = code
            docs.append(create_mda_summary_doc(mda, year, source))

    # Process detailed analysis
    detailed = data.get("detailed_analysis", {})
    for code, analysis in detailed.items():
        if isinstance(analysis, dict):
            # Create travel items docs
            for item in analysis.get("top_travel_items", []):
                item["mda_code"] = code
                docs.append(create_line_item_doc(
                    item,
                    analysis.get("name", "Unknown"),
                    code,
                    year
                ))

    return docs

def load_and_process_anomalies(filepath: Path, year: int) -> list:
    """Load anomalies JSON and create documents."""
    docs = []

    with open(filepath) as f:
        data = json.load(f)

    for anomaly in data.get("anomalies", []):
        docs.append(create_anomaly_doc(anomaly, year))

    return docs

def create_key_comparisons() -> list:
    """Create documents for key comparisons we've discovered."""
    comparisons = [
        {
            "title": "NIA Hospital Budget vs Health Ministry Hospital Budget",
            "year": 2026,
            "item1_name": "NIA (Spy Agency) Hospital Repairs",
            "item1_amount": 31_104_141_419,
            "item2_name": "Health Ministry Hospital Repairs",
            "item2_amount": 675_949_052,
            "ratio": 46.0,
            "analysis": "The National Intelligence Agency, a spy agency, is spending 46 times more on hospital repairs than the Federal Ministry of Health headquarters. This raises serious questions about budget transparency and whether funds are being hidden in security agencies.",
            "impact_schools": 207,
            "impact_health_centers": 207,
            "impact_boreholes": 6220
        },
        {
            "title": "National Assembly Travel vs Health Ministry Drugs",
            "year": 2026,
            "item1_name": "National Assembly Travel Budget",
            "item1_amount": 22_490_000_000,
            "item2_name": "Health Ministry Drugs & Medical Supplies (HQ)",
            "item2_amount": 42_175_897_021,
            "ratio": 0.53,
            "analysis": "The National Assembly's travel budget of ₦22.49 billion is substantial. While less than Health's drug budget, it's worth noting that 469 legislators are allocated this much for travel alone.",
            "impact_schools": 150,
            "impact_health_centers": 150,
            "impact_boreholes": 4498
        },
        {
            "title": "Police Academy School Meals vs Education Sector",
            "year": 2026,
            "item1_name": "Nigeria Police Academy Wudil - School Meal Subsidy",
            "item1_amount": 5_900_000_000,
            "item2_name": "Expected: Under Education Ministry",
            "item2_amount": 0,
            "ratio": 0,
            "analysis": "A Police Academy is budgeting ₦5.9 billion for 'Meal Subsidy to Government Schools'. This is a mandate that should belong to the Education Ministry or the National School Feeding Programme, not the Police.",
            "impact_schools": 39,
            "impact_health_centers": 39,
            "impact_boreholes": 1180
        }
    ]

    return [create_comparison_doc(c) for c in comparisons]

def main():
    """Main processing function."""
    print("=" * 60)
    print("PREPARING BUDGET DATA FOR RAG")
    print("=" * 60)

    all_docs = []
    extracted_dir = Path("extracted")
    output_dir = Path("webapp/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process analysis files
    for filepath in extracted_dir.glob("*_analysis.json"):
        print(f"\nProcessing: {filepath.name}")
        year_match = re.search(r"20\d{2}", filepath.name)
        year = int(year_match.group()) if year_match else 2026

        docs = load_and_process_analysis(filepath, year)
        all_docs.extend(docs)
        print(f"  Created {len(docs)} documents")

    # Process anomaly files
    for filepath in extracted_dir.glob("*_anomalies.json"):
        print(f"\nProcessing: {filepath.name}")
        year_match = re.search(r"20\d{2}", filepath.name)
        year = int(year_match.group()) if year_match else 2026

        docs = load_and_process_anomalies(filepath, year)
        all_docs.extend(docs)
        print(f"  Created {len(docs)} anomaly documents")

    # Add key comparisons
    print("\nAdding key comparisons...")
    comparison_docs = create_key_comparisons()
    all_docs.extend(comparison_docs)
    print(f"  Created {len(comparison_docs)} comparison documents")

    # Save all documents
    output_file = output_dir / "rag_documents.json"
    with open(output_file, 'w') as f:
        json.dump([asdict(doc) for doc in all_docs], f, indent=2)

    print(f"\n" + "=" * 60)
    print(f"COMPLETE!")
    print(f"Total documents: {len(all_docs)}")
    print(f"Output: {output_file}")
    print("=" * 60)

    # Print sample
    print("\nSample document:")
    print("-" * 40)
    if all_docs:
        sample = all_docs[0]
        print(f"ID: {sample.id}")
        print(f"Content:\n{sample.content[:500]}...")

if __name__ == "__main__":
    main()
