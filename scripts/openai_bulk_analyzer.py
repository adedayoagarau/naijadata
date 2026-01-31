#!/usr/bin/env python3
"""
OpenAI GPT-4 Bulk Budget Analyzer
Uses OpenAI's GPT-4 model to perform line-by-line forensic analysis
of Nigerian federal and state budget data.
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Model options: gpt-4o, gpt-4o-mini, gpt-4-turbo
MODEL = "gpt-4o-mini"  # Cost-effective for bulk analysis

# Processing configuration
BATCH_SIZE = 25  # Items per batch (smaller for GPT to ensure quality)
MAX_CONCURRENT_REQUESTS = 3  # Parallel API calls
RATE_LIMIT_DELAY = 1.0  # Seconds between requests (OpenAI rate limits)
CHECKPOINT_INTERVAL = 50  # Save progress every N batches

# Paths
BASE_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = BASE_DIR / "extracted"
FINDINGS_DIR = BASE_DIR / "findings"
CHECKPOINT_DIR = BASE_DIR / "data" / "openai_checkpoints"


@dataclass
class AnalysisResult:
    """Result from GPT analysis of a budget item."""
    item_id: str
    budget_code: str
    description: str
    amount: float
    mda: str
    year: int
    level: str
    state: Optional[str]

    # Analysis fields
    risk_score: int  # 0-100
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    anomaly_types: List[str]
    red_flags: List[str]
    explanation: str
    recommendation: str
    confidence: float  # 0-1

    # Comparisons
    similar_items_concern: Optional[str] = None
    historical_pattern: Optional[str] = None

    # Metadata
    analyzed_at: str = ""
    model_used: str = MODEL


SYSTEM_PROMPT = """You are an expert forensic budget analyst specializing in Nigerian government finances. You have deep knowledge of:

1. **Nigerian Budget Structure**:
   - MDAs (Ministries, Departments, Agencies)
   - Budget codes: 21xxx=Personnel, 22xxx=Overhead, 23xxx=Capital
   - Appropriation patterns and fiscal year cycles

2. **Common Corruption Patterns in Nigeria**:
   - Round number bias (exact billions/millions suggest estimation, not actual costing)
   - Mandate violations (agencies spending outside their legal scope)
   - Ghost workers (inflated personnel costs without corresponding staff)
   - Budget padding (inflated unit costs for procurement items)
   - Duplicate allocations across MDAs
   - Vague descriptions ("miscellaneous", "contingency", "sundry")
   - Election year spending spikes

3. **High-Risk MDAs** (historically problematic):
   - National Assembly (NASS) - excessive overhead, travel abuse
   - NNPC - opacity, subsidy fraud
   - NDDC - project abandonment, fraud
   - NIA/DIA - classified spending abuse
   - Presidency - security vote opacity
   - Ministry of Niger Delta - duplicate projects

4. **Reasonable Cost Benchmarks**:
   - Laptop/computer: ₦300,000-500,000
   - Standard official vehicle: ₦15-30 million
   - Primary school construction: ₦100-150 million
   - Health center: ₦150-250 million
   - Borehole: ₦5-10 million
   - Road per km: ₦200-500 million (depending on terrain)

5. **Red Flags to Watch**:
   - Security agencies with education/health/infrastructure spending (mandate violation)
   - Travel budgets exceeding operational budgets
   - Annual furniture replacement
   - Training costs > ₦500,000 per staff
   - Overtime exceeding 30% of base salary
   - Single vendor getting multiple contracts
   - Projects in non-existent locations

Analyze budget items objectively and identify genuine concerns, not false positives."""

USER_PROMPT_TEMPLATE = """Analyze these Nigerian government budget items for anomalies, corruption indicators, and red flags.

BUDGET ITEMS TO ANALYZE:
{items_json}

