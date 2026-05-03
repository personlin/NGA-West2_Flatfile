# NGA-West2 Flatfile Explorer

Run from the repository root:

```r
shiny::runApp("shiny-app")
```

Before launching, build the data products:

```bash
Rscript scripts/build_nga_west2_sqlite.R
Rscript scripts/build_nga_west2_rds.R
```

The app uses SQLite for maps, tables, and statistics. Wide RDS files are loaded lazily on the Analysis page.

