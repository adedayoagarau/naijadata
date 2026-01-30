#!/usr/bin/env python3
"""
Budget Forensic Auditor - Main Analysis Runner

Orchestrates all analyzers and aggregates findings into a unified database.
Supports multi-year analysis and year-over-year comparisons.

Usage:
    python run_analysis.py --input ../extracted/ --output ../findings/
    python run_analysis.py --input ../extracted/master_budget_data.json  # All years
    python run_analysis.py --analyzer benford --input file.json
    python run_analysis.py --watch --input ../extracted/  # Continuous mode
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.benford_analyzer import analyze_budget_file as run_benford, format_result as format_benford
from analyzers.variance_analyzer import VarianceAnalyzer, format_finding as format_variance
from analyzers.nigerian_context_analyzer import NigerianContextAnalyzer, format_finding as format_context
from analyzers.findings_db import FindingsDatabase


class BudgetAuditor:
    """
    Main auditor class that orchestrates all analyses.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.db = FindingsDatabase(output_dir / "findings_db.json")
        self.variance_analyzer = VarianceAnalyzer()
        self.context_analyzer = NigerianContextAnalyzer()

    def _analyze_cross_state(self, by_state: Dict[str, List]) -> List:
        """
        Cross-state comparison analysis.
        Compares budget patterns across states to identify outliers.
        """
        from dataclasses import dataclass, field

        @dataclass
        class CrossStateFinding:
            finding_type: str = "CROSS_STATE_OUTLIER"
            entity: str = ""
            budget_code: str = ""
            description: str = ""
            amount: float = 0
            severity: str = "MEDIUM"
            confidence: float = 70
            context: Dict = field(default_factory=dict)
            recommendation: str = ""

        findings = []

        # Compare total budgets per state
        state_totals = {}
        for state, items in by_state.items():
            total = sum(i.get('amount', 0) for i in items)
            state_totals[state] = {
                'total': total,
                'item_count': len(items),
                'avg_per_item': total / len(items) if items else 0
            }

        if len(state_totals) < 3:
            return findings

        # Calculate statistics
        totals = [s['total'] for s in state_totals.values()]
        import statistics
        median_total = statistics.median(totals)
        mean_total = statistics.mean(totals)

        # Find outlier states
        for state, data in state_totals.items():
            if median_total > 0:
                ratio = data['total'] / median_total

                if ratio >= 3:  # 3x median or more
                    findings.append(CrossStateFinding(
                        finding_type="STATE_BUDGET_OUTLIER",
                        entity=f"{state} State",
                        budget_code="",
                        description=f"State budget {ratio:.1f}x higher than median",
                        amount=data['total'],
                        severity="HIGH" if ratio >= 5 else "MEDIUM",
                        confidence=75,
                        context={
                            'state_total': data['total'],
                            'median_total': median_total,
                            'ratio_to_median': ratio,
                            'item_count': data['item_count']
                        },
                        recommendation=f"Compare {state}'s budget methodology with similar-sized states."
                    ))

        # Compare budget codes across states
        by_code = defaultdict(dict)
        for state, items in by_state.items():
            for item in items:
                code = item.get('budget_code', '')
                if code:
                    if code not in by_code:
                        by_code[code] = {}
                    if state not in by_code[code]:
                        by_code[code][state] = 0
                    by_code[code][state] += item.get('amount', 0)

        # Find codes with high variance across states
        for code, state_amounts in by_code.items():
            if len(state_amounts) < 3:
                continue

            amounts = list(state_amounts.values())
            if all(a == 0 for a in amounts):
                continue

            median = statistics.median(amounts)
            if median == 0:
                continue

            for state, amount in state_amounts.items():
                ratio = amount / median
                if ratio >= 5:  # 5x median
                    findings.append(CrossStateFinding(
                        finding_type="CROSS_STATE_CODE_OUTLIER",
                        entity=f"{state} State",
                        budget_code=code,
                        description=f"Budget code {code} is {ratio:.1f}x state median",
                        amount=amount,
                        severity="HIGH" if ratio >= 10 else "MEDIUM",
                        confidence=70,
                        context={
                            'state_amount': amount,
                            'median_amount': median,
                            'ratio_to_median': ratio,
                            'states_compared': len(state_amounts)
                        },
                        recommendation=f"Investigate why {state} spends significantly more on {code}."
                    ))

        return findings

    def analyze_file(self, filepath: Path, year: int = 2026) -> Dict:
        """
        Run all analyses on a single budget file.
        Returns summary of findings.
        """
        print(f"\n{'='*60}")
        print(f"ANALYZING: {filepath.name}")
        print(f"{'='*60}")

        # Load data
        with open(filepath) as f:
            raw_data = json.load(f)

        # Handle different data structures
        if isinstance(raw_data, list):
            data = raw_data
        elif isinstance(raw_data, dict):
            data = raw_data.get('items', raw_data.get('line_items', raw_data.get('anomalies', [])))
        else:
            print(f"  Unknown data format in {filepath}")
            return {'error': 'unknown_format'}

        if not data:
            print(f"  No data found in {filepath}")
            return {'error': 'no_data'}

        print(f"  Loaded {len(data)} items")

        results = {
            'file': str(filepath),
            'items_analyzed': len(data),
            'findings': {
                'benford': 0,
                'variance': 0,
                'context': 0,
                'total': 0
            },
            'new_findings': 0,
            'duplicate_findings': 0
        }

        # 1. Benford's Law Analysis
        print("\n  [1/3] Running Benford's Law analysis...")
        try:
            benford_results = run_benford(filepath)
            for result in benford_results:
                finding_dict = format_benford(result)
                added = self.db.add_finding(
                    finding_type=finding_dict['type'],
                    entity=finding_dict['entity'],
                    budget_code='',
                    description=finding_dict['summary'],
                    amount=0,  # Benford doesn't have a single amount
                    severity=finding_dict['severity'],
                    confidence=finding_dict['confidence'],
                    analyzer='benford',
                    rule_triggered='benford_violation',
                    evidence=finding_dict['details'],
                    recommendation=finding_dict['recommendation'],
                    year=year
                )
                if added:
                    results['new_findings'] += 1
                else:
                    results['duplicate_findings'] += 1
                results['findings']['benford'] += 1
            print(f"    Found {len(benford_results)} Benford anomalies")
        except Exception as e:
            print(f"    Benford analysis error: {e}")

        # 2. Variance Analysis
        print("\n  [2/3] Running variance analysis...")
        try:
            # Cross-MDA
            cross_mda = self.variance_analyzer.analyze_cross_mda(data)
            for finding in cross_mda:
                added = self.db.add_from_analyzer(finding, 'variance_cross_mda', year)
                if added:
                    results['new_findings'] += 1
                else:
                    results['duplicate_findings'] += 1
                results['findings']['variance'] += 1

            # Statistical outliers
            stat_outliers = self.variance_analyzer.analyze_statistical_outliers(data)
            for finding in stat_outliers:
                added = self.db.add_from_analyzer(finding, 'variance_statistical', year)
                if added:
                    results['new_findings'] += 1
                else:
                    results['duplicate_findings'] += 1
                results['findings']['variance'] += 1

            # Round numbers
            round_nums = self.variance_analyzer.analyze_round_numbers(data)
            for finding in round_nums:
                added = self.db.add_from_analyzer(finding, 'variance_round', year)
                if added:
                    results['new_findings'] += 1
                else:
                    results['duplicate_findings'] += 1
                results['findings']['variance'] += 1

            print(f"    Found {len(cross_mda)} cross-MDA, {len(stat_outliers)} statistical, {len(round_nums)} round number anomalies")
        except Exception as e:
            print(f"    Variance analysis error: {e}")

        # 3. Nigerian Context Analysis
        print("\n  [3/3] Running Nigerian context analysis...")
        try:
            context_findings = self.context_analyzer.run_all_analyses(data, year)
            for finding in context_findings:
                added = self.db.add_from_analyzer(finding, 'nigerian_context', year)
                if added:
                    results['new_findings'] += 1
                else:
                    results['duplicate_findings'] += 1
                results['findings']['context'] += 1
            print(f"    Found {len(context_findings)} Nigerian context anomalies")
        except Exception as e:
            print(f"    Context analysis error: {e}")

        results['findings']['total'] = (
            results['findings']['benford'] +
            results['findings']['variance'] +
            results['findings']['context']
        )

        return results

    def analyze_directory(self, input_dir: Path, year: int = 2026) -> Dict:
        """
        Analyze all JSON files in a directory.
        """
        json_files = list(input_dir.glob("*.json"))
        print(f"\nFound {len(json_files)} JSON files to analyze")

        all_results = {
            'files_analyzed': 0,
            'total_items': 0,
            'total_findings': 0,
            'new_findings': 0,
            'duplicate_findings': 0,
            'by_file': []
        }

        for filepath in json_files:
            result = self.analyze_file(filepath, year)
            if 'error' not in result:
                all_results['files_analyzed'] += 1
                all_results['total_items'] += result['items_analyzed']
                all_results['total_findings'] += result['findings']['total']
                all_results['new_findings'] += result['new_findings']
                all_results['duplicate_findings'] += result['duplicate_findings']
                all_results['by_file'].append({
                    'file': filepath.name,
                    'findings': result['findings']['total']
                })

        return all_results

    def analyze_master_file(self, filepath: Path) -> Dict:
        """
        Analyze master budget data file containing all years.
        Enables proper YoY comparisons across years.
        """
        print(f"\n{'='*60}")
        print("MULTI-YEAR BUDGET FORENSIC ANALYSIS")
        print(f"{'='*60}")

        # Load master data
        with open(filepath) as f:
            raw_data = json.load(f)

        # Extract items
        if isinstance(raw_data, dict):
            items = raw_data.get('items', raw_data.get('line_items', []))
            years_info = raw_data.get('years_covered', [])
        else:
            items = raw_data
            years_info = []

        if not items:
            print("  No items found in master file")
            return {'error': 'no_data'}

        print(f"  Loaded {len(items):,} total line items")

        # Group by year
        by_year = defaultdict(list)
        by_level = defaultdict(list)
        by_state = defaultdict(list)

        for item in items:
            year = item.get('year', 2026)
            level = item.get('level', 'federal')
            state = item.get('state')

            by_year[year].append(item)
            by_level[level].append(item)
            if state:
                by_state[state].append(item)

        years = sorted(by_year.keys())
        print(f"  Years covered: {years}")

        for year in years:
            print(f"    {year}: {len(by_year[year]):,} items")

        # Print level breakdown
        print(f"\n  By Level:")
        for level, level_items in sorted(by_level.items()):
            print(f"    {level}: {len(level_items):,} items")

        # Print state breakdown if any
        if by_state:
            print(f"\n  By State ({len(by_state)} states):")
            for state, state_items in sorted(by_state.items(), key=lambda x: -len(x[1]))[:5]:
                print(f"    {state}: {len(state_items):,} items")
            if len(by_state) > 5:
                print(f"    ... and {len(by_state) - 5} more states")

        results = {
            'years_analyzed': years,
            'levels_analyzed': list(by_level.keys()),
            'states_analyzed': list(by_state.keys()),
            'total_items': len(items),
            'findings': {
                'benford': 0,
                'variance': 0,
                'yoy': 0,
                'context': 0,
                'cross_state': 0,
                'total': 0
            },
            'new_findings': 0,
            'duplicate_findings': 0,
            'by_year': {}
        }

        # Cross-state analysis if we have multiple states
        if len(by_state) > 1:
            print(f"\n{'='*60}")
            print("CROSS-STATE ANALYSIS")
            print(f"{'='*60}")
            try:
                cross_state_findings = self._analyze_cross_state(by_state)
                for finding in cross_state_findings:
                    added = self.db.add_from_analyzer(finding, 'cross_state', 2026)
                    if added:
                        results['new_findings'] += 1
                    else:
                        results['duplicate_findings'] += 1
                    results['findings']['cross_state'] += 1
                print(f"  Found {len(cross_state_findings)} cross-state anomalies")
            except Exception as e:
                print(f"  Cross-state analysis error: {e}")

        # Analyze each year
        for year in years:
            year_data = by_year[year]
            print(f"\n{'='*60}")
            print(f"ANALYZING YEAR {year}")
            print(f"{'='*60}")
            print(f"  {len(year_data):,} items")

            year_results = {
                'items': len(year_data),
                'findings': {'benford': 0, 'variance': 0, 'yoy': 0, 'context': 0}
            }

            # 1. Benford's Law (per year)
            print("  [1/4] Running Benford's Law analysis...")
            try:
                # Group by MDA for Benford
                by_mda = defaultdict(list)
                for item in year_data:
                    mda = item.get('mda', 'UNKNOWN')
                    by_mda[mda].append(item)

                benford_count = 0
                for mda, mda_items in by_mda.items():
                    amounts = [i.get('amount', 0) for i in mda_items if i.get('amount', 0) > 0]
                    if len(amounts) >= 50:  # Need enough samples
                        from analyzers.benford_analyzer import analyze_benford
                        benford_result = analyze_benford(amounts, mda, mda_items)
                        if benford_result and benford_result.severity != "LOW":
                            finding_dict = format_benford(benford_result)
                            added = self.db.add_finding(
                                finding_type=finding_dict['type'],
                                entity=finding_dict['entity'],
                                budget_code='',
                                description=finding_dict['summary'],
                                amount=sum(amounts),
                                severity=finding_dict['severity'],
                                confidence=finding_dict['confidence'],
                                analyzer='benford',
                                rule_triggered='benford_violation',
                                evidence=finding_dict['details'],
                                recommendation=finding_dict['recommendation'],
                                year=year
                            )
                            if added:
                                results['new_findings'] += 1
                                benford_count += 1
                            else:
                                results['duplicate_findings'] += 1
                            results['findings']['benford'] += 1
                            year_results['findings']['benford'] += 1

                print(f"    Found {benford_count} Benford anomalies")
            except Exception as e:
                print(f"    Benford analysis error: {e}")

            # 2. Cross-MDA and Statistical Variance (per year)
            print("  [2/4] Running variance analysis...")
            try:
                cross_mda = self.variance_analyzer.analyze_cross_mda(year_data)
                for finding in cross_mda:
                    added = self.db.add_from_analyzer(finding, 'variance_cross_mda', year)
                    if added:
                        results['new_findings'] += 1
                    else:
                        results['duplicate_findings'] += 1
                    results['findings']['variance'] += 1
                    year_results['findings']['variance'] += 1

                stat_outliers = self.variance_analyzer.analyze_statistical_outliers(year_data)
                for finding in stat_outliers:
                    added = self.db.add_from_analyzer(finding, 'variance_statistical', year)
                    if added:
                        results['new_findings'] += 1
                    else:
                        results['duplicate_findings'] += 1
                    results['findings']['variance'] += 1
                    year_results['findings']['variance'] += 1

                round_nums = self.variance_analyzer.analyze_round_numbers(year_data)
                for finding in round_nums:
                    added = self.db.add_from_analyzer(finding, 'variance_round', year)
                    if added:
                        results['new_findings'] += 1
                    else:
                        results['duplicate_findings'] += 1
                    results['findings']['variance'] += 1
                    year_results['findings']['variance'] += 1

                print(f"    Found {len(cross_mda)} cross-MDA, {len(stat_outliers)} statistical, {len(round_nums)} round number anomalies")
            except Exception as e:
                print(f"    Variance analysis error: {e}")

            # 3. Year-over-Year Analysis
            print("  [3/4] Running YoY analysis...")
            prev_year = year - 1
            if prev_year in by_year:
                try:
                    prev_data = by_year[prev_year]
                    yoy_findings = self.variance_analyzer.analyze_yoy(
                        year_data, prev_data, str(year), str(prev_year)
                    )
                    for finding in yoy_findings:
                        added = self.db.add_from_analyzer(finding, 'variance_yoy', year)
                        if added:
                            results['new_findings'] += 1
                        else:
                            results['duplicate_findings'] += 1
                        results['findings']['yoy'] += 1
                        year_results['findings']['yoy'] += 1

                    print(f"    Found {len(yoy_findings)} YoY anomalies vs {prev_year}")
                except Exception as e:
                    print(f"    YoY analysis error: {e}")
            else:
                print(f"    No {prev_year} data for YoY comparison")

            # 4. Nigerian Context Analysis
            print("  [4/4] Running Nigerian context analysis...")
            try:
                context_findings = self.context_analyzer.run_all_analyses(year_data, year)
                for finding in context_findings:
                    added = self.db.add_from_analyzer(finding, 'nigerian_context', year)
                    if added:
                        results['new_findings'] += 1
                    else:
                        results['duplicate_findings'] += 1
                    results['findings']['context'] += 1
                    year_results['findings']['context'] += 1
                print(f"    Found {len(context_findings)} Nigerian context anomalies")
            except Exception as e:
                print(f"    Context analysis error: {e}")

            results['by_year'][year] = year_results

        results['findings']['total'] = (
            results['findings']['benford'] +
            results['findings']['variance'] +
            results['findings']['yoy'] +
            results['findings']['context'] +
            results['findings']['cross_state']
        )

        return results

    def print_summary(self):
        """Print database summary"""
        stats = self.db.get_statistics()

        print(f"\n{'='*60}")
        print("AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"\nTotal Findings: {stats['total_findings']}")
        print(f"Total Impact: {stats['total_impact_formatted']}")

        print("\nBy Severity:")
        for sev, count in stats['by_severity'].items():
            print(f"  {sev}: {count}")

        print("\nBy Type:")
        for typ, count in sorted(stats['by_type'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {typ}: {count}")

        print("\nTop Entities by Amount:")
        for entity, info in list(stats['top_entities'].items())[:10]:
            formatted = self.db._format_amount(info['amount'])
            print(f"  {entity}: {formatted} ({info['count']} findings)")

    def export_for_webapp(self, output_path: Path, limit: int = 100):
        """Export findings for webapp consumption"""
        findings = self.db.export_for_webapp(limit)

        with open(output_path, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total': len(findings),
                'findings': findings
            }, f, indent=2)

        print(f"\nExported {len(findings)} findings to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Budget Forensic Auditor')
    parser.add_argument('--input', '-i', type=Path, required=True,
                       help='Input file or directory')
    parser.add_argument('--output', '-o', type=Path, default=Path('./findings'),
                       help='Output directory for findings')
    parser.add_argument('--year', '-y', type=int, default=2026,
                       help='Budget year being analyzed')
    parser.add_argument('--analyzer', '-a', type=str,
                       choices=['all', 'benford', 'variance', 'context'],
                       default='all', help='Which analyzer to run')
    parser.add_argument('--export-webapp', action='store_true',
                       help='Export findings formatted for webapp')
    parser.add_argument('--watch', action='store_true',
                       help='Watch mode - re-analyze periodically')
    parser.add_argument('--watch-interval', type=int, default=3600,
                       help='Watch interval in seconds (default: 1 hour)')

    args = parser.parse_args()

    auditor = BudgetAuditor(args.output)

    if args.watch:
        print("Starting continuous analysis mode...")
        print(f"Interval: {args.watch_interval} seconds")
        print("Press Ctrl+C to stop\n")

        while True:
            try:
                if args.input.is_dir():
                    auditor.analyze_directory(args.input, args.year)
                else:
                    auditor.analyze_file(args.input, args.year)

                auditor.print_summary()

                if args.export_webapp:
                    webapp_path = args.output / "webapp_findings.json"
                    auditor.export_for_webapp(webapp_path)

                print(f"\nNext analysis in {args.watch_interval} seconds...")
                time.sleep(args.watch_interval)

            except KeyboardInterrupt:
                print("\nStopping continuous analysis.")
                break
    else:
        # Single run
        if args.input.is_dir():
            results = auditor.analyze_directory(args.input, args.year)
            print(f"\n\nAnalyzed {results['files_analyzed']} files")
            print(f"Total items: {results['total_items']}")
            print(f"New findings: {results['new_findings']}")
            print(f"Duplicates skipped: {results['duplicate_findings']}")
        else:
            # Check if this is a master file with multi-year data
            is_master = 'master' in args.input.name.lower()

            if not is_master:
                # Peek at the file to check for multi-year data
                with open(args.input) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        items = data.get('items', [])
                        years = set(i.get('year', 2026) for i in items[:100])
                        is_master = len(years) > 1

            if is_master:
                results = auditor.analyze_master_file(args.input)
                print(f"\n\n{'='*60}")
                print("MULTI-YEAR ANALYSIS COMPLETE")
                print(f"{'='*60}")
                if 'error' not in results:
                    print(f"Years analyzed: {results['years_analyzed']}")
                    print(f"Total items: {results['total_items']:,}")
                    print(f"New findings: {results['new_findings']}")
                    print(f"Duplicates skipped: {results['duplicate_findings']}")
                    print(f"\nBy Type:")
                    for typ, count in results['findings'].items():
                        if count > 0:
                            print(f"  {typ}: {count}")
            else:
                auditor.analyze_file(args.input, args.year)

        auditor.print_summary()

        if args.export_webapp:
            webapp_path = args.output / "webapp_findings.json"
            auditor.export_for_webapp(webapp_path)


if __name__ == "__main__":
    main()
