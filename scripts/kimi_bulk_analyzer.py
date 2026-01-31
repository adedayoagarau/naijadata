#!/usr/bin/env python3
"""
Kimi 2.5 Bulk Budget Analyzer
Uses Moonshot AI's Kimi model to perform line-by-line forensic analysis
of Nigerian federal and state budget data.
"""

import os
import json
import time
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

MOONSHOT_API_KEY = os.getenv('MOONSHOT_API_KEY')
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

# Kimi model options: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k, kimi-latest
KIMI_MODEL = "kimi-latest"

# Processing configuration
BATCH_SIZE = 50  # Items per batch for analysis
MAX_CONCURRENT_REQUESTS = 5  # Parallel API calls
RATE_LIMIT_DELAY = 0.5  # Seconds between requests
CHECKPOINT_INTERVAL = 100  # Save progress every N batches

# Paths
BASE_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = BASE_DIR / "extracted"
FINDINGS_DIR = BASE_DIR / "findings"
CHECKPOINT_DIR = BASE_DIR / "data" / "kimi_checkpoints"


@dataclass
class KimiAnalysisResult:
    """Result from Kimi analysis of a budget item."""
    item_id: str
    budget_code: str
    description: str
    amount: float
    mda: str
    year: int

    # Kimi analysis fields
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
    model_used: str = KIMI_MODEL


SYSTEM_PROMPT = """You are a forensic budget analyst specializing in Nigerian government finances. You have deep knowledge of:

1. **Nigerian Budget Structure**: MDAs, budget codes (21xxx=Personnel, 22xxx=Overhead, 23xxx=Capital), appropriation patterns
2. **Common Corruption Patterns**:
   - Round number bias (exact billions/millions suggest estimation, not actual costing)
   - Mandate violations (agencies spending outside their scope)
   - Ghost workers (inflated personnel costs)
   - Padding (inflated unit costs for items)
   - Duplicate allocations
   - Vague descriptions ("miscellaneous", "contingency")

3. **High-Risk MDAs**: National Assembly, NNPC, NDDC, NIA, DIA, Presidency, Ministry of Niger Delta
4. **Benchmarks**:
   - Reasonable laptop: ₦300-500K
   - Standard vehicle: ₦15-30M
   - Primary school construction: ₦100-150M
   - Health center: ₦150-250M
   - Borehole: ₦5-10M

5. **Red Flags**:
   - Security agencies with education/health spending
   - Travel budgets exceeding operational budgets
   - Furniture replacement every year
   - Training costs > ₦500K per staff
   - Overtime exceeding 30% of base salary

Analyze each budget item and return a JSON object with your assessment."""

USER_PROMPT_TEMPLATE = """Analyze these Nigerian budget items for anomalies, corruption indicators, and red flags.

BUDGET ITEMS:
{items_json}

For EACH item, provide analysis in this exact JSON format:
{{
  "analyses": [
    {{
      "item_id": "<item_id>",
      "risk_score": <0-100>,
      "risk_level": "<CRITICAL|HIGH|MEDIUM|LOW>",
      "anomaly_types": ["<type1>", "<type2>"],
      "red_flags": ["<specific concern 1>", "<specific concern 2>"],
      "explanation": "<why this is suspicious or normal>",
      "recommendation": "<what investigators should check>",
      "confidence": <0.0-1.0>,
      "similar_items_concern": "<if pattern with other items>",
      "historical_pattern": "<if unusual compared to typical budgets>"
    }}
  ]
}}

Anomaly types to use: ROUND_NUMBER, MANDATE_VIOLATION, EXCESSIVE_AMOUNT, VAGUE_DESCRIPTION, PADDING_INDICATOR, HIGH_RISK_MDA, DUPLICATE_SUSPECTED, YOY_SPIKE, GHOST_WORKER_PATTERN, ELECTION_YEAR_ANOMALY, BENFORD_VIOLATION, NORMAL

Risk scoring guide:
- 0-25: LOW - Normal budget item, no concerns
- 26-50: MEDIUM - Minor irregularities, worth noting
- 51-75: HIGH - Significant red flags, needs review
- 76-100: CRITICAL - Strong corruption indicators, priority investigation

Return ONLY valid JSON, no markdown or explanation outside the JSON."""


