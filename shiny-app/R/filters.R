safe_choices <- function(x) {
  x <- sort(unique(as.character(x)))
  x[!is.na(x) & nzchar(x)]
}

limit_points <- function(dt, show_all, cap = 2500) {
  if (isTRUE(show_all) || nrow(dt) <= cap) return(dt)
  dt[order(dt$record_count, decreasing = TRUE), , drop = FALSE][seq_len(min(cap, nrow(dt))), , drop = FALSE]
}

valid_table_choices <- c(
  "events",
  "event_sources",
  "mechanism_classes",
  "stations",
  "sites",
  "networks",
  "paths",
  "records",
  "record_quality_flags",
  "intensity_measures",
  "response_spectra_common_periods",
  "release_files",
  "field_catalog",
  "build_manifest",
  "vw_records_overview",
  "vw_ground_motion_rotd50_d050"
)

table_sql <- function(table_name, limit = 1000) {
  stopifnot(table_name %in% valid_table_choices)
  limit <- max(1, min(as.integer(limit), 20000))
  sprintf("SELECT * FROM %s LIMIT %d", table_name, limit)
}