For EACH item, provide analysis in this exact JSON format:
{{
  "analyses": [
    {{
      "item_id": "<item_id from input>",
      "risk_score": <0-100 integer>,
      "risk_level": "<CRITICAL|HIGH|MEDIUM|LOW>",
      "anomaly_types": ["<type1>", "<type2>"],
      "red_flags": ["<specific concern 1>", "<specific concern 2>"],
      "explanation": "<brief explanation of why this is suspicious or normal>",
      "recommendation": "<what investigators should verify>",
      "confidence": <0.0-1.0 float>,
      "similar_items_concern": "<if pattern detected with other items in batch, else null>",
      "historical_pattern": "<if unusual compared to typical budgets, else null>"
    }}
  ]
}}

ANOMALY TYPES (use these exact strings):
- ROUND_NUMBER: Suspiciously round figures (exact billions/millions)
- MANDATE_VIOLATION: Agency spending outside its legal mandate
- EXCESSIVE_AMOUNT: Amount too high for the described item
- VAGUE_DESCRIPTION: Description too vague to verify spending
- PADDING_INDICATOR: Unit cost appears inflated
- HIGH_RISK_MDA: From historically problematic agency
- DUPLICATE_SUSPECTED: Appears similar to other allocations
- YOY_SPIKE: Unusual increase from previous years
- GHOST_WORKER_PATTERN: Personnel costs inconsistent with staffing
- ELECTION_YEAR_ANOMALY: Suspicious spending timing around elections
- PROCUREMENT_RED_FLAG: Procurement process concerns
- NORMAL: No significant concerns

RISK SCORING GUIDE:
- 0-25 (LOW): Normal budget item, standard government spending
- 26-50 (MEDIUM): Minor irregularities worth noting, may need context
- 51-75 (HIGH): Significant red flags requiring review
- 76-100 (CRITICAL): Strong corruption indicators, priority for investigation

Be rigorous but fair. Not every large amount is suspicious. Consider context.

