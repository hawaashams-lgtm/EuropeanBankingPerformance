# Data Validation

## Audit scope

The original ECB export contains 44 quarterly rows from 2015 Q2 to 2026 Q1 and 27 statistical series: 9 indicators for each of 3 geographies.

The project uses 2020 Q2 to 2026 Q1 because it is the first common period with complete observations for every selected series. In particular, the NPL and Stage 2 series begin in 2020 Q2.

## Structural checks

| Check | Expected | Observed | Status |
|---|---:|---:|---|
| Analysis rows | 24 × 3 × 9 = 648 | 648 | Pass |
| Distinct quarters | 24 | 24 | Pass |
| Distinct geographies | 3 | 3 | Pass |
| Distinct indicators | 9 | 9 | Pass |
| Missing values | 0 | 0 | Pass |
| Non-numeric values | 0 | 0 | Pass |
| Duplicate analytical keys | 0 | 0 | Pass |
| Coverage per geography-indicator | 24 | 24 | Pass |
| Invalid dates | 0 | 0 | Pass |
| Duplicate dates in source | 0 | 0 | Pass |

The analytical key is:

```text
Time Period + Geography + Indicator
```

## Source reconciliation

The original wide ECB export was compared with the analysis-ready table. All 27 statistical series across the 24 dates in the analysis period were compared numerically. All 648 values matched.

Series metadata embedded in the ECB codes identifies:

- 24 ratio series with the `PCT.C` suffix: percent
- 3 total-assets series with the `LE.E.C` suffix: EUR billions

Dates parse successfully, follow chronological order, match their `YYYYQ#` labels, and fall on calendar quarter ends.

## Outlier review

Cost-of-risk observations were assessed separately for each geography using Tukey's rule:

```text
Lower bound = Q1 − 1.5 × IQR
Upper bound = Q3 + 1.5 × IQR
```

| Geography | Q1 | Median | Q3 | Maximum | Tukey result |
|---|---:|---:|---:|---:|---|
| Germany | 0.2875% | 0.4000% | 0.4950% | 0.87% in 2025 Q1 | Outlier |
| Italy | 0.3175% | 0.4300% | 0.5900% | 0.90% in 2020 Q4 | Not flagged |
| SSM | 0.4675% | 0.4850% | 0.5625% | 0.70% in 2020 Q2 | Not flagged |

Germany's 2025 Q1 value appears identically in both source exports. It is therefore retained as a valid extreme observation rather than removed.

## Range and plausibility checks

- All 648 values are finite and numeric.
- No ratio is negative or above 200% in the selected window.
- All total-asset observations are positive.
- Geography and indicator labels are consistent across all 27 series.

## Reproducibility

Run:

```bash
python3 scripts/ValidateData.py
```

The script checks both CSV files. It exits with an error if the row count, dimensions, coverage, uniqueness, value type, date consistency, units, or source reconciliation differ from the documented expectations.
