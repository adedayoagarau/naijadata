#!/usr/bin/env python3
"""
Download ALL budget documents from Budget Office - including HTML, Excel, and PDF.
"""

import os
import re
import time
import requests
from pathlib import Path
from tqdm import tqdm
from urllib.parse import urlparse

BASE_URL = "https://budgetoffice.gov.ng"
OUTPUT_DIR = Path("raw_pdfs/federal")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "*/*",
}

# Content-Type to extension mapping
CONTENT_TYPE_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "text/html": ".html",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/octet-stream": ".pdf",  # Assume PDF if unknown
}


def get_extension(content_type: str, url: str) -> str:
    """Determine file extension from content-type or URL."""
    content_type = content_type.lower().split(';')[0].strip()

    # Check content-type first
    for ct, ext in CONTENT_TYPE_EXT.items():
        if ct in content_type:
            return ext

    # Check URL for extension hints
    url_lower = url.lower()
    if '.xlsx' in url_lower:
        return '.xlsx'
    elif '.xls' in url_lower:
        return '.xls'
    elif '.pdf' in url_lower:
        return '.pdf'
    elif '.csv' in url_lower:
        return '.csv'

    # Default to .pdf
    return '.pdf'


def download_all_formats(url: str, base_name: str, year_dir: Path) -> dict:
    """Download a file, accepting any format."""
    result = {"url": url, "status": "unknown", "file": None, "type": None}

    try:
        response = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        content_length = len(response.content)

        # Skip if too small (likely error page)
        if content_length < 1000:
            result["status"] = "too_small"
            return result

        # Get appropriate extension
        ext = get_extension(content_type, url)

        # Clean filename
        clean_name = re.sub(r'[^\w\-]', '_', base_name)[:80]
        filename = f"{clean_name}{ext}"
        filepath = year_dir / filename

        # Don't overwrite existing
        if filepath.exists():
            result["status"] = "exists"
            result["file"] = str(filepath)
            return result

        # Save file
        with open(filepath, 'wb') as f:
            f.write(response.content)

        result["status"] = "downloaded"
        result["file"] = str(filepath)
        result["type"] = ext
        result["size"] = content_length

    except Exception as e:
        result["status"] = f"error: {e}"

    return result


def scrape_all_documents():
    """Scrape Budget Office for all document links."""
    from bs4 import BeautifulSoup

    all_docs = []
    years = list(range(2019, 2027))

    print("Scraping Budget Office for all document links...")

    for year in years:
        url = f"{BASE_URL}/index.php/resources/internal-resources/budget-documents/{year}-budget"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)

                # Look for document links
                if '/download' in href or 'appropriation' in href.lower() or 'budget' in href.lower():
                    full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                    all_docs.append({
                        "year": year,
                        "name": text or href.split('/')[-1],
                        "url": full_url
                    })

            print(f"  {year}: found {len([d for d in all_docs if d['year'] == year])} links")

        except Exception as e:
            print(f"  {year}: error - {e}")

        time.sleep(1)

    return all_docs


def main():
    """Download all documents in all formats."""
    print("=" * 60)
    print("BUDGET OFFICE - DOWNLOAD ALL FORMATS")
    print("Includes: PDF, Excel (.xlsx/.xls), HTML, CSV")
    print("=" * 60)

    # Scrape for documents
    docs = scrape_all_documents()
    print(f"\nFound {len(docs)} document links total")

    # Download each
    results = {"downloaded": [], "skipped": [], "errors": []}

    for doc in tqdm(docs, desc="Downloading"):
        year_dir = OUTPUT_DIR / str(doc["year"])
        year_dir.mkdir(parents=True, exist_ok=True)

        result = download_all_formats(doc["url"], doc["name"], year_dir)

        if result["status"] == "downloaded":
            results["downloaded"].append(result)
        elif result["status"] == "exists":
            results["skipped"].append(result)
        else:
            results["errors"].append({**doc, **result})

        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)

    print(f"\nDownloaded: {len(results['downloaded'])}")
    print(f"Already existed: {len(results['skipped'])}")
    print(f"Errors: {len(results['errors'])}")

    # By type
    by_type = {}
    for r in results["downloaded"]:
        ext = r.get("type", "unknown")
        by_type[ext] = by_type.get(ext, 0) + 1

    print("\nBy file type:")
    for ext, count in sorted(by_type.items()):
        print(f"  {ext}: {count}")

    # List errors
    if results["errors"]:
        print("\nFailed downloads:")
        for err in results["errors"][:10]:
            print(f"  - {err['name'][:50]}: {err['status']}")

    # Show what we have now
    print("\n" + "=" * 60)
    print("CURRENT INVENTORY")
    print("=" * 60)

    for year_dir in sorted(OUTPUT_DIR.iterdir()):
        if year_dir.is_dir():
            files = list(year_dir.iterdir())
            by_ext = {}
            total_size = 0
            for f in files:
                ext = f.suffix.lower()
                by_ext[ext] = by_ext.get(ext, 0) + 1
                total_size += f.stat().st_size

            ext_str = ", ".join(f"{c} {e}" for e, c in sorted(by_ext.items()))
            print(f"  {year_dir.name}: {len(files)} files ({total_size/1e6:.1f} MB) - {ext_str}")


if __name__ == "__main__":
    main()
