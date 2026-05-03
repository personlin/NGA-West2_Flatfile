suppressPackageStartupMessages({
  library(data.table)
  library(readxl)
  library(digest)
})

project_root <- function() {
  normalizePath(file.path(dirname(sys.frame(1)$ofile %||% "."), ".."), mustWork = FALSE)
}

`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0) y else x
}

clean_names <- function(x) {
  x <- ifelse(is.na(x) | x == "", "unnamed", x)
  x <- iconv(x, to = "ASCII//TRANSLIT", sub = "")
  x <- gsub("%", " percent ", x, fixed = TRUE)
  x <- gsub("[\r\n]+", " ", x)
  x <- gsub("[^A-Za-z0-9]+", "_", x)
  x <- gsub("^_+|_+$", "", x)
  x <- tolower(x)
  x[x == ""] <- "unnamed"
  make.unique(x, sep = "_")
}

list_input_files <- function(root = ".") {
  paths <- sort(list.files(file.path(root, "data"), "[.]xlsx$", full.names = TRUE))
  out <- rbindlist(lapply(seq_along(paths), function(i) {
    path <- paths[[i]]
    name <- basename(path)
    component <- if (grepl("Vertical", name, ignore.case = TRUE)) "Vertical" else "RotD50"
    damping_code <- if (component == "Vertical") "050" else sub(".*_d([0-9]{3})_.*", "\\1", name)
    damping_percent <- as.numeric(damping_code) / 10
    sheets <- readxl::excel_sheets(path)
    data.table(
      release_file_id = i,
      path = normalizePath(path),
      file_name = name,
      component = component,
      damping_code = damping_code,
      damping_percent = damping_percent,
      sheet_name = sheets[[1]],
      file_size_bytes = file.info(path)$size,
      sha256 = digest::digest(file = path, algo = "sha256")
    )
  }))
  out[order(component, damping_percent)]
}

read_excel_clean <- function(path, sheet = NULL, col_types = NULL, n_max = Inf) {
  dt <- as.data.table(readxl::read_excel(
    path,
    sheet = sheet %||% readxl::excel_sheets(path)[[1]],
    col_types = col_types,
    n_max = n_max,
    .name_repair = "minimal",
    guess_max = 1000
  ))
  original_names <- names(dt)
  setnames(dt, clean_names(original_names))
  attr(dt, "original_names") <- original_names
  dt
}

read_header_catalog <- function(path, sheet = NULL) {
  raw <- readxl::read_excel(
    path,
    sheet = sheet %||% readxl::excel_sheets(path)[[1]],
    n_max = 0,
    .name_repair = "minimal"
  )
  original <- names(raw)
  data.table(
    column_position = seq_along(original),
    original_name = original,
    clean_name = clean_names(original),
    field_group = field_group(seq_along(original), original)
  )
}

field_group <- function(pos, original_name) {
  fifelse(pos <= 47, "source",
    fifelse(pos <= 73, "path",
      fifelse(pos <= 112, "site",
        fifelse(pos <= 131, "record_processing",
          fifelse(grepl("^T[0-9]", original_name) | original_name %in% c("PGA (g)", "PGV (cm/sec)", "PGD (cm)"),
            "ground_motion",
            fifelse(pos <= 258, "classification_directivity", "quality")
          )
        )
      )
    )
  )
}

col_or_na <- function(dt, name, type = c("numeric", "character", "integer")) {
  type <- match.arg(type)
  if (!name %in% names(dt)) {
    return(rep(if (type == "character") NA_character_ else NA_real_, nrow(dt)))
  }
  x <- dt[[name]]
  if (type == "character") return(as.character(x))
  if (type == "integer") return(as.integer(suppressWarnings(as.numeric(x))))
  suppressWarnings(as.numeric(x))
}

first_present <- function(dt, names, type = "numeric") {
  found <- names[names %in% names(dt)][1]
  if (is.na(found)) col_or_na(dt, "__missing__", type) else col_or_na(dt, found, type)
}

period_columns <- function(dt) {
  cols <- names(dt)[grepl("^t[0-9]+_[0-9]+s$", names(dt))]
  vals <- as.numeric(gsub("_", ".", sub("^t", "", sub("s$", "", cols))))
  cols[order(vals)]
}

period_values <- function(period_cols) {
  as.numeric(gsub("_", ".", sub("^t", "", sub("s$", "", period_cols))))
}

mechanism_classes <- function() {
  data.table(
    mechanism_code = c(0L, 1L, 2L, 3L, 4L, -999L),
    mechanism_class_original = c("strike-slip", "normal", "reverse", "reverse-oblique", "normal-oblique", "unknown"),
    mechanism_class_simple = c("strike-slip", "normal", "reverse", "oblique", "oblique", "unknown"),
    description = c(
      "Rake in strike-slip ranges from Appendix D.",
      "Rake between -120 and -60 degrees.",
      "Rake between 60 and 120 degrees.",
      "Rake between 30-60 or 120-150 degrees.",
      "Rake between -150--120 or -60--30 degrees.",
      "Missing, blank, or official unknown code."
    )
  )
}

classify_mechanism <- function(x, simple = TRUE) {
  code <- suppressWarnings(as.integer(as.numeric(x)))
  map <- mechanism_classes()
  idx <- match(code, map$mechanism_code)
  out <- if (simple) map$mechanism_class_simple[idx] else map$mechanism_class_original[idx]
  out[is.na(out)] <- "unknown"
  out
}

parse_event_datetime <- function(year, mody, hrmn) {
  y <- suppressWarnings(as.integer(year))
  md <- sprintf("%04d", suppressWarnings(as.integer(mody)))
  hm <- sprintf("%04d", suppressWarnings(as.integer(hrmn)))
  out <- rep(NA_character_, length(y))
  ok <- !is.na(y) & !is.na(mody) & !is.na(hrmn) & nchar(md) == 4 & nchar(hm) == 4
  if (any(ok)) {
    dates <- sprintf(
      "%04d-%02d-%02d %02d:%02d:00",
      y[ok],
      as.integer(substr(md[ok], 1, 2)),
      as.integer(substr(md[ok], 3, 4)),
      as.integer(substr(hm[ok], 1, 2)),
      as.integer(substr(hm[ok], 3, 4))
    )
    parsed <- as.POSIXct(dates, tz = "UTC", format = "%Y-%m-%d %H:%M:%S")
    out[ok] <- format(parsed, "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
  }
  out
}

derive_event_region <- function(event_name) {
  x <- tolower(event_name %||% "")
  out <- rep("unknown", length(x))
  rules <- list(
    "United States" = "california|imperial|landers|northridge|loma|hector|parkfield|morgan|coalinga|whittier|chino|san fernando|alaska|kobe_ceor",
    "Japan" = "japan|kobe|niigata|tohoku|iwate|miyagi|kumamoto|chuetsu",
    "Taiwan" = "taiwan|chi-chi|hualien|nantou|kaohsiung",
    "Turkey" = "turkey|kocaeli|duzce|erzincan|van",
    "Italy" = "italy|l'aquila|umbria|irpinia|friuli",
    "China" = "china|wenchuan|tangshan|lushan",
    "Mexico" = "mexico|el mayor|mexicali|colima",
    "New Zealand" = "new zealand|christchurch|darfield",
    "Chile" = "chile|maule|valparaiso",
    "Greece" = "greece|athens|kalamata",
    "Iran" = "iran|tabas|bam|manjil",
    "India" = "india|bhuj"
  )
  for (nm in names(rules)) {
    out[grepl(rules[[nm]], x)] <- nm
  }
  out
}

derive_station_region <- function(lat, lon) {
  out <- rep("unknown", length(lat))
  ok <- !is.na(lat) & !is.na(lon)
  in_taiwan <- ok & lat >= 21 & lat <= 26 & lon >= 119 & lon <= 123
  out[ok & lat >= 24 & lat <= 50 & lon >= -125 & lon <= -66] <- "United States"
  out[ok & lat >= 30 & lat <= 46 & lon >= 128 & lon <= 146] <- "Japan"
  out[in_taiwan] <- "Taiwan"
  out[ok & lat >= 35 & lat <= 43 & lon >= 25 & lon <= 45] <- "Turkey"
  out[ok & lat >= 36 & lat <= 47 & lon >= 6 & lon <= 19] <- "Italy"
  out[ok & lat >= 18 & lat <= 33 & lon >= -118 & lon <= -86] <- "Mexico"
  out[ok & lat >= -47 & lat <= -34 & lon >= 166 & lon <= 179] <- "New Zealand"
  out[ok & lat >= -56 & lat <= -17 & lon >= -76 & lon <= -66] <- "Chile"
  out[ok & lat >= 34 & lat <= 42 & lon >= 19 & lon <= 30] <- "Greece"
  out[ok & lat >= 25 & lat <= 40 & lon >= 44 & lon <= 64] <- "Iran"
  out[ok & !in_taiwan & lat >= 18 & lat <= 54 & lon >= 73 & lon <= 135] <- "China"
  out
}

make_release_files <- function(files) {
  files[, .(
    release_file_id,
    file_name,
    component,
    damping_code,
    damping_percent,
    sheet_name,
    row_count = NA_integer_,
    column_count = NA_integer_,
    file_size_bytes,
    sha256
  )]
}

add_excel_counts <- function(files) {
  files[, `:=`(row_count = NA_integer_, column_count = NA_integer_)]
  for (i in seq_len(nrow(files))) {
    hdr <- read_header_catalog(files$path[i], files$sheet_name[i])
    one_col <- readxl::read_excel(
      files$path[i],
      sheet = files$sheet_name[i],
      range = readxl::cell_cols(1),
      col_names = TRUE,
      .name_repair = "minimal"
    )
    files$row_count[i] <- nrow(one_col)
    files$column_count[i] <- nrow(hdr)
  }
  files[]
}

build_core_tables <- function(base_dt, files, field_catalog) {
  event_rows <- base_dt[!duplicated(col_or_na(base_dt, "eqid", "integer"))]
  events <- data.table(
    eqid = col_or_na(event_rows, "eqid", "integer"),
    earthquake_name = col_or_na(event_rows, "earthquake_name", "character"),
    event_region_derived = derive_event_region(col_or_na(event_rows, "earthquake_name", "character")),
    year = col_or_na(event_rows, "year", "integer"),
    mody = col_or_na(event_rows, "mody", "integer"),
    hrmn = col_or_na(event_rows, "hrmn", "integer"),
    event_datetime_utc = parse_event_datetime(
      col_or_na(event_rows, "year", "integer"),
      col_or_na(event_rows, "mody", "integer"),
      col_or_na(event_rows, "hrmn", "integer")
    ),
    earthquake_magnitude = col_or_na(event_rows, "earthquake_magnitude"),
    magnitude_type = col_or_na(event_rows, "magnitude_type", "character"),
    magnitude_uncertainty_kagan = col_or_na(event_rows, "magnitude_uncertainty_kagan_model"),
    magnitude_uncertainty_statistical = col_or_na(event_rows, "magnitude_uncertainty_statistical"),
    magnitude_sample_size = col_or_na(event_rows, "magnitude_sample_size", "integer"),
    magnitude_uncertainty_study_class = col_or_na(event_rows, "magnitude_uncertainty_study_class"),
    hypocenter_latitude = col_or_na(event_rows, "hypocenter_latitude_deg"),
    hypocenter_longitude = col_or_na(event_rows, "hypocenter_longitude_deg"),
    hypocenter_depth_km = col_or_na(event_rows, "hypocenter_depth_km"),
    mechanism_code = col_or_na(event_rows, "mechanism_based_on_rake_angle", "integer"),
    mechanism_class_original = classify_mechanism(col_or_na(event_rows, "mechanism_based_on_rake_angle"), simple = FALSE),
    mechanism_class_simple = classify_mechanism(col_or_na(event_rows, "mechanism_based_on_rake_angle"), simple = TRUE)
  )

  event_sources <- data.table(
    eqid = col_or_na(event_rows, "eqid", "integer"),
    seismic_moment_dyne_cm = col_or_na(event_rows, "mo_dyne_cm"),
    strike_deg = col_or_na(event_rows, "strike_deg"),
    dip_deg = col_or_na(event_rows, "dip_deg"),
    rake_angle_deg = col_or_na(event_rows, "rake_angle_deg"),
    finite_rupture_model = col_or_na(event_rows, "finite_rupture_model_1_yes_0_no", "integer"),
    ztor_km = col_or_na(event_rows, "depth_to_top_of_fault_rupture_model"),
    rupture_length_km = col_or_na(event_rows, "fault_rupture_length_for_calculation_of_ry_km"),
    rupture_width_km = col_or_na(event_rows, "fault_rupture_width_km"),
    rupture_area_km2 = col_or_na(event_rows, "fault_rupture_area_km_2"),
    avg_fault_displacement_cm = col_or_na(event_rows, "avg_fault_disp_cm"),
    rise_time_s = col_or_na(event_rows, "rise_time_s"),
    avg_slip_velocity_cm_s = col_or_na(event_rows, "avg_slip_velocity_cm_s"),
    static_stress_drop_bars = col_or_na(event_rows, "static_stress_drop_bars"),
    preferred_rupture_velocity_km_s = col_or_na(event_rows, "preferred_rupture_velocity_km_s"),
    avg_vr_vs = col_or_na(event_rows, "average_vr_vs"),
    shallow_moment_release_percent = col_or_na(event_rows, "percent_of_moment_release_in_the_top_5_km_of_crust"),
    shallow_asperity_exists = col_or_na(event_rows, "existence_of_shallow_asperity_0_no_1_yes", "integer"),
    shallow_asperity_top_km = col_or_na(event_rows, "depth_to_top_of_shallowest_asperity_km"),
    extensional_regime = col_or_na(event_rows, "earthquake_in_extensional_regime_1_yes_0_no", "integer"),
    fault_name = col_or_na(event_rows, "fault_name", "character"),
    slip_rate_mm_yr = col_or_na(event_rows, "slip_rate_mm_yr")
  )

  station_rows <- base_dt[!duplicated(col_or_na(base_dt, "station_sequence_number", "integer"))]
  station_region <- derive_station_region(
    col_or_na(station_rows, "station_latitude"),
    col_or_na(station_rows, "station_longitude")
  )
  stations_raw <- data.table(
    station_sequence_number = col_or_na(station_rows, "station_sequence_number", "integer"),
    station_name = col_or_na(station_rows, "station_name", "character"),
    station_id_no = col_or_na(station_rows, "station_id_no", "character"),
    owner = col_or_na(station_rows, "owner", "character"),
    network_name = col_or_na(station_rows, "owner", "character"),
    station_region_derived = station_region,
    station_latitude = col_or_na(station_rows, "station_latitude"),
    station_longitude = col_or_na(station_rows, "station_longitude"),
    stories = col_or_na(station_rows, "stories"),
    instrument_location = col_or_na(station_rows, "instloc", "character"),
    nga_type = col_or_na(station_rows, "nga_type", "character"),
    type_of_recording = col_or_na(station_rows, "type_of_recording", "character"),
    instrument_model = col_or_na(station_rows, "instrument_model", "character")
  )
  networks <- unique(stations_raw[, .(network_name)])
  networks[is.na(network_name) | network_name == "" | network_name == "-999", network_name := "unknown"]
  networks <- unique(networks)
  networks[, network_id := .I]
  setcolorder(networks, c("network_id", "network_name"))
  stations <- merge(stations_raw, networks, by = "network_name", all.x = TRUE)
  setcolorder(stations, c("station_sequence_number", "station_name", "station_id_no", "network_id"))

  sites <- data.table(
    site_id = seq_len(nrow(station_rows)),
    station_sequence_number = col_or_na(station_rows, "station_sequence_number", "integer"),
    gmx_c1 = col_or_na(station_rows, "gmx_s_c1", "character"),
    gmx_c2 = col_or_na(station_rows, "gmx_s_c2", "character"),
    gmx_c3 = col_or_na(station_rows, "gmx_s_c3", "character"),
    campbell_geocode = col_or_na(station_rows, "campbell_s_geocode", "character"),
    bray_rodriguez_marek_sgs = col_or_na(station_rows, "bray_and_rodriguez_marek_sgs", "character"),
    depth = col_or_na(station_rows, "depth"),
    preferred_nehrp = col_or_na(station_rows, "preferred_nehrp_based_on_vs30", "character"),
    vs30_m_s = col_or_na(station_rows, "vs30_m_s_selected_for_analysis"),
    measured_inferred_class = col_or_na(station_rows, "measured_inferred_class", "character"),
    sigma_ln_vs30 = col_or_na(station_rows, "sigma_of_vs30_in_natural_log_units"),
    cgs_nehrp = col_or_na(station_rows, "nehrp_classification_from_cgs_s_site_condition_map", "character"),
    geological_unit = col_or_na(station_rows, "geological_unit", "character"),
    geology = col_or_na(station_rows, "geology", "character"),
    basin = col_or_na(station_rows, "basin", "character"),
    depth_to_basement_rock = col_or_na(station_rows, "depth_to_basement_rock"),
    site_visited = col_or_na(station_rows, "site_visited", "character"),
    age = col_or_na(station_rows, "age", "character"),
    grain_size = col_or_na(station_rows, "grain_size", "character"),
    depositional_history = col_or_na(station_rows, "depositional_history", "character"),
    z1_h11_m = col_or_na(station_rows, "northern_ca_southern_ca_h11_z1_m"),
    z1p5_h11_m = col_or_na(station_rows, "northern_ca_southern_ca_h11_z1_5_m"),
    z2p5_h11_m = col_or_na(station_rows, "northern_ca_southern_ca_h11_z2_5_m")
  )

  records <- data.table(
    rsn = col_or_na(base_dt, "record_sequence_number", "integer"),
    eqid = col_or_na(base_dt, "eqid", "integer"),
    station_sequence_number = col_or_na(base_dt, "station_sequence_number", "integer"),
    file_name_horizontal_1 = col_or_na(base_dt, "file_name_horizontal_1", "character"),
    file_name_horizontal_2 = col_or_na(base_dt, "file_name_horizontal_2", "character"),
    file_name_vertical = col_or_na(base_dt, "file_name_vertical", "character"),
    h1_azimuth_deg = first_present(base_dt, c("h1_azimth_degrees", "h1_azimuth_degrees")),
    h2_azimuth_deg = first_present(base_dt, c("h2_azimith_degrees", "h2_azimuth_degrees")),
    type_of_recording = col_or_na(base_dt, "type_of_recording", "character"),
    pea_processing_flag = col_or_na(base_dt, "pea_processing_flag", "character"),
    type_of_filter = col_or_na(base_dt, "type_of_filter", "character"),
    npass = col_or_na(base_dt, "npass"),
    nroll = col_or_na(base_dt, "nroll"),
    hp_h1_hz = col_or_na(base_dt, "hp_h1_hz"),
    hp_h2_hz = col_or_na(base_dt, "hp_h2_hz"),
    lp_h1_hz = col_or_na(base_dt, "lp_h1_hz"),
    lp_h2_hz = col_or_na(base_dt, "lp_h2_hz"),
    factor = col_or_na(base_dt, "factor"),
    lowest_usable_freq_h1_hz = col_or_na(base_dt, "lowest_usable_freq_h1_hz"),
    lowest_usable_freq_h2_hz = first_present(base_dt, c("lowest_usable_freq_h2_h2", "lowest_usable_freq_h2_hz")),
    lowest_usable_freq_ave_component_hz = col_or_na(base_dt, "lowest_usable_freq_ave_component_hz"),
    instrument_nat_freq = col_or_na(base_dt, "instrument_nat_freq"),
    instrument_damping = col_or_na(base_dt, "instrument_damping"),
    instrument_type = col_or_na(base_dt, "instrument_type", "character")
  )

  paths <- data.table(
    path_id = seq_len(nrow(base_dt)),
    rsn = col_or_na(base_dt, "record_sequence_number", "integer"),
    epi_distance_km = col_or_na(base_dt, "epid_km"),
    hypocentral_distance_km = col_or_na(base_dt, "hypd_km"),
    rjb_km = col_or_na(base_dt, "joyner_boore_dist_km"),
    rrup_km = col_or_na(base_dt, "campbell_r_dist_km"),
    rmsd_km = col_or_na(base_dt, "rmsd_km"),
    closest_distance_km = col_or_na(base_dt, "clstd_km"),
    rx_km = col_or_na(base_dt, "rx"),
    fw_hw_indicator = col_or_na(base_dt, "fw_hw_indicator", "character"),
    source_to_site_azimuth_deg = col_or_na(base_dt, "source_to_site_azimuth_deg"),
    x = col_or_na(base_dt, "x"),
    theta_d_deg = col_or_na(base_dt, "theta_d_deg"),
    y = col_or_na(base_dt, "y"),
    phi_d_deg = col_or_na(base_dt, "phi_d_deg"),
    s = col_or_na(base_dt, "s"),
    d = col_or_na(base_dt, "d"),
    ctildepr = col_or_na(base_dt, "ctildepr"),
    directivity_d = first_present(base_dt, c("d_1", "d")),
    rfn_hyp = col_or_na(base_dt, "rfn_hyp"),
    rfp_hyp = col_or_na(base_dt, "rfp_hyp"),
    t = col_or_na(base_dt, "t"),
    ave_strike_deg = col_or_na(base_dt, "ave_strike_deg"),
    u = col_or_na(base_dt, "u"),
    idpv4 = col_or_na(base_dt, "idpv4"),
    xci = col_or_na(base_dt, "xci"),
    xci1 = col_or_na(base_dt, "xci1"),
    idirectivity = col_or_na(base_dt, "idirectivity"),
    tp = col_or_na(base_dt, "tp"),
    ry2 = col_or_na(base_dt, "ry_2")
  )

  record_quality_flags <- data.table(
    rsn = col_or_na(base_dt, "record_sequence_number", "integer"),
    quality_flag = col_or_na(base_dt, "quality_flag", "character"),
    spectra_quality_flag = col_or_na(base_dt, "spectra_quality_flag", "character"),
    late_s_trigger = col_or_na(base_dt, "late_s_trigger", "character"),
    late_p_trigger = col_or_na(base_dt, "late_p_trigger", "character")
  )

  class2_distances <- rbindlist(lapply(c(0, 2, 5, 10, 20, 40), function(d) {
    type_col <- switch(as.character(d),
      "0" = "type_crjb_0",
      "2" = "type_crjb_2",
      "5" = "type_crjb_5",
      "10" = "type_crjb_10",
      "20" = "type_crjb_20",
      "40" = "type_crjb_40"
    )
    crjb_cols <- names(base_dt)[grepl("^crjb", names(base_dt))]
    idx <- match(d, c(0, 2, 5, 10, 20, 40))
    crjb_col <- crjb_cols[idx]
    data.table(
      rsn = col_or_na(base_dt, "record_sequence_number", "integer"),
      crjb_reference_km = d,
      class_type = col_or_na(base_dt, type_col, "character"),
      crjb_km = if (!is.na(crjb_col)) col_or_na(base_dt, crjb_col) else rep(NA_real_, nrow(base_dt))
    )
  }))
  class2_distances[, class2_distance_id := .I]
  setcolorder(class2_distances, "class2_distance_id")

  list(
    release_files = make_release_files(files),
    field_catalog = field_catalog,
    damping_levels = unique(files[, .(damping_percent, damping_code)])[order(damping_percent)],
    spectral_periods = data.table(
      period_id = seq_along(period_values(period_columns(base_dt))),
      period_s = period_values(period_columns(base_dt))
    ),
    mechanism_classes = mechanism_classes(),
    events = events[!is.na(eqid)],
    event_sources = event_sources[!is.na(eqid)],
    networks = networks,
    stations = stations[!is.na(station_sequence_number)],
    sites = sites[!is.na(station_sequence_number)],
    records = records[!is.na(rsn)],
    paths = paths[!is.na(rsn)],
    record_quality_flags = record_quality_flags[!is.na(rsn)],
    class2_distances = class2_distances[!is.na(rsn)]
  )
}
