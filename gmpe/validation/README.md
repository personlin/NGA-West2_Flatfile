# NGA-West2 GMPE Validation

This directory contains CI-friendly validation fixtures for the native Python
and R GMPE implementations.

- `golden_cases.csv` stores representative scalar inputs.
- `golden_outputs.csv` stores expected outputs generated from the native port
  of the audit-only VBA reference.
- `compare_python_r.R` compares Python native and R native outputs for every
  golden case, including applicability warning text.

Runtime validation does not require Excel, VBA, or extracted `.bas` files.

Recommended checks from the repository root:

```bash
/Users/person/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest gmpe/python/tests
/Library/Frameworks/R.framework/Resources/bin/Rscript -e 'testthat::test_local("gmpe/R")'
/Library/Frameworks/R.framework/Resources/bin/Rscript gmpe/validation/compare_python_r.R
```
