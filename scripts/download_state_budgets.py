#!/usr/bin/env python3
"""
Nigerian State Budget Downloader

Downloads all available budget PDFs from state government portals.
Uses the state_budget_db.py database of known URLs.

Usage:
    python3 download_state_budgets.py                    # Download all
    python3 download_state_budgets.py --state lagos      # Specific state
    python3 download_state_budgets.py --year 2025        # Specific year
    python3 download_state_budgets.py --list             # List available docs
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import state database
from state_budget_db import STATES, FEDERAL, get_all_doc_urls


def download_file(url: str, output_path: Path, timeout: int = 60) -> bool:
    """Download a file with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except requests.exceptions.RequestException as e:
            print(f"    Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)  # Exponential backoff

    return False


def download_state_budgets(
    output_dir: Path,
    state_filter: str = None,
    year_filter: str = None,
    max_workers: int = 4
):
    """Download all available state budget PDFs"""

    print("=" * 60)
    print("NIGERIAN STATE BUDGET DOWNLOADER")
    print("=" * 60)

    # Get all document URLs
    all_docs = get_all_doc_urls()

    # Apply filters
    if state_filter:
        all_docs = [d for d in all_docs if state_filter.lower() in d['state'].lower()]

    if year_filter:
        all_docs = [d for d in all_docs if d['year'] == year_filter]

    print(f"\nFound {len(all_docs)} documents to download")

    if not all_docs:
        print("No documents match your filters.")
        return

    # Download each document
    success_count = 0
    fail_count = 0

    for doc in all_docs:
        state = doc['state'].lower().replace(' ', '_')
        year = doc['year']
        doc_type = doc['type']
        url = doc['url']

        # Create output path
        filename = f"{state}_{year}_{doc_type}.pdf"
        output_path = output_dir / "states" / state / year / filename

        print(f"\n[{doc['state']} {year}] {doc_type}")
        print(f"  URL: {url}")
        print(f"  Saving to: {output_path}")

        if output_path.exists():
            print(f"  Already exists, skipping")
            success_count += 1
            continue

        if download_file(url, output_path):
            print(f"  Downloaded successfully ({output_path.stat().st_size / 1024:.1f} KB)")
            success_count += 1
        else:
            print(f"  FAILED to download")
            fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total: {len(all_docs)}")


def try_discover_pdfs(state_key: str, state_data: dict, output_dir: Path):
    """Try to discover additional PDFs from state portals"""
    portal = state_data.get('portal', '')
    if not portal:
        return []

    discovered = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(portal, headers=headers, timeout=30)
        response.raise_for_status()

        # Look for PDF links
        import re
        pdf_links = re.findall(r'href=["\']([^"\']*\.pdf)["\']', response.text, re.IGNORECASE)

        for link in pdf_links:
            # Make absolute URL
            if link.startswith('/'):
                parsed = urlparse(portal)
                link = f"{parsed.scheme}://{parsed.netloc}{link}"
            elif not link.startswith('http'):
                link = portal.rstrip('/') + '/' + link

            # Check if it looks like a budget document
            link_lower = link.lower()
            if any(kw in link_lower for kw in ['budget', 'appropriation', 'fiscal', 'expenditure']):
                discovered.append(link)

        return list(set(discovered))

    except Exception as e:
        print(f"  Error discovering PDFs for {state_data['name']}: {e}")
        return []


def discover_all_portals(output_dir: Path):
    """Scan all state portals for additional budget documents"""
    print("=" * 60)
    print("SCANNING STATE PORTALS FOR BUDGET DOCUMENTS")
    print("=" * 60)

    all_discovered = {}

    for state_key, state_data in STATES.items():
        print(f"\n{state_data['name']}...")
        portal = state_data.get('portal', '')

        if not portal:
            print(f"  No portal URL")
            continue

        print(f"  Portal: {portal}")
        discovered = try_discover_pdfs(state_key, state_data, output_dir)

        if discovered:
            all_discovered[state_data['name']] = discovered
            print(f"  Found {len(discovered)} potential budget documents:")
            for url in discovered[:5]:
                print(f"    - {url}")
            if len(discovered) > 5:
                print(f"    ... and {len(discovered) - 5} more")

    # Save discovered URLs
    if all_discovered:
        output_file = output_dir / "discovered_budget_urls.txt"
        with open(output_file, 'w') as f:
            for state, urls in all_discovered.items():
                f.write(f"\n# {state}\n")
                for url in urls:
                    f.write(f"{url}\n")
        print(f"\nSaved discovered URLs to: {output_file}")

    return all_discovered


def list_available():
    """List all available documents"""
    print("=" * 60)
    print("AVAILABLE STATE BUDGET DOCUMENTS")
    print("=" * 60)

    docs = get_all_doc_urls()

    by_state = {}
    for doc in docs:
        state = doc['state']
        if state not in by_state:
            by_state[state] = []
        by_state[state].append(doc)

    for state in sorted(by_state.keys()):
        state_docs = by_state[state]
        print(f"\n{state} ({len(state_docs)} documents)")
        for doc in state_docs:
            print(f"  [{doc['year']}] {doc['type']}")
            print(f"       {doc['url']}")


def main():
    parser = argparse.ArgumentParser(description='Download Nigerian State Budget PDFs')
    parser.add_argument('--output', '-o', type=Path, default=Path('./raw_pdfs'),
                       help='Output directory for PDFs')
    parser.add_argument('--state', '-s', type=str,
                       help='Filter by state name')
    parser.add_argument('--year', '-y', type=str,
                       help='Filter by year (2025 or 2026)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List available documents without downloading')
    parser.add_argument('--discover', action='store_true',
                       help='Scan state portals for additional documents')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel downloads')

    args = parser.parse_args()

    if args.list:
        list_available()
        return

    if args.discover:
        discover_all_portals(args.output)
        return

    download_state_budgets(
        output_dir=args.output,
        state_filter=args.state,
        year_filter=args.year,
        max_workers=args.workers
    )


if __name__ == "__main__":
    main()
