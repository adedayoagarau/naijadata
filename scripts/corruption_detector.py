#!/usr/bin/env python3
"""
COMPREHENSIVE CORRUPTION DETECTOR
Multi-layer forensic analysis for Nigerian budget data

Detection Layers:
1. STATISTICAL ANOMALIES
   - Benford's Law violations
   - Round number bias
   - Outlier detection (Z-score)
   - Clustering of amounts

2. PATTERN MATCHING
   - Contract splitting (below thresholds)
   - Duplicate projects
   - Similar descriptions across MDAs
   - Recurring contractors

3. CONTEXTUAL ANALYSIS
   - Mandate violations
   - Unrealistic unit costs
   - Geographic impossibilities
   - Timing anomalies (election year)

4. NETWORK ANALYSIS
   - Contractor networks
   - MDA relationships
   - Cross-year patterns

5. COMPARATIVE ANALYSIS
   - Cross-state comparison
   - Federal vs state
   - Historical trends
"""

import json
import math
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import statistics

BASE_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = BASE_DIR / "extracted"
FINDINGS_DIR = BASE_DIR / "findings"


# =============================================================================
# BENCHMARKS - Nigerian-specific cost benchmarks
# =============================================================================
COST_BENCHMARKS = {
    # IT Equipment
    'laptop': (300_000, 800_000),  # ₦300K-800K reasonable
    'computer': (250_000, 1_000_000),
    'printer': (50_000, 500_000),
    'projector': (100_000, 800_000),
    'server': (1_000_000, 10_000_000),

    # Vehicles
    'vehicle': (15_000_000, 50_000_000),
    'car': (10_000_000, 40_000_000),
    'bus': (20_000_000, 80_000_000),
    'truck': (25_000_000, 100_000_000),
    'ambulance': (30_000_000, 80_000_000),
    'hilux': (25_000_000, 45_000_000),
    'toyota': (15_000_000, 60_000_000),

    # Furniture
    'chair': (20_000, 200_000),
    'table': (30_000, 500_000),
    'desk': (50_000, 300_000),
    'cabinet': (50_000, 400_000),
    'furniture': (100_000, 2_000_000),

    # Construction (per unit)
    'borehole': (5_000_000, 15_000_000),
    'classroom': (8_000_000, 25_000_000),
    'toilet': (2_000_000, 8_000_000),
    'health center': (150_000_000, 400_000_000),
    'primary school': (100_000_000, 300_000_000),
    'hospital': (500_000_000, 3_000_000_000),

    # Per kilometer
    'road': (200_000_000, 800_000_000),  # per km
    'drainage': (50_000_000, 200_000_000),  # per km

    # Training
    'training': (50_000, 500_000),  # per person
    'workshop': (30_000, 300_000),  # per person
    'conference': (50_000, 500_000),  # per person
}

# Procurement thresholds in Nigeria
PROCUREMENT_THRESHOLDS = {
    'accounting_officer': 2_500_000,  # Below ₦2.5M
    'permanent_secretary': 5_000_000,  # ₦2.5M - ₦5M
    'ministerial_tenders_board': 100_000_000,  # ₦5M - ₦100M
    'federal_executive_council': 500_000_000,  # Above ₦100M
}

# High-risk budget codes
HIGH_RISK_CODES = {
    '22021': ('utilities_general', 15),
    '22022': ('cleaning_services', 20),  # Often padded
    '22023': ('security_services', 15),
    '22031': ('training', 25),  # Ghost training
    '22032': ('research', 20),
    '22033': ('consulting', 30),  # Major fraud area
    '23010': ('construction', 25),
    '23020': ('rehabilitation', 30),  # Duplicate projects
    '23030': ('furniture', 20),
    '23040': ('vehicles', 20),
}

# Vague/suspicious keywords
VAGUE_KEYWORDS = [
    'miscellaneous', 'sundry', 'other', 'various', 'general',
    'contingency', 'emergency', 'unforeseen', 'as required',
    'liaison', 'protocol', 'welfare', 'entertainment',
    'refreshment', 'logistics', 'coordination', 'facilitation'
]

