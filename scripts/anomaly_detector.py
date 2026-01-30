#!/usr/bin/env python3
"""
Cross-MDA Anomaly Detector
Finds suspicious spending patterns - agencies spending outside their mandate

Red Flags:
- Security agencies building schools/hospitals
- Non-health MDAs with large medical budgets
- Non-works MDAs with major construction
- Duplicate projects across MDAs
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

import pdfplumber
from tqdm import tqdm

# MDA categories and what they SHOULD be spending on
MDA_MANDATES = {
    "security": {
        "codes": ["0111", "0116", "0124", "0305"],  # Presidency security, Defence, Interior, Police
        "names": ["defence", "police", "security", "civil defence", "immigration", "customs", "prison", "correctional"],
        "allowed": ["security", "arms", "ammunition", "uniform", "barracks"],
        "suspicious": ["school", "hospital", "health centre", "education", "borehole", "water"]
    },
    "legislature": {
        "codes": ["0112", "0113"],
        "names": ["assembly", "senate", "house of rep", "judicial"],
        "allowed": ["legislative", "sitting", "committee"],
        "suspicious": ["hospital", "school", "road", "borehole", "construction"]
    },
    "executive": {
        "codes": ["0111"],
        "names": ["presidency", "state house", "governor"],
        "allowed": ["protocol", "security", "travel"],
        "suspicious": ["school", "hospital", "borehole"]
    }
}

# Line items that should only appear in specific MDAs
RESTRICTED_ITEMS = {
    "hospital": ["health", "medical"],
    "health centre": ["health", "medical", "primary health"],
    "school": ["education", "ubec", "universal basic"],
    "classroom": ["education"],
    "drugs": ["health", "medical", "pharmaceutical"],
    "borehole": ["water", "rural development", "works"],
    "road": ["works", "transport", "highway"],
}


@dataclass
class Anomaly:
    mda_code: str
    mda_name: str
    line_item: str
    amount: float
    page: int
    reason: str
    severity: str  # HIGH, MEDIUM, LOW


def format_naira(n: float) -> str:
    if n >= 1e12: return f"₦{n/1e12:.2f}T"
    if n >= 1e9: return f"₦{n/1e9:.2f}B"
    if n >= 1e6: return f"₦{n/1e6:.2f}M"
    return f"₦{n:,.0f}"


def parse_amount(text: str) -> float:
    if not text: return 0.0
    cleaned = re.sub(r'[₦N,\s]', '', str(text))
    try:
        return float(cleaned)
    except:
        return 0.0


def get_mda_category(mda_name: str) -> str:
    """Determine what category an MDA belongs to."""
    name_lower = mda_name.lower()
    for category, rules in MDA_MANDATES.items():
        for term in rules["names"]:
            if term in name_lower:
                return category
    return "other"


def is_suspicious_for_mda(mda_name: str, line_item: str) -> tuple:
    """Check if a line item is suspicious for this MDA."""
    mda_lower = mda_name.lower()
    item_lower = line_item.lower()

    # Check restricted items
    for restricted_term, allowed_mdas in RESTRICTED_ITEMS.items():
        if restricted_term in item_lower:
            # Check if MDA is allowed to have this
            mda_allowed = any(allowed in mda_lower for allowed in allowed_mdas)
            if not mda_allowed:
                return True, f"'{restricted_term}' should be under {', '.join(allowed_mdas)}"

    # Check MDA-specific rules
    for category, rules in MDA_MANDATES.items():
        if any(term in mda_lower for term in rules["names"]):
            for suspicious_term in rules["suspicious"]:
                if suspicious_term in item_lower:
                    return True, f"{category.upper()} agency with '{suspicious_term}' expenditure"

    return False, ""


def scan_for_anomalies(pdf_path: Path, max_pages: int = None) -> list:
    """Scan entire budget for cross-MDA anomalies."""
    anomalies = []
    current_mda_code = ""
    current_mda_name = ""

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = max_pages or len(pdf.pages)
        print(f"Scanning {total_pages} pages for anomalies...")

        for i in tqdm(range(total_pages), desc="Scanning"):
            page = pdf.pages[i]
            text = page.extract_text() or ""

            # Detect MDA header (e.g., "0124004001 NIGERIA SECURITY AND CIVIL DEFENCE CORPS")
            mda_match = re.search(r'(0\d{9})\s+([A-Z][A-Z\s\-&]+)', text)
            if mda_match:
                current_mda_code = mda_match.group(1)
                current_mda_name = mda_match.group(2).strip()

            # Also check for shorter MDA codes
            mda_short = re.search(r'\n(0\d{3})\s+([A-Z][A-Z\s\-&]+(?:MINISTRY|AGENCY|COMMISSION|CORPS|COUNCIL))', text)
            if mda_short:
                current_mda_code = mda_short.group(1)
                current_mda_name = mda_short.group(2).strip()

            # Scan line items
            for line in text.split('\n'):
                # Match: CODE DESCRIPTION AMOUNT
                match = re.match(r'(\d{8})\s+(.+?)\s+([\d,]+(?:\.\d+)?)\s*$', line.strip())
                if match:
                    code = match.group(1)
                    description = match.group(2).strip()
                    amount = parse_amount(match.group(3))

                    # Check if suspicious
                    is_sus, reason = is_suspicious_for_mda(current_mda_name, description)

                    if is_sus and amount > 50_000_000:  # Only flag if > ₦50M
                        severity = "HIGH" if amount > 500_000_000 else "MEDIUM" if amount > 100_000_000 else "LOW"

                        anomalies.append(Anomaly(
                            mda_code=current_mda_code,
                            mda_name=current_mda_name,
                            line_item=description,
                            amount=amount,
                            page=i + 1,
                            reason=reason,
                            severity=severity
                        ))

    return anomalies


def print_report(anomalies: list):
    """Print anomaly report."""
    print("\n" + "=" * 70)
    print("CROSS-MDA ANOMALY REPORT")
    print("=" * 70)

    # Sort by severity and amount
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sorted_anomalies = sorted(anomalies, key=lambda x: (severity_order[x.severity], -x.amount))

    # Summary
    high = len([a for a in anomalies if a.severity == "HIGH"])
    medium = len([a for a in anomalies if a.severity == "MEDIUM"])
    low = len([a for a in anomalies if a.severity == "LOW"])
    total_amount = sum(a.amount for a in anomalies)

    print(f"\nTotal Anomalies: {len(anomalies)}")
    print(f"  HIGH: {high} | MEDIUM: {medium} | LOW: {low}")
    print(f"  Total Amount Flagged: {format_naira(total_amount)}")

    # Group by MDA
    by_mda = defaultdict(list)
    for a in sorted_anomalies:
        by_mda[a.mda_name].append(a)

    print("\n" + "-" * 70)
    print("ANOMALIES BY MDA")
    print("-" * 70)

    for mda_name, mda_anomalies in sorted(by_mda.items(), key=lambda x: -sum(a.amount for a in x[1])):
        mda_total = sum(a.amount for a in mda_anomalies)
        print(f"\n[{mda_anomalies[0].severity}] {mda_name}")
        print(f"    Total flagged: {format_naira(mda_total)}")

        for a in mda_anomalies[:5]:  # Top 5 per MDA
            print(f"    - {a.line_item[:45]:<45} {format_naira(a.amount):>12}")
            print(f"      Reason: {a.reason}")
            print(f"      Page: {a.page}")

    # Top 10 overall
    print("\n" + "-" * 70)
    print("TOP 10 LARGEST ANOMALIES")
    print("-" * 70)

    for i, a in enumerate(sorted_anomalies[:10], 1):
        print(f"\n{i}. [{a.severity}] {format_naira(a.amount)}")
        print(f"   MDA: {a.mda_name}")
        print(f"   Item: {a.line_item}")
        print(f"   Why flagged: {a.reason}")
        print(f"   Page: {a.page}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 anomaly_detector.py <pdf_path> [max_pages]")
        print("\nExample:")
        print("  python3 anomaly_detector.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf")
        print("  python3 anomaly_detector.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf 500")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    anomalies = scan_for_anomalies(pdf_path, max_pages)
    print_report(anomalies)

    # Save to JSON
    import json
    output = {
        "source": pdf_path.name,
        "total_anomalies": len(anomalies),
        "total_flagged_amount": sum(a.amount for a in anomalies),
        "anomalies": [
            {
                "mda": a.mda_name,
                "item": a.line_item,
                "amount": a.amount,
                "reason": a.reason,
                "severity": a.severity,
                "page": a.page
            }
            for a in anomalies
        ]
    }

    output_path = Path("extracted") / f"{pdf_path.stem}_anomalies.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