Return ONLY valid JSON, no markdown formatting or text outside the JSON structure."""


class OpenAIBulkAnalyzer:
    """Bulk analyzer using OpenAI GPT-4 for Nigerian budget forensics."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.api_key = OPENAI_API_KEY
        self.results: List[AnalysisResult] = []
        self.errors: List[Dict] = []
        self.processed_ids: set = set()
        self.batch_size = BATCH_SIZE
        self.model = MODEL

        # Stats
        self.total_tokens_used = 0
        self.api_calls_made = 0

        # Create directories
        FINDINGS_DIR.mkdir(exist_ok=True)
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

        # Load checkpoint if exists
        self._load_checkpoint()

    def _generate_item_id(self, item: Dict) -> str:
        """Generate unique ID for a budget item."""
        key = f"{item.get('year', '')}-{item.get('budget_code', '')}-{item.get('mda', '')}-{item.get('amount', '')}-{item.get('description', '')[:50]}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def _load_checkpoint(self):
        """Load previous progress if available."""
        checkpoint_file = CHECKPOINT_DIR / "latest_checkpoint.json"
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)
                self.processed_ids = set(data.get('processed_ids', []))
                self.total_tokens_used = data.get('total_tokens_used', 0)
                self.api_calls_made = data.get('api_calls_made', 0)
                print(f"✓ Loaded checkpoint: {len(self.processed_ids):,} items already processed")
                print(f"  Tokens used so far: {self.total_tokens_used:,}")
            except Exception as e:
                print(f"⚠ Could not load checkpoint: {e}")

    def _save_checkpoint(self):
        """Save current progress."""
        checkpoint_file = CHECKPOINT_DIR / "latest_checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'processed_ids': list(self.processed_ids),
                'total_tokens_used': self.total_tokens_used,
                'api_calls_made': self.api_calls_made,
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(self.processed_ids),
                'model': self.model
            }, f)

    async def _call_openai_api(self, session: aiohttp.ClientSession, items: List[Dict]) -> Optional[Dict]:
        """Make API call to OpenAI."""
        # Prepare items for analysis
        items_for_analysis = []
        for item in items:
            item_id = self._generate_item_id(item)
            items_for_analysis.append({
                "item_id": item_id,
                "budget_code": item.get('budget_code', 'N/A'),
                "description": item.get('description', 'N/A'),
                "amount": item.get('amount', 0),
                "amount_formatted": f"₦{item.get('amount', 0):,.2f}",
                "mda": item.get('mda', 'N/A'),
                "mda_code": item.get('mda_code', 'N/A'),
                "category": item.get('category', 'N/A'),
                "year": item.get('year', 'N/A'),
                "level": item.get('level', 'federal'),
                "state": item.get('state')
            })

        user_prompt = USER_PROMPT_TEMPLATE.format(
            items_json=json.dumps(items_for_analysis, indent=2)
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,  # Lower for consistent analysis
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}  # Ensure JSON output
        }

        try:
            async with session.post(OPENAI_API_URL, headers=headers, json=payload) as response:
                self.api_calls_made += 1

                if response.status == 200:
                    result = await response.json()

                    # Track token usage
                    usage = result.get('usage', {})
                    self.total_tokens_used += usage.get('total_tokens', 0)

                    content = result['choices'][0]['message']['content']

                    try:
                        return json.loads(content.strip())
                    except json.JSONDecodeError as e:
                        print(f"    ⚠ JSON parse error: {e}")
                        self.errors.append({
                            'type': 'json_parse_error',
                            'content': content[:500],
                            'error': str(e)
                        })
                        return None

                elif response.status == 429:
                    # Rate limited - wait and retry
                    print("    ⚠ Rate limited, waiting 60s...")
                    await asyncio.sleep(60)
                    return await self._call_openai_api(session, items)

                else:
                    error_text = await response.text()
                    print(f"    ✗ API error {response.status}: {error_text[:200]}")
                    self.errors.append({
                        'type': 'api_error',
                        'status': response.status,
                        'error': error_text[:500]
                    })
                    return None

        except Exception as e:
            print(f"    ✗ Request error: {e}")
            self.errors.append({
                'type': 'request_error',
                'error': str(e)
            })
            return None

    def _parse_analysis_results(self, response: Dict, original_items: List[Dict]) -> List[AnalysisResult]:
        """Parse OpenAI response into structured results."""
        results = []
        analyses = response.get('analyses', [])

        # Create lookup for original items
        item_lookup = {self._generate_item_id(item): item for item in original_items}

        for analysis in analyses:
            item_id = analysis.get('item_id', '')
            original = item_lookup.get(item_id, {})

            if not original:
                continue

            result = AnalysisResult(
                item_id=item_id,
                budget_code=original.get('budget_code', 'N/A'),
                description=original.get('description', 'N/A'),
                amount=original.get('amount', 0),
                mda=original.get('mda', 'N/A'),
                year=original.get('year', 0),
                level=original.get('level', 'federal'),
                state=original.get('state'),
                risk_score=analysis.get('risk_score', 0),
                risk_level=analysis.get('risk_level', 'LOW'),
                anomaly_types=analysis.get('anomaly_types', []),
                red_flags=analysis.get('red_flags', []),
                explanation=analysis.get('explanation', ''),
                recommendation=analysis.get('recommendation', ''),
                confidence=analysis.get('confidence', 0.5),
                similar_items_concern=analysis.get('similar_items_concern'),
                historical_pattern=analysis.get('historical_pattern'),
                analyzed_at=datetime.now().isoformat(),
                model_used=self.model
            )
            results.append(result)
            self.processed_ids.add(item_id)

        return results

    async def analyze_batch(self, session: aiohttp.ClientSession, batch: List[Dict], batch_num: int) -> List[AnalysisResult]:
        """Analyze a batch of items."""
        # Filter out already processed items
        unprocessed = [item for item in batch if self._generate_item_id(item) not in self.processed_ids]

        if not unprocessed:
            return []

        response = await self._call_openai_api(session, unprocessed)

        if response:
            results = self._parse_analysis_results(response, unprocessed)
            return results

        return []

    async def run_analysis(self, items: List[Dict], max_items: Optional[int] = None):
        """Run bulk analysis on all items."""
        if max_items:
            items = items[:max_items]

        total_items = len(items)
        remaining = len([i for i in items if self._generate_item_id(i) not in self.processed_ids])

        print(f"\n{'='*60}")
        print(f"OpenAI GPT-4 Bulk Budget Analyzer")
        print(f"{'='*60}")
        print(f"Total items: {total_items:,}")
        print(f"Already processed: {len(self.processed_ids):,}")
        print(f"Remaining: {remaining:,}")
        print(f"Batch size: {self.batch_size}")
        print(f"Model: {self.model}")
        print(f"{'='*60}\n")

        if remaining == 0:
            print("All items already processed!")
            return

        # Create batches
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
        total_batches = len(batches)

        start_time = datetime.now()

        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS)
        timeout = aiohttp.ClientTimeout(total=120)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i, batch in enumerate(batches):
                batch_num = i + 1

                # Skip if all items in batch are processed
                unprocessed_count = len([item for item in batch if self._generate_item_id(item) not in self.processed_ids])
                if unprocessed_count == 0:
                    continue

                # Rate limiting
                await asyncio.sleep(RATE_LIMIT_DELAY)

                try:
                    print(f"Batch {batch_num}/{total_batches} ({unprocessed_count} items)...", end=" ")
                    results = await self.analyze_batch(session, batch, batch_num)
                    self.results.extend(results)

                    # Count risk levels in this batch
                    critical = len([r for r in results if r.risk_level == 'CRITICAL'])
                    high = len([r for r in results if r.risk_level == 'HIGH'])

                    print(f"✓ {len(results)} analyzed", end="")
                    if critical or high:
                        print(f" [🔴 {critical} CRITICAL, 🟠 {high} HIGH]", end="")
                    print()

                    # Progress stats
                    if batch_num % 10 == 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        rate = len(self.processed_ids) / elapsed if elapsed > 0 else 0
                        print(f"    → Progress: {len(self.processed_ids):,} items, {self.total_tokens_used:,} tokens, {rate:.1f} items/sec")

                    # Checkpoint
                    if batch_num % CHECKPOINT_INTERVAL == 0:
                        self._save_checkpoint()
                        self._save_interim_results()
                        print(f"    💾 Checkpoint saved")

                except KeyboardInterrupt:
                    print("\n\n⚠ Interrupted! Saving progress...")
                    self._save_checkpoint()
                    self._save_interim_results()
                    raise
                except Exception as e:
                    print(f"✗ Error: {e}")
                    continue

        # Final save
        self._save_checkpoint()
        self._save_final_results()

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Total items analyzed: {len(self.processed_ids):,}")
        print(f"Total findings: {len(self.results):,}")
        print(f"Total tokens used: {self.total_tokens_used:,}")
        print(f"API calls made: {self.api_calls_made}")
        print(f"Errors: {len(self.errors)}")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        print(f"{'='*60}")
        self._print_summary()

    def _save_interim_results(self):
        """Save interim results."""
        output_file = FINDINGS_DIR / "openai_analysis_interim.json"
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'total_analyzed': len(self.results),
                'total_tokens': self.total_tokens_used,
                'results': [asdict(r) for r in self.results[-1000:]]  # Last 1000 for interim
            }, f, indent=2)

    def _save_final_results(self):
        """Save final results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Full results
        output_file = FINDINGS_DIR / f"openai_analysis_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'total_analyzed': len(self.results),
                'total_tokens': self.total_tokens_used,
                'results': [asdict(r) for r in self.results]
            }, f, indent=2)

        # Also save as latest
        latest_file = FINDINGS_DIR / "openai_analysis_latest.json"
        with open(latest_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'total_analyzed': len(self.results),
                'total_tokens': self.total_tokens_used,
                'results': [asdict(r) for r in self.results]
            }, f, indent=2)

        # Save high-risk items separately (CRITICAL and HIGH)
        high_risk = [r for r in self.results if r.risk_level in ['CRITICAL', 'HIGH']]
        high_risk_file = FINDINGS_DIR / "openai_high_risk_findings.json"
        with open(high_risk_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'total_high_risk': len(high_risk),
                'critical_count': len([r for r in high_risk if r.risk_level == 'CRITICAL']),
                'high_count': len([r for r in high_risk if r.risk_level == 'HIGH']),
                'total_amount_flagged': sum(r.amount for r in high_risk),
                'findings': [asdict(r) for r in sorted(high_risk, key=lambda x: x.risk_score, reverse=True)]
            }, f, indent=2)

        # Save errors
        if self.errors:
            error_file = FINDINGS_DIR / f"openai_errors_{timestamp}.json"
            with open(error_file, 'w') as f:
                json.dump(self.errors, f, indent=2)

        print(f"\n📁 Results saved to:")
        print(f"   {output_file.name}")
        print(f"   {latest_file.name}")
        print(f"   {high_risk_file.name} ({len(high_risk):,} high-risk items)")

    def _print_summary(self):
        """Print analysis summary."""
        if not self.results:
            return

        # Count by risk level
        risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        anomaly_counts = {}
        total_amount_flagged = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        mda_risk = {}

        for r in self.results:
            level = r.risk_level
            risk_counts[level] = risk_counts.get(level, 0) + 1
            total_amount_flagged[level] += r.amount

            # Track MDA risk
            if level in ['CRITICAL', 'HIGH']:
                mda_risk[r.mda] = mda_risk.get(r.mda, 0) + 1

            for anomaly in r.anomaly_types:
                if anomaly != 'NORMAL':
                    anomaly_counts[anomaly] = anomaly_counts.get(anomaly, 0) + 1

        print("\n📊 RISK LEVEL DISTRIBUTION:")
        print("-" * 50)
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = risk_counts[level]
            amount = total_amount_flagged[level]
            pct = (count / len(self.results) * 100) if self.results else 0
            icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}[level]
            print(f"  {icon} {level:10} {count:>8,} ({pct:5.1f}%)  ₦{amount:>20,.0f}")

        print("\n🚨 TOP ANOMALY TYPES:")
        print("-" * 50)
        sorted_anomalies = sorted(anomaly_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for anomaly, count in sorted_anomalies:
            print(f"  • {anomaly:30} {count:>8,}")

        if mda_risk:
            print("\n🏛️ HIGHEST RISK MDAs:")
            print("-" * 50)
            sorted_mdas = sorted(mda_risk.items(), key=lambda x: x[1], reverse=True)[:10]
            for mda, count in sorted_mdas:
                print(f"  • {mda[:40]:40} {count:>6,} findings")


def load_budget_data() -> List[Dict]:
    """Load all budget data from master file."""
    master_file = EXTRACTED_DIR / "master_budget_data.json"

    if not master_file.exists():
        raise FileNotFoundError(f"Master budget file not found: {master_file}")

    print(f"Loading budget data from {master_file}...")
    with open(master_file) as f:
        data = json.load(f)

    items = data.get('items', [])
    print(f"Loaded {len(items):,} budget items")
    return items


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='OpenAI GPT-4 Bulk Budget Analyzer')
    parser.add_argument('--max-items', type=int, help='Maximum items to analyze (for testing)')
    parser.add_argument('--batch-size', type=int, default=25, help='Items per API call (default: 25)')
    parser.add_argument('--model', type=str, default='gpt-4o-mini',
                        choices=['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
                        help='OpenAI model to use (default: gpt-4o-mini)')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--reset', action='store_true', help='Reset checkpoint and start fresh')
    args = parser.parse_args()

    # Handle reset
    if args.reset:
        checkpoint_file = CHECKPOINT_DIR / "latest_checkpoint.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print("✓ Checkpoint reset")

    # Load data
    items = load_budget_data()

    # Run analysis
    analyzer = OpenAIBulkAnalyzer()
    analyzer.batch_size = args.batch_size
    analyzer.model = args.model

    await analyzer.run_analysis(items, max_items=args.max_items)


if __name__ == "__main__":
    asyncio.run(main())