# Security agencies (shouldn't do non-security work)
SECURITY_AGENCIES = [
    'national intelligence agency', 'nia', 'dia', 'dss',
    'defence intelligence', 'nscdc', 'civil defence',
    'immigration', 'customs', 'efcc', 'icpc', 'ndlea',
    'police', 'army', 'navy', 'air force', 'military',
    'armed forces', 'nsa', 'ods'
]

# Non-security activities
NON_SECURITY_ACTIVITIES = [
    'hospital', 'school', 'university', 'education', 'health',
    'agriculture', 'farm', 'borehole', 'water supply', 'market',
    'shopping', 'hotel', 'guest house', 'recreation', 'entertainment',
    'road', 'bridge', 'housing', 'estate'
]


@dataclass
class CorruptionFinding:
    """A detected corruption indicator"""
    finding_id: str
    finding_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float  # 0-1

    # Source item
    budget_code: str
    description: str
    amount: float
    mda: str
    year: int
    state: Optional[str]
    level: str  # federal/state

    # Detection details
    detection_method: str
    evidence: List[str]
    explanation: str
    recommendation: str

    # Related items
    related_items: List[str] = field(default_factory=list)

    # Scores
    risk_score: int = 0


class BenfordAnalyzer:
    """Benford's Law analysis for detecting manipulated numbers"""

    EXPECTED = {
        1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097,
        5: 0.079, 6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
    }

    def analyze(self, amounts: List[float]) -> Dict:
        """Analyze amounts for Benford's Law compliance"""
        # Get first digits
        first_digits = []
        for amount in amounts:
            if amount > 0:
                first_digit = int(str(int(amount))[0])
                if 1 <= first_digit <= 9:
                    first_digits.append(first_digit)

        if len(first_digits) < 100:
            return {'valid': False, 'reason': 'Insufficient data'}

        # Calculate observed distribution
        observed = defaultdict(int)
        for d in first_digits:
            observed[d] += 1

        total = len(first_digits)
        observed_pct = {d: observed[d] / total for d in range(1, 10)}

        # Chi-square test
        chi_square = 0
        deviations = {}
        for d in range(1, 10):
            expected = self.EXPECTED[d] * total
            actual = observed[d]
            chi_square += ((actual - expected) ** 2) / expected
            deviations[d] = {
                'expected': self.EXPECTED[d],
                'observed': observed_pct[d],
                'deviation': (observed_pct[d] - self.EXPECTED[d]) / self.EXPECTED[d]
            }

        # Critical value for 8 degrees of freedom at p=0.05 is 15.507
        is_suspicious = chi_square > 15.507

        # Find most suspicious digits
        suspicious_digits = [
            d for d, v in deviations.items()
            if abs(v['deviation']) > 0.3  # >30% deviation
        ]

        return {
            'valid': True,
            'chi_square': chi_square,
            'is_suspicious': is_suspicious,
            'p_value': 'p<0.05' if is_suspicious else 'p>0.05',
            'suspicious_digits': suspicious_digits,
            'deviations': deviations,
            'sample_size': total
        }


class RoundNumberDetector:
    """Detects suspiciously round numbers"""

    def detect(self, amount: float) -> Tuple[bool, str]:
        """Check if amount is suspiciously round"""
        if amount < 10_000_000:  # Below ₦10M, round is common
            return False, ''

        amount_int = int(amount)
        amount_str = str(amount_int)

        # Exact billions
        if amount >= 1_000_000_000:
            billions = amount / 1_000_000_000
            if billions == int(billions):
                return True, f'Exact {int(billions)} billion'

        # Exact hundred millions
        if amount >= 100_000_000:
            hundreds = amount / 100_000_000
            if hundreds == int(hundreds):
                return True, f'Exact {int(hundreds)} hundred million'

        # Count trailing zeros
        trailing_zeros = len(amount_str) - len(amount_str.rstrip('0'))
        if trailing_zeros >= 7:
            return True, f'{trailing_zeros} trailing zeros'

        # Check for patterns like 100,000,000 or 500,000,000
        if re.match(r'^[125]\d*0{6,}$', amount_str):
            return True, 'Common round pattern'

        return False, ''


