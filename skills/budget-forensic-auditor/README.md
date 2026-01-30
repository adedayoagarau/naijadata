# Budget Forensic Auditor

A CFA-level forensic accounting system for Nigerian budget analysis.

## Capabilities

### 1. Benford's Law Analysis
Detects manipulated numbers by analyzing first-digit distribution. Natural financial data follows Benford's Law - deviations indicate potential fraud.

### 2. Variance Analysis
- **Year-over-Year (YoY)**: Flags items with >50% change without justification
- **Cross-MDA Comparison**: Same budget codes, different agencies - why the 10x difference?
- **Inflation-Adjusted**: Compares against expected inflation growth

### 3. Classification Fraud Detection
- Items miscoded to hide in "miscellaneous" or "others"
- Security agencies doing non-security work
- Capital expenditure disguised as recurrent (or vice versa)

### 4. Pattern Recognition
- Recurring contractor names across unrelated MDAs
- Round number bias (₦1,000,000,000 exactly = suspicious)
- End-of-year spending spikes
- Election year anomalies

### 5. Nigerian Context Rules
- Ghost worker detection patterns
- Padding indicators
- Security vote opacity flags
- Known problematic MDAs
- State-federal duplication

## Output

Findings are stored in `/findings/` as JSON with:
- Severity: CRITICAL, HIGH, MEDIUM, LOW
- Confidence: 0-100%
- Evidence: Supporting data points
- Impact: Estimated naira value
- Recommendation: Suggested action

## Usage

```bash
# Run full analysis on extracted budget data
python scripts/run_analysis.py --input ../extracted/ --output findings/

# Run specific analyzer
python scripts/run_analysis.py --analyzer benford --input ../extracted/

# Continuous monitoring mode
python scripts/run_analysis.py --watch --input ../extracted/
```
