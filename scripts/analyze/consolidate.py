#!/usr/bin/env python3
"""
Consolidate all findings into a single source of truth.

This script:
1. Reads all finding files (webapp_curated, webapp_consolidated, etc.)
2. Deduplicates based on entity + description + amount
3. Normalizes to canonical schema
4. Outputs to findings/consolidated.json

Run: python scripts/analyze/consolidate.py
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
FINDINGS_DIR = BASE_DIR / "findings"
OUTPUT_FILE = FINDINGS_DIR / "consolidated.json"
ARCHIVE_DIR = FINDINGS_DIR / "archive"

# Valid severity levels
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

# Valid finding types
VALID_TYPES = {
    "MANDATE_VIOLATION",
    "YOY_VARIANCE",
    "YOY_SPIKE",
    "ROUND_NUMBER",
    "CROSS_MDA_OUTLIER",
    "PADDING_INDICATOR",
    "BENFORD_VIOLATION",
    "DUPLICATE_ALLOCATION",
    "CATEGORY_TOTAL",
    "VAGUE_ALLOCATION",
    "MISPLACED_LUXURY",
    "ELECTION_YEAR_SPIKE",
    "STATE_COMPARISON",
    "EDUCATION_ALLOCATION",
    "HEALTH_ALLOCATION",
    "VEHICLE_PADDING",
    "TRAVEL_ABUSE",
}


def load_json(path: Path) -> Optional[dict]:
    """Load JSON file safely"""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"  Error loading {path.name}: {e}")
    return None


def extract_findings(data) -> List[dict]:
    """Extract findings from various data structures"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Try common keys
        for key in ["findings", "items", "data", "records"]:
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def generate_id(finding: dict) -> str:
    """Generate a unique ID based on finding content"""
    content = f"{finding.get('entity', '')}-{finding.get('amount', 0)}-{finding.get('year', 0)}"
    return hashlib.md5(content.encode()).hexdigest()[:8]


def normalize_finding(finding: dict, index: int) -> Optional[dict]:
    """Normalize a finding to canonical schema"""
    # Extract required fields
    entity = finding.get("entity") or finding.get("mda") or finding.get("name")
    description = finding.get("description") or finding.get("desc") or ""
    amount = finding.get("amount") or finding.get("total") or 0
    severity = (finding.get("severity") or "MEDIUM").upper()
    year = finding.get("year") or 2026
    finding_type = finding.get("type") or finding.get("finding_type") or "UNKNOWN"

    # Validate required fields
    if not entity:
        return None
    if not isinstance(amount, (int, float)) or amount <= 0:
        return None

    # Normalize severity
    if severity not in VALID_SEVERITIES:
        severity = "MEDIUM"

    # Normalize type
    finding_type = finding_type.upper().replace(" ", "_")
    if finding_type not in VALID_TYPES:
        finding_type = "UNKNOWN"

    # Build normalized finding
    normalized = {
        "id": finding.get("id") or generate_id(finding),
        "type": finding_type,
        "entity": entity.strip(),
        "description": description.strip(),
        "amount": int(amount),
        "severity": severity,
        "year": int(year),
    }

    # Add optional fields if present
    optional_fields = [
        "state", "budget_code", "recommendation", "risk_score",
        "risk_factors", "change_percentage", "amount_2025",
        "shareable_text", "impact", "mda_count", "category"
    ]
    for field in optional_fields:
        if field in finding and finding[field]:
            normalized[field] = finding[field]

    return normalized


def deduplicate_findings(findings: List[dict]) -> List[dict]:
    """Remove duplicate findings based on entity + amount + year"""
    seen: Set[str] = set()
    unique = []

    for finding in findings:
        # Create dedup key
        key = f"{finding['entity'].lower()}-{finding['amount']}-{finding['year']}"
        if key not in seen:
            seen.add(key)
            unique.append(finding)

    return unique


def archive_current(output_file: Path, archive_dir: Path):
    """Archive current consolidated file if it exists"""
    if output_file.exists():
        archive_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        archive_path = archive_dir / f"{timestamp}_consolidated.json"
        output_file.rename(archive_path)
        print(f"  Archived previous file to: {archive_path.name}")


