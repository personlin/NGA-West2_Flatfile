# NGA-West2 GMPE Python and R Implementation Plan

## Implementation Status

Current status as of 2026-05-03:

- Phase 1 coefficient extraction is implemented and coefficient CSVs are
  versioned under `gmpe/coefficients/`.
- VBA extraction is implemented as an audit-only local workflow under ignored
  `output/gmpe_vba/`; VBA source is not a runtime dependency.
- Native Python equation source is generated into
  `gmpe/python/src/ngaw2gmpe/models/_native.py` from the audit VBA reference.
- Python scalar APIs, batch prediction, golden fixtures, and residual workflow
  are implemented for ASK14, BSSA14, CB14, CY14, and I14.
- R exposes matching scalar and batch APIs through generated pure R equation
  source in `gmpe/R/R/native.R`; the previous Python JSON bridge has been
  removed from runtime prediction workflows.
- Python and R scalar APIs now expose workbook-style applicability warnings,
  and batch prediction outputs include a `warnings` column.
- Optional flatfile missing-value sentinels such as `-999` are normalized to
  workbook-style `999` sentinels for optional depth/geometry inputs before
  prediction.
- Shiny Analysis tab integration is implemented for selected 5 percent RotD50
  PGA/PSA prediction overlays and residual plots.

This document plans a reproducible Python and R implementation of the NGA-West2 GMPE spreadsheet workbook:

```text
data/NGAW2_GMPE_Spreadsheets_v5.7_041415_ProtectedLocked.xlsm
```

The plan is based on:

- workbook cell formulas and coefficient sheets readable from the `.xlsm`;
- extracted VBA source code from `xl/vbaProject.bin`;
- the current project data pipeline and Shiny app architecture.

## 1. Goals

Implement the NGA-West2 GMPE calculations in both Python and R with a shared coefficient dataset and matching behavior:

- ASK14: Abrahamson, Silva, and Kamai 2014
- BSSA14: Boore, Stewart, Seyhan, and Atkinson 2014
- CB14: Campbell and Bozorgnia 2014
- CY14: Chiou and Youngs 2014
- I14: Idriss 2014

The implementation should:

- reproduce workbook/VBA median predictions and standard deviations;
- expose scalar and vectorized APIs;
- use versioned, machine-readable coefficient tables;
- avoid requiring Excel or VBA at runtime;
- include golden-case validation against the original workbook/VBA behavior.

## 1.1 VBA-Free Runtime Requirement

The final Python and R implementations must run independently after the extracted VBA source code is deleted.

VBA is allowed only as a porting and audit reference during development. It must not be imported, executed, sourced, shell-called, or otherwise required by the production Python/R packages. After equations are ported and validated, the runtime dependency graph should be:

```text
Python/R source code
  + versioned coefficient CSV/JSON files
  + validation fixtures
  + ordinary Python/R numeric libraries
```

The runtime dependency graph must not include:

```text
Excel
VBA
xl/vbaProject.bin
output/vba/
gmpe/reference/vba/
oletools
LibreOffice macro execution
Microsoft Excel automation
```

Allowed uses of the workbook/VBA after the port is complete:

- regenerate coefficient CSVs from workbook sheets;
- regenerate audit documentation;
- regenerate golden outputs in a controlled validation workflow.

Disallowed uses in normal prediction workflows:

- calling Excel formulas directly;
- calling VBA functions directly;
- reading extracted `.bas` files to compute predictions;
- relying on cached workbook formula values for model output.

This means deleting `output/vba/` or removing committed `gmpe/reference/vba/` files must not break:

- Python package imports;
- R package loading;
- scalar prediction functions;
- batch prediction functions;
- Python/R parity tests using committed fixtures;
- Shiny integrations that call the Python/R implementation.

## 2. Source Inventory

### Workbook Sheets

The workbook contains 16 sheets. Important sheets for implementation:

