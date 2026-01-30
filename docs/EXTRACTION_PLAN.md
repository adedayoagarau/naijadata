# Nigeria Budget Data Extraction Plan
## For Claude Code Implementation

---

## DATA SOURCES

### 1. Federal Budget Office (budgetoffice.gov.ng)
**Documents Available: 750+ PDFs (2009-2026)**

| Year | Docs | Key Files |
|------|------|-----------|
| 2026 | 2 | Appropriation Bill Details (7.46MB) |
| 2025 | 6 | Appropriation Bill, ACT, Implementation Guidelines |
| 2024 | 13 | Bill, ACT, Amendments, Quarterly Reports |
| 2023 | 64 | Full MDA breakdowns by sector |
| 2022 | 57 | Full MDA breakdowns |
| 2021 | 29 | COVID-adjusted budgets |
| 2020 | 65 | Full breakdowns |
| 2019 | 15 | Pre-COVID baseline |
| 2018-2009 | 400+ | Historical data |

**Download Pattern:**
```
Base URL: https://budgetoffice.gov.ng/index.php/
Document URL: {doc-name}/{doc-name}/download
View URL: {doc-name}/{doc-name}/viewdocument/{id}
```

**Example Downloads:**
- 2026 Bill Details: `/index.php/2026-appropriation-bill-details/2026-appropriation-bill-details/download`
- 2025 Bill: `/index.php/2025-appropriation-bill/2025-appropriation-bill/download`
- 2024 Bill: `/index.php/2024-appropriation-bill/2024-appropriation-bill/download`

### 2. Budgetpedia.ng (State Budgets)
**Documents Available: All 36 states, 2019-2025**

State budget PDFs with full appropriation details including:
- MDA-level allocations
- Budget codes
- Line-item descriptions
- Personnel/Overhead/Capital splits

**Example Files:**
- Osun 2025: 37.28MB (confirmed GST source)
- Lagos 2025: Available
- Rivers 2025: 3.19MB

### 3. OpenStates.ng (BudgIT)
- Interactive data portal
- May have API access
- Covers all 36 states + FCT

---

## EXTRACTION STRATEGY

### Phase 1: Download All PDFs

```python
# Step 1: Scrape document listing pages
# Budget Office has predictable URL structure:
# /index.php/resources/internal-resources/budget-documents/{year}-budget

years = list(range(2009, 2027))
base_url = "https://budgetoffice.gov.ng/index.php/resources/internal-resources/budget-documents"

# For each year, scrape the document links
# Then download each PDF
```

### Phase 2: Parse PDFs

**Tool: pdfplumber (recommended for tables)**
```python
import pdfplumber

def extract_budget_tables(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Process table rows
                pass
```

**Alternative: tabula-py (for complex tables)**
```python
import tabula

dfs = tabula.read_pdf(pdf_path, pages='all')
```

### Phase 3: Structure Data

**Target Schema:**
```json
{
  "source": "federal",
  "year": 2026,
  "document_type": "appropriation_bill",
  "mdas": [
    {
      "code": "0111001001",
      "name": "Presidency",
      "personnel": 123456789,
      "overhead": 234567890,
      "capital": 345678901,
      "total": 703703580,
      "line_items": [
        {
          "code": "22020801",
          "description": "International Travel",
          "amount": 7014000000
        }
      ]
    }
  ]
}
```

---

## SPECIFIC EXTRACTIONS NEEDED

### For Accountability Tool:

1. **Legislature Spending (All States)**
   - House of Assembly total budget
   - International travel allocation
   - Local travel allocation
   - Sitting allowances
   - Vehicle purchases
   - Number of legislators

2. **Health Ministry (All States)**
   - Total health budget
   - Drugs & medical supplies
   - Primary healthcare
   - Per-capita calculation

3. **Education (All States)**
   - Total education budget
   - % of total budget
   - Per-student calculation

4. **Executive Office (All States)**
   - Governor's Office total
   - Travel allocations
   - Security vote (if disclosed)

---

## PDF STRUCTURE NOTES

### Federal Budget PDFs typically contain:

1. **Summary Tables**
   - Revenue projections
   - Expenditure summary by economic classification
   - Deficit/surplus

2. **MDA Details**
   - One section per Ministry/Department/Agency
   - Personnel costs breakdown
   - Overhead costs breakdown
   - Capital projects list

3. **Budget Codes**
   - Standard classification system
   - 22020801 = International Travel
   - 22020803 = Local Travel
   - etc.

### State Budget PDFs vary but usually have:

1. **Recurrent Expenditure by MDA**
2. **Capital Expenditure by MDA**
3. **Revenue Estimates**
4. **Detailed line items within each MDA**

---

## KNOWN CHALLENGES

1. **PDF Format Inconsistency**
   - Different states use different formats
   - Some years have different structures
   - May need per-state/per-year extraction logic

2. **Scanned vs. Text PDFs**
   - Some older documents are scanned images
   - Will need OCR (pytesseract) for these

3. **Large File Sizes**
   - Some PDFs are 30-50MB
   - Need efficient processing

4. **Budget Code Mapping**
   - Need to build a lookup table for budget codes
   - Codes may vary slightly between states

---

## RECOMMENDED LIBRARIES

```python
# PDF extraction
pip install pdfplumber
pip install tabula-py  # requires Java
pip install PyPDF2
pip install pytesseract  # for scanned PDFs

# Data processing
pip install pandas
pip install openpyxl  # for Excel output

# Web scraping
pip install requests
pip install beautifulsoup4
pip install lxml

# Progress tracking
pip install tqdm
```

---

## FILE ORGANIZATION

```
/budget_data/
├── raw_pdfs/
│   ├── federal/
│   │   ├── 2026/
│   │   ├── 2025/
│   │   └── ...
│   └── states/
│       ├── osun/
│       ├── lagos/
│       └── ...
├── extracted/
│   ├── federal_budgets.json
│   ├── state_budgets.json
│   └── legislature_comparison.json
├── scripts/
│   ├── download_pdfs.py
│   ├── extract_federal.py
│   ├── extract_states.py
│   └── build_database.py
└── output/
    ├── all_budgets.csv
    ├── legislature_analysis.csv
    └── health_analysis.csv
```

---

## SUCCESS CRITERIA

- [ ] All 750+ federal PDFs downloaded
- [ ] All 36 state 2025 PDFs downloaded
- [ ] Federal legislature allocations extracted (2009-2026)
- [ ] State legislature allocations extracted (all 36)
- [ ] Health allocations extracted
- [ ] Education allocations extracted
- [ ] Per-capita calculations complete
- [ ] Comparison database built
- [ ] Data validated against news sources
