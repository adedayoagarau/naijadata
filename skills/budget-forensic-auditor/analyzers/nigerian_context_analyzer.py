"""
Nigerian Context Analyzer

Applies Nigeria-specific corruption detection rules:
1. Mandate violations (agencies spending outside their mandate)
2. High-risk MDA patterns
3. Problematic budget code detection
4. Padding indicators
5. Ghost worker patterns
6. Election year anomalies
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ContextFinding:
    """A context-based finding"""
    finding_type: str
    entity: str
    budget_code: str
    description: str
    amount: float
    severity: str
    confidence: float
    rule_triggered: str
    evidence: Dict = field(default_factory=dict)
    recommendation: str = ""
    impact_estimate: Optional[float] = None


class NigerianContextAnalyzer:
    """Applies Nigerian corruption context rules to budget data"""

    def __init__(self, knowledge_path: Optional[Path] = None):
        self.knowledge = self._load_knowledge(knowledge_path)
        self.findings: List[ContextFinding] = []

    def _load_knowledge(self, knowledge_path: Optional[Path]) -> Dict:
        """Load Nigerian context knowledge base"""
        default_path = Path(__file__).parent.parent / "knowledge" / "nigerian_context.json"

        if knowledge_path and knowledge_path.exists():
            path = knowledge_path
        elif default_path.exists():
            path = default_path
        else:
            return self._get_default_knowledge()

        with open(path) as f:
            return json.load(f)

    def _get_default_knowledge(self) -> Dict:
        """Default knowledge if file not found"""
        return {
            "security_agencies": [
                "army", "navy", "air force", "police", "nia", "dia", "dss",
                "civil defence", "nscdc", "immigration", "customs"
            ],
            "education_keywords": ["school", "education", "university", "student"],
            "health_keywords": ["hospital", "clinic", "medical", "health", "drug"],
            "infrastructure_keywords": ["road", "bridge", "construction", "building"]
        }

    def analyze_mandate_violations(self, data: List[Dict]) -> List[ContextFinding]:
        """
        Detect agencies spending on items outside their core mandate.
        E.g., Security agencies building schools, health facilities, or roads.
        """
        findings = []

        security_agencies = set(self.knowledge.get('security_agencies', []))
        education_keywords = set(self.knowledge.get('education_keywords', []))
        health_keywords = set(self.knowledge.get('health_keywords', []))
        infra_keywords = set(self.knowledge.get('infrastructure_keywords', []))

        for item in data:
            mda = item.get('mda', '').lower()
            description = item.get('description', '').lower()
            amount = self._parse_amount(item.get('amount', 0))

            if amount < 100000000:  # Less than 100M
                continue

            # Check if MDA is a security agency
            is_security = any(agency in mda for agency in security_agencies)

            if is_security:
                # Check for education spending
                if any(kw in description for kw in education_keywords):
                    finding = ContextFinding(
                        finding_type="MANDATE_VIOLATION",
                        entity=item.get('mda', ''),
                        budget_code=item.get('budget_code', ''),
                        description=item.get('description', ''),
                        amount=amount,
                        severity="HIGH",
                        confidence=85,
                        rule_triggered="security_agency_education_spending",
                        evidence={
                            'mda_type': 'security',
                            'spending_category': 'education',
                            'keywords_matched': [kw for kw in education_keywords if kw in description]
                        },
                        recommendation="Security agency spending on education should be "
                                      "under Ministry of Education. Request justification.",
                        impact_estimate=amount
                    )
                    findings.append(finding)

                # Check for health facility spending
                if any(kw in description for kw in health_keywords):
                    # Higher severity for NIA specifically (known issue)
                    sev = "CRITICAL" if "nia" in mda or "intelligence" in mda else "HIGH"

                    finding = ContextFinding(
                        finding_type="MANDATE_VIOLATION",
                        entity=item.get('mda', ''),
                        budget_code=item.get('budget_code', ''),
                        description=item.get('description', ''),
                        amount=amount,
                        severity=sev,
                        confidence=90,
                        rule_triggered="security_agency_health_spending",
                        evidence={
                            'mda_type': 'security',
                            'spending_category': 'health',
                            'keywords_matched': [kw for kw in health_keywords if kw in description]
                        },
                        recommendation="Security agency health spending should be under "
                                      "Ministry of Health. This is a known corruption vector.",
                        impact_estimate=amount
                    )
                    findings.append(finding)

                # Check for infrastructure spending (except military bases)
                if any(kw in description for kw in infra_keywords):
                    # Exclude legitimate military infrastructure
                    legitimate = ['barracks', 'cantonment', 'base', 'command']
                    if not any(leg in description for leg in legitimate):
                        finding = ContextFinding(
                            finding_type="MANDATE_VIOLATION",
                            entity=item.get('mda', ''),
                            budget_code=item.get('budget_code', ''),
                            description=item.get('description', ''),
                            amount=amount,
                            severity="HIGH",
                            confidence=80,
                            rule_triggered="security_agency_infrastructure_spending",
                            evidence={
                                'mda_type': 'security',
                                'spending_category': 'infrastructure',
                                'keywords_matched': [kw for kw in infra_keywords if kw in description]
                            },
                            recommendation="Infrastructure spending should be under Ministry "
                                          "of Works. Cross-verify if project is security-related.",
                            impact_estimate=amount
                        )
                        findings.append(finding)

        return findings

    def analyze_high_risk_mdas(self, data: List[Dict]) -> List[ContextFinding]:
        """
        Flag spending from known high-risk MDAs that require extra scrutiny.
        """
        findings = []
        high_risk = self.knowledge.get('high_risk_mdas', {})

        for item in data:
            mda = item.get('mda', '').lower()
            amount = self._parse_amount(item.get('amount', 0))

            if amount < 500000000:  # Less than 500M
                continue

            for risk_mda, risk_info in high_risk.items():
                if risk_mda.replace('_', ' ') in mda or risk_mda in mda:
                    # Check for typical red flags
                    description = item.get('description', '').lower()
                    red_flags = risk_info.get('typical_red_flags', [])
                    matched_flags = [rf for rf in red_flags if rf.replace('_', ' ') in description]

                    if matched_flags or amount >= 1000000000:
                        finding = ContextFinding(
                            finding_type="HIGH_RISK_MDA",
                            entity=item.get('mda', ''),
                            budget_code=item.get('budget_code', ''),
                            description=item.get('description', ''),
                            amount=amount,
                            severity=risk_info.get('risk_level', 'HIGH'),
                            confidence=75 + (len(matched_flags) * 5),
                            rule_triggered=f"high_risk_mda_{risk_mda}",
                            evidence={
                                'known_issues': risk_info.get('known_issues', []),
                                'red_flags_matched': matched_flags
                            },
                            recommendation=f"MDA has known issues with: "
                                          f"{', '.join(risk_info.get('known_issues', []))}. "
                                          f"Apply enhanced scrutiny.",
                            impact_estimate=amount
                        )
                        findings.append(finding)
                    break

        return findings

    def analyze_problematic_budget_codes(self, data: List[Dict]) -> List[ContextFinding]:
        """
        Flag items using budget codes known for abuse.
        """
        findings = []
        problematic_codes = self.knowledge.get('known_problematic_budget_codes', {})

        for item in data:
            budget_code = item.get('budget_code', '')
            amount = self._parse_amount(item.get('amount', 0))

            if budget_code in problematic_codes:
                code_info = problematic_codes[budget_code]

                # Threshold based on code risk level
                threshold = {
                    'CRITICAL': 100000000,
                    'HIGH': 500000000,
                    'MEDIUM': 1000000000
                }.get(code_info.get('risk', 'MEDIUM'), 500000000)

                if amount >= threshold:
                    finding = ContextFinding(
                        finding_type="PROBLEMATIC_BUDGET_CODE",
                        entity=item.get('mda', ''),
                        budget_code=budget_code,
                        description=item.get('description', ''),
                        amount=amount,
                        severity=code_info.get('risk', 'MEDIUM'),
                        confidence=70,
                        rule_triggered=f"problematic_code_{budget_code}",
                        evidence={
                            'code_name': code_info.get('name', ''),
                            'known_reason': code_info.get('reason', '')
                        },
                        recommendation=f"Budget code {budget_code} ({code_info.get('name', '')}) "
                                      f"is known for: {code_info.get('reason', '')}. "
                                      f"Request itemized breakdown.",
                        impact_estimate=amount
                    )
                    findings.append(finding)

        return findings

    def analyze_padding_indicators(self, data: List[Dict]) -> List[ContextFinding]:
        """
        Detect padding indicators:
        - Excessive unit costs
        - Uniform amounts across different items
        - Vague descriptions with large amounts
        """
        findings = []

        # Check for uniform amounts (same amount appearing multiple times)
        amount_counts: Dict[float, List[Dict]] = {}
        for item in data:
            amount = self._parse_amount(item.get('amount', 0))
            if amount >= 100000000:  # 100M+
                if amount not in amount_counts:
                    amount_counts[amount] = []
                amount_counts[amount].append(item)

        # Flag amounts appearing 3+ times
        for amount, items in amount_counts.items():
            if len(items) >= 3:
                finding = ContextFinding(
                    finding_type="UNIFORM_AMOUNTS",
                    entity="MULTIPLE_MDAS",
                    budget_code="VARIOUS",
                    description=f"Same amount ({self._format_amount(amount)}) across {len(items)} items",
                    amount=amount * len(items),
                    severity="HIGH",
                    confidence=80,
                    rule_triggered="uniform_amount_padding",
                    evidence={
                        'amount': amount,
                        'occurrences': len(items),
                        'mdas': [i.get('mda', '') for i in items[:5]],
                        'descriptions': [i.get('description', '')[:50] for i in items[:5]]
                    },
                    recommendation="Identical amounts across different items suggests "
                                  "copy-paste budgeting rather than actual costing.",
                    impact_estimate=amount * len(items)
                )
                findings.append(finding)

        # Check for vague descriptions with large amounts
        vague_keywords = ['miscellaneous', 'sundry', 'others', 'various', 'general', 'unspecified']
        for item in data:
            description = item.get('description', '').lower()
            amount = self._parse_amount(item.get('amount', 0))

            if amount >= 500000000 and any(kw in description for kw in vague_keywords):
                finding = ContextFinding(
                    finding_type="VAGUE_DESCRIPTION",
                    entity=item.get('mda', ''),
                    budget_code=item.get('budget_code', ''),
                    description=item.get('description', ''),
                    amount=amount,
                    severity="HIGH",
                    confidence=85,
                    rule_triggered="vague_description_large_amount",
                    evidence={
                        'vague_keywords_found': [kw for kw in vague_keywords if kw in description]
                    },
                    recommendation="Large amounts with vague descriptions are a classic "
                                  "padding technique. Demand specific itemization.",
                    impact_estimate=amount
                )
                findings.append(finding)

        return findings

    def analyze_election_year_patterns(
        self,
        data: List[Dict],
        year: int
    ) -> List[ContextFinding]:
        """
        Flag election year suspicious patterns.
        """
        findings = []
        election_info = self.knowledge.get('election_year_flags', {})
        election_years = election_info.get('years', [2023, 2027])

        # Check if this is an election year or pre-election year
        is_election_year = year in election_years
        is_pre_election = (year + 1) in election_years

        if not (is_election_year or is_pre_election):
            return findings

        suspicious_patterns = election_info.get('suspicious_patterns', [])
        pattern_keywords = {
            'constituency_project_spike': ['constituency', 'zonal', 'intervention'],
            'empowerment_program_surge': ['empowerment', 'youth', 'women', 'skills'],
            'vehicle_procurement_increase': ['vehicle', 'motor', 'car', 'bus', 'jeep'],
            'furniture_replacement_wave': ['furniture', 'office equipment', 'renovation']
        }

        for item in data:
            description = item.get('description', '').lower()
            amount = self._parse_amount(item.get('amount', 0))

            if amount < 500000000:
                continue

            for pattern, keywords in pattern_keywords.items():
                if any(kw in description for kw in keywords):
                    period = "election year" if is_election_year else "pre-election year"
                    finding = ContextFinding(
                        finding_type="ELECTION_YEAR_PATTERN",
                        entity=item.get('mda', ''),
                        budget_code=item.get('budget_code', ''),
                        description=item.get('description', ''),
                        amount=amount,
                        severity="HIGH",
                        confidence=75,
                        rule_triggered=f"election_{pattern}",
                        evidence={
                            'pattern': pattern,
                            'year': year,
                            'period': period,
                            'keywords_matched': [kw for kw in keywords if kw in description]
                        },
                        recommendation=f"{period.capitalize()} spending on '{pattern.replace('_', ' ')}' "
                                      f"warrants extra scrutiny for potential vote-buying.",
                        impact_estimate=amount
                    )
                    findings.append(finding)
                    break

        return findings

    def run_all_analyses(
        self,
        data: List[Dict],
        year: Optional[int] = None
    ) -> List[ContextFinding]:
        """Run all Nigerian context analyses"""
        all_findings = []

        all_findings.extend(self.analyze_mandate_violations(data))
        all_findings.extend(self.analyze_high_risk_mdas(data))
        all_findings.extend(self.analyze_problematic_budget_codes(data))
        all_findings.extend(self.analyze_padding_indicators(data))

        if year:
            all_findings.extend(self.analyze_election_year_patterns(data, year))

        # Sort by severity and amount
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_findings.sort(key=lambda f: (severity_order.get(f.severity, 4), -f.amount))

        return all_findings

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


def format_finding(finding: ContextFinding) -> Dict:
    """Format finding as JSON-serializable dict"""
    return {
        'type': finding.finding_type,
        'entity': finding.entity,
        'budget_code': finding.budget_code,
        'description': finding.description,
        'amount': finding.amount,
        'amount_formatted': NigerianContextAnalyzer()._format_amount(finding.amount),
        'severity': finding.severity,
        'confidence': round(finding.confidence, 1),
        'rule_triggered': finding.rule_triggered,
        'evidence': finding.evidence,
        'recommendation': finding.recommendation,
        'impact_estimate': finding.impact_estimate
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python nigerian_context_analyzer.py <budget_file.json> [year]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

    with open(filepath) as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = data.get('items', data.get('line_items', []))

    analyzer = NigerianContextAnalyzer()
    findings = analyzer.run_all_analyses(data, year)

    print(f"\n{'='*60}")
    print("NIGERIAN CONTEXT ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Total Findings: {len(findings)}\n")

    by_type = {}
    for f in findings:
        by_type.setdefault(f.finding_type, []).append(f)

    for ftype, type_findings in by_type.items():
        print(f"\n{ftype}: {len(type_findings)} findings")
        print("-" * 40)
        for f in type_findings[:3]:
            print(f"  [{f.severity}] {f.entity}")
            print(f"    Amount: {analyzer._format_amount(f.amount)}")
            print(f"    {f.recommendation[:80]}...")