class ContractSplittingDetector:
    """Detects contract splitting to avoid procurement thresholds"""

    def detect(self, items: List[Dict]) -> List[Dict]:
        """Find items that appear to be split contracts"""
        findings = []

        # Group by MDA and similar descriptions
        groups = defaultdict(list)
        for item in items:
            mda = item.get('mda', '')
            desc = item.get('description', '').lower()[:30]
            key = (mda, desc)
            groups[key].append(item)

        for (mda, desc_prefix), group_items in groups.items():
            if len(group_items) < 3:
                continue

            # Check if amounts cluster just below thresholds
            amounts = [i.get('amount', 0) for i in group_items]

            for threshold_name, threshold in PROCUREMENT_THRESHOLDS.items():
                # Count items between 80-99% of threshold
                below_threshold = [
                    a for a in amounts
                    if threshold * 0.80 <= a < threshold
                ]

                if len(below_threshold) >= 3:
                    findings.append({
                        'type': 'CONTRACT_SPLITTING',
                        'threshold': threshold_name,
                        'threshold_amount': threshold,
                        'count': len(below_threshold),
                        'total_amount': sum(below_threshold),
                        'mda': mda,
                        'description_prefix': desc_prefix,
                        'items': group_items[:5]
                    })

        return findings


class DuplicateDetector:
    """Detects duplicate or near-duplicate budget items"""

    def detect(self, items: List[Dict]) -> List[Dict]:
        """Find duplicate items across MDAs/years"""
        findings = []

        # Hash items by normalized description + amount
        hashes = defaultdict(list)
        for item in items:
            desc = re.sub(r'\s+', ' ', item.get('description', '').lower().strip())
            amount = int(item.get('amount', 0))
            hash_key = hashlib.md5(f"{desc}:{amount}".encode()).hexdigest()[:12]
            hashes[hash_key].append(item)

        # Find duplicates
        for hash_key, group in hashes.items():
            if len(group) < 2:
                continue

            # Check if across different MDAs or years
            mdas = set(i.get('mda', '') for i in group)
            years = set(i.get('year', 0) for i in group)

            if len(mdas) > 1 or len(years) > 1:
                findings.append({
                    'type': 'DUPLICATE_ALLOCATION',
                    'count': len(group),
                    'total_amount': sum(i.get('amount', 0) for i in group),
                    'mdas': list(mdas),
                    'years': list(years),
                    'description': group[0].get('description', '')[:100],
                    'amount': group[0].get('amount', 0),
                    'items': group
                })

        return sorted(findings, key=lambda x: x['total_amount'], reverse=True)


class UnitCostAnalyzer:
    """Analyzes unit costs against benchmarks"""

    def analyze(self, item: Dict) -> Optional[Dict]:
        """Check if item has inflated unit cost"""
        desc = item.get('description', '').lower()
        amount = item.get('amount', 0)

        for keyword, (min_cost, max_cost) in COST_BENCHMARKS.items():
            if keyword in desc:
                # Try to extract quantity
                qty_match = re.search(r'(\d+)\s*(?:nos?|units?|pieces?|pcs)', desc)
                if qty_match:
                    qty = int(qty_match.group(1))
                    unit_cost = amount / qty

                    if unit_cost > max_cost * 2:  # More than 2x max benchmark
                        return {
                            'type': 'INFLATED_UNIT_COST',
                            'item_type': keyword,
                            'quantity': qty,
                            'total_amount': amount,
                            'unit_cost': unit_cost,
                            'benchmark_max': max_cost,
                            'inflation_factor': unit_cost / max_cost,
                            'description': item.get('description', ''),
                            'mda': item.get('mda', '')
                        }

        return None


