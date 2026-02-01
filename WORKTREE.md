# DECIDE9JA - CANONICAL WORKTREE STRUCTURE

**STRICT ADHERENCE REQUIRED** - All data and code must follow this structure.

---

## ROOT DIRECTORY STRUCTURE

```
naijadata/
├── README.md                    # Project overview
├── WORKTREE.md                  # THIS FILE - canonical structure
├── .gitignore                   # Git ignore rules
├── .env.example                 # Environment variable template
│
├── data/                        # RAW & REFERENCE DATA (read-only after setup)
│   ├── context/                 # Static reference data
│   ├── federal/                 # Federal budget raw data by year
│   └── states/                  # State budget raw data by state/year
│
├── findings/                    # ANALYSIS OUTPUT (generated/curated)
│   ├── consolidated.json        # SINGLE SOURCE OF TRUTH for webapp
│   ├── by_state/                # State-specific findings
│   └── archive/                 # Historical/superseded findings
│
├── extracted/                   # PDF EXTRACTION OUTPUT (intermediate)
│   └── {source}_{year}.json     # Raw extracted data
│
├── scripts/                     # PYTHON SCRIPTS
│   ├── extract/                 # PDF extraction scripts
│   ├── analyze/                 # Analysis & scoring scripts
│   └── utils/                   # Shared utilities
│
└── webapp/                      # NEXT.JS APPLICATION
    ├── src/
    │   ├── app/                 # Pages & API routes
    │   ├── components/          # React components
    │   └── data/                # Hardcoded reference (governors, etc.)
    └── public/                  # Static assets
```

---

## DETAILED STRUCTURE

### 1. `/data/` - Raw & Reference Data

```
data/
├── context/                     # STATIC REFERENCE DATA
│   ├── benchmarks.json          # Procurement price benchmarks
│   ├── budget_codes.json        # Budget code taxonomy & risk levels
│   ├── corruption_patterns.json # Known fraud patterns
│   ├── mda_mandates.json        # Federal MDA information
│   └── population.json          # State demographics
│
├── federal/                     # FEDERAL BUDGET DATA
│   ├── 2024/
│   │   └── budget_items.json    # All line items
│   ├── 2025/
│   │   └── budget_items.json
│   └── 2026/
│       └── budget_items.json
│
└── states/                      # STATE BUDGET DATA
    ├── abia/
    │   ├── 2024.json
    │   ├── 2025.json
    │   └── 2026.json
    ├── adamawa/
    │   └── ...
    └── {state_slug}/
        └── {year}.json
```

**State Slugs (use lowercase, no spaces):**
```
abia, adamawa, akwa-ibom, anambra, bauchi, bayelsa, benue, borno,
cross-river, delta, ebonyi, edo, ekiti, enugu, fct, gombe, imo,
jigawa, kaduna, kano, katsina, kebbi, kogi, kwara, lagos, nasarawa,
niger, ogun, ondo, osun, oyo, plateau, rivers, sokoto, taraba,
yobe, zamfara
```

---

### 2. `/findings/` - Analysis Output

```
findings/
├── consolidated.json            # MASTER FILE - webapp reads this
├── outrage.json                 # High-impact shareable findings
│
├── by_state/                    # State-specific findings
│   ├── federal.json             # Federal-level findings
│   ├── lagos.json
│   ├── osun.json
│   └── {state_slug}.json
│
└── archive/                     # Historical versions
    ├── 2024-01-15_consolidated.json
    └── ...
```

**CRITICAL: `consolidated.json` is the SINGLE SOURCE OF TRUTH**

The webapp ONLY reads from `findings/consolidated.json`. All other files are for:
- Historical reference (`archive/`)
- State-specific drilling (`by_state/`)
- Social media content (`outrage.json`)

---

### 3. `/extracted/` - PDF Extraction Output

```
extracted/
├── federal_2024.json
├── federal_2025.json
├── federal_2026.json
├── osun_2025.json
├── lagos_2026.json
└── {source}_{year}.json
```

**Naming Convention:** `{source}_{year}.json`
- Source: `federal` or state slug (lowercase)
- Year: 4-digit year

---

### 4. `/scripts/` - Python Scripts

