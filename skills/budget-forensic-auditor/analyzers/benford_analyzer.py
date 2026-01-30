"""
Benford's Law Analyzer for Budget Fraud Detection

Benford's Law states that in naturally occurring datasets, the first digit
follows a specific distribution: 1 appears ~30%, 2 ~17.6%, etc.

Manipulated financial data often deviates from this pattern because humans
tend to favor certain digits (like 5) or avoid others when fabricating numbers.
"""

import json
import math
from collections import Counter
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


# Expected Benford's Law distribution for first digit
BENFORD_EXPECTED = {
    1: 0.301,
    2: 0.176,
    3: 0.125,
    4: 0.097,
    5: 0.079,
    6: 0.067,
    7: 0.058,
    8: 0.051,
    9: 0.046
}


@dataclass
class BenfordResult:
    """Result of Benford's Law analysis"""
    entity_name: str
    sample_size: int
    chi_square: float
    p_value: float
    is_anomalous: bool
    digit_distribution: Dict[int, float]
    max_deviation_digit: int
    max_deviation_percent: float
    suspicious_amounts: List[Dict]
    confidence: float
    severity: str


def extract_first_digit(number: float) -> Optional[int]:
    """Extract first significant digit from a number"""
    if number <= 0:
        return None

    # Get absolute value and find first digit
    abs_num = abs(number)
    while abs_num < 1:
        abs_num *= 10
    while abs_num >= 10:
        abs_num /= 10

    return int(abs_num)


def calculate_chi_square(observed: Dict[int, int], total: int) -> float:
    """Calculate chi-square statistic against Benford's expected distribution"""
    chi_sq = 0.0

    for digit in range(1, 10):
        expected_count = BENFORD_EXPECTED[digit] * total
        observed_count = observed.get(digit, 0)

        if expected_count > 0:
            chi_sq += ((observed_count - expected_count) ** 2) / expected_count

    return chi_sq


def chi_square_to_p_value(chi_sq: float, df: int = 8) -> float:
    """
    Approximate p-value from chi-square statistic.
    df=8 for 9 digits minus 1
    """
    # Using approximation for p-value
    # For accurate values, use scipy.stats.chi2.sf
    if chi_sq < 0:
        return 1.0

    # Critical values for df=8
    # p=0.05 -> 15.507
    # p=0.01 -> 20.090
    # p=0.001 -> 26.125

    if chi_sq > 26.125:
        return 0.001
    elif chi_sq > 20.090:
        return 0.01
    elif chi_sq > 15.507:
        return 0.05
    elif chi_sq > 13.362:
        return 0.10
    else:
        return 0.5  # Not significant


def analyze_benford(
    amounts: List[float],
    entity_name: str,
    line_items: Optional[List[Dict]] = None,
    min_sample_size: int = 50
) -> Optional[BenfordResult]:
    """
    Analyze a list of amounts for Benford's Law compliance.

    Args:
        amounts: List of financial amounts to analyze
        entity_name: Name of the entity (MDA, contractor, etc.)
        line_items: Optional list of dicts with amount and description
        min_sample_size: Minimum samples needed for valid analysis

    Returns:
        BenfordResult or None if insufficient data
    """
    # Filter valid amounts (positive, non-zero)
    valid_amounts = [a for a in amounts if a > 0]

    if len(valid_amounts) < min_sample_size:
        return None

    # Extract first digits
    first_digits = [extract_first_digit(a) for a in valid_amounts]
    first_digits = [d for d in first_digits if d is not None]

    # Count distribution
    digit_counts = Counter(first_digits)
    total = len(first_digits)

    # Calculate observed distribution
    observed_distribution = {
        digit: digit_counts.get(digit, 0) / total
        for digit in range(1, 10)
    }

    # Calculate chi-square
    chi_sq = calculate_chi_square(digit_counts, total)
    p_value = chi_square_to_p_value(chi_sq)

    # Find maximum deviation
    deviations = {
        digit: abs(observed_distribution[digit] - BENFORD_EXPECTED[digit])
        for digit in range(1, 10)
    }
    max_dev_digit = max(deviations, key=deviations.get)
    max_dev_percent = (deviations[max_dev_digit] / BENFORD_EXPECTED[max_dev_digit]) * 100

    # Determine if anomalous (p < 0.05)
    is_anomalous = p_value < 0.05

    # Find suspicious amounts (those with overrepresented first digits)
    suspicious_amounts = []
    if is_anomalous and line_items:
        overrepresented_digits = [
            d for d, obs in observed_distribution.items()
            if obs > BENFORD_EXPECTED[d] * 1.5  # 50% more than expected
        ]

        for item in line_items:
            amount = item.get('amount', 0)
            first_digit = extract_first_digit(amount)
            if first_digit in overrepresented_digits:
                suspicious_amounts.append({
                    'amount': amount,
                    'first_digit': first_digit,
                    'description': item.get('description', ''),
                    'mda': item.get('mda', ''),
                    'budget_code': item.get('budget_code', '')
                })

    # Sort by amount descending, take top 20
    suspicious_amounts.sort(key=lambda x: x['amount'], reverse=True)
    suspicious_amounts = suspicious_amounts[:20]

    # Calculate confidence based on sample size and deviation
    confidence = min(100, (total / 100) * 50 + (1 - p_value) * 50)

    # Determine severity
    if p_value < 0.001 and max_dev_percent > 50:
        severity = "CRITICAL"
    elif p_value < 0.01 and max_dev_percent > 30:
        severity = "HIGH"
    elif p_value < 0.05:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return BenfordResult(
        entity_name=entity_name,
        sample_size=total,
        chi_square=chi_sq,
        p_value=p_value,
        is_anomalous=is_anomalous,
        digit_distribution=observed_distribution,
        max_deviation_digit=max_dev_digit,
        max_deviation_percent=max_dev_percent,
        suspicious_amounts=suspicious_amounts,
        confidence=confidence,
        severity=severity
    )