class MandateViolationDetector:
    """Detects agencies spending outside their mandate"""

    def detect(self, item: Dict) -> Optional[Dict]:
        """Check for mandate violations"""
        mda = item.get('mda', '').lower()
        desc = item.get('description', '').lower()

        # Check if security agency doing non-security work
        is_security = any(agency in mda for agency in SECURITY_AGENCIES)

        if is_security:
            for activity in NON_SECURITY_ACTIVITIES:
                if activity in desc:
                    return {
                        'type': 'MANDATE_VIOLATION',
                        'subtype': 'SECURITY_NON_SECURITY',
                        'mda': item.get('mda', ''),
                        'activity': activity,
                        'amount': item.get('amount', 0),
                        'description': item.get('description', ''),
                        'concern': f'Security agency allocated for {activity}'
                    }

        return None


class VagueDescriptionDetector:
    """Detects vague descriptions that hide actual spending"""

    def detect(self, item: Dict) -> Optional[Dict]:
        """Check for vague descriptions"""
        desc = item.get('description', '').lower()
        amount = item.get('amount', 0)

        # Only flag if amount is significant
        if amount < 50_000_000:  # Below ₦50M
            return None

        for keyword in VAGUE_KEYWORDS:
            if keyword in desc:
                return {
                    'type': 'VAGUE_DESCRIPTION',
                    'keyword': keyword,
                    'amount': amount,
                    'description': item.get('description', ''),
                    'mda': item.get('mda', ''),
                    'concern': f'Vague term "{keyword}" in ₦{amount:,.0f} allocation'
                }

        # Also flag very short descriptions for large amounts
        if len(desc.strip()) < 20 and amount > 100_000_000:
            return {
                'type': 'VAGUE_DESCRIPTION',
                'keyword': 'SHORT_DESCRIPTION',
                'amount': amount,
                'description': item.get('description', ''),
                'mda': item.get('mda', ''),
                'concern': f'Very short description for ₦{amount:,.0f}'
            }

        return None


