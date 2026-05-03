#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(DBI)
  library(RSQLite)
  library(data.table)
})

db_path <- "output/sqlite/nga_west2.sqlite"
if (!file.exists(db_path)) stop("SQLite output not found: ", db_path)

con <- dbConnect(SQLite(), db_path)
on.exit(dbDisconnect(con), add = TRUE)

checks <- rbindlist(list(
  data.table(check = "integrity_check", value = dbGetQuery(con, "PRAGMA integrity_check")[[1]]),
  data.table(check = "events", value = as.character(dbGetQuery(con, "SELECT COUNT(*) FROM events")[[1]])),
  data.table(check = "stations", value = as.character(dbGetQuery(con, "SELECT COUNT(*) FROM stations")[[1]])),
  data.table(check = "records", value = as.character(dbGetQuery(con, "SELECT COUNT(*) FROM records")[[1]])),
  data.table(check = "spectral_periods", value = as.character(dbGetQuery(con, "SELECT COUNT(*) FROM spectral_periods")[[1]])),
  data.table(check = "intensity_measures", value = as.character(dbGetQuery(con, "SELECT COUNT(*) FROM intensity_measures")[[1]])),
  data.table(check = "response_spectra", value = as.character(dbGetQuery(con, "SELECT COUNT(*) FROM response_spectra")[[1]]))
))

dir.create("manifests", showWarnings = FALSE, recursive = TRUE)
fwrite(checks, "manifests/nga_west2_validation_summary.csv")
print(checks)

if (checks[check == "integrity_check", value] != "ok") {
  stop("SQLite integrity check failed.")
}

