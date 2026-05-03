# AGENTS.md

This file is the project-specific guide for future coding agents and contributors working on the NGA-West2 Flatfile Explorer.

## Project Purpose

This repository converts the public NGA-West2 flatfile Excel workbooks into reproducible SQLite and RDS data products, then serves them through a Shiny app for exploring earthquakes, stations, records, ground-motion values, maps, and summary statistics.

The SQLite database is an application-oriented normalized database reconstructed from public flatfiles. Do not describe it as an official PEER internal database dump.

## Start Here

Before making changes, read:

1. `README.md` or `README.zh-TW.md`
2. `docs/nga_west2_shiny_app_development_plan.md`
3. `docs/data_processing_notes.md`
4. `docs/sqlite_usage.md`
5. `docs/rds_usage.md`

For data model decisions, treat `scripts/nga_west2_common.R` as the central source of truth.

## Repository Layout

```text
data/        Original NGA-West2 public flatfile Excel workbooks
docs/        Plans, usage docs, processing notes, and source report
manifests/   Versioned input/validation summaries
scripts/     Reproducible data inspection, build, and validation scripts
shiny-app/   Shiny dashboard
output/      Generated SQLite/RDS outputs, ignored by Git
```

## Generated Outputs

These paths are generated and intentionally ignored:

```text
output/sqlite/nga_west2.sqlite
output/rds/
shiny-app/data/cache/
```

Do not commit generated SQLite, RDS, or Shiny cache files unless the user explicitly asks for that. Rebuild them locally as needed.

## Core Commands

Run from the repository root.

Inspect source files:

```bash
Rscript scripts/inspect_nga_west2_inputs.R
```

Build SQLite and Shiny cache:

```bash
Rscript scripts/build_nga_west2_sqlite.R
```

Build RDS products:

```bash
Rscript scripts/build_nga_west2_rds.R
```

Validate outputs:

```bash
Rscript scripts/validate_nga_west2_outputs.R
```

Run the Shiny app:

```bash
Rscript -e 'shiny::runApp("shiny-app", host = "127.0.0.1", port = 3838, launch.browser = FALSE)'
```

Expected validation counts:

```text
SQLite integrity_check: ok
events: 600
stations: 4151
records: 21540
spectral_periods: 111
intensity_measures: 258480
response_spectra: 258480
```

## Development Rules

- Keep the pipeline reproducible. Any manual data transformation must be encoded in `scripts/`.
- Preserve official missing-value codes such as `-999` unless a clearly documented analysis view converts them.
- Preserve original Excel field names through `field_catalog` and RDS attributes.
- Keep clean field names stable. Downstream app modules expect snake_case names produced by `clean_names()`.
- Use the 5% RotD50 flatfile as the canonical source for normalized metadata unless the data processing plan is explicitly revised.
- Treat region fields as derived browsing aids, not official metadata.
- Keep Taiwan separated from the broad China station-coordinate rule in `derive_station_region()`.
- If classification, region, or schema logic changes, rebuild SQLite, rebuild RDS, and update affected docs/manifests.
- Do not rely on optional Shiny packages unless you also update requirements and graceful fallbacks.

## Shiny App Notes

The app is intentionally modular:

```text
shiny-app/app.R
shiny-app/R/db.R
shiny-app/R/filters.R
shiny-app/R/module_overview.R
shiny-app/R/module_map.R
shiny-app/R/module_tables.R
shiny-app/R/module_stats.R
shiny-app/R/module_analysis.R
shiny-app/R/module_about.R
```

Guidelines:

- Prefer SQLite queries for overview, maps, tables, and statistics.
- Use RDS only for lazy-loaded analysis workflows.
- Do not load all wide RDS files at app startup.
- Keep table browsing server-friendly; avoid collecting full spectra unless the user explicitly requests an export or subset.
- For maps, keep point caps and clustering available so the app remains responsive.

## Data Model Notes

Important identifiers:

- `RSN` / `record_sequence_number` -> records
- `EQID` / `eqid` -> events
- `Station Sequence Number` / `station_sequence_number` -> stations

Important SQLite views:

- `vw_events_map`
- `vw_stations_map`
- `vw_records_overview`
- `vw_ground_motion_rotd50_d050`

Response spectra are stored as JSON arrays in `response_spectra` to avoid an overly large long-format spectra table. Common periods are also available in `response_spectra_common_periods`.

## Verification Checklist

After data-pipeline changes:

1. Run `Rscript scripts/build_nga_west2_sqlite.R`.
2. Run `Rscript scripts/build_nga_west2_rds.R` if core tables, names, regions, or RDS outputs changed.
3. Run `Rscript scripts/validate_nga_west2_outputs.R`.
4. Confirm `manifests/nga_west2_validation_summary.csv` if validation expectations changed.
5. Smoke-test the Shiny app with an HTTP request, for example `curl -I http://127.0.0.1:3838`.

After Shiny-only changes:

1. Parse R files or run a quick app startup test.
2. Check Overview, Map, Tables, Statistics, Analysis, and About tabs when feasible.
3. Keep UI dependencies limited to packages listed in `README.md`, or document additions.

## Git Hygiene

- Check `git status --short` before editing and before finalizing.
- Do not revert unrelated user changes.
- Keep generated `output/` and `shiny-app/data/cache/` out of commits.
- Commit source scripts, docs, manifests, and Shiny source files when requested.
- If pushing is requested and the remote has new commits, fetch and integrate them without overwriting remote work.

