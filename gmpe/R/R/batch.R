predict_dataframe <- function(df, model, periods, column_map = NULL) {
  model_functions <- list(
    ASK14 = ask14,
    BSSA14 = bssa14,
    CB14 = cb14,
    CY14 = cy14,
    I14 = idriss14,
    IDRISS14 = idriss14
  )
  model_name <- toupper(model)
  if (!model_name %in% names(model_functions)) {
    stop(sprintf("Unknown GMPE model: %s", model), call. = FALSE)
  }
  fn <- model_functions[[model_name]]

  map <- c(
    earthquake_magnitude = "M",
    campbell_r_dist_km = "Rrup",
    joyner_boore_dist_km = "Rjb",
    rx = "Rx",
    vs30_m_s_selected_for_analysis = "Vs30",
    depth_to_top_of_fault_rupture_model = "Ztor",
    fault_rupture_width_km = "W",
    dip_deg = "dip",
    hypocenter_depth_km = "Zhyp"
  )
  if (!is.null(column_map)) {
    map[names(column_map)] <- column_map
  }

  out <- list()
  k <- 1L
  for (i in seq_len(nrow(df))) {
    args <- list()
    for (source in names(map)) {
      if (source %in% names(df)) {
        args[[map[[source]]]] <- df[[source]][i]
      }
    }
    for (period in periods) {
      args$period <- period
      result <- do.call(fn, args)
      out[[k]] <- data.table::data.table(
        row_index = i,
        model = result$model,
        period_s = result$period_s,
        median = result$median,
        ln_median = result$ln_median,
        sigma = result$sigma,
        tau = result$tau,
        phi = result$phi,
        warnings = paste(result$warnings, collapse = "; ")
      )
      k <- k + 1L
    }
  }
  data.table::rbindlist(out, fill = TRUE)
}