def main():
    print("=" * 60)
    print("FINDINGS CONSOLIDATOR")
    print("=" * 60)
    print(f"Source: {FINDINGS_DIR}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    # Collect all findings
    all_findings = []
    source_files = []

    # Define files to process in priority order
    finding_files = [
        "webapp_curated_findings.json",
        "webapp_consolidated.json",
        "webapp_findings.json",
        "outrage_findings.json",
        "all_scored.json",
        "all_findings.json",
    ]

    print("Loading finding files...")
    for filename in finding_files:
        filepath = FINDINGS_DIR / filename
        if filepath.exists():
            print(f"  Reading: {filename}")
            data = load_json(filepath)
            if data:
                findings = extract_findings(data)
                if findings:
                    print(f"    Found {len(findings)} findings")
                    all_findings.extend(findings)
                    source_files.append(filename)

    if not all_findings:
        print("\nERROR: No findings found!")
        print("Make sure finding files exist in:", FINDINGS_DIR)
        return

    print(f"\nTotal raw findings: {len(all_findings)}")

    # Normalize all findings
    print("\nNormalizing findings...")
    normalized = []
    skipped = 0
    for i, finding in enumerate(all_findings):
        norm = normalize_finding(finding, i)
        if norm:
            normalized.append(norm)
        else:
            skipped += 1

    print(f"  Normalized: {len(normalized)}")
    print(f"  Skipped (invalid): {skipped}")

    # Deduplicate
    print("\nDeduplicating...")
    unique = deduplicate_findings(normalized)
    print(f"  Unique findings: {len(unique)}")
    print(f"  Duplicates removed: {len(normalized) - len(unique)}")

    # Add jurisdiction field and ensure no "Unknown" entities
    print("\nCategorizing by jurisdiction...")
    for finding in unique:
        # Set jurisdiction: State name or "Federal"
        finding["jurisdiction"] = finding.get("state") or "Federal"

        # Ensure entity is never empty or "Unknown"
        if not finding.get("entity") or finding["entity"].lower() == "unknown":
            if finding.get("state"):
                finding["entity"] = f"{finding['state']} Budget Item"
            else:
                finding["entity"] = finding.get("type", "").replace("_", " ").title() or "Federal Budget Item"

        # Add category based on type
        type_to_category = {
            "MANDATE_VIOLATION": "Governance",
            "YOY_VARIANCE": "Year-over-Year",
            "YOY_SPIKE": "Year-over-Year",
            "ROUND_NUMBER": "Accounting",
            "CROSS_MDA_OUTLIER": "Comparative",
            "PADDING_INDICATOR": "Procurement",
            "BENFORD_VIOLATION": "Statistical",
            "DUPLICATE_ALLOCATION": "Duplication",
            "CATEGORY_TOTAL": "Aggregate",
            "VAGUE_ALLOCATION": "Transparency",
            "MISPLACED_LUXURY": "Priority",
            "VEHICLE_PADDING": "Procurement",
            "TRAVEL_ABUSE": "Travel",
        }
        finding["category"] = type_to_category.get(finding.get("type", ""), "Other")

    # Sort by: Jurisdiction → Category → Severity → Amount (descending)
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    unique.sort(key=lambda x: (
        0 if x["jurisdiction"] == "Federal" else 1,  # Federal first
        x["category"],
        severity_order.get(x["severity"], 4),
        -x["amount"]
    ))

    # Reassign IDs
    for i, finding in enumerate(unique, 1):
        finding["id"] = str(i)

    # Build categorized view
    by_jurisdiction = {}
    for finding in unique:
        jur = finding["jurisdiction"]
        if jur not in by_jurisdiction:
            by_jurisdiction[jur] = {"total": 0, "amount": 0, "findings": []}
        by_jurisdiction[jur]["total"] += 1
        by_jurisdiction[jur]["amount"] += finding["amount"]
        by_jurisdiction[jur]["findings"].append(finding["id"])

    # Calculate summary
    summary = {
        "total": len(unique),
        "critical": len([f for f in unique if f["severity"] == "CRITICAL"]),
        "high": len([f for f in unique if f["severity"] == "HIGH"]),
        "medium": len([f for f in unique if f["severity"] == "MEDIUM"]),
        "low": len([f for f in unique if f["severity"] == "LOW"]),
        "total_amount": sum(f["amount"] for f in unique),
        "years": sorted(list(set(f["year"] for f in unique))),
        "states": sorted(list(set(f.get("state") for f in unique if f.get("state")))),
        "types": sorted(list(set(f["type"] for f in unique))),
        "categories": sorted(list(set(f["category"] for f in unique))),
        "by_jurisdiction": by_jurisdiction,
    }

    # Archive existing file
    archive_current(OUTPUT_FILE, ARCHIVE_DIR)

    # Write output
    output = {
        "generated_at": datetime.now().isoformat(),
        "source_files": source_files,
        "summary": summary,
        "findings": unique,
    }

    # Print jurisdiction breakdown
    print("\nBy Jurisdiction:")
    for jur, data in sorted(by_jurisdiction.items(), key=lambda x: -x[1]["amount"]):
        print(f"  {jur}: {data['total']} findings, ₦{data['amount']:,.0f}")

    FINDINGS_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("CONSOLIDATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"\nSummary:")
    print(f"  Total findings: {summary['total']}")
    print(f"  CRITICAL: {summary['critical']}")
    print(f"  HIGH: {summary['high']}")
    print(f"  MEDIUM: {summary['medium']}")
    print(f"  LOW: {summary['low']}")
    print(f"  Total flagged: ₦{summary['total_amount']:,.0f}")
    print(f"  Years covered: {summary['years']}")
    if summary['states']:
        print(f"  States: {', '.join(summary['states'])}")
    print()


if __name__ == "__main__":
    main()
