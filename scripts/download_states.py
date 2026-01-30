#!/usr/bin/env python3
"""
Download State Budget PDFs from Budgetpedia.ng

This script downloads budget documents for all 36 Nigerian states.
"""

import os
import time
import requests
from pathlib import Path
from tqdm import tqdm

# Configuration
BASE_URL = "https://budgetpedia.ng"
OUTPUT_DIR = Path(__file__).parent.parent / "raw_pdfs" / "states"

# All 36 Nigerian states
STATES = [
    "abia", "adamawa", "akwa-ibom", "anambra", "bauchi", "bayelsa",
    "benue", "borno", "cross-river", "delta", "ebonyi", "edo",
    "ekiti", "enugu", "gombe", "imo", "jigawa", "kaduna",
    "kano", "katsina", "kebbi", "kogi", "kwara", "lagos",
    "nasarawa", "niger", "ogun", "ondo", "osun", "oyo",
    "plateau", "rivers", "sokoto", "taraba", "yobe", "zamfara"
]

# Known PDF sizes (2025 budgets)
KNOWN_SIZES = {
    "osun": "37.28MB",
    "ogun": "5.64MB",
    "rivers": "3.19MB",
    "plateau": "2.14MB",
    "sokoto": "14.94MB",
    "taraba": "14.14MB",
    "ondo": "13.51MB"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get_state_budget_url(state: str, year: int) -> str:
    """Construct URL for state budget download."""
    # URL pattern may vary - this needs verification
    return f"{BASE_URL}/state/{state}/approved-budget/{year}/download"


def download_state_budget(state: str, year: int) -> bool:
    """Download budget PDF for a state."""
    state_dir = OUTPUT_DIR / state
    state_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{state}_{year}_budget.pdf"
    filepath = state_dir / filename

    if filepath.exists():
        print(f"  ✓ {filename} (already exists)")
        return True

    url = get_state_budget_url(state, year)
    print(f"  ⬇ Downloading {filename}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"    ✓ Downloaded ({size_mb:.2f} MB)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"    ✗ Failed: {e}")
        return False


def scrape_budgetpedia():
    """Scrape Budgetpedia to find actual download URLs."""
    from bs4 import BeautifulSoup

    discovered = []

    for state in tqdm(STATES, desc="Scanning states"):
        try:
            # Try state page
            url = f"{BASE_URL}/state/{state}"
            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find PDF links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '.pdf' in href.lower() or 'download' in href.lower():
                        discovered.append({
                            'state': state,
                            'url': href if href.startswith('http') else f"{BASE_URL}{href}",
                            'text': link.get_text(strip=True)
                        })

        except Exception as e:
            print(f"  Error scanning {state}: {e}")

        time.sleep(0.5)  # Rate limiting

    return discovered


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Download Nigerian state budget PDFs")
    parser.add_argument("--year", type=int, default=2025, help="Budget year to download")
    parser.add_argument("--state", help="Specific state to download (default: all)")
    parser.add_argument("--scrape", action="store_true", help="Scrape site to discover URLs first")
    args = parser.parse_args()

    print("🇳🇬 Nigeria State Budget PDF Downloader")
    print(f"Output directory: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.scrape:
        print("\n🔍 Scraping Budgetpedia for download URLs...")
        discovered = scrape_budgetpedia()
        print(f"\nDiscovered {len(discovered)} potential downloads")

        # Save discovered URLs
        import json
        with open(OUTPUT_DIR.parent / "discovered_state_urls.json", 'w') as f:
            json.dump(discovered, f, indent=2)
        print(f"Saved to discovered_state_urls.json")
        return

    states_to_download = [args.state] if args.state else STATES

    print(f"\n📥 Downloading {args.year} budgets for {len(states_to_download)} states...")

    success = 0
    failed = []

    for state in states_to_download:
        print(f"\n📁 {state.title()}:")
        if download_state_budget(state, args.year):
            success += 1
        else:
            failed.append(state)
        time.sleep(1)

    print(f"\n✅ Downloaded: {success}/{len(states_to_download)}")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
