# Discovered Budget Document URLs
## For Bulk Download in Claude Code

---

## FEDERAL BUDGET OFFICE (budgetoffice.gov.ng)

### Download URL Pattern:
```
https://budgetoffice.gov.ng/index.php/{document-slug}/{document-slug}/download
```

### 2026 Documents:
1. `2026-appropriation-bill-details` (7.46MB) - Full MDA breakdown
2. `2026-appropriation-bill` - Main bill

### 2025 Documents:
1. `2025-appropriation-bill` (Dec 2024)
2. `2025-executive-proposal` (Mar 2025)
3. `2025-appropriation-act` (Mar 2025)
4. `2025-appropriation-act-as-passed` (Jul 2025)
5. `2025-appropriation-act-implementation-guideline` (Oct 2025)
6. Additional quarterly reports

### 2024 Documents:
1. `2024-appropriation-bill` (Dec 2023)
2. `2024-appropriation-amendment-act` (3 documents)
3. Quarterly implementation reports

### Document Listing Pages:
```
https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents/2026-budget
https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents/2025-budget
https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents/2024-budget
https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents/2023-budget
https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents/2022-budget
... (continue for all years down to 2009)
```

### Other Useful Pages:
- MTEF: `/index.php/resources/internal-resources/policy-documents/mtef`
- Quarterly Reports: `/index.php/resources/internal-resources/reports/quarterly-budget-implementation`
- Citizens Guide: `/index.php/resources/internal-resources/citizens-guide-to-the-budget`

---

## BUDGETPEDIA.NG (State Budgets)

### Main Page:
```
https://budgetpedia.ng/
```

### Known State Budget Sizes (2025):
- Osun: 37.28MB
- Ogun: 5.64MB
- Rivers: 3.19MB (FY2025 only, no 2026)
- Plateau: 2.14MB
- Sokoto: 14.94MB
- Taraba: 14.14MB
- Ondo: 13.51MB

### URL Pattern (needs verification):
```
https://budgetpedia.ng/state/{state-name}/approved-budget/{year}
```

---

## OPENSTATES.NG (BudgIT)

### Main Portal:
```
https://openstates.ng/
```

### May have API at:
```
https://api.openstates.ng/ (needs verification)
```

---

## OTHER USEFUL SOURCES

### Debt Management Office:
```
https://dmo.gov.ng/
```
- State debt profiles
- Federal debt data

### National Bureau of Statistics:
```
https://nigerianstat.gov.ng/
```
- Population data (for per-capita calculations)
- IGR reports

### RMAFC (Revenue Mobilisation):
```
https://rmafc.gov.ng/
```
- Official legislature salary scales

---

## SCRAPING STRATEGY

### Step 1: Get all document links from Budget Office
```python
import requests
from bs4 import BeautifulSoup

years = list(range(2009, 2027))
base_url = "https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents"

all_docs = []

for year in years:
    url = f"{base_url}/{year}-budget"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all document links
    # Pattern: /index.php/{doc-name}
    links = soup.find_all('a', href=True)
    for link in links:
        if '/download' in link.get('href', ''):
            all_docs.append({
                'year': year,
                'url': link['href'],
                'name': link.text.strip()
            })
```

### Step 2: Download all PDFs
```python
import os
from tqdm import tqdm

for doc in tqdm(all_docs):
    year_dir = f"raw_pdfs/federal/{doc['year']}"
    os.makedirs(year_dir, exist_ok=True)

    filename = doc['name'].replace(' ', '_') + '.pdf'
    filepath = os.path.join(year_dir, filename)

    if not os.path.exists(filepath):
        response = requests.get(doc['url'])
        with open(filepath, 'wb') as f:
            f.write(response.content)
```