| Sheet | Role |
|---|---|
| `Main` | User inputs, model weights, combined output formulas |
| `ASK14` | ASK14 formula wiring and outputs |
| `ASK14_Coeffs` | ASK14 coefficient table |
| `BSSA14` | BSSA14 formula wiring and outputs |
| `BSSA14_Coeffs` | BSSA14 coefficient table |
| `CB14` | CB14 formula wiring and outputs |
| `CB14_Coeffs` | CB14 coefficient table |
| `CY14` | CY14 formula wiring and outputs |
| `CY14_Coeffs` | CY14 coefficient table |
| `I14` | I14 formula wiring and outputs |
| `I14_Coeffs` | I14 coefficient table |
| `DSF` | Directivity/simple fault helper calculations |
| `GMPEs Comparison` | Hidden comparison/output sheet |

### Coefficient Sheets

Initial extraction confirms the coefficient sheets are readable:

| Coefficients | Approximate Used Range | Notes |
|---|---|---|
| `ASK14_Coeffs` | `A1:AT28` | No cell formulas detected |
| `BSSA14_Coeffs` | `A1:AK27` | No cell formulas detected |
| `CB14_Coeffs` | `A1:AR27` | No cell formulas detected |
| `CY14_Coeffs` | `A1:AT30` | Contains a few formulas duplicating/extending rows |
| `I14_Coeffs` | `A1:M26` | No cell formulas detected |

### VBA Modules

Extracted VBA source code maps to the implementation work as follows:

| VBA File | Functions | GMPE Area |
|---|---|---|
| `Module1.bas` | `A1100_CB`, `CB_14` | CB14 median and A1100 helper |
| `Module2.bas` | `CY_14`, `CY14_stdev` | CY14 median and sigma |
| `Module3.bas` | `ASK_14`, `ASK14_Z1`, `ASK14_stdev` | ASK14 median, basin helper, sigma |
| `Module4.bas` | `BSSA_14`, `BSSA14_stdev` | BSSA14 median and sigma |
| `Module5.bas` | `PGAr_calc` | BSSA14 reference PGA helper |
| `Module6.bas` | `dz1_calc` | BSSA14 basin-depth helper |
| `Module7.bas` | `I_14`, `I_14_stdev` | Idriss 2014 median and sigma |
| `Sheet8.cls` | `CommandButton1_Click` | UI/event helper, not core GMPE logic |

## 3. Repository Layout

Recommended layout:

```text
gmpe/
  README.md
  coefficients/
    ask14.csv
    bssa14.csv
    cb14.csv
    cy14.csv
    i14.csv
    periods.csv
    coefficient_manifest.json
  reference/
    vba/                 # optional audit-only copy; not a runtime dependency
      Module1.bas
      Module2.bas
      Module3.bas
      Module4.bas
      Module5.bas
      Module6.bas
      Module7.bas
    workbook_formula_catalog.csv
  python/
    pyproject.toml
    src/ngaw2gmpe/
      __init__.py
      coefficients.py
      models/
        _native.py
        ask14.py
        bssa14.py
        cb14.py
        cy14.py
        idriss14.py
      utils.py
      validation.py
    tests/
  R/
    DESCRIPTION
    NAMESPACE
    R/
      coefficients.R
      native.R
      models.R
      batch.R
      utils.R
    tests/testthat/
  validation/
    golden_cases.csv
    golden_outputs.csv
    compare_python_r.R
    compare_against_workbook.py
scripts/
  extract_ngaw2_gmpe_coefficients.py
  extract_ngaw2_gmpe_vba.py
```

Rationale:

- `gmpe/coefficients/` is shared by Python and R.
- `gmpe/reference/vba/` may keep a readable copy of the original extracted VBA for audit, but Python/R code must not depend on it.
- Python and R implementations live side-by-side but are validated against the same fixtures.
- Extraction scripts remain in `scripts/`, matching the current project convention.

## 4. Coefficient Extraction Plan

Create `scripts/extract_ngaw2_gmpe_coefficients.py`.