```
scripts/
├── extract/
│   ├── pdf_extractor.py         # Main PDF extraction
│   └── table_parser.py          # Table extraction utilities
│
├── analyze/
│   ├── risk_scorer.py           # Risk scoring algorithm
│   ├── outrage_generator.py     # Find shareable findings
│   ├── yoy_comparison.py        # Year-over-year analysis
│   └── consolidate.py           # Merge all findings → consolidated.json
│
└── utils/
    ├── format_naira.py          # Currency formatting
    ├── validate_data.py         # Data validation
    └── constants.py             # Shared constants
```

---

### 5. `/webapp/` - Next.js Application

```
webapp/
├── src/
│   ├── app/
│   │   ├── page.tsx             # Homepage/Dashboard
│   │   ├── layout.tsx           # Root layout
│   │   ├── globals.css          # Global styles
│   │   │
│   │   ├── api/                 # API ROUTES
│   │   │   ├── chat/route.ts    # AI chat endpoint
│   │   │   ├── findings/
│   │   │   │   ├── route.ts     # GET all findings
│   │   │   │   └── [id]/route.ts# GET single finding
│   │   │   ├── aggregations/route.ts
│   │   │   ├── impact/route.ts
│   │   │   └── synthesize/route.ts
│   │   │
│   │   ├── red-flags/page.tsx   # Red flags listing
│   │   ├── compare/page.tsx     # YoY comparison
│   │   ├── explore/page.tsx     # Browse/search
│   │   ├── impact/page.tsx      # Impact calculator
│   │   ├── about/page.tsx       # About page
│   │   │
│   │   ├── finding/[id]/        # Individual finding detail
│   │   │   ├── page.tsx
│   │   │   └── layout.tsx
│   │   │
│   │   ├── card/[id]/page.tsx   # Share card generator
│   │   └── state/[slug]/page.tsx# State-specific page
│   │
│   ├── components/
│   │   ├── Header.tsx           # Site header with nav
│   │   ├── MobileNav.tsx        # Mobile bottom nav
│   │   ├── ImpactCalculator.tsx # What money could build
│   │   ├── SeverityChart.tsx    # Severity breakdown
│   │   ├── TopFindings.tsx      # Top findings display
│   │   └── ...
│   │
│   └── data/
│       └── governors.ts         # State governors reference
│
├── public/
│   └── ...                      # Static assets
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.mjs
```

---

## DATA SCHEMAS

### Finding Schema (consolidated.json)

```typescript
interface Finding {
  id: string;                    // Unique ID (required)
  type: string;                  // Finding type (see below)
  entity: string;                // MDA or entity name
  description: string;           // Human-readable description
  amount: number;                // Amount in Naira
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  year: number;                  // Budget year

  // Optional fields
  state?: string;                // State name (if state-level)
  budget_code?: string;          // Budget code if applicable
  recommendation?: string;       // Recommended action
  risk_score?: number;           // 0-100 risk score
  risk_factors?: string[];       // Contributing factors
  change_percentage?: number;    // YoY change if applicable
  amount_2025?: number;          // Previous year amount
  shareable_text?: string;       // Pre-formatted social text
  impact?: object;               // What money could build
}
```

**Finding Types:**
```
MANDATE_VIOLATION    - Agency acting outside mandate
YOY_VARIANCE        - Significant year-over-year change
YOY_SPIKE           - Extreme increase (>100%)
ROUND_NUMBER        - Suspiciously round allocation
CROSS_MDA_OUTLIER   - Spending far from peer average
PADDING_INDICATOR   - Price inflation detected
BENFORD_VIOLATION   - Statistical anomaly
DUPLICATE_ALLOCATION- Same project in multiple budgets
CATEGORY_TOTAL      - Aggregate of concerning category
VAGUE_ALLOCATION    - Unclear purpose (miscellaneous)
MISPLACED_LUXURY    - Luxury spending in wrong context
```

**Severity Criteria:**
| Severity | Amount Threshold | Risk Score | Description |
|----------|------------------|------------|-------------|
| CRITICAL | >₦10B OR any mandate violation | >80 | Requires immediate attention |
| HIGH     | ₦1B-₦10B | 60-80 | Significant concern |
| MEDIUM   | ₦100M-₦1B | 40-60 | Worth investigating |
| LOW      | <₦100M | <40 | Minor anomaly |