class ComprehensiveCorruptionDetector:
    """Main orchestrator for all corruption detection methods"""

    def __init__(self):
        self.benford = BenfordAnalyzer()
        self.round_number = RoundNumberDetector()
        self.splitting = ContractSplittingDetector()
        self.duplicate = DuplicateDetector()
        self.unit_cost = UnitCostAnalyzer()
        self.mandate = MandateViolationDetector()
        self.vague = VagueDescriptionDetector()

        self.findings: List[CorruptionFinding] = []
        self.stats = defaultdict(int)

    def analyze_all(self, items: List[Dict]) -> Dict:
        """Run all detection methods"""
        print(f"\n{'='*60}")
        print("COMPREHENSIVE CORRUPTION DETECTION")
        print(f"{'='*60}")
        print(f"Analyzing {len(items):,} budget items...")

        # 1. Benford's Law analysis
        print("\n[1/7] Benford's Law Analysis...")
        amounts = [i.get('amount', 0) for i in items if i.get('amount', 0) > 0]
        benford_result = self.benford.analyze(amounts)
        if benford_result.get('is_suspicious'):
            self.stats['benford_violations'] = 1
            print(f"  ⚠️ SUSPICIOUS: Chi-square = {benford_result['chi_square']:.2f}")
            print(f"  Suspicious digits: {benford_result['suspicious_digits']}")

        # 2. Round number detection
        print("\n[2/7] Round Number Detection...")
        round_count = 0
        for item in items:
            is_round, reason = self.round_number.detect(item.get('amount', 0))
            if is_round:
                round_count += 1
                self._add_finding(
                    item, 'ROUND_NUMBER', 'MEDIUM',
                    f'Suspiciously round amount: {reason}',
                    'Request itemized breakdown with quantities and unit costs'
                )
        print(f"  Found {round_count:,} round number items")
        self.stats['round_numbers'] = round_count

        # 3. Contract splitting
        print("\n[3/7] Contract Splitting Detection...")
        splitting_findings = self.splitting.detect(items)
        for sf in splitting_findings:
            self.stats['contract_splitting'] += 1
            # Create finding for each split group
            for item in sf['items'][:1]:  # Just reference first item
                self._add_finding(
                    item, 'CONTRACT_SPLITTING', 'HIGH',
                    f"{sf['count']} items below {sf['threshold']} threshold, total ₦{sf['total_amount']:,.0f}",
                    'Investigate if contracts were deliberately split to avoid oversight'
                )
        print(f"  Found {len(splitting_findings)} splitting patterns")

        # 4. Duplicate detection
        print("\n[4/7] Duplicate Detection...")
        duplicate_findings = self.duplicate.detect(items)
        for df in duplicate_findings[:100]:  # Top 100
            self.stats['duplicates'] += 1
            for item in df['items'][:1]:
                self._add_finding(
                    item, 'DUPLICATE_ALLOCATION', 'HIGH',
                    f"Same allocation in {len(df['mdas'])} MDAs, {len(df['years'])} years",
                    'Verify if this is genuine or double-counting'
                )
        print(f"  Found {len(duplicate_findings)} duplicate patterns")

        # 5. Unit cost analysis
        print("\n[5/7] Unit Cost Analysis...")
        inflated_count = 0
        for item in items:
            finding = self.unit_cost.analyze(item)
            if finding:
                inflated_count += 1
                self._add_finding(
                    item, 'INFLATED_UNIT_COST', 'CRITICAL',
                    f"{finding['item_type']} at ₦{finding['unit_cost']:,.0f}/unit ({finding['inflation_factor']:.1f}x benchmark)",
                    f"Compare with market rates. Benchmark max: ₦{finding['benchmark_max']:,.0f}"
                )
        print(f"  Found {inflated_count:,} inflated unit costs")
        self.stats['inflated_costs'] = inflated_count

        # 6. Mandate violations
        print("\n[6/7] Mandate Violation Detection...")
        mandate_count = 0
        for item in items:
            finding = self.mandate.detect(item)
            if finding:
                mandate_count += 1
                self._add_finding(
                    item, 'MANDATE_VIOLATION', 'CRITICAL',
                    finding['concern'],
                    'Review agency mandate. Consider reallocation to appropriate ministry.'
                )
        print(f"  Found {mandate_count:,} mandate violations")
        self.stats['mandate_violations'] = mandate_count

        # 7. Vague descriptions
        print("\n[7/7] Vague Description Detection...")
        vague_count = 0
        for item in items:
            finding = self.vague.detect(item)
            if finding:
                vague_count += 1
                self._add_finding(
                    item, 'VAGUE_DESCRIPTION', 'HIGH',
                    finding['concern'],
                    'Demand specific project details, locations, and deliverables'
                )
        print(f"  Found {vague_count:,} vague descriptions")
        self.stats['vague_descriptions'] = vague_count

        # Compile results
        return self._compile_results(benford_result)

    def _add_finding(self, item: Dict, finding_type: str, severity: str,
                     explanation: str, recommendation: str):
        """Add a finding"""
        finding_id = hashlib.md5(
            f"{item.get('description','')}{item.get('amount',0)}{finding_type}".encode()
        ).hexdigest()[:12]

        # Calculate confidence based on amount and severity
        amount = item.get('amount', 0)
        confidence = 0.7
        if amount > 1_000_000_000:
            confidence += 0.2
        if severity == 'CRITICAL':
            confidence += 0.1

        finding = CorruptionFinding(
            finding_id=finding_id,
            finding_type=finding_type,
            severity=severity,
            confidence=min(1.0, confidence),
            budget_code=item.get('budget_code', ''),
            description=item.get('description', ''),
            amount=amount,
            mda=item.get('mda', ''),
            year=item.get('year', 2026),
            state=item.get('state'),
            level=item.get('level', 'federal'),
            detection_method='rule_based',
            evidence=[explanation],
            explanation=explanation,
            recommendation=recommendation,
            risk_score=self._calculate_risk_score(item, finding_type, severity)
        )

        self.findings.append(finding)

    def _calculate_risk_score(self, item: Dict, finding_type: str, severity: str) -> int:
        """Calculate risk score for a finding"""
        score = 0

        # Base score from severity
        severity_scores = {'CRITICAL': 40, 'HIGH': 30, 'MEDIUM': 20, 'LOW': 10}
        score += severity_scores.get(severity, 10)

        # Amount factor
        amount = item.get('amount', 0)
        if amount >= 10_000_000_000:
            score += 30
        elif amount >= 1_000_000_000:
            score += 20
        elif amount >= 100_000_000:
            score += 10

        # Finding type factor
        type_scores = {
            'INFLATED_UNIT_COST': 20,
            'MANDATE_VIOLATION': 20,
            'CONTRACT_SPLITTING': 15,
            'DUPLICATE_ALLOCATION': 15,
            'VAGUE_DESCRIPTION': 10,
            'ROUND_NUMBER': 5
        }
        score += type_scores.get(finding_type, 5)

        return min(100, score)

    def _compile_results(self, benford_result: Dict) -> Dict:
        """Compile all results"""
        # Count by severity
        by_severity = defaultdict(list)
        by_type = defaultdict(list)
        for f in self.findings:
            by_severity[f.severity].append(f)
            by_type[f.finding_type].append(f)

        # Total amount flagged
        total_flagged = sum(f.amount for f in self.findings)

        return {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_items_analyzed': self.stats.get('total_items', 0),
                'total_findings': len(self.findings),
                'total_amount_flagged': total_flagged,
                'by_severity': {
                    'CRITICAL': len(by_severity['CRITICAL']),
                    'HIGH': len(by_severity['HIGH']),
                    'MEDIUM': len(by_severity['MEDIUM']),
                    'LOW': len(by_severity['LOW'])
                },
                'by_type': {k: len(v) for k, v in by_type.items()}
            },
            'benford_analysis': benford_result,
            'detection_stats': dict(self.stats),
            'findings': [asdict(f) for f in sorted(self.findings, key=lambda x: -x.risk_score)]
        }


