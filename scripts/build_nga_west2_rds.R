#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(data.table)
})

source("scripts/nga_west2_common.R")

dir.create("output/rds", showWarnings = FALSE, recursive = TRUE)

files <- add_excel_counts(list_input_files("."))
base_info <- files[component == "RotD50" & abs(damping_percent - 5) < 1e-9][1]
if (nrow(base_info) != 1) stop("Could not find the RotD50 5 percent base flatfile.")

cat("Reading core metadata:", base_info$file_name, "\n")
base_dt <- read_excel_clean(base_info$path, base_info$sheet_name)
field_catalog <- read_header_catalog(base_info$path, base_info$sheet_name)
field_catalog[, field_id := .I]
setcolorder(field_catalog, "field_id")
core <- build_core_tables(base_dt, files, field_catalog)
saveRDS(core, "output/rds/nga_west2_core_normalized.rds")

manifest <- list()
for (i in seq_len(nrow(files))) {
  info <- files[i]
  cat("Writing wide RDS:", info$file_name, "\n")
  dt <- read_excel_clean(info$path, info$sheet_name)
  attr(dt, "source_file") <- info$file_name
  attr(dt, "component") <- info$component
  attr(dt, "damping_percent") <- info$damping_percent
  attr(dt, "na_codes") <- -999
  out_name <- if (info$component == "Vertical") {
    "nga_west2_vertical_d050_flatfile.rds"
  } else {
    sprintf("nga_west2_rotd50_d%s_flatfile.rds", info$damping_code)
  }
  out_path <- file.path("output/rds", out_name)
  saveRDS(dt, out_path)
  manifest[[i]] <- data.table(
    file = out_name,
    source_file = info$file_name,
    component = info$component,
    damping_percent = info$damping_percent,
    rows = nrow(dt),
    columns = ncol(dt),
    sha256 = digest::digest(file = out_path, algo = "sha256")
  )
  rm(dt)
  gc()
}

rds_manifest <- rbindlist(manifest)
saveRDS(rds_manifest, "output/rds/nga_west2_rds_manifest.rds")
fwrite(rds_manifest, "output/rds/nga_west2_rds_manifest.csv")

dir.create("shiny-app/data/cache", showWarnings = FALSE, recursive = TRUE)
events_map <- merge(
  core$events,
  core$records[, .(record_count = .N), by = eqid],
  by = "eqid",
  all.x = TRUE
)
events_map[is.na(record_count), record_count := 0L]
stations_map <- merge(
  core$stations,
  core$sites[, .(station_sequence_number, vs30_m_s, measured_inferred_class)],
  by = "station_sequence_number",
  all.x = TRUE
)
stations_map <- merge(
  stations_map,
  core$records[, .(record_count = .N), by = station_sequence_number],
  by = "station_sequence_number",
  all.x = TRUE
)
stations_map[is.na(record_count), record_count := 0L]

saveRDS(events_map, "shiny-app/data/cache/events_map.rds")
saveRDS(stations_map, "shiny-app/data/cache/stations_map.rds")
saveRDS(core$events[, .N, by = mechanism_class_simple], "shiny-app/data/cache/event_summary.rds")
saveRDS(core$stations[, .N, by = station_region_derived], "shiny-app/data/cache/station_summary.rds")
saveRDS(core$stations[, .N, by = network_name][order(-N)][1:min(.N, 50)], "shiny-app/data/cache/network_summary.rds")

cat("RDS complete: output/rds\n")
print(rds_manifest)

