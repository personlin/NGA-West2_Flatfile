#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(data.table)
  library(DBI)
  library(RSQLite)
  library(jsonlite)
})

source("scripts/nga_west2_common.R")

dir.create("output/sqlite", showWarnings = FALSE, recursive = TRUE)
dir.create("shiny-app/data/cache", showWarnings = FALSE, recursive = TRUE)

files <- add_excel_counts(list_input_files("."))
base_info <- files[component == "RotD50" & abs(damping_percent - 5) < 1e-9][1]
if (nrow(base_info) != 1) stop("Could not find the RotD50 5 percent base flatfile.")

cat("Reading base metadata:", base_info$file_name, "\n")
base_dt <- read_excel_clean(base_info$path, base_info$sheet_name)
field_catalog <- read_header_catalog(base_info$path, base_info$sheet_name)
field_catalog[, field_id := .I]
setcolorder(field_catalog, "field_id")

core <- build_core_tables(base_dt, files, field_catalog)
core$release_files <- make_release_files(files)
core$release_files <- files[, .(
  release_file_id, file_name, component, damping_code, damping_percent,
  sheet_name, row_count, column_count, file_size_bytes, sha256
)]

db_path <- "output/sqlite/nga_west2.sqlite"
if (file.exists(db_path)) unlink(db_path)
con <- dbConnect(SQLite(), db_path)
on.exit(dbDisconnect(con), add = TRUE)

for (nm in names(core)) {
  cat("Writing table:", nm, "\n")
  dbWriteTable(con, nm, as.data.frame(core[[nm]]), overwrite = TRUE)
}

make_ground_motion_subset <- function(info) {
  header <- read_header_catalog(info$path, info$sheet_name)
  keep <- header$clean_name %in% c("record_sequence_number", "pga_g", "pgv_cm_sec", "pgd_cm") |
    grepl("^t[0-9]+_[0-9]+s$", header$clean_name)
  col_types <- rep("skip", nrow(header))
  col_types[keep] <- "guess"
  dt <- read_excel_clean(info$path, info$sheet_name, col_types = col_types)
  pcols <- period_columns(dt)
  if (!length(pcols)) stop("No spectral period columns found in ", info$file_name)
  mat <- as.matrix(dt[, ..pcols])
  storage.mode(mat) <- "numeric"
  data.table(
    rsn = col_or_na(dt, "record_sequence_number", "integer"),
    component = info$component,
    damping_percent = info$damping_percent,
    pga_g = col_or_na(dt, "pga_g"),
    pgv_cm_sec = col_or_na(dt, "pgv_cm_sec"),
    pgd_cm = col_or_na(dt, "pgd_cm"),
    psa_json = apply(mat, 1, function(x) jsonlite::toJSON(as.numeric(x), auto_unbox = TRUE, na = "null"))
  )
}

common_periods <- c(0.01, 0.2, 1.0, 3.0, 10.0)
all_intensity <- list()
all_common <- list()

for (i in seq_len(nrow(files))) {
  info <- files[i]
  cat("Reading ground motions:", info$file_name, "\n")
  gm <- make_ground_motion_subset(info)
  intensity <- gm[, .(rsn, component, damping_percent, pga_g, pgv_cm_sec, pgd_cm)]
  intensity[, intensity_measure_id := .I + if (length(all_intensity)) sum(vapply(all_intensity, nrow, integer(1))) else 0L]
  setcolorder(intensity, "intensity_measure_id")
  all_intensity[[i]] <- intensity

  spectra <- gm[, .(rsn, component, damping_percent, psa_json)]
  spectra[, spectrum_id := .I]
  dbWriteTable(con, "response_spectra", as.data.frame(spectra), append = dbExistsTable(con, "response_spectra"))

  header <- read_header_catalog(info$path, info$sheet_name)
  pvals <- period_values(header$clean_name[grepl("^t[0-9]+_[0-9]+s$", header$clean_name)])
  idx <- match(common_periods, pvals)
  header_periods <- header$clean_name[grepl("^t[0-9]+_[0-9]+s$", header$clean_name)]
  col_types <- rep("skip", nrow(header))
  keep_common <- header$clean_name %in% c("record_sequence_number", header_periods[idx[!is.na(idx)]])
  col_types[keep_common] <- "guess"
  cdt <- read_excel_clean(info$path, info$sheet_name, col_types = col_types)
  common <- data.table(
    rsn = col_or_na(cdt, "record_sequence_number", "integer"),
    component = info$component,
    damping_percent = info$damping_percent
  )
  for (j in seq_along(common_periods)) {
    cname <- sprintf("psa_%s_s", gsub("[.]", "p", format(common_periods[j], trim = TRUE, scientific = FALSE)))
    src <- if (!is.na(idx[j])) header_periods[idx[j]] else NA_character_
    common[, (cname) := if (!is.na(src) && src %in% names(cdt)) col_or_na(cdt, src) else NA_real_]
  }
  all_common[[i]] <- common
  rm(gm, spectra, intensity, common, cdt)
  gc()
}

intensity_measures <- rbindlist(all_intensity, use.names = TRUE)
dbWriteTable(con, "intensity_measures", as.data.frame(intensity_measures), overwrite = TRUE)

response_spectra_common_periods <- rbindlist(all_common, use.names = TRUE, fill = TRUE)
dbWriteTable(con, "response_spectra_common_periods", as.data.frame(response_spectra_common_periods), overwrite = TRUE)

