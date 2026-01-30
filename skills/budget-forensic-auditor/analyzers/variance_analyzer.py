"""
Variance Analyzer for Budget Forensic Analysis

Detects anomalies through:
1. Year-over-Year (YoY) variance analysis
2. Cross-MDA comparison (same budget codes, different agencies)
3. Inflation-adjusted analysis
4. Statistical outlier detection
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class VarianceFinding:
    """A variance anomaly finding"""
    finding_type: str  # YOY, CROSS_MDA, OUTLIER, INFLATION
    entity: str
    budget_code: str
    description: str
    current_amount: float
    comparison_amount: float
    variance_percent: float
    variance_absolute: float
    severity: str
    confidence: float
    context: Dict = field(default_factory=dict)
    recommendation: str = ""


class VarianceAnalyzer:
    """Analyzes budget data for variance anomalies"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.findings: List[VarianceFinding] = []

    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load configuration thresholds"""
        default_config = {
            "yoy_critical_percent": 200,
            "yoy_high_percent": 100,
            "yoy_medium_percent": 50,
            "cross_mda_ratio_critical": 10,
            "cross_mda_ratio_high": 5,
            "outlier_std_devs": 3,
            "inflation_rates": {
                "2020": 13.25,
                "2021": 16.95,
                "2022": 18.85,
                "2023": 24.08,
                "2024": 28.92,
                "2025": 24.5,
                "2026": 15.0
            },
            "min_amount_threshold": 10000000  # 10M naira minimum
        }

        if config_path and config_path.exists():
            with open(config_path) as f:
                loaded = json.load(f)
                default_config.update(loaded.get('variance', {}))

        return default_config

    def analyze_yoy(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        current_year: str,
        previous_year: str
    ) -> List[VarianceFinding]:
        """
        Year-over-Year variance analysis.
        Compares same budget codes between years.
        """
        findings = []

        # Index previous year by budget_code + mda
        prev_index = {}
        for item in previous_data:
            key = (item.get('budget_code', ''), item.get('mda', ''))
            if key[0]:  # Has budget code
                prev_index[key] = item

        # Compare current to previous
        for item in current_data:
            budget_code = item.get('budget_code', '')
            mda = item.get('mda', '')
            current_amount = self._parse_amount(item.get('amount', 0))

            if current_amount < self.config['min_amount_threshold']:
                continue

            key = (budget_code, mda)
            if key in prev_index:
                prev_amount = self._parse_amount(prev_index[key].get('amount', 0))

                if prev_amount > 0:
                    variance_percent = ((current_amount - prev_amount) / prev_amount) * 100
                    variance_absolute = current_amount - prev_amount

                    # Expected inflation
                    expected_inflation = self.config['inflation_rates'].get(current_year, 20)

                    # Check if variance exceeds inflation + threshold
                    excess_variance = variance_percent - expected_inflation

                    if abs(excess_variance) > self.config['yoy_medium_percent']:
                        severity = self._classify_yoy_severity(excess_variance)

                        finding = VarianceFinding(
                            finding_type="YOY_VARIANCE",
                            entity=mda,
                            budget_code=budget_code,
                            description=item.get('description', ''),
                            current_amount=current_amount,
                            comparison_amount=prev_amount,
                            variance_percent=variance_percent,
                            variance_absolute=variance_absolute,
                            severity=severity,
                            confidence=self._calculate_confidence(current_amount, variance_percent),
                            context={
                                'current_year': current_year,
                                'previous_year': previous_year,
                                'expected_inflation': expected_inflation,
                                'excess_variance': excess_variance
                            },
                            recommendation=self._generate_yoy_recommendation(
                                variance_percent, excess_variance, mda, budget_code
                            )
                        )
                        findings.append(finding)

        return findings

    def analyze_cross_mda(self, data: List[Dict]) -> List[VarianceFinding]:
        """
        Cross-MDA comparison.
        Same budget codes should have similar amounts across agencies of similar size.
        """
        findings = []

        # Group by budget code
        by_budget_code = defaultdict(list)
        for item in data:
            code = item.get('budget_code', '')
            if code:
                amount = self._parse_amount(item.get('amount', 0))
                if amount >= self.config['min_amount_threshold']:
                    by_budget_code[code].append({
                        'mda': item.get('mda', ''),
                        'amount': amount,
                        'description': item.get('description', '')
                    })

        # Analyze each budget code
        for code, items in by_budget_code.items():
            if len(items) < 3:  # Need at least 3 MDAs for comparison
                continue

            amounts = [item['amount'] for item in items]
            median = statistics.median(amounts)
            mean = statistics.mean(amounts)

            if median == 0:
                continue

            # Find outliers
            for item in items:
                ratio = item['amount'] / median

                if ratio >= self.config['cross_mda_ratio_high']:
                    severity = "CRITICAL" if ratio >= self.config['cross_mda_ratio_critical'] else "HIGH"

                    # Find the "normal" comparisons
                    normal_items = [i for i in items if i['mda'] != item['mda']]
                    normal_items.sort(key=lambda x: x['amount'])

                    finding = VarianceFinding(
                        finding_type="CROSS_MDA_OUTLIER",
                        entity=item['mda'],
                        budget_code=code,
                        description=item['description'],
                        current_amount=item['amount'],
                        comparison_amount=median,
                        variance_percent=(ratio - 1) * 100,
                        variance_absolute=item['amount'] - median,
                        severity=severity,
                        confidence=min(95, 60 + (len(items) * 5)),
                        context={
                            'ratio_to_median': ratio,
                            'other_mdas_count': len(items) - 1,
                            'median_amount': median,
                            'mean_amount': mean,
                            'comparison_examples': [
                                {'mda': i['mda'], 'amount': i['amount']}
                                for i in normal_items[:3]
                            ]
                        },
                        recommendation=f"MDA '{item['mda']}' spends {ratio:.1f}x the median "
                                      f"for budget code {code}. Compare with similar agencies."
                    )
                    findings.append(finding)

        return findings

    def analyze_statistical_outliers(self, data: List[Dict]) -> List[VarianceFinding]:
        """
        Statistical outlier detection using Z-scores.
        Flags items that are statistical anomalies within their category.
        """
        findings = []

        # Group by budget code prefix (category)
        by_category = defaultdict(list)
        for item in data:
            code = item.get('budget_code', '')[:4]  # First 4 digits = category
            if code:
                amount = self._parse_amount(item.get('amount', 0))
                if amount > 0:
                    by_category[code].append({
                        'mda': item.get('mda', ''),
                        'amount': amount,
                        'description': item.get('description', ''),
                        'full_code': item.get('budget_code', '')
                    })

        # Find outliers in each category
        for category, items in by_category.items():
            if len(items) < 10:  # Need enough samples
                continue

            amounts = [item['amount'] for item in items]
            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts)

            if stdev == 0:
                continue

            for item in items:
                z_score = (item['amount'] - mean) / stdev

                if abs(z_score) >= self.config['outlier_std_devs']:
                    severity = "CRITICAL" if abs(z_score) >= 5 else "HIGH" if abs(z_score) >= 4 else "MEDIUM"

                    finding = VarianceFinding(
                        finding_type="STATISTICAL_OUTLIER",
                        entity=item['mda'],
                        budget_code=item['full_code'],
                        description=item['description'],
                        current_amount=item['amount'],
                        comparison_amount=mean,
                        variance_percent=((item['amount'] - mean) / mean) * 100,
                        variance_absolute=item['amount'] - mean,
                        severity=severity,
                        confidence=min(95, 70 + (abs(z_score) * 5)),
                        context={
                            'z_score': z_score,
                            'category': category,
                            'category_mean': mean,
                            'category_stdev': stdev,
                            'samples_in_category': len(items)
                        },
                        recommendation=f"Amount is {abs(z_score):.1f} standard deviations from mean. "
                                      f"Review for potential padding or error."
                    )
                    findings.append(finding)

        return findings

    def analyze_round_numbers(self, data: List[Dict]) -> List[VarianceFinding]:
        """
        Detect suspiciously round numbers.
        Real costs rarely end in exact millions or billions.
        """
        findings = []

        for item in data:
            amount = self._parse_amount(item.get('amount', 0))

            if amount < 100000000:  # Less than 100M, skip
                continue

            # Check if it's a round number
            billions = amount / 1000000000
            millions = amount / 1000000

            is_exact_billion = billions == int(billions) and billions >= 1
            is_exact_hundred_million = (millions == int(millions) and
                                       millions >= 100 and
                                       int(millions) % 100 == 0)

            if is_exact_billion or is_exact_hundred_million:
                finding = VarianceFinding(
                    finding_type="ROUND_NUMBER",
                    entity=item.get('mda', ''),
                    budget_code=item.get('budget_code', ''),
                    description=item.get('description', ''),
                    current_amount=amount,
                    comparison_amount=0,
                    variance_percent=0,
                    variance_absolute=0,
                    severity="MEDIUM",
                    confidence=60,
                    context={
                        'is_exact_billion': is_exact_billion,
                        'is_exact_hundred_million': is_exact_hundred_million,
                        'formatted_amount': self._format_amount(amount)
                    },
                    recommendation="Exact round amounts suggest estimation rather than "
                                  "actual costing. Request detailed breakdown."
                )
                findings.append(finding)

        return findings

    def _parse_amount(self, amount) -> float:
        """Parse amount to float"""
        if isinstance(amount, (int, float)):
            return float(amount)
        if isinstance(amount, str):
            cleaned = amount.replace(',', '').replace('₦', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0

    def _format_amount(self, amount: float) -> str:
        """Format amount in human-readable form"""
        if amount >= 1000000000000:
            return f"₦{amount/1000000000000:.2f}T"
        elif amount >= 1000000000:
            return f"₦{amount/1000000000:.2f}B"
        elif amount >= 1000000:
            return f"₦{amount/1000000:.2f}M"
        else:
            return f"₦{amount:,.0f}"

    def _classify_yoy_severity(self, excess_variance: float) -> str:
        """Classify YoY variance severity"""
        abs_var = abs(excess_variance)
        if abs_var >= self.config['yoy_critical_percent']:
            return "CRITICAL"
        elif abs_var >= self.config['yoy_high_percent']:
            return "HIGH"
        else:
            return "MEDIUM"

    def _calculate_confidence(self, amount: float, variance: float) -> float:
        """Calculate confidence score based on amount and variance"""
        # Higher amounts and higher variances = higher confidence in finding
        amount_factor = min(30, (amount / 10000000000) * 30)  # Max 30 from amount
        variance_factor = min(50, (abs(variance) / 100) * 50)  # Max 50 from variance
        base = 20

        return min(95, base + amount_factor + variance_factor)

    def _generate_yoy_recommendation(
        self,
        variance: float,
        excess: float,
        mda: str,
        code: str
    ) -> str:
        """Generate actionable recommendation for YoY variance"""
        direction = "increase" if variance > 0 else "decrease"

        if abs(excess) >= 200:
            return (f"Extreme {direction} of {abs(variance):.0f}% for {mda}, "
                   f"budget code {code}. Requires immediate justification.")
        elif abs(excess) >= 100:
            return (f"Significant {direction} of {abs(variance):.0f}% exceeds "
                   f"inflation by {abs(excess):.0f}%. Request detailed explanation.")
        else:
            return (f"Notable {direction} of {abs(variance):.0f}%. "
                   f"Verify against program changes or policy updates.")


def format_finding(finding: VarianceFinding) -> Dict:
    """Format finding as JSON-serializable dict"""
    return {
        'type': finding.finding_type,
        'entity': finding.entity,
        'budget_code': finding.budget_code,
        'description': finding.description,
        'severity': finding.severity,
        'confidence': round(finding.confidence, 1),
        'amounts': {
            'current': finding.current_amount,
            'comparison': finding.comparison_amount,
            'variance_percent': round(finding.variance_percent, 1),
            'variance_absolute': finding.variance_absolute
        },
        'context': finding.context,
        'recommendation': finding.recommendation
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python variance_analyzer.py <budget_file.json> [previous_file.json]")
        sys.exit(1)

    analyzer = VarianceAnalyzer()

    current_file = Path(sys.argv[1])
    with open(current_file) as f:
        current_data = json.load(f)
        if isinstance(current_data, dict):
            current_data = current_data.get('items', [])

    print(f"\n{'='*60}")
    print("VARIANCE ANALYSIS RESULTS")
    print(f"{'='*60}\n")

    # Cross-MDA analysis
    cross_mda_findings = analyzer.analyze_cross_mda(current_data)
    print(f"Cross-MDA Outliers: {len(cross_mda_findings)}")
    for f in cross_mda_findings[:5]:
        print(f"  [{f.severity}] {f.entity}: {analyzer._format_amount(f.current_amount)}")
        print(f"    {f.recommendation}")

    # Statistical outliers
    stat_findings = analyzer.analyze_statistical_outliers(current_data)
    print(f"\nStatistical Outliers: {len(stat_findings)}")
    for f in stat_findings[:5]:
        print(f"  [{f.severity}] {f.entity}: {analyzer._format_amount(f.current_amount)}")

    # Round numbers
    round_findings = analyzer.analyze_round_numbers(current_data)
    print(f"\nSuspicious Round Numbers: {len(round_findings)}")
    for f in round_findings[:5]:
        print(f"  {f.entity}: {analyzer._format_amount(f.current_amount)}")

    # YoY if previous file provided
    if len(sys.argv) >= 3:
        prev_file = Path(sys.argv[2])
        with open(prev_file) as f:
            prev_data = json.load(f)
            if isinstance(prev_data, dict):
                prev_data = prev_data.get('items', [])

        yoy_findings = analyzer.analyze_yoy(current_data, prev_data, "2026", "2025")
        print(f"\nYear-over-Year Anomalies: {len(yoy_findings)}")
        for f in yoy_findings[:5]:
            print(f"  [{f.severity}] {f.entity}: {f.variance_percent:.0f}% change")
