# Decide9ja - Nigeria Budget Transparency Tool

A data extraction and analysis toolkit for Nigerian government budgets, powering the Decide9ja budget accountability platform.

## Overview

This project extracts and structures budget data from:
- **Federal Budget Office** (budgetoffice.gov.ng) - 750+ PDFs from 2009-2026
- **State Budgets** (via Budgetpedia.ng) - All 36 states, 2019-2025
- **Supporting Data** - Population, debt profiles, legislature details

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download Federal budget PDFs
python scripts/download_federal.py

# 3. Download State budget PDFs
python scripts/download_states.py --year 2025

# 4. Extract data from a PDF
python scripts/extract_budget.py raw_pdfs/federal/2026/2026_Appropriation_Bill_Details.pdf

# 5. Build comparison database
python scripts/build_comparison.py
```

## Project Structure

```
naijadata/
├── docs/                    # Project documentation
│   ├── EXTRACTION_PLAN.md   # Detailed extraction strategy
│   ├── STATE_DATA_STATUS.md # Status of all 36 states
│   └── DISCOVERED_URLS.md   # All known download URLs
├── raw_pdfs/                # Downloaded PDF files
│   ├── federal/             # Federal budget documents by year
│   └── states/              # State budgets by state name
├── extracted/               # Extracted JSON data
│   └── sample_budget_data.json
├── scripts/                 # Python extraction scripts
│   ├── download_federal.py  # Download federal PDFs
│   ├── download_states.py   # Download state PDFs
│   ├── extract_budget.py    # Extract data from PDFs
│   └── build_comparison.py  # Build comparison database
└── output/                  # Final processed data
    └── comparison_database.json
```

## Key Features

### 1. Legislature vs Health Comparison
Compare what states spend on legislators vs. healthcare:
- International travel allocations
- Sitting allowances
- Drug/medical supply budgets
- Per-capita healthcare spending

### 2. State Rankings
Rank all 36 states by:
- Education spending (% of budget)
- Health spending (% of budget)
- Cost per legislator
- Travel vs drugs ratio

### 3. Red Flag Detection
Automatically flag suspicious allocations:
- Travel budgets exceeding medical supplies
- Abnormally high cost per legislator
- Large "miscellaneous" allocations

## Data Schema

Each extracted budget follows this structure:

```json
{
  "source": "osun",
  "year": 2025,
  "total_budget": 578900000000,
  "mdas": [
    {
      "code": "011100100100",
      "name": "House of Assembly",
      "category": "legislature",
      "total": 4200000000,
      "line_items": [
        {
          "code": "22020801",
          "description": "International Travel",
          "amount": 700000000
        }
      ]
    }
  ],
  "red_flags": [
    {
      "type": "ratio_alert",
      "description": "Legislature travel exceeds Health drugs",
      "severity": "high"
    }
  ]
}
```

## Budget Code Reference

Common budget codes used across Nigerian government:

| Code | Description |
|------|-------------|
| 22020801 | International Travel & Transport |
| 22020802 | Sitting Allowances |
| 22020803 | Local Travel & Transport |
| 22020901 | Drugs & Medical Supplies |
| 23010105 | Purchase of Motor Vehicles |

## Data Sources

| Source | URL | Content |
|--------|-----|---------|
| Budget Office | budgetoffice.gov.ng | Federal budgets 2009-2026 |
| Budgetpedia | budgetpedia.ng | All 36 state budgets |
| OpenStates | openstates.ng | Interactive data portal |
| NBS | nigerianstat.gov.ng | Population data |
| DMO | dmo.gov.ng | Debt profiles |

## Current Status

- **Federal 2026**: Bill submitted, awaiting NASS passage
- **States 2026**: 35/36 states have passed budgets
- **Rivers State**: NO 2026 budget (political crisis)

See `docs/STATE_DATA_STATUS.md` for complete status of all states.

## Contributing

This is part of the Decide9ja civic tech initiative. Contributions welcome:
1. Data validation and corrections
2. Additional state budget sources
3. Extraction improvements for different PDF formats

## License

Open source for civic accountability purposes.

## Credits

- Research: GST (@wearegst) viral budget analysis
- Data: Budgetpedia (CSJ partnership)
- Inspiration: BudgIT OpenStates platform
