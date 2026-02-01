#!/usr/bin/env python3
"""
Validate all data files against canonical schemas.

Checks:
1. JSON validity
2. Required fields present
3. Field types correct
4. Values in expected ranges
5. File structure matches worktree

Run: python scripts/utils/validate_data.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
FINDINGS_DIR = BASE_DIR / "findings"
EXTRACTED_DIR = BASE_DIR / "extracted"

# Validation rules
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
VALID_YEARS = set(range(2019, 2031))
STATE_SLUGS = {
    "abia", "adamawa", "akwa-ibom", "anambra", "bauchi", "bayelsa", "benue", "borno",
    "cross-river", "delta", "ebonyi", "edo", "ekiti", "enugu", "fct", "gombe", "imo",
    "jigawa", "kaduna", "kano", "katsina", "kebbi", "kogi", "kwara", "lagos", "nasarawa",
    "niger", "ogun", "ondo", "osun", "oyo", "plateau", "rivers", "sokoto", "taraba",
    "yobe", "zamfara"
}


class ValidationError:
    def __init__(self, file: str, message: str, severity: str = "ERROR"):
        self.file = file
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity}] {self.file}: {self.message}"


def validate_json(path: Path) -> Tuple[bool, dict | None, str]:
    """Validate JSON file is parseable"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return True, data, ""
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {e}"
    except Exception as e:
        return False, None, f"Read error: {e}"


def validate_finding(finding: dict, index: int) -> List[str]:
    """Validate a single finding object"""
    errors = []

    # Required fields
    required = ["id", "type", "entity", "description", "amount", "severity", "year"]
    for field in required:
        if field not in finding:
            errors.append(f"Finding {index}: Missing required field '{field}'")

    # Validate types
    if "amount" in finding:
        if not isinstance(finding["amount"], (int, float)):
            errors.append(f"Finding {index}: 'amount' must be a number")
        elif finding["amount"] <= 0:
            errors.append(f"Finding {index}: 'amount' must be positive")

    if "year" in finding:
        if not isinstance(finding["year"], int):
            errors.append(f"Finding {index}: 'year' must be an integer")
        elif finding["year"] not in VALID_YEARS:
            errors.append(f"Finding {index}: 'year' {finding['year']} out of range")

    if "severity" in finding:
        if finding["severity"] not in VALID_SEVERITIES:
            errors.append(f"Finding {index}: Invalid severity '{finding['severity']}'")

    if "state" in finding and finding["state"]:
        state_slug = finding["state"].lower().replace(" ", "-")
        if state_slug not in STATE_SLUGS and state_slug != "federal":
            errors.append(f"Finding {index}: Unknown state '{finding['state']}'")

    return errors


def validate_consolidated(path: Path) -> List[ValidationError]:
    """Validate consolidated.json structure"""
    errors = []

    valid, data, error = validate_json(path)
    if not valid:
        return [ValidationError(path.name, error)]

    # Check top-level structure
    if not isinstance(data, dict):
        errors.append(ValidationError(path.name, "Root must be an object"))
        return errors

    # Check required keys
    if "findings" not in data:
        errors.append(ValidationError(path.name, "Missing 'findings' key"))
        return errors

    findings = data["findings"]
    if not isinstance(findings, list):
        errors.append(ValidationError(path.name, "'findings' must be an array"))
        return errors

    # Validate each finding
    for i, finding in enumerate(findings):
        finding_errors = validate_finding(finding, i)
        for err in finding_errors:
            errors.append(ValidationError(path.name, err))

    # Check for duplicate IDs
    ids = [f.get("id") for f in findings if f.get("id")]
    if len(ids) != len(set(ids)):
        errors.append(ValidationError(path.name, "Duplicate finding IDs detected"))

    return errors


