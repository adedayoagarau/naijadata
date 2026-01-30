---
name: nigerian-corruption-spotter
description: |
  Advanced budget forensics tool for detecting corruption, budget padding, and financial anomalies in Nigerian government budgets (Federal, State, LGA). Combines historical corruption pattern analysis, statistical anomaly detection, and impact quantification. Use this skill when: (1) Analyzing Nigerian budget documents for irregularities, (2) Comparing allocations to detect padding, (3) Calculating what misappropriated funds could have built/funded, (4) Identifying red flags in MDAs (Ministries, Departments, Agencies), (5) Benchmarking spending against national/international standards, (6) Tracking known corruption hotspots (legislature, security votes, emergency procurements), (7) Converting corruption amounts into citizen impact metrics.
---

# Nigerian Corruption Spotter

## Quick Start Workflow
1. LOAD budget data (PDF, JSON, or structured text)
2. RUN red flag scan (see references/red-flags.md)
3. CALCULATE anomaly scores (see references/benchmarks.md)
4. QUANTIFY impact (see references/impact-calculator.md)
5. GENERATE report with findings

## Red Flag Categories

### Category A: Structural (High Confidence)
- Budget padding: Line items 200%+ above previous year
- Phantom projects: Capital allocations with no implementation
- Vague descriptions: "Miscellaneous", "Sundry" over ₦100M

### Category B: Ratio Anomalies
- Overhead > Capital in development MDAs
- Travel > Service Delivery costs
- Admin > 30% of total allocation

### Category C: Comparative
- Allocation 150%+ above peer states
- 100%+ YoY increase without policy change

## Risk Scoring
Score = (Structural Flags × 3) + (Ratio Anomalies × 2) + (Comparative × 1)
- 0-3: Low | 4-6: Medium | 7-9: High | 10+: Critical

## Key References
- references/red-flags.md - Detection rules
- references/benchmarks.md - Nigerian cost standards
- references/impact-calculator.md - Naira to impact conversion
- references/corruption-history.md - Historical cases
- scripts/impact_calculator.py - Calculation tool
- scripts/red_flag_scanner.py - Automated scanning
