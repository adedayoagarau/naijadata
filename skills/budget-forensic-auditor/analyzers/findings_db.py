"""
Findings Database

Stores, deduplicates, and manages audit findings.
Provides aggregation, filtering, and export capabilities.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import uuid


@dataclass
class Finding:
    """A standardized audit finding"""
    id: str
    finding_type: str
    entity: str
    budget_code: str
    description: str
    amount: float
    amount_formatted: str
    severity: str
    confidence: float
    analyzer: str
    rule_triggered: str
    evidence: Dict
    recommendation: str
    impact_estimate: Optional[float]
    year: int
    created_at: str
    hash: str  # For deduplication
    tags: List[str] = field(default_factory=list)
    status: str = "NEW"  # NEW, REVIEWED, CONFIRMED, DISMISSED


class FindingsDatabase:
    """
    Manages a database of audit findings.
    Handles persistence, deduplication, and querying.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.findings: Dict[str, Finding] = {}
        self.hashes: Set[str] = set()
        self._load()

    def _load(self):
        """Load existing findings from disk"""
        if self.db_path.exists():
            with open(self.db_path) as f:
                data = json.load(f)
                for item in data.get('findings', []):
                    finding = Finding(**item)
                    self.findings[finding.id] = finding
                    self.hashes.add(finding.hash)

    def _save(self):
        """Save findings to disk"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'total_findings': len(self.findings),
            'findings': [asdict(f) for f in self.findings.values()]
        }
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _compute_hash(self, finding_type: str, entity: str, budget_code: str, amount: float) -> str:
        """Compute hash for deduplication"""
        key = f"{finding_type}|{entity}|{budget_code}|{amount}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

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

    def add_finding(
        self,
        finding_type: str,
        entity: str,
        budget_code: str,
        description: str,
        amount: float,
        severity: str,
        confidence: float,
        analyzer: str,
        rule_triggered: str,
        evidence: Dict,
        recommendation: str,
        impact_estimate: Optional[float] = None,
        year: int = 2026,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Add a finding to the database.
        Returns finding ID if added, None if duplicate.
        """
        # Check for duplicate
        hash_val = self._compute_hash(finding_type, entity, budget_code, amount)
        if hash_val in self.hashes:
            return None

        finding_id = str(uuid.uuid4())[:8]
        finding = Finding(
            id=finding_id,
            finding_type=finding_type,
            entity=entity,
            budget_code=budget_code,
            description=description,
            amount=amount,
            amount_formatted=self._format_amount(amount),
            severity=severity,
            confidence=confidence,
            analyzer=analyzer,
            rule_triggered=rule_triggered,
            evidence=evidence,
            recommendation=recommendation,
            impact_estimate=impact_estimate,
            year=year,
            created_at=datetime.now().isoformat(),
            hash=hash_val,
            tags=tags or [],
            status="NEW"
        )

        self.findings[finding_id] = finding
        self.hashes.add(hash_val)
        self._save()

        return finding_id

    def add_from_analyzer(self, finding_obj, analyzer_name: str, year: int = 2026) -> Optional[str]:
        """Add finding from analyzer output object"""
        # Handle different analyzer output formats
        if hasattr(finding_obj, '__dataclass_fields__'):
            # Dataclass
            return self.add_finding(
                finding_type=getattr(finding_obj, 'finding_type', getattr(finding_obj, 'type', 'UNKNOWN')),
                entity=getattr(finding_obj, 'entity', getattr(finding_obj, 'entity_name', '')),
                budget_code=getattr(finding_obj, 'budget_code', ''),
                description=getattr(finding_obj, 'description', ''),
                amount=getattr(finding_obj, 'amount', getattr(finding_obj, 'current_amount', 0)),
                severity=getattr(finding_obj, 'severity', 'MEDIUM'),
                confidence=getattr(finding_obj, 'confidence', 50),
                analyzer=analyzer_name,
                rule_triggered=getattr(finding_obj, 'rule_triggered', ''),
                evidence=getattr(finding_obj, 'evidence', getattr(finding_obj, 'context', {})),
                recommendation=getattr(finding_obj, 'recommendation', ''),
                impact_estimate=getattr(finding_obj, 'impact_estimate', None),
                year=year,
                tags=getattr(finding_obj, 'tags', [])
            )
        elif isinstance(finding_obj, dict):
            return self.add_finding(
                finding_type=finding_obj.get('type', finding_obj.get('finding_type', 'UNKNOWN')),
                entity=finding_obj.get('entity', ''),
                budget_code=finding_obj.get('budget_code', ''),
                description=finding_obj.get('description', ''),
                amount=finding_obj.get('amount', finding_obj.get('current_amount', 0)),
                severity=finding_obj.get('severity', 'MEDIUM'),
                confidence=finding_obj.get('confidence', 50),
                analyzer=analyzer_name,
                rule_triggered=finding_obj.get('rule_triggered', ''),
                evidence=finding_obj.get('evidence', finding_obj.get('context', {})),
                recommendation=finding_obj.get('recommendation', ''),
                impact_estimate=finding_obj.get('impact_estimate'),
                year=year,
                tags=finding_obj.get('tags', [])
            )
        return None

    def get_finding(self, finding_id: str) -> Optional[Finding]:
        """Get a specific finding by ID"""
        return self.findings.get(finding_id)

    def query(
        self,
        severity: Optional[str] = None,
        finding_type: Optional[str] = None,
        entity: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Finding]:
        """Query findings with filters"""
        results = []

        for finding in self.findings.values():
            if severity and finding.severity != severity:
                continue
            if finding_type and finding.finding_type != finding_type:
                continue
            if entity and entity.lower() not in finding.entity.lower():
                continue
            if min_amount and finding.amount < min_amount:
                continue
            if max_amount and finding.amount > max_amount:
                continue
            if year and finding.year != year:
                continue
            if status and finding.status != status:
                continue

            results.append(finding)

        # Sort by severity, then amount
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        results.sort(key=lambda f: (severity_order.get(f.severity, 4), -f.amount))

        return results[:limit]

    def get_statistics(self) -> Dict:
        """Get aggregate statistics"""
        stats = {
            'total_findings': len(self.findings),
            'by_severity': defaultdict(int),
            'by_type': defaultdict(int),
            'by_analyzer': defaultdict(int),
            'by_status': defaultdict(int),
            'total_impact': 0,
            'top_entities': defaultdict(lambda: {'count': 0, 'amount': 0})
        }

        for finding in self.findings.values():
            stats['by_severity'][finding.severity] += 1
            stats['by_type'][finding.finding_type] += 1
            stats['by_analyzer'][finding.analyzer] += 1
            stats['by_status'][finding.status] += 1

            if finding.impact_estimate:
                stats['total_impact'] += finding.impact_estimate

            stats['top_entities'][finding.entity]['count'] += 1
            stats['top_entities'][finding.entity]['amount'] += finding.amount

        # Convert defaultdicts to regular dicts
        stats['by_severity'] = dict(stats['by_severity'])
        stats['by_type'] = dict(stats['by_type'])
        stats['by_analyzer'] = dict(stats['by_analyzer'])
        stats['by_status'] = dict(stats['by_status'])

        # Top 10 entities
        entities = list(stats['top_entities'].items())
        entities.sort(key=lambda x: x[1]['amount'], reverse=True)
        stats['top_entities'] = dict(entities[:10])
        stats['total_impact_formatted'] = self._format_amount(stats['total_impact'])

        return stats

    def update_status(self, finding_id: str, status: str) -> bool:
        """Update finding status"""
        if finding_id in self.findings:
            self.findings[finding_id].status = status
            self._save()
            return True
        return False

    def export_json(self, filepath: Path, **filters):
        """Export findings to JSON file"""
        findings = self.query(**filters, limit=10000)
        data = {
            'exported_at': datetime.now().isoformat(),
            'total': len(findings),
            'filters': filters,
            'findings': [asdict(f) for f in findings]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def export_for_webapp(self, limit: int = 50) -> List[Dict]:
        """
        Export findings formatted for the webapp display.
        Groups and prioritizes for maximum impact.
        """
        # Get all findings
        all_findings = self.query(limit=1000)

        # Group by entity to avoid repetition
        by_entity = defaultdict(list)
        for f in all_findings:
            by_entity[f.entity].append(f)

        # Select most impactful finding per entity
        selected = []
        for entity, findings in by_entity.items():
            # Sort by severity, then amount
            findings.sort(key=lambda f: (
                {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(f.severity, 4),
                -f.amount
            ))
            selected.append(findings[0])

        # Sort final list
        selected.sort(key=lambda f: (
            {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(f.severity, 4),
            -f.amount
        ))

        # Format for webapp
        webapp_findings = []
        for f in selected[:limit]:
            webapp_findings.append({
                'id': f.id,
                'tag': f.finding_type.replace('_', ' ').title(),
                'tagColor': self._severity_to_color(f.severity),
                'title': f.entity,
                'stat1': {'label': f.finding_type.replace('_', ' '), 'value': f.amount_formatted},
                'highlight': f.severity,
                'highlightColor': self._severity_to_highlight_color(f.severity),
                'description': f.description[:200] if f.description else f.recommendation[:200],
                'shareText': f"{f.entity}: {f.amount_formatted} flagged for {f.finding_type}. {f.recommendation[:100]} #Decide9ja",
                'confidence': f.confidence,
                'recommendation': f.recommendation
            })

        return webapp_findings

    def _severity_to_color(self, severity: str) -> str:
        """Convert severity to Tailwind color class"""
        return {
            'CRITICAL': 'bg-red-500/20 text-red-400',
            'HIGH': 'bg-orange-500/20 text-orange-400',
            'MEDIUM': 'bg-yellow-500/20 text-yellow-400',
            'LOW': 'bg-blue-500/20 text-blue-400'
        }.get(severity, 'bg-gray-500/20 text-gray-400')

    def _severity_to_highlight_color(self, severity: str) -> str:
        """Convert severity to highlight color"""
        return {
            'CRITICAL': 'bg-red-500 text-white',
            'HIGH': 'bg-orange-500 text-white',
            'MEDIUM': 'bg-yellow-500 text-black',
            'LOW': 'bg-blue-500 text-white'
        }.get(severity, 'bg-gray-500 text-white')


if __name__ == "__main__":
    # Demo usage
    db = FindingsDatabase(Path("./findings/findings_db.json"))

    # Add sample finding
    db.add_finding(
        finding_type="MANDATE_VIOLATION",
        entity="National Intelligence Agency",
        budget_code="22020901",
        description="Hospital construction budget",
        amount=31100000000,
        severity="CRITICAL",
        confidence=95,
        analyzer="nigerian_context",
        rule_triggered="security_agency_health_spending",
        evidence={'mda_type': 'security', 'spending_category': 'health'},
        recommendation="Security agency health spending should be under Ministry of Health.",
        impact_estimate=31100000000,
        year=2026
    )

    # Print stats
    stats = db.get_statistics()
    print(json.dumps(stats, indent=2))