Responsibilities:

1. Open the `.xlsm` with `openpyxl`.
2. Read coefficient sheets with `data_only=False` and `data_only=True`.
3. Preserve:
   - model name;
   - source workbook;
   - source sheet;
   - source range;
   - period column or row;
   - original coefficient names;
   - numeric values;
   - formula text where present.
4. Write one normalized CSV per model:

```text
model,period_s,imt,row_index,coefficient,value,source_sheet,source_cell
ASK14,0.01,SA,5,c2,...
BSSA14,0.01,SA,5,e0,...
CB14,0.01,SA,5,c0,...
CY14,0.01,SA,5,c2,...
I14,0.01,SA,5,a1,...
```

5. Write wide CSVs only if they help manual review.
6. Write `coefficient_manifest.json` with workbook SHA-256, sheet dimensions, extraction timestamp, and row counts.

Implementation details:

- Treat `T = 0` as PGA if the workbook/VBA does.
- Treat `T = -1` as PGV if the workbook/VBA does.
- Keep all period values as numeric plus a stable string key, for example `p0p010`, `p1p000`, `pga`, `pgv`.
- Do not silently evaluate formulas in coefficient sheets; store formula text and cached value separately when present.

## 5. VBA Extraction Plan

Create `scripts/extract_ngaw2_gmpe_vba.py`.

Responsibilities:

1. Extract `xl/vbaProject.bin` from the workbook.
2. Use `oletools.olevba` when available.
3. Export `.bas` and `.cls` files to `gmpe/reference/vba/`.
4. Write a `vba_manifest.csv` with:
   - stream path;
   - exported file name;
   - line count;
   - function names discovered by regex;
   - SHA-256 of exported source.

The extracted source should be committed only if licensing and redistribution are acceptable for this project. If not, keep it as generated output and commit only the extraction script plus manifest.

Regardless of whether the extracted source is committed, it must be treated as disposable reference material. The implementation should continue to pass tests if `gmpe/reference/vba/` and `output/vba/` are removed after the port is complete.

## 6. Shared Model Semantics

Both Python and R should implement the same conceptual API.

Required inputs should cover the workbook/VBA arguments:

| Concept | Common Names |
|---|---|
| Magnitude | `M` |
| Rupture distance | `Rrup` |
| Joyner-Boore distance | `Rjb` |
| Hanging-wall distance | `Rx` |
| Vs30 | `Vs30` |
| Fault flags | `Frv`, `Fnm`, `Fhw`, `FAS`, `U`, `RS`, `NS` |
| Geometry | `W`, `dip`, `Ztor`, `Zhyp`, `Ry0` |
| Basin depth | `Z1`, `Z25` |
| Region | numeric region code and named region helper |
| Period | `T` or `period` |

Use a shared region-code table documenting workbook behavior:

| Code | Meaning in VBA comments |
|---|---|
| `0` | global / California / Taiwan / New Zealand in several functions |
| `1` | Japan |
| `3` | China |
| `4` | Italy |
| `5` | Turkey in BSSA helper comments |

This table must be verified function by function because the VBA comments differ slightly among models.

## 7. Python API Plan

Package name:

```text
ngaw2gmpe
```

Example scalar API:

```python
from ngaw2gmpe import ask14, bssa14, cb14, cy14, idriss14

result = cb14(
    M=6.5,
    Rrup=20.0,
    Rjb=18.0,
    Rx=5.0,
    Frv=1,
    Fnm=0,
    Fhw=1,
    Ztor=2.0,
    W=15.0,
    dip=30.0,
    Vs30=760.0,
    Z25=999,
    Zhyp=999,
    region="global",
    period=1.0,
)

result.median
result.sigma
```

Recommended implementation details:

- Use `numpy` for vectorization.
- Use `pandas` only for coefficient loading and tabular batch prediction.
- Return a dataclass or named tuple with:
  - `median`;
  - `ln_median`;
  - `sigma`;
  - optional `tau`, `phi` where available;
  - `warnings` for workbook-style applicability messages;
  - model metadata.