def validate_context_files(context_dir: Path) -> List[ValidationError]:
    """Validate context reference files"""
    errors = []

    expected_files = [
        "benchmarks.json",
        "budget_codes.json",
        "corruption_patterns.json",
        "mda_mandates.json",
        "population.json"
    ]

    for filename in expected_files:
        filepath = context_dir / filename
        if not filepath.exists():
            errors.append(ValidationError(filename, "Missing context file", "WARNING"))
        else:
            valid, data, error = validate_json(filepath)
            if not valid:
                errors.append(ValidationError(filename, error))

    return errors


def validate_directory_structure() -> List[ValidationError]:
    """Validate directory structure matches worktree"""
    errors = []

    required_dirs = [
        DATA_DIR / "context",
        FINDINGS_DIR,
        EXTRACTED_DIR,
        BASE_DIR / "scripts",
        BASE_DIR / "webapp" / "src",
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            errors.append(ValidationError(
                str(dir_path.relative_to(BASE_DIR)),
                "Required directory missing",
                "WARNING"
            ))

    return errors


def print_errors(errors: List[ValidationError], title: str):
    """Print errors with formatting"""
    if not errors:
        print(f"  {title}: OK")
        return

    print(f"  {title}:")
    for error in errors:
        color = "\033[91m" if error.severity == "ERROR" else "\033[93m"
        reset = "\033[0m"
        print(f"    {color}{error}{reset}")


def main():
    print("=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)
    print(f"Base directory: {BASE_DIR}")
    print()

    all_errors = []
    all_warnings = []

    # 1. Validate directory structure
    print("1. Directory Structure")
    dir_errors = validate_directory_structure()
    all_warnings.extend([e for e in dir_errors if e.severity == "WARNING"])
    all_errors.extend([e for e in dir_errors if e.severity == "ERROR"])
    print_errors(dir_errors, "Structure")

    # 2. Validate context files
    print("\n2. Context Files")
    context_dir = DATA_DIR / "context"
    if context_dir.exists():
        context_errors = validate_context_files(context_dir)
        all_warnings.extend([e for e in context_errors if e.severity == "WARNING"])
        all_errors.extend([e for e in context_errors if e.severity == "ERROR"])
        print_errors(context_errors, "Context")
    else:
        print("  Context directory missing!")

    # 3. Validate consolidated.json
    print("\n3. Consolidated Findings")
    consolidated_path = FINDINGS_DIR / "consolidated.json"
    if consolidated_path.exists():
        cons_errors = validate_consolidated(consolidated_path)
        all_errors.extend([e for e in cons_errors if e.severity == "ERROR"])
        print_errors(cons_errors, "consolidated.json")
        if not cons_errors:
            with open(consolidated_path) as f:
                data = json.load(f)
                findings = data.get("findings", [])
                print(f"    Total findings: {len(findings)}")
    else:
        print("  consolidated.json: NOT FOUND (run consolidate.py first)")
        all_warnings.append(ValidationError("consolidated.json", "File not found", "WARNING"))

    # 4. Validate other finding files
    print("\n4. Other Finding Files")
    for json_file in FINDINGS_DIR.glob("*.json"):
        if json_file.name == "consolidated.json":
            continue
        valid, data, error = validate_json(json_file)
        if not valid:
            all_errors.append(ValidationError(json_file.name, error))
            print(f"  {json_file.name}: INVALID - {error}")
        else:
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("findings", data.get("items", []))
            print(f"  {json_file.name}: OK ({len(items)} items)")

    # 5. Validate extracted files
    print("\n5. Extracted Data Files")
    if EXTRACTED_DIR.exists():
        for json_file in EXTRACTED_DIR.glob("*.json"):
            valid, data, error = validate_json(json_file)
            if not valid:
                all_errors.append(ValidationError(json_file.name, error))
                print(f"  {json_file.name}: INVALID - {error}")
            else:
                print(f"  {json_file.name}: OK")
    else:
        print("  Extracted directory not found")

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Errors: {len(all_errors)}")
    print(f"Warnings: {len(all_warnings)}")

    if all_errors:
        print("\nErrors must be fixed:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    elif all_warnings:
        print("\nWarnings (non-blocking):")
        for warning in all_warnings:
            print(f"  - {warning}")
        sys.exit(0)
    else:
        print("\nAll validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
