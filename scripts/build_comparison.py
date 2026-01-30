#!/usr/bin/env python3
"""
Build comparison database from extracted budget data.

This script aggregates extracted budget data and generates comparison
metrics for the Decide9ja accountability tool.
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class StateComparison:
    """Comparison data for a single state."""
    state: str
    year: int
    total_budget: float
    population: int

    # Legislature
    legislature_total: float = 0
    legislature_travel: float = 0
    legislature_sitting: float = 0
    legislature_vehicles: float = 0
    legislators_count: int = 0
    cost_per_legislator: float = 0

    # Health
    health_total: float = 0
    health_drugs: float = 0
    health_per_capita: float = 0
    health_percent: float = 0

    # Education
    education_total: float = 0
    education_percent: float = 0
    education_per_capita: float = 0

    # Red flags
    travel_vs_drugs_ratio: float = 0
    flags: list = None


def load_extracted_data(filepath: Path) -> dict:
    """Load extracted budget JSON."""
    with open(filepath) as f:
        return json.load(f)


def calculate_comparison(data: dict) -> StateComparison:
    """Calculate comparison metrics from extracted data."""
    comp = StateComparison(
        state=data.get("source", "unknown"),
        year=data.get("year", 0),
        total_budget=data.get("total_budget", 0),
        population=data.get("population", 1),
        legislators_count=data.get("legislators_count", 0)
    )

    # Find key MDAs
    for mda in data.get("mdas", []):
        category = mda.get("category", "")

        if category == "legislature":
            comp.legislature_total = mda.get("total", 0)
            for item in mda.get("line_items", []):
                code = item.get("code", "")
                amount = item.get("amount", 0)
                if "22020801" in code:  # International travel
                    comp.legislature_travel += amount
                elif "22020802" in code:  # Sitting allowances
                    comp.legislature_sitting += amount
                elif "23010105" in code:  # Vehicles
                    comp.legislature_vehicles += amount

        elif category == "health":
            comp.health_total = mda.get("total", 0)
            for item in mda.get("line_items", []):
                if "22020901" in item.get("code", ""):
                    comp.health_drugs = item.get("amount", 0)

        elif category == "education":
            comp.education_total = mda.get("total", 0)

    # Calculate derived metrics
    if comp.legislators_count > 0:
        comp.cost_per_legislator = comp.legislature_total / comp.legislators_count

    if comp.population > 0:
        comp.health_per_capita = comp.health_total / comp.population
        comp.education_per_capita = comp.education_total / comp.population

    if comp.total_budget > 0:
        comp.health_percent = (comp.health_total / comp.total_budget) * 100
        comp.education_percent = (comp.education_total / comp.total_budget) * 100

    if comp.health_drugs > 0:
        comp.travel_vs_drugs_ratio = comp.legislature_travel / comp.health_drugs

    # Generate flags
    comp.flags = []
    if comp.travel_vs_drugs_ratio > 1:
        comp.flags.append({
            "type": "ratio_alert",
            "message": f"Legislature travel ({comp.legislature_travel:,.0f}) exceeds Health drugs ({comp.health_drugs:,.0f})",
            "ratio": round(comp.travel_vs_drugs_ratio, 1),
            "severity": "high" if comp.travel_vs_drugs_ratio > 3 else "medium"
        })

    if comp.cost_per_legislator > 100_000_000:  # Over 100M per legislator
        comp.flags.append({
            "type": "high_cost",
            "message": f"Cost per legislator is ₦{comp.cost_per_legislator:,.0f}",
            "severity": "high"
        })

    return comp


def generate_rankings(comparisons: list) -> dict:
    """Generate state rankings across different metrics."""
    rankings = {
        "education_percent": sorted(comparisons, key=lambda x: x.education_percent, reverse=True),
        "health_percent": sorted(comparisons, key=lambda x: x.health_percent, reverse=True),
        "cost_per_legislator": sorted(comparisons, key=lambda x: x.cost_per_legislator, reverse=True),
        "travel_vs_drugs": sorted(comparisons, key=lambda x: x.travel_vs_drugs_ratio, reverse=True),
    }

    return {
        metric: [{"rank": i+1, "state": c.state, "value": getattr(c, metric.replace("_ranking", ""))}
                 for i, c in enumerate(sorted_list)]
        for metric, sorted_list in rankings.items()
    }


def build_database(extracted_dir: Path) -> dict:
    """Build complete comparison database from all extracted files."""
    comparisons = []

    for filepath in extracted_dir.glob("*_extracted.json"):
        print(f"Processing: {filepath.name}")
        data = load_extracted_data(filepath)
        comp = calculate_comparison(data)
        comparisons.append(comp)

    # Generate rankings
    rankings = generate_rankings(comparisons) if comparisons else {}

    return {
        "states": [asdict(c) for c in comparisons],
        "rankings": rankings,
        "summary": {
            "total_states": len(comparisons),
            "total_budget_all": sum(c.total_budget for c in comparisons),
            "avg_education_percent": sum(c.education_percent for c in comparisons) / len(comparisons) if comparisons else 0,
            "avg_health_percent": sum(c.health_percent for c in comparisons) / len(comparisons) if comparisons else 0,
        }
    }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Build budget comparison database")
    parser.add_argument("--input", type=Path, default=Path("extracted"),
                        help="Directory with extracted JSON files")
    parser.add_argument("--output", type=Path, default=Path("output/comparison_database.json"),
                        help="Output file path")
    args = parser.parse_args()

    print("🔄 Building comparison database...")

    # Ensure directories exist
    args.output.parent.mkdir(parents=True, exist_ok=True)

    database = build_database(args.input)

    with open(args.output, 'w') as f:
        json.dump(database, f, indent=2, default=str)

    print(f"✅ Database saved to: {args.output}")
    print(f"   States processed: {database['summary']['total_states']}")


if __name__ == "__main__":
    main()