- Provide `predict_dataframe(df, model, periods)` for batch use with flatfiles.
- Provide coefficient loaders that cache CSV contents.
- Keep equations close to the VBA structure in the first port; refactor only after validation is stable.
- Do not parse `.bas` files at runtime. The model equations must live as native Python source.

Python tests:

- Unit tests for helper functions such as `ASK14_Z1`, `PGAr_calc`, `dz1_calc`.
- Golden-case tests for each model and period.
- Vectorized vs scalar equivalence tests.
- Missing/default value behavior tests for `999` and `-999` where workbook logic uses those sentinels.

## 8. R API Plan

R package name:

```text
ngaw2gmpe
```

Example scalar API:

```r
library(ngaw2gmpe)

result <- cb14(
  M = 6.5,
  Rrup = 20,
  Rjb = 18,
  Rx = 5,
  Frv = 1,
  Fnm = 0,
  Fhw = 1,
  Ztor = 2,
  W = 15,
  dip = 30,
  Vs30 = 760,
  Z25 = 999,
  Zhyp = 999,
  region = "global",
  period = 1.0
)

result$median
result$sigma
```

Recommended implementation details:

- Use base R plus `data.table` for coefficient loading and batch prediction.
- Return a list or `data.table` with `median`, `ln_median`, `sigma`,
  optional `tau`/`phi`, `warnings`, and metadata.
- Implement vectorized functions using standard R recycling rules cautiously; validate length compatibility.
- Generate `R/native.R` from the same audit-only VBA source used for Python
  native source so R runtime prediction does not call Python.
- Keep function argument names aligned with the Python package where possible.
- Add thin wrappers for flatfile columns, for example mapping `earthquake_magnitude`, `joyner_boore_dist_km`, `campbell_r_dist_km`, and `vs30_m_s_selected_for_analysis` to model inputs.
- Do not source or parse VBA files at runtime. The model equations must live as
  native R source.

R tests:

- `testthat` golden-case tests matching Python and workbook outputs.
- CSV coefficient loading tests.
- R/Python parity tests using the same `golden_cases.csv` and both native
  runtimes.
- Batch prediction tests on small flatfile subsets.

## 9. Validation Strategy

Validation should have three layers.

### Layer 1: Source Extraction Checks

- Compare extracted coefficient table dimensions to workbook dimensions.
- Check coefficient row/period coverage against VBA `Select Case T` blocks.
- Check exported VBA function names against expected function inventory.

### Layer 2: Workbook Golden Cases

Build `gmpe/validation/golden_cases.csv` with representative inputs:

- magnitudes: low, mid, high within applicability ranges;
- distances: near-fault, moderate, far;
- Vs30: soft soil, reference, hard rock;
- fault styles: strike-slip, normal, reverse;
- region codes: global/California, Japan, China, Italy, Turkey where supported;
- missing/default sentinels: `999` for optional depths/geometry where VBA uses that convention;
- periods: PGA (`T=0`), PGV (`T=-1` where applicable), 0.01, 0.2, 1.0, 3.0, 10.0.

Generate `golden_outputs.csv` from the original workbook using one of:

1. Microsoft Excel automation, if available.
2. LibreOffice headless, only if macro/function evaluation is verified.
3. A one-time manual workbook export for selected cases.
4. The extracted VBA run in a controlled VBA/Excel host.

Do not trust `openpyxl` for formula evaluation; it can read formulas and cached values but does not calculate Excel/VBA formulas.

### Layer 3: Cross-Language Parity

For every golden case:

- Python output must match golden output within tolerance.
- R output must match golden output within tolerance.
- Python and R must match each other even when no workbook golden value is available yet.

Suggested tolerance:

```text
absolute tolerance for ln values: 1e-6 to 1e-5
relative tolerance for median values: 1e-5
```

Use looser tolerance only where the workbook itself uses rounded display values.