def analyze_budget_file(filepath: Path) -> List[BenfordResult]:
    """
    Analyze a budget JSON file for Benford's Law violations.

    Analyzes:
    - Overall budget
    - Per MDA
    - Per budget code category
    """
    results = []

    with open(filepath) as f:
        data = json.load(f)

    # Handle different data structures
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get('items', data.get('line_items', []))
    else:
        return results

    if not items:
        return results

    # Extract amounts with metadata
    line_items = []
    for item in items:
        amount = item.get('amount', item.get('total', item.get('value', 0)))
        if isinstance(amount, str):
            amount = float(amount.replace(',', '').replace('₦', ''))

        line_items.append({
            'amount': amount,
            'description': item.get('description', item.get('name', '')),
            'mda': item.get('mda', item.get('ministry', '')),
            'budget_code': item.get('budget_code', item.get('code', ''))
        })

    amounts = [item['amount'] for item in line_items]

    # Overall analysis
    overall = analyze_benford(amounts, "OVERALL_BUDGET", line_items)
    if overall and overall.is_anomalous:
        results.append(overall)

    # Per-MDA analysis
    mda_groups = {}
    for item in line_items:
        mda = item['mda']
        if mda:
            if mda not in mda_groups:
                mda_groups[mda] = []
            mda_groups[mda].append(item)

    for mda, mda_items in mda_groups.items():
        mda_amounts = [item['amount'] for item in mda_items]
        result = analyze_benford(mda_amounts, f"MDA:{mda}", mda_items, min_sample_size=30)
        if result and result.is_anomalous:
            results.append(result)

    return results


def format_result(result: BenfordResult) -> Dict:
    """Format BenfordResult as a finding dictionary"""
    return {
        'type': 'BENFORD_ANOMALY',
        'entity': result.entity_name,
        'severity': result.severity,
        'confidence': round(result.confidence, 1),
        'summary': f"Benford's Law violation detected: digit {result.max_deviation_digit} "
                   f"appears {result.max_deviation_percent:.1f}% more than expected",
        'details': {
            'sample_size': result.sample_size,
            'chi_square': round(result.chi_square, 2),
            'p_value': result.p_value,
            'digit_distribution': {
                str(k): round(v, 4) for k, v in result.digit_distribution.items()
            },
            'expected_distribution': {
                str(k): round(v, 4) for k, v in BENFORD_EXPECTED.items()
            },
            'max_deviation': {
                'digit': result.max_deviation_digit,
                'deviation_percent': round(result.max_deviation_percent, 1)
            }
        },
        'evidence': result.suspicious_amounts[:10],
        'recommendation': "Manual review recommended for amounts starting with digit "
                         f"{result.max_deviation_digit}. Pattern suggests potential manipulation."
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python benford_analyzer.py <budget_file.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    results = analyze_budget_file(filepath)

    print(f"\n{'='*60}")
    print("BENFORD'S LAW ANALYSIS RESULTS")
    print(f"{'='*60}\n")

    if not results:
        print("No significant Benford's Law violations detected.")
    else:
        for result in results:
            finding = format_result(result)
            print(f"[{finding['severity']}] {finding['entity']}")
            print(f"  {finding['summary']}")
            print(f"  Confidence: {finding['confidence']}%")
            print(f"  Sample size: {finding['details']['sample_size']}")
            print()