dbExecute(con, "CREATE INDEX idx_records_eqid ON records(eqid)")
dbExecute(con, "CREATE INDEX idx_records_station ON records(station_sequence_number)")
dbExecute(con, "CREATE INDEX idx_events_mechanism ON events(mechanism_class_simple)")
dbExecute(con, "CREATE INDEX idx_events_mag ON events(earthquake_magnitude)")
dbExecute(con, "CREATE INDEX idx_stations_network ON stations(network_id)")
dbExecute(con, "CREATE INDEX idx_paths_rjb ON paths(rjb_km)")
dbExecute(con, "CREATE INDEX idx_paths_rrup ON paths(rrup_km)")
dbExecute(con, "CREATE INDEX idx_im_rsn_component_damping ON intensity_measures(rsn, component, damping_percent)")
dbExecute(con, "CREATE INDEX idx_spectra_rsn_component_damping ON response_spectra(rsn, component, damping_percent)")

dbExecute(con, "
CREATE VIEW vw_events_map AS
SELECT
  e.eqid,
  e.earthquake_name,
  e.event_region_derived,
  e.event_datetime_utc,
  e.year,
  e.earthquake_magnitude,
  e.hypocenter_latitude,
  e.hypocenter_longitude,
  e.hypocenter_depth_km,
  e.mechanism_code,
  e.mechanism_class_original,
  e.mechanism_class_simple,
  COUNT(r.rsn) AS record_count
FROM events e
LEFT JOIN records r ON r.eqid = e.eqid
GROUP BY e.eqid
")

dbExecute(con, "
CREATE VIEW vw_stations_map AS
SELECT
  s.station_sequence_number,
  s.station_name,
  s.station_id_no,
  s.network_id,
  n.network_name,
  s.station_region_derived,
  s.station_latitude,
  s.station_longitude,
  site.vs30_m_s,
  site.measured_inferred_class,
  COUNT(r.rsn) AS record_count
FROM stations s
LEFT JOIN networks n ON n.network_id = s.network_id
LEFT JOIN sites site ON site.station_sequence_number = s.station_sequence_number
LEFT JOIN records r ON r.station_sequence_number = s.station_sequence_number
GROUP BY s.station_sequence_number
")

dbExecute(con, "
CREATE VIEW vw_records_overview AS
SELECT
  r.rsn,
  r.eqid,
  e.earthquake_name,
  e.earthquake_magnitude,
  e.mechanism_class_simple,
  e.event_region_derived,
  r.station_sequence_number,
  s.station_name,
  n.network_name,
  s.station_region_derived,
  p.rjb_km,
  p.rrup_km,
  site.vs30_m_s,
  im.pga_g,
  im.pgv_cm_sec,
  im.pgd_cm
FROM records r
LEFT JOIN events e ON e.eqid = r.eqid
LEFT JOIN stations s ON s.station_sequence_number = r.station_sequence_number
LEFT JOIN networks n ON n.network_id = s.network_id
LEFT JOIN sites site ON site.station_sequence_number = s.station_sequence_number
LEFT JOIN paths p ON p.rsn = r.rsn
LEFT JOIN intensity_measures im
  ON im.rsn = r.rsn AND im.component = 'RotD50' AND im.damping_percent = 5
")

dbExecute(con, "
CREATE VIEW vw_ground_motion_rotd50_d050 AS
SELECT
  v.*,
  cp.psa_0p01_s,
  cp.psa_0p2_s,
  cp.psa_1_s,
  cp.psa_3_s,
  cp.psa_10_s
FROM vw_records_overview v
LEFT JOIN response_spectra_common_periods cp
  ON cp.rsn = v.rsn AND cp.component = 'RotD50' AND cp.damping_percent = 5
")

build_manifest <- data.table(
  build_time_utc = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  sqlite_path = db_path,
  events = dbGetQuery(con, "SELECT COUNT(*) AS n FROM events")$n,
  stations = dbGetQuery(con, "SELECT COUNT(*) AS n FROM stations")$n,
  records = dbGetQuery(con, "SELECT COUNT(*) AS n FROM records")$n,
  intensity_measures = dbGetQuery(con, "SELECT COUNT(*) AS n FROM intensity_measures")$n,
  response_spectra = dbGetQuery(con, "SELECT COUNT(*) AS n FROM response_spectra")$n,
  integrity_check = dbGetQuery(con, "PRAGMA integrity_check")[[1]]
)
dbWriteTable(con, "build_manifest", as.data.frame(build_manifest), overwrite = TRUE)

saveRDS(dbGetQuery(con, "SELECT * FROM vw_events_map"), "shiny-app/data/cache/events_map.rds")
saveRDS(dbGetQuery(con, "SELECT * FROM vw_stations_map"), "shiny-app/data/cache/stations_map.rds")
saveRDS(build_manifest, "shiny-app/data/cache/overview_counts.rds")
saveRDS(dbGetQuery(con, "SELECT mechanism_class_simple, COUNT(*) AS n FROM events GROUP BY mechanism_class_simple"), "shiny-app/data/cache/event_summary.rds")
saveRDS(dbGetQuery(con, "SELECT station_region_derived, COUNT(*) AS n FROM stations GROUP BY station_region_derived"), "shiny-app/data/cache/station_summary.rds")
saveRDS(dbGetQuery(con, "SELECT network_name, COUNT(*) AS n FROM vw_stations_map GROUP BY network_name ORDER BY n DESC LIMIT 50"), "shiny-app/data/cache/network_summary.rds")

cat("SQLite complete:", db_path, "\n")
print(build_manifest)

