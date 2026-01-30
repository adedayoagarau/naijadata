#!/usr/bin/env python3
"""
Nigerian Budget Red Flag Scanner
Analyzes budget allocations for corruption indicators

Usage:
    python red_flag_scanner.py --item "International Travel" --amount 700M --mda "House of Assembly"
    python red_flag_scanner.py --item "Miscellaneous" --amount 500M --previous 100M
"""

import argparse
import json

# Benchmarks
BENCHMARKS = {
    "travel_state_assembly_max": 150_000_000,
    "travel_ministry_max": 500_000_000,
    "cost_per_state_legislator_max": 80_000_000,
    "misc_threshold": 100_000_000,
    "yoy_normal_max": 0.30,
    "yoy_flag": 1.00,
    "yoy_critical": 2.00,
}

VAGUE_TERMS = ["miscellaneous", "sundry", "other expenses", "contingency",
               "welfare", "stakeholder", "sensitization", "empowerment"]

def parse_amount(s):
    if isinstance(s, (int, float)): return int(s)
    s = str(s).upper().replace(",", "").replace("₦", "").strip()
    mult = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
    for suf, m in mult.items():
        if s.endswith(suf): return int(float(s[:-1]) * m)
    return int(float(s))

def format_naira(n):
    if n >= 1e12: return f"₦{n/1e12:.2f}T"
    if n >= 1e9: return f"₦{n/1e9:.2f}B"
    if n >= 1e6: return f"₦{n/1e6:.2f}M"
    return f"₦{n:,.0f}"

def scan(description, amount, mda="Unknown", mda_type="ministry", previous=0, legislators=0):
    """Scan a budget line item for red flags"""
    flags = []
    amount = parse_amount(amount)
    previous = parse_amount(previous) if previous else 0

    # Check vague description
    desc_lower = description.lower()
    for term in VAGUE_TERMS:
        if term in desc_lower:
            flags.append({
                "severity": "HIGH",
                "category": "Vague Description",
                "detail": f"Contains suspicious term: '{term}'",
                "action": "Request detailed breakdown"
            })
            break

    # Check travel amounts
    if any(t in desc_lower for t in ["travel", "transport", "trip", "tour"]):
        threshold = BENCHMARKS["travel_state_assembly_max"] if "assembly" in mda.lower() else BENCHMARKS["travel_ministry_max"]
        if amount > threshold * 3:
            flags.append({
                "severity": "CRITICAL",
                "category": "Excessive Travel",
                "detail": f"{format_naira(amount)} is 3x+ above benchmark ({format_naira(threshold)})",
                "action": "Investigate immediately"
            })
        elif amount > threshold * 2:
            flags.append({
                "severity": "HIGH",
                "category": "High Travel",
                "detail": f"{format_naira(amount)} is 2x above benchmark",
                "action": "Request justification"
            })
        elif amount > threshold:
            flags.append({
                "severity": "MEDIUM",
                "category": "Elevated Travel",
                "detail": f"{format_naira(amount)} exceeds benchmark",
                "action": "Monitor and compare"
            })

    # Check YoY change
    if previous > 0:
        change = (amount - previous) / previous
        if change > BENCHMARKS["yoy_critical"]:
            flags.append({
                "severity": "CRITICAL",
                "category": "Extreme YoY Increase",
                "detail": f"{change*100:.0f}% increase (from {format_naira(previous)})",
                "action": "Major red flag - investigate"
            })
        elif change > BENCHMARKS["yoy_flag"]:
            flags.append({
                "severity": "HIGH",
                "category": "High YoY Increase",
                "detail": f"{change*100:.0f}% increase",
                "action": "Request justification"
            })

    # Check miscellaneous threshold
    if "misc" in desc_lower and amount > BENCHMARKS["misc_threshold"]:
        flags.append({
            "severity": "HIGH",
            "category": "High Miscellaneous",
            "detail": f"{format_naira(amount)} exceeds ₦100M threshold",
            "action": "Request itemized breakdown"
        })

    # Check per-legislator cost
    if legislators > 0 and "assembl" in mda.lower():
        per_leg = amount / legislators
        if per_leg > BENCHMARKS["cost_per_state_legislator_max"] * 2:
            flags.append({
                "severity": "CRITICAL",
                "category": "Excessive Per-Legislator Cost",
                "detail": f"{format_naira(int(per_leg))}/legislator (2x+ above norm)",
                "action": "Systematic padding likely"
            })

    # Calculate risk score
    score_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    score = sum(score_map.get(f["severity"], 0) for f in flags)

    if score >= 10: level, color = "CRITICAL", "[!!!]"
    elif score >= 7: level, color = "HIGH", "[!!]"
    elif score >= 4: level, color = "MEDIUM", "[!]"
    else: level, color = "LOW", "[OK]"

    return {
        "item": description,
        "mda": mda,
        "amount": amount,
        "amount_fmt": format_naira(amount),
        "flags": flags,
        "risk_score": score,
        "risk_level": level,
        "risk_color": color
    }

def print_report(result):
    """Print human-readable report"""
    print("=" * 60)
    print("BUDGET LINE ITEM ANALYSIS")
    print("=" * 60)
    print(f"MDA: {result['mda']}")
    print(f"Item: {result['item']}")
    print(f"Amount: {result['amount_fmt']}")
    print(f"\nRisk: {result['risk_color']} {result['risk_level']} (Score: {result['risk_score']})")

    if result['flags']:
        print("\n[!] RED FLAGS:")
        print("-" * 40)
        for i, f in enumerate(result['flags'], 1):
            print(f"\n{i}. [{f['severity']}] {f['category']}")
            print(f"   {f['detail']}")
            print(f"   -> {f['action']}")
    else:
        print("\n[OK] No significant red flags")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nigerian Budget Red Flag Scanner")
    parser.add_argument("--item", "-i", required=True, help="Line item description")
    parser.add_argument("--amount", "-a", required=True, help="Amount")
    parser.add_argument("--mda", "-m", default="Unknown MDA", help="MDA name")
    parser.add_argument("--type", "-t", default="ministry", help="MDA type")
    parser.add_argument("--previous", "-p", default=0, help="Previous year amount")
    parser.add_argument("--legislators", "-l", type=int, default=0, help="Number of legislators")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")

    args = parser.parse_args()

    result = scan(
        args.item, args.amount, args.mda, args.type,
        args.previous, args.legislators
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)
