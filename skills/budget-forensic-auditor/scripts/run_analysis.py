#!/usr/bin/env python3
"""
Budget Forensic Auditor - Main Analysis Runner

Orchestrates all analyzers and aggregates findings into a unified database.

Usage:
    python run_analysis.py --input ../extracted/ --output ../findings/
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
            auditor.analyze_file(args.input, args.year)

        auditor.print_summary()

        if args.export_webapp:
            webapp_path = args.output / "webapp_findings.json"
            auditor.export_for_webapp(webapp_path)


if __name__ == "__main__":
    main()
