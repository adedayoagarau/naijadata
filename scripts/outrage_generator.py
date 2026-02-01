#!/usr/bin/env python3
"""
Outrage Generator - Find the most shareable budget findings

Surfaces findings that will resonate with Nigerians:
- Vehicle/convoy spending while people suffer
- Travel allowances exceeding common sense
- Luxury spending in wrong places
- Massive YoY increases
- Per-unit padding (₦180M Land Cruisers)
- What the money could have built instead

Output: JSON file ready for webapp display and social media sharing
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = BASE_DIR / "extracted"
OUTPUT_DIR = BASE_DIR / "findings"

# What Nigerian money can build (impact calculator)
IMPACT_BENCHMARKS = {
    "primary_school": {"cost": 150_000_000, "description": "Primary school (6 classrooms, 240 students)"},
    "health_center": {"cost": 150_000_000, "description": "Primary health center (10,000 people)"},
    "borehole": {"cost": 5_000_000, "description": "Borehole with pump (500 people)"},
    "ambulance": {"cost": 50_000_000, "description": "Fully equipped ambulance"},
    "road_km": {"cost": 150_000_000, "description": "1km paved road"},
    "affordable_house": {"cost": 15_000_000, "description": "Affordable 2-bedroom house"},
    "child_vaccination": {"cost": 15_000, "description": "Full childhood vaccination"},
    "malaria_treatment": {"cost": 5_000, "description": "Malaria treatment course"},
    "monthly_minimum_wage": {"cost": 70_000, "description": "Monthly minimum wage"},
    "yearly_minimum_wage": {"cost": 840_000, "description": "Annual minimum wage"},
    "university_scholarship": {"cost": 500_000, "description": "1-year university scholarship"},
}

# High-outrage budget codes
OUTRAGE_CODES = {
    "23010105": "Motor Vehicles (CONVOYS)",
    "22020801": "International Travel",
    "22020802": "Local Travel",
    "22020803": "Transport & Escort",
    "2205": "Consultancy Services",
    "22021000": "Miscellaneous Expenses",
    "22020901": "Honorarium & Sitting Allowances",
    "23030105": "Rehabilitation of Buildings",
}

# Market benchmarks for padding detection
VEHICLE_BENCHMARKS = {
    "land cruiser": 85_000_000,
    "prado": 65_000_000,
    "hilux": 45_000_000,
    "camry": 35_000_000,
    "hiace": 40_000_000,
    "coaster": 55_000_000,
    "mercedes": 150_000_000,
    "suv": 60_000_000,
    "vehicle": 50_000_000,  # Generic
}


def load_json(path: Path) -> Optional[dict]:
    """Load JSON file safely"""
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except Exception as e:
        print(f"Failed to load {path}: {e}")
    return None


def load_all_budget_items() -> List[dict]:
    """Load all budget items from various sources"""
    items = []

    # Try master file first
    master = load_json(DATA_DIR / "master" / "all_items.json")
    if master:
        if isinstance(master, list):
            items.extend(master)
        elif isinstance(master, dict) and "items" in master:
            items.extend(master["items"])

    # Try extracted master
    extracted = load_json(EXTRACTED_DIR / "master_budget_data.json")
    if extracted:
        if isinstance(extracted, list):
            items.extend(extracted)
        elif isinstance(extracted, dict) and "items" in extracted:
            items.extend(extracted["items"])

    # Try individual year files
    for year in range(2019, 2027):
        year_file = load_json(EXTRACTED_DIR / f"budget_{year}.json")
        if year_file:
            if isinstance(year_file, list):
                items.extend(year_file)
            elif isinstance(year_file, dict) and "items" in year_file:
                items.extend(year_file["items"])

    # Try federal year folders
    federal_dir = DATA_DIR / "federal"
    if federal_dir.exists():
        for year_dir in federal_dir.iterdir():
            if year_dir.is_dir():
                budget_file = load_json(year_dir / "budget_items.json")
                if budget_file:
                    if isinstance(budget_file, list):
                        items.extend(budget_file)
                    elif isinstance(budget_file, dict) and "items" in budget_file:
                        items.extend(budget_file["items"])

    print(f"Loaded {len(items)} total budget items")
    return items


def calculate_impact(amount: float) -> Dict[str, int]:
    """Calculate what the money could build instead"""
    impact = {}
    for key, bench in IMPACT_BENCHMARKS.items():
        count = int(amount / bench["cost"])
        if count > 0:
            impact[key] = {
                "count": count,
                "description": bench["description"],
                "total_value": count * bench["cost"]
            }
    return impact


def format_naira(amount: float) -> str:
    """Format amount in Naira with B/M/T suffixes"""
    if amount >= 1_000_000_000_000:
        return f"₦{amount/1_000_000_000_000:.2f}T"
    elif amount >= 1_000_000_000:
        return f"₦{amount/1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"₦{amount/1_000_000:.2f}M"
    else:
        return f"₦{amount:,.0f}"


def detect_vehicle_padding(item: dict) -> Optional[dict]:
    """Detect overpriced vehicle purchases"""
    desc = (item.get("description") or "").lower()
    amount = item.get("amount", 0)

    if not amount or amount < 10_000_000:
        return None

    # Check if it's a vehicle purchase
    budget_code = str(item.get("budget_code", ""))
    if not (budget_code.startswith("230101") or "vehicle" in desc or "motor" in desc):
        return None

    # Try to extract quantity
    import re
    qty_match = re.search(r'(\d+)\s*(?:units?|nos?|vehicles?)', desc)
    quantity = int(qty_match.group(1)) if qty_match else 1

    unit_cost = amount / quantity

    # Find matching benchmark
    for vehicle_type, benchmark in VEHICLE_BENCHMARKS.items():
        if vehicle_type in desc:
            if unit_cost > benchmark * 1.5:  # 50% over market
                padding_pct = ((unit_cost / benchmark) - 1) * 100
                return {
                    "type": "VEHICLE_PADDING",
                    "vehicle_type": vehicle_type.title(),
                    "quantity": quantity,
                    "unit_cost": unit_cost,
                    "market_price": benchmark,
                    "padding_percentage": padding_pct,
                    "excess_amount": (unit_cost - benchmark) * quantity,
                }

    return None


def aggregate_by_code(items: List[dict], year: int = 2026) -> Dict[str, dict]:
    """Aggregate spending by budget code for a specific year"""
    by_code = defaultdict(lambda: {"total": 0, "count": 0, "mdas": set(), "items": []})

    for item in items:
        if item.get("year") != year:
            continue

        code = str(item.get("budget_code", ""))[:8]
        amount = item.get("amount", 0)
        mda = item.get("mda", "Unknown")

        if code and amount:
            by_code[code]["total"] += amount
            by_code[code]["count"] += 1
            by_code[code]["mdas"].add(mda)
            by_code[code]["items"].append(item)

    # Convert sets to lists for JSON
    for code in by_code:
        by_code[code]["mdas"] = list(by_code[code]["mdas"])

    return dict(by_code)


def find_yoy_changes(items: List[dict]) -> List[dict]:
    """Find biggest year-over-year changes by MDA"""
    by_mda_year = defaultdict(lambda: defaultdict(float))

    for item in items:
        mda = item.get("mda", "Unknown")
        year = item.get("year")
        amount = item.get("amount", 0)

        if mda and year and amount:
            by_mda_year[mda][year] += amount

    changes = []
    for mda, years in by_mda_year.items():
        if 2025 in years and 2026 in years:
            old = years[2025]
            new = years[2026]
            if old > 100_000_000:  # Only significant amounts
                pct_change = ((new - old) / old) * 100
                if abs(pct_change) > 50:  # More than 50% change
                    changes.append({
                        "mda": mda,
                        "2025": old,
                        "2026": new,
                        "change_amount": new - old,
                        "change_percentage": pct_change,
                        "direction": "increase" if pct_change > 0 else "decrease"
                    })

    # Sort by absolute change percentage
    changes.sort(key=lambda x: abs(x["change_percentage"]), reverse=True)
    return changes


def generate_outrage_findings(items: List[dict]) -> List[dict]:
    """Generate the most shareable findings"""
    findings = []
    finding_id = 1

    # 1. Aggregate vehicle spending
    by_code = aggregate_by_code(items, 2026)

    # Find total vehicle spending
    vehicle_codes = ["23010105", "2301010"]
    total_vehicles = sum(
        by_code.get(code, {}).get("total", 0)
        for code in vehicle_codes
        if code in by_code
    )

    if total_vehicles > 1_000_000_000:
        vehicle_mdas = set()
        for code in vehicle_codes:
            if code in by_code:
                vehicle_mdas.update(by_code[code].get("mdas", []))

        impact = calculate_impact(total_vehicles)
        findings.append({
            "id": str(finding_id),
            "type": "CATEGORY_TOTAL",
            "category": "Vehicle Purchases (Convoys)",
            "entity": "Federal Government",
            "description": f"Total of {format_naira(total_vehicles)} allocated for vehicle purchases across {len(vehicle_mdas)} MDAs in 2026. This is enough to buy a fleet of luxury SUVs while Nigerians struggle with inflation and hunger.",
            "amount": total_vehicles,
            "severity": "CRITICAL",
            "year": 2026,
            "mda_count": len(vehicle_mdas),
            "impact": impact,
            "shareable_text": f"🚨 BREAKING: {format_naira(total_vehicles)} for government vehicles in 2026 Budget!\n\nThis could build {impact.get('primary_school', {}).get('count', 0)} schools or {impact.get('health_center', {}).get('count', 0)} health centers.\n\n#Decide9ja #OpenNASS",
            "risk_factors": ["CONVOY_SPENDING", "LUXURY_PURCHASES", "PUBLIC_OUTRAGE"]
        })
        finding_id += 1

    # 2. Travel allowances
    travel_codes = ["22020801", "22020802", "22020803"]
    total_travel = sum(
        by_code.get(code, {}).get("total", 0)
        for code in travel_codes
        if code in by_code
    )

    if total_travel > 5_000_000_000:
        impact = calculate_impact(total_travel)
        findings.append({
            "id": str(finding_id),
            "type": "CATEGORY_TOTAL",
            "category": "Travel Allowances",
            "entity": "Federal Government",
            "description": f"Total of {format_naira(total_travel)} allocated for travel (local and international) in 2026. That's {int(total_travel / 840_000):,} years of minimum wage.",
            "amount": total_travel,
            "severity": "CRITICAL" if total_travel > 20_000_000_000 else "HIGH",
            "year": 2026,
            "impact": impact,
            "shareable_text": f"🚨 {format_naira(total_travel)} for TRAVEL in 2026 Budget!\n\nWhile workers earn ₦70k/month, politicians travel in style.\n\nThis = {int(total_travel / 840_000):,} years of minimum wage!\n\n#Decide9ja",
            "risk_factors": ["TRAVEL_ABUSE", "INEQUALITY", "PUBLIC_OUTRAGE"]
        })
        finding_id += 1

    # 3. Miscellaneous/slush funds
    misc_total = by_code.get("22021000", {}).get("total", 0)
    if misc_total > 1_000_000_000:
        impact = calculate_impact(misc_total)
        findings.append({
            "id": str(finding_id),
            "type": "VAGUE_ALLOCATION",
            "category": "Miscellaneous Expenses",
            "entity": "Federal Government",
            "description": f"{format_naira(misc_total)} allocated to 'Miscellaneous Expenses' - a vague category with zero accountability. What exactly is this money for?",
            "amount": misc_total,
            "severity": "HIGH",
            "year": 2026,
            "impact": impact,
            "shareable_text": f"🚨 {format_naira(misc_total)} for 'MISCELLANEOUS' in 2026 Budget!\n\nNo details. No accountability. Just vibes.\n\nDemand transparency! #Decide9ja",
            "risk_factors": ["SLUSH_FUND", "NO_ACCOUNTABILITY", "OPACITY"]
        })
        finding_id += 1

    # 4. Find YoY spikes
    yoy_changes = find_yoy_changes(items)
    for change in yoy_changes[:10]:  # Top 10 increases
        if change["change_percentage"] > 100:  # More than doubled
            impact = calculate_impact(change["change_amount"])
            findings.append({
                "id": str(finding_id),
                "type": "YOY_SPIKE",
                "category": "Year-over-Year Increase",
                "entity": change["mda"],
                "description": f"{change['mda']} budget increased by {change['change_percentage']:.0f}% from {format_naira(change['2025'])} to {format_naira(change['2026'])}. An increase of {format_naira(change['change_amount'])}.",
                "amount": change["2026"],
                "amount_2025": change["2025"],
                "change_amount": change["change_amount"],
                "change_percentage": change["change_percentage"],
                "severity": "CRITICAL" if change["change_percentage"] > 200 else "HIGH",
                "year": 2026,
                "impact": impact,
                "shareable_text": f"🚨 {change['mda']}: {change['change_percentage']:.0f}% BUDGET INCREASE!\n\n2025: {format_naira(change['2025'])}\n2026: {format_naira(change['2026'])}\n\nWhy the spike? #Decide9ja",
                "risk_factors": ["EXTREME_INCREASE", "NEEDS_JUSTIFICATION"]
            })
            finding_id += 1

    # 5. Detect vehicle padding
    for item in items:
        if item.get("year") != 2026:
            continue

        padding = detect_vehicle_padding(item)
        if padding and padding["padding_percentage"] > 100:
            impact = calculate_impact(padding["excess_amount"])
            findings.append({
                "id": str(finding_id),
                "type": "PADDING_DETECTED",
                "category": "Price Inflation",
                "entity": item.get("mda", "Unknown MDA"),
                "description": f"{padding['vehicle_type']} budgeted at {format_naira(padding['unit_cost'])} per unit - {padding['padding_percentage']:.0f}% above market price of {format_naira(padding['market_price'])}. Quantity: {padding['quantity']}.",
                "amount": item.get("amount", 0),
                "unit_cost": padding["unit_cost"],
                "market_price": padding["market_price"],
                "padding_percentage": padding["padding_percentage"],
                "excess_amount": padding["excess_amount"],
                "severity": "CRITICAL",
                "year": 2026,
                "impact": impact,
                "shareable_text": f"🚨 PADDING ALERT: {padding['vehicle_type']} at {format_naira(padding['unit_cost'])}!\n\nMarket price: {format_naira(padding['market_price'])}\nOverprice: {padding['padding_percentage']:.0f}%\n\n#Decide9ja #BudgetPadding",
                "risk_factors": ["PRICE_INFLATION", "PROCUREMENT_FRAUD"]
            })
            finding_id += 1

    # 6. Find luxury spending in wrong places (universities, health, etc.)
    for code in ["23010105"]:  # Vehicle purchases
        if code not in by_code:
            continue

        for item in by_code[code].get("items", []):
            mda = (item.get("mda") or "").lower()
            amount = item.get("amount", 0)

            # Universities shouldn't be buying expensive vehicles
            if ("university" in mda or "polytechnic" in mda) and amount > 500_000_000:
                impact = calculate_impact(amount)
                findings.append({
                    "id": str(finding_id),
                    "type": "MISPLACED_LUXURY",
                    "category": "Luxury in Education",
                    "entity": item.get("mda", "Unknown"),
                    "description": f"Educational institution allocated {format_naira(amount)} for vehicles. Shouldn't this money go to laboratories, libraries, and scholarships?",
                    "amount": amount,
                    "severity": "HIGH",
                    "year": 2026,
                    "impact": impact,
                    "shareable_text": f"🚨 {format_naira(amount)} for VEHICLES at a university!\n\nMeanwhile: No labs, no books, students sitting on floors.\n\nPriorities? #Decide9ja",
                    "risk_factors": ["MISPLACED_PRIORITY", "EDUCATION_NEGLECT"]
                })
                finding_id += 1

    # Sort by amount (biggest scandals first)
    findings.sort(key=lambda x: x.get("amount", 0), reverse=True)

    return findings


def main():
    print("=" * 60)
    print("OUTRAGE GENERATOR - Finding Shareable Budget Scandals")
    print("=" * 60)

    # Load all data
    items = load_all_budget_items()

    if not items:
        print("ERROR: No budget items found!")
        print("Make sure data exists in:")
        print("  - data/master/all_items.json")
        print("  - extracted/master_budget_data.json")
        print("  - data/federal/*/budget_items.json")
        return

    # Generate findings
    findings = generate_outrage_findings(items)

    print(f"\nGenerated {len(findings)} outrage-worthy findings")

    # Summary
    print("\n" + "=" * 60)
    print("TOP FINDINGS FOR SOCIAL MEDIA:")
    print("=" * 60)

    for i, finding in enumerate(findings[:10], 1):
        print(f"\n{i}. [{finding['severity']}] {finding['category']}")
        print(f"   {finding['entity']}: {format_naira(finding['amount'])}")
        print(f"   {finding['description'][:100]}...")

    # Save output
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "outrage_findings.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "total_items_analyzed": len(items),
        "findings_count": len(findings),
        "findings": findings
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Saved to {output_file}")

    # Also save shareable text file
    shareable_file = OUTPUT_DIR / "shareable_posts.txt"
    with open(shareable_file, "w") as f:
        f.write("DECIDE9JA - SHAREABLE BUDGET FINDINGS\n")
        f.write("=" * 50 + "\n\n")
        for finding in findings:
            if "shareable_text" in finding:
                f.write(finding["shareable_text"])
                f.write("\n\n" + "-" * 50 + "\n\n")

    print(f"✅ Shareable posts saved to {shareable_file}")


if __name__ == "__main__":
    main()