class KimiBulkAnalyzer:
    """Bulk analyzer using Kimi 2.5 for Nigerian budget forensics."""

    def __init__(self):
        if not MOONSHOT_API_KEY:
            raise ValueError("MOONSHOT_API_KEY not found in environment")

        self.api_key = MOONSHOT_API_KEY
        self.results: List[KimiAnalysisResult] = []
        self.errors: List[Dict] = []
        self.processed_ids: set = set()
        self.batch_size = BATCH_SIZE  # Can be overridden

        # Create directories
        FINDINGS_DIR.mkdir(exist_ok=True)
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

        # Load checkpoint if exists
        self._load_checkpoint()

    def _generate_item_id(self, item: Dict) -> str:
        """Generate unique ID for a budget item."""
        key = f"{item.get('year', '')}-{item.get('budget_code', '')}-{item.get('mda', '')}-{item.get('amount', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def _load_checkpoint(self):
        """Load previous progress if available."""
        checkpoint_file = CHECKPOINT_DIR / "latest_checkpoint.json"
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)
                self.processed_ids = set(data.get('processed_ids', []))
                print(f"Loaded checkpoint: {len(self.processed_ids)} items already processed")
            except Exception as e:
                print(f"Could not load checkpoint: {e}")

    def _save_checkpoint(self):
        """Save current progress."""
        checkpoint_file = CHECKPOINT_DIR / "latest_checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'processed_ids': list(self.processed_ids),
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(self.processed_ids)
            }, f)

    async def _call_kimi_api(self, session: aiohttp.ClientSession, items: List[Dict]) -> Optional[Dict]:
        """Make API call to Kimi."""
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
                "state": item.get('state', None)
            })

        user_prompt = USER_PROMPT_TEMPLATE.format(
            items_json=json.dumps(items_for_analysis, indent=2)
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": KIMI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,  # Lower for more consistent analysis
            "max_tokens": 4096
        }

        try:
            async with session.post(MOONSHOT_API_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']

                    # Parse JSON from response
                    try:
                        # Handle potential markdown code blocks
                        if '```json' in content:
                            content = content.split('```json')[1].split('```')[0]
                        elif '```' in content:
                            content = content.split('```')[1].split('```')[0]

                        return json.loads(content.strip())
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}")
                        self.errors.append({
                            'type': 'json_parse_error',
                            'content': content[:500],
                            'error': str(e)
                        })
                        return None
                else:
                    error_text = await response.text()
                    print(f"API error {response.status}: {error_text[:200]}")
                    self.errors.append({
                        'type': 'api_error',
                        'status': response.status,
                        'error': error_text[:500]
                    })
                    return None

        except Exception as e:
            print(f"Request error: {e}")
            self.errors.append({
                'type': 'request_error',
                'error': str(e)
            })
            return None

    def _parse_analysis_results(self, response: Dict, original_items: List[Dict]) -> List[KimiAnalysisResult]:
        """Parse Kimi response into structured results."""
        results = []
        analyses = response.get('analyses', [])

        # Create lookup for original items
        item_lookup = {self._generate_item_id(item): item for item in original_items}

        for analysis in analyses:
            item_id = analysis.get('item_id', '')
            original = item_lookup.get(item_id, {})

            result = KimiAnalysisResult(
                item_id=item_id,
                budget_code=original.get('budget_code', 'N/A'),
                description=original.get('description', 'N/A'),
                amount=original.get('amount', 0),
                mda=original.get('mda', 'N/A'),
                year=original.get('year', 0),
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
                model_used=KIMI_MODEL
            )
            results.append(result)
            self.processed_ids.add(item_id)

        return results

    async def analyze_batch(self, session: aiohttp.ClientSession, batch: List[Dict], batch_num: int) -> List[KimiAnalysisResult]:
        """Analyze a batch of items."""
        # Filter out already processed items
        unprocessed = [item for item in batch if self._generate_item_id(item) not in self.processed_ids]

        if not unprocessed:
            return []

        print(f"  Batch {batch_num}: Analyzing {len(unprocessed)} items...")

        response = await self._call_kimi_api(session, unprocessed)

        if response:
            results = self._parse_analysis_results(response, unprocessed)
            return results

        return []

    async def run_analysis(self, items: List[Dict], max_items: Optional[int] = None):
        """Run bulk analysis on all items."""
        if max_items:
            items = items[:max_items]

        total_items = len(items)
        print(f"\nStarting Kimi 2.5 bulk analysis")
        print(f"Total items: {total_items:,}")
        print(f"Already processed: {len(self.processed_ids):,}")
        print(f"Batch size: {self.batch_size}")
        print(f"Model: {KIMI_MODEL}")
        print("-" * 50)

        # Create batches
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
        total_batches = len(batches)

        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS)
        async with aiohttp.ClientSession(connector=connector) as session:
            for i, batch in enumerate(batches):
                batch_num = i + 1

                # Rate limiting
                await asyncio.sleep(RATE_LIMIT_DELAY)

                try:
                    results = await self.analyze_batch(session, batch, batch_num)
                    self.results.extend(results)

                    # Progress update
                    progress = (batch_num / total_batches) * 100
                    print(f"  Progress: {batch_num}/{total_batches} batches ({progress:.1f}%) - {len(self.results):,} findings")

                    # Checkpoint
                    if batch_num % CHECKPOINT_INTERVAL == 0:
                        self._save_checkpoint()
                        self._save_interim_results()
                        print(f"  [Checkpoint saved at batch {batch_num}]")

                except KeyboardInterrupt:
                    print("\n\nInterrupted! Saving progress...")
                    self._save_checkpoint()
                    self._save_interim_results()
                    raise
                except Exception as e:
                    print(f"  Batch {batch_num} error: {e}")
                    continue

        # Final save
        self._save_checkpoint()
        self._save_final_results()

        print("\n" + "=" * 50)
        print("ANALYSIS COMPLETE")
        print(f"Total items analyzed: {len(self.processed_ids):,}")
        print(f"Total findings: {len(self.results):,}")
        print(f"Errors: {len(self.errors)}")
        self._print_summary()

    def _save_interim_results(self):
        """Save interim results."""
        output_file = FINDINGS_DIR / "kimi_analysis_interim.json"
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': KIMI_MODEL,
                'total_analyzed': len(self.results),
                'results': [asdict(r) for r in self.results]
            }, f, indent=2)

    def _save_final_results(self):
        """Save final results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Full results
        output_file = FINDINGS_DIR / f"kimi_analysis_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': KIMI_MODEL,
                'total_analyzed': len(self.results),
                'results': [asdict(r) for r in self.results]
            }, f, indent=2)

        # Also save as latest
        latest_file = FINDINGS_DIR / "kimi_analysis_latest.json"
        with open(latest_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': KIMI_MODEL,
                'total_analyzed': len(self.results),
                'results': [asdict(r) for r in self.results]
            }, f, indent=2)

        # Save high-risk items separately
        high_risk = [r for r in self.results if r.risk_level in ['CRITICAL', 'HIGH']]
        high_risk_file = FINDINGS_DIR / "kimi_high_risk_findings.json"
        with open(high_risk_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': KIMI_MODEL,
                'total_high_risk': len(high_risk),
                'findings': [asdict(r) for r in high_risk]
            }, f, indent=2)

        # Save errors
        if self.errors:
            error_file = FINDINGS_DIR / f"kimi_errors_{timestamp}.json"
            with open(error_file, 'w') as f:
                json.dump(self.errors, f, indent=2)

        print(f"\nResults saved to:")
        print(f"  - {output_file}")
        print(f"  - {latest_file}")
        print(f"  - {high_risk_file}")

    def _print_summary(self):
        """Print analysis summary."""
        if not self.results:
            return

        # Count by risk level
        risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        anomaly_counts = {}
        total_amount_flagged = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

        for r in self.results:
            risk_counts[r.risk_level] = risk_counts.get(r.risk_level, 0) + 1
            total_amount_flagged[r.risk_level] += r.amount

            for anomaly in r.anomaly_types:
                anomaly_counts[anomaly] = anomaly_counts.get(anomaly, 0) + 1

        print("\nRISK LEVEL DISTRIBUTION:")
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = risk_counts[level]
            amount = total_amount_flagged[level]
            print(f"  {level}: {count:,} items (₦{amount:,.0f})")

        print("\nTOP ANOMALY TYPES:")
        sorted_anomalies = sorted(anomaly_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for anomaly, count in sorted_anomalies:
            print(f"  {anomaly}: {count:,}")


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

    parser = argparse.ArgumentParser(description='Kimi 2.5 Bulk Budget Analyzer')
    parser.add_argument('--max-items', type=int, help='Maximum items to analyze (for testing)')
    parser.add_argument('--batch-size', type=int, default=50, help='Items per API call')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()

    batch_size = args.batch_size

    # Load data
    items = load_budget_data()

    # Run analysis
    analyzer = KimiBulkAnalyzer()
    analyzer.batch_size = batch_size
    await analyzer.run_analysis(items, max_items=args.max_items)


if __name__ == "__main__":
    asyncio.run(main())