### Layer 4: VBA-Deletion Independence Test

Add an explicit independence test before declaring the port complete:

1. Move or delete `output/vba/`.
2. Move or delete `gmpe/reference/vba/`, if it exists.
3. Run Python unit tests and golden tests.
4. Run R `testthat` tests and golden tests.
5. Run Python/R parity comparison.
6. Run one batch prediction on a small NGA-West2 flatfile subset.

All tests must pass without any VBA source files present. Coefficient CSV/JSON files and golden fixtures are allowed because they are the intended runtime and validation artifacts.

## 10. Integration with Existing Flatfile Project

After Python/R packages are validated:

- Shiny analysis support for GMPE prediction overlays has been added to the
  existing Analysis tab.
- A script computes residuals between observed RotD50 values and selected GMPE predictions.
- SQLite helper tables or cached RDS files for selected GMPE predictions remain
  unnecessary for the current subset-on-demand workflow.

Potential app features:

- select GMPE model and period;
- compute predicted median and sigma for filtered records;
- plot observed vs predicted PSA/PGA;
- plot residuals vs magnitude, distance, and Vs30;
- compare ASK14/BSSA14/CB14/CY14/I14 medians.

## 11. Implementation Phases

### Phase 1: Extraction and Audit

- Add coefficient extraction script.
- Add VBA extraction script.
- Export coefficient CSVs and manifests.
- Decide whether extracted VBA source can be committed.
- Document function inventory and coefficient sheet coverage.
- Mark extracted VBA as audit-only and disposable in documentation.

### Phase 2: Python Prototype

- Implement coefficient loader.
- Port helper functions first: `ASK14_Z1`, `PGAr_calc`, `dz1_calc`, `A1100_CB`.
- Port median equations one model at a time.
- Add scalar golden tests.
- Add vectorized/batch API after scalar outputs are stable.
- Verify Python tests do not read VBA files.

### Phase 3: R Prototype

- Mirror Python coefficient loader and helper functions.
- Generate native R raw/helper functions from the audit-only VBA source.
- Wrap generated raw/helper functions with public R APIs matching Python.
- Add `testthat` golden tests.
- Add flatfile-column wrappers.
- Verify R tests do not read VBA files or shell out to Python for predictions.

### Phase 4: Golden Validation Harness

- Generate workbook-based golden cases.
- Build automated Python/R comparison reports that compare Python native and R
  native outputs.
- Store validation summaries under `gmpe/validation/`.
- Add CI-friendly tests that do not require Excel.
- Add the VBA-deletion independence test.

### Phase 5: Documentation and Shiny Integration

- Write Python and R usage docs.
- Add examples for scalar and batch predictions.
- Add Shiny residual/prediction comparison module in the Analysis tab.
- Document model applicability warnings from workbook sheets.

## 12. Risks and Open Questions

- VBA source and workbook content may have redistribution/licensing constraints; confirm before committing extracted VBA source.
- Excel cached values are not a substitute for recalculation.
- Region-code behavior is model-specific and must be checked against VBA comments and equations.
- Workbook formulas include applicability warnings that should become structured warnings in Python/R.
- Some VBA uses sentinels such as `999` for missing values; the flatfile uses `-999` in many places. Wrapper functions must translate carefully and explicitly.
- The first implementation should prioritize exact workbook parity over idiomatic refactoring.
- If extracted VBA cannot be committed, the project can still be completed by committing coefficient tables, native Python/R ports, manifests, and golden fixtures.

## 13. Definition of Done

The Python/R GMPE port is complete when:

- all coefficient tables are extracted and versioned;
- all core VBA functions have native Python and R equivalents;
- Python and R APIs are documented;
- golden-case tests pass for each model and representative periods;
- Python/R parity tests pass;
- tests still pass after extracted VBA source files are deleted;
- known workbook applicability warnings are represented;
- a user can run batch predictions on NGA-West2 flatfile records without Excel.
