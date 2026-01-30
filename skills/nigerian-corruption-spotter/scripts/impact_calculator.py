#!/usr/bin/env python3
"""
Nigerian Corruption Impact Calculator
Converts naira amounts into tangible impact metrics

Usage:
    python impact_calculator.py 400B
    python impact_calculator.py 1.3B --state osun
    python impact_calculator.py 700M --json
"""

import sys
import json
import argparse

# Infrastructure costs (2024-2025 Naira)
INFRA = {
    "primary_school": (150_000_000, 240, "students educated"),
    "secondary_school": (450_000_000, 720, "students educated"),
    "primary_health_center": (150_000_000, 10_000, "people covered"),
    "general_hospital": (2_000_000_000, 100_000, "people served"),
    "borehole": (5_000_000, 500, "people with water"),
    "road_km_paved": (150_000_000, 5, "communities connected"),
    "road_km_rural": (50_000_000, 3, "communities connected"),
    "affordable_house": (15_000_000, 5, "people housed"),
    "ambulance": (50_000_000, 0, ""),
    "computer_lab": (15_000_000, 20, "students per lab"),
}

# Service costs per person (Naira)
SERVICES = {
    "vaccination_full": (15_000, "children vaccinated"),
    "malaria_treatment": (5_000, "malaria treatments"),
    "maternal_care": (50_000, "safe deliveries"),
    "primary_education_year": (100_000, "children educated (1yr)"),
    "school_feeding_year": (50_000, "school meals (1yr)"),
    "cash_transfer_year": (60_000, "cash transfers (1yr)"),
    "npower_job_year": (360_000, "N-Power jobs (1yr)"),
}

# State populations (millions, 2024 est)
POPULATIONS = {
    "abia": 3.7, "adamawa": 4.2, "akwa_ibom": 5.5, "anambra": 5.5,
    "bauchi": 6.5, "bayelsa": 2.3, "benue": 5.7, "borno": 5.9,
    "cross_river": 3.9, "delta": 5.7, "ebonyi": 2.9, "edo": 4.2,
    "ekiti": 3.3, "enugu": 4.4, "fct": 4.0, "gombe": 3.3,
    "imo": 5.4, "jigawa": 5.8, "kaduna": 8.3, "kano": 13.1,
    "katsina": 7.8, "kebbi": 4.4, "kogi": 4.5, "kwara": 3.2,
    "lagos": 15.4, "nasarawa": 2.5, "niger": 5.6, "ogun": 5.2,
    "ondo": 4.7, "osun": 4.7, "oyo": 8.0, "plateau": 4.2,
    "rivers": 7.3, "sokoto": 4.9, "taraba": 3.1, "yobe": 3.3,
    "zamfara": 4.5, "nigeria": 220.0
}

def parse_amount(s):
    """Parse '400B', '1.3T', '500M' into integer naira"""
    s = str(s).upper().replace(",", "").replace("₦", "").replace("N", "").strip()
    multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
    for suffix, mult in multipliers.items():
        if s.endswith(suffix):
            return int(float(s[:-1]) * mult)
    return int(float(s))

def format_naira(n):
    """Format as readable naira"""
    if n >= 1e12: return f"₦{n/1e12:.2f}T"
    if n >= 1e9: return f"₦{n/1e9:.2f}B"
    if n >= 1e6: return f"₦{n/1e6:.2f}M"
    return f"₦{n:,.0f}"