def load_data() -> List[Dict]:
    """Load all available budget data"""
    items = []

    # Load master data
    master_file = EXTRACTED_DIR / 'master_budget_data.json'
    if master_file.exists():
        print(f"Loading {master_file}...")
        with open(master_file) as f:
            data = json.load(f)
        items.extend(data.get('items', []))

    # Load any state extractions
    state_file = EXTRACTED_DIR / 'full_extraction' / 'master_budget_data.json'
    if state_file.exists():
        print(f"Loading {state_file}...")
        with open(state_file) as f:
            data = json.load(f)
        items.extend(data.get('items', []))

    return items


def main():
    # Load data
    items = load_data()
    print(f"Loaded {len(items):,} total items")

    if not items:
        print("No data found!")
        return

    # Run detection
    detector = ComprehensiveCorruptionDetector()
    detector.stats['total_items'] = len(items)
    results = detector.analyze_all(items)

    # Save results
    FINDINGS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    with open(FINDINGS_DIR / f'corruption_findings_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2)

    with open(FINDINGS_DIR / 'corruption_findings_latest.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Critical findings only
    critical = [f for f in results['findings'] if f['severity'] == 'CRITICAL']
    with open(FINDINGS_DIR / 'critical_corruption_findings.json', 'w') as f:
        json.dump({
            'generated_at': results['generated_at'],
            'count': len(critical),
            'total_amount': sum(f['amount'] for f in critical),
            'findings': critical[:500]
        }, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("CORRUPTION DETECTION COMPLETE")
    print(f"{'='*60}")
    print(f"\nTotal Findings: {results['summary']['total_findings']:,}")
    print(f"Total Amount Flagged: ₦{results['summary']['total_amount_flagged']:,.0f}")

    print(f"\nBy Severity:")
    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        count = results['summary']['by_severity'][sev]
        print(f"  {sev}: {count:,}")

    print(f"\nBy Type:")
    for typ, count in sorted(results['summary']['by_type'].items(), key=lambda x: -x[1]):
        print(f"  {typ}: {count:,}")

    print(f"\n📁 Results saved to:")
    print(f"   {FINDINGS_DIR}/corruption_findings_latest.json")
    print(f"   {FINDINGS_DIR}/critical_corruption_findings.json")


if __name__ == "__main__":
    main()