---

### Budget Item Schema (data/federal/*/budget_items.json)

```typescript
interface BudgetItem {
  mda: string;                   // MDA name
  mda_code?: string;             // MDA code
  budget_code: string;           // Economic code (e.g., "23010105")
  description: string;           // Line item description
  amount: number;                // Amount in Naira
  year: number;                  // Budget year

  // Optional
  personnel?: number;            // Personnel cost component
  overhead?: number;             // Overhead component
  capital?: number;              // Capital component
  category?: string;             // Recurrent/Capital
}
```

---

## API DATA PATHS

**CRITICAL: All APIs must use these paths in this exact order:**

```typescript
// findings/route.ts and findings/[id]/route.ts
const FINDINGS_PATHS = [
  path.join(process.cwd(), "..", "findings", "consolidated.json"),  // PRIMARY
  path.join(process.cwd(), "..", "findings", "outrage.json"),       // Fallback
  path.join(process.cwd(), "data", "findings.json"),                // Local fallback
];

// chat/route.ts - Budget data
const BUDGET_PATHS = [
  path.join(process.cwd(), "..", "data", "federal", "2026", "budget_items.json"),
  path.join(process.cwd(), "..", "data", "federal", "2025", "budget_items.json"),
  path.join(process.cwd(), "..", "extracted", "federal_2026.json"),
];

// chat/route.ts - Context data
const CONTEXT_PATHS = {
  benchmarks: path.join(process.cwd(), "..", "data", "context", "benchmarks.json"),
  budgetCodes: path.join(process.cwd(), "..", "data", "context", "budget_codes.json"),
  patterns: path.join(process.cwd(), "..", "data", "context", "corruption_patterns.json"),
  mandates: path.join(process.cwd(), "..", "data", "context", "mda_mandates.json"),
  population: path.join(process.cwd(), "..", "data", "context", "population.json"),
};
```

---

## FILE SIZE GUIDELINES

| File Type | Max Size | Git Status |
|-----------|----------|------------|
| Context files | <100KB | Committed |
| Individual findings | <500KB | Committed |
| consolidated.json | <5MB | Committed |
| Raw budget data | <50MB | Committed |
| Master data files | >100MB | .gitignore |

**Files that MUST be in .gitignore:**
```
# Large data files
data/master/*.json
extracted/master_*.json
*.log
*.tmp
```

---

## WORKFLOW

### Adding New Budget Data

1. Extract PDF → `/extracted/{source}_{year}.json`
2. Run risk scoring → Updates findings
3. Run consolidation → Updates `/findings/consolidated.json`
4. Webapp automatically picks up new data

### Generating Findings

```bash
# 1. Score raw data
python scripts/analyze/risk_scorer.py

# 2. Generate outrage findings
python scripts/analyze/outrage_generator.py

# 3. Consolidate all findings
python scripts/analyze/consolidate.py
```

### Webapp Development

```bash
cd webapp
npm run dev      # Development
npm run build    # Production build
npm run lint     # Lint check
```

---

## VALIDATION RULES

1. **All JSON files must be valid JSON** - Run `python -m json.tool file.json`
2. **All findings must have required fields** - id, type, entity, description, amount, severity, year
3. **All amounts must be positive integers** - No negative or string amounts
4. **Severity must be one of:** CRITICAL, HIGH, MEDIUM, LOW
5. **Year must be 2019-2030** - Reasonable budget year range
6. **State slugs must be lowercase with hyphens** - e.g., "akwa-ibom" not "Akwa Ibom"

---

## MIGRATION CHECKLIST

- [ ] Rename `webapp_curated_findings.json` → `consolidated.json`
- [ ] Move deprecated files to `findings/archive/`
- [ ] Update all API paths to use canonical structure
- [ ] Create missing directories
- [ ] Validate all JSON files
- [ ] Update .gitignore
- [ ] Run consolidation script

---

*Last Updated: 2026-02-01*
*Maintained by: Decide9ja Team*
