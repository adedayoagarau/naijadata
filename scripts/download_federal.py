#!/usr/bin/env python3
"""
Download Federal Budget PDFs from budgetoffice.gov.ng

This script scrapes the Budget Office website to discover and download
all available budget documents from 2009-2026.
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path

# Configuration
BASE_URL = "https://budgetoffice.gov.ng"
DOCS_BASE = f"{BASE_URL}/index.php/resources/internal-resources/budget-documents"
OUTPUT_DIR = Path(__file__).parent.parent / "raw_pdfs" / "federal"
YEARS = list(range(2019, 2027))  # Start with recent years

# Known direct download URLs for key documents
KNOWN_DOCUMENTS = {
    2026: [
        {
            "slug": "2026-appropriation-bill-details",
            "name": "2026_Appropriation_Bill_Details",
            "description": "Full MDA breakdown (7.46MB)"
        },
        {
            "slug": "2026-appropriation-bill",
            "name": "2026_Appropriation_Bill",
            "description": "Main bill"
        }
    ],
    2025: [
        {
            "slug": "2025-appropriation-bill",
            "name": "2025_Appropriation_Bill",
            "description": "December 2024"
        },
        {
            "slug": "2025-appropriation-act",
            "name": "2025_Appropriation_Act",
            "description": "March 2025"
        },
        {
            "slug": "2025-appropriation-act-as-passed",
            "name": "2025_Appropriation_Act_As_Passed",
            "description": "July 2025"
        }
    ],
    2024: [
        {
            "slug": "2024-appropriation-bill",
            "name": "2024_Appropriation_Bill",
            "description": "December 2023"
        },
        {
            "slug": "2024-appropriation-act",
            "name": "2024_Appropriation_Act",
            "description": "Signed act"
        }
    ]
}

# Request headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_download_url(slug: str) -> str:
    """Construct download URL from document slug."""
    return f"{BASE_URL}/index.php/{slug}/{slug}/download"


def download_file(url: str, filepath: Path, retries: int = 3) -> bool:
    """Download a file with retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=60, stream=True)
            response.raise_for_status()

            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and 'octet-stream' not in content_type.lower():
                print(f"  Warning: Content-Type is {content_type}, may not be PDF")

            # Write file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except requests.exceptions.RequestException as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    return False


def scrape_year_documents(year: int) -> list:
    """Scrape document links from a year's budget page."""
    url = f"{DOCS_BASE}/{year}-budget"
    documents = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links that look like document downloads
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)

            # Look for download links or document links
            if '/download' in href or (f'{year}' in href and 'appropriation' in href.lower()):
                # Extract slug from URL
                match = re.search(r'/index\.php/([^/]+)', href)
                if match:
                    slug = match.group(1)
                    documents.append({
                        "slug": slug,
                        "name": text or slug.replace('-', '_'),
                        "url": href if href.startswith('http') else f"{BASE_URL}{href}"
                    })

    except requests.exceptions.RequestException as e:
        print(f"  Error scraping {year}: {e}")

    return documents


def download_known_documents():
    """Download documents from the known URLs list."""
    print("=" * 60)
    print("Downloading known Federal Budget documents")
    print("=" * 60)

    for year, docs in KNOWN_DOCUMENTS.items():
        year_dir = OUTPUT_DIR / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Year {year}:")

        for doc in docs:
            filename = f"{doc['name']}.pdf"
            filepath = year_dir / filename

            if filepath.exists():
                print(f"  ✓ {filename} (already exists)")
                continue

            url = get_download_url(doc['slug'])
            print(f"  ⬇ Downloading {filename}...")
            print(f"    URL: {url}")

            if download_file(url, filepath):
                size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"    ✓ Downloaded ({size_mb:.2f} MB)")
            else:
                print(f"    ✗ Failed to download")

            time.sleep(1)  # Be polite to the server


def scrape_and_download_all():
    """Scrape the Budget Office website and download all discovered documents."""
    print("\n" + "=" * 60)
    print("Scraping Budget Office for additional documents")
    print("=" * 60)

    all_documents = []

    for year in YEARS:
        print(f"\n🔍 Scanning {year}...")
        docs = scrape_year_documents(year)

        if docs:
            print(f"   Found {len(docs)} documents")
            for doc in docs:
                doc['year'] = year
                all_documents.append(doc)
        else:
            print(f"   No documents found or page not accessible")

        time.sleep(1)

    # Download discovered documents
    print(f"\n📥 Downloading {len(all_documents)} discovered documents...")

    for doc in tqdm(all_documents):
        year_dir = OUTPUT_DIR / str(doc['year'])
        year_dir.mkdir(parents=True, exist_ok=True)

        # Clean filename
        filename = re.sub(r'[^\w\-_]', '_', doc['name'])[:100] + '.pdf'
        filepath = year_dir / filename

        if filepath.exists():
            continue

        url = doc.get('url', get_download_url(doc['slug']))
        if download_file(url, filepath):
            pass  # tqdm handles progress

        time.sleep(0.5)

    return all_documents


def main():
    """Main entry point."""
    print("🇳🇬 Nigeria Federal Budget PDF Downloader")
    print(f"Output directory: {OUTPUT_DIR}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # First, download known documents
    download_known_documents()

    # Then scrape for additional documents
    discovered = scrape_and_download_all()

    # Summary
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)

    total_files = 0
    total_size = 0

    for year_dir in sorted(OUTPUT_DIR.iterdir()):
        if year_dir.is_dir():
            files = list(year_dir.glob('*.pdf'))
            size = sum(f.stat().st_size for f in files)
            total_files += len(files)
            total_size += size
            print(f"  {year_dir.name}: {len(files)} files ({size / (1024*1024):.2f} MB)")

    print(f"\nTotal: {total_files} files ({total_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