def calculate(amount, state=None):
    """Calculate impact metrics"""
    result = {
        "amount": amount,
        "amount_formatted": format_naira(amount),
        "infrastructure": {},
        "services": {},
    }

    for name, (cost, capacity, desc) in INFRA.items():
        count = amount // cost
        result["infrastructure"][name] = {
            "count": int(count),
            "impact": int(count * capacity) if capacity else 0,
            "impact_desc": desc
        }

    for name, (cost, desc) in SERVICES.items():
        result["services"][name] = {
            "beneficiaries": int(amount // cost),
            "desc": desc
        }

    if state and state.lower() in POPULATIONS:
        pop = POPULATIONS[state.lower()] * 1_000_000
        result["per_capita"] = {
            "state": state,
            "population": int(pop),
            "per_person": round(amount / pop, 2),
            "min_wage_equivalent": round((amount / pop) / 70_000, 2)
        }

    return result

def print_report(amount, state=None, context=""):
    """Print human-readable report"""
    r = calculate(amount, state)

    print("=" * 60)
    print(f"CORRUPTION IMPACT ANALYSIS")
    print(f"   Amount: {r['amount_formatted']}")
    if context:
        print(f"   Context: {context}")
    print("=" * 60)

    print("\nINFRASTRUCTURE THIS COULD BUILD:")
    print("-" * 40)
    inf = r["infrastructure"]
    print(f"  {inf['primary_school']['count']:,} primary schools ({inf['primary_school']['impact']:,} children)")
    print(f"  {inf['primary_health_center']['count']:,} health centers ({inf['primary_health_center']['impact']:,} people)")
    print(f"  {inf['borehole']['count']:,} boreholes ({inf['borehole']['impact']:,} with water)")
    print(f"  {inf['road_km_paved']['count']:,} km paved roads")
    print(f"  {inf['affordable_house']['count']:,} houses ({inf['affordable_house']['impact']:,} housed)")
    print(f"  {inf['ambulance']['count']:,} ambulances")

    print("\nSERVICES THIS COULD PROVIDE:")
    print("-" * 40)
    svc = r["services"]
    print(f"  {svc['vaccination_full']['beneficiaries']:,} children vaccinated")
    print(f"  {svc['malaria_treatment']['beneficiaries']:,} malaria treatments")
    print(f"  {svc['maternal_care']['beneficiaries']:,} safe deliveries")
    print(f"  {svc['primary_education_year']['beneficiaries']:,} children educated (1yr)")
    print(f"  {svc['school_feeding_year']['beneficiaries']:,} school meals (1yr)")
    print(f"  {svc['cash_transfer_year']['beneficiaries']:,} cash transfers (1yr)")
    print(f"  {svc['npower_job_year']['beneficiaries']:,} N-Power jobs (1yr)")

    if "per_capita" in r:
        pc = r["per_capita"]
        print(f"\nSTATE IMPACT ({pc['state'].upper()}):")
        print("-" * 40)
        print(f"  Population: {pc['population']/1e6:.1f} million")
        print(f"  Per citizen: ₦{pc['per_person']:,.0f}")
        print(f"  = {pc['min_wage_equivalent']:.1f} months minimum wage each")

    print("\n" + "=" * 60)
    print("Source: Nigerian Corruption Spotter - Decide9ja")

def print_social(amount, item1, amount2, item2, state=""):
    """Generate social media card"""
    r = calculate(amount)
    ratio = amount / amount2 if amount2 > 0 else 0

    print(f"[ALERT] {state.upper() + ' ' if state else ''}BUDGET SPOTLIGHT\n")
    print(f"Legislature {item1}: {format_naira(amount)}")
    print(f"Health {item2}: {format_naira(amount2)}\n")
    print(f"That's {ratio:.0f}x MORE!\n")
    print(f"{format_naira(amount)} could have built:")
    print(f"* {r['infrastructure']['primary_school']['count']:,} schools")
    print(f"* {r['infrastructure']['primary_health_center']['count']:,} health centers")
    print(f"* {r['infrastructure']['borehole']['count']:,} boreholes\n")
    print("#Decide9ja #OpenBudget #Accountability")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nigerian Corruption Impact Calculator")
    parser.add_argument("amount", nargs="?", default="1B", help="Amount (e.g., 400B, 1.3T)")
    parser.add_argument("--state", "-s", help="State for per-capita")
    parser.add_argument("--context", "-c", default="", help="Context description")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--social", action="store_true", help="Social media card")
    parser.add_argument("--compare", help="Comparison amount for social card")
    parser.add_argument("--item1", default="Item A", help="First item name")
    parser.add_argument("--item2", default="Item B", help="Second item name")

    args = parser.parse_args()
    amount = parse_amount(args.amount)

    if args.json:
        print(json.dumps(calculate(amount, args.state), indent=2))
    elif args.social and args.compare:
        print_social(amount, args.item1, parse_amount(args.compare), args.item2, args.state or "")
    else:
        print_report(amount, args.state, args.context)
