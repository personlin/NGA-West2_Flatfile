# NGA-West2 GMPE

This directory contains the shared coefficient data and side-by-side Python and
R package skeletons for a native, VBA-free NGA-West2 GMPE implementation.

The current milestone establishes stable APIs, coefficient loading, native
Python and R equations generated from audit-only VBA, validation fixtures, and
batch prediction helpers.

Generated VBA exports are audit-only and belong under `output/gmpe_vba/`, which
is ignored by Git.

## Python

```python
from ngaw2gmpe import ask14, predict_dataframe

result = ask14(
    M=6.5, Rrup=20, Rjb=18, Rx=5, Frv=1, Fhw=1,
    Ztor=2, W=15, dip=30, Vs30=760, period=1.0
)
result.median
result.sigma
result.warnings
```

Batch predictions accept NGA-West2 flatfile-style column names:

```python
pred = predict_dataframe(df, "ASK14", [0.2, 1.0])
```

Scalar results include workbook-style applicability warnings. Optional
depth/geometry sentinels from the public flatfiles, such as `-999`, are
normalized to the workbook missing-value convention before prediction.

## R

```r
pkgload::load_all("gmpe/R")

ask14(
  M = 6.5, Rrup = 20, Rjb = 18, Rx = 5, Frv = 1, Fhw = 1,
  Ztor = 2, W = 15, dip = 30, Vs30 = 760, period = 1.0
)
```

The R API calls native R equation source in `gmpe/R/R/native.R`; it does not
shell out to Python, Excel, or VBA at runtime.

R scalar results include the same `warnings` field as Python, and
`predict_dataframe()` includes a semicolon-separated `warnings` column.

Run R package tests with:

```bash
Rscript -e 'testthat::test_local("gmpe/R")'
```

Compare Python and R native outputs with:

```bash
Rscript gmpe/validation/compare_python_r.R
```

## Residuals

After building `output/sqlite/nga_west2.sqlite`, compute residuals with:

```bash
PYTHONPATH=gmpe/python/src python3 scripts/compute_ngaw2_gmpe_residuals.py \
  --model ASK14 --period 1.0 --out output/gmpe_residuals/ask14_1s.csv
```
