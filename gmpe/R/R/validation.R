optional_sentinels <- c(-999, 999)

workbook_missing <- function(value, default = 999) {
  numeric <- suppressWarnings(as.numeric(value))
  if (length(numeric) == 0L || is.na(numeric) || numeric %in% optional_sentinels) {
    return(default)
  }
  numeric
}

is_missing_optional <- function(value) {
  is.null(value) || is.na(value) || as.numeric(value) %in% optional_sentinels
}

outside_range <- function(value, low, high) {
  !is.null(value) && !is.na(value) && (as.numeric(value) < low || as.numeric(value) > high)
}

applicability_warnings <- function(model, ...) {
  args <- list(...)
  name <- toupper(model)
  if (name %in% c("IDRISS", "IDRISS14")) {
    name <- "I14"
  }

  get_num <- function(key, default = NULL) {
    if (!key %in% names(args) || is.null(args[[key]])) {
      return(default)
    }
    suppressWarnings(as.numeric(args[[key]]))
  }

  warnings <- character()
  M <- get_num("M")
  Rrup <- get_num("Rrup")
  Rjb <- get_num("Rjb")
  Vs30 <- get_num("Vs30")

  if (!is.null(Rrup) && !is.null(Rjb) && !is.na(Rrup) && !is.na(Rjb) && Rrup < Rjb) {
    warnings <- c(warnings, "Rrup cannot be less than Rjb.")
  }

  if (name == "ASK14") {
    if (outside_range(M, 3.0, 8.5)) {
      warnings <- c(warnings, "ASK14 magnitude is outside the workbook applicability range 3.0 to 8.5.")
    }
    if (outside_range(Rrup, 0.0, 300.0)) {
      warnings <- c(warnings, "ASK14 Rrup is outside the workbook applicability range 0 to 300 km.")
    }
    if (!is.null(Vs30) && !is.na(Vs30) && Vs30 < 180) {
      warnings <- c(warnings, "ASK14 Vs30 is below the workbook applicability minimum of 180 m/s.")
    } else if (!is.null(Vs30) && !is.na(Vs30) && Vs30 > 1000) {
      warnings <- c(warnings, "ASK14 Vs30 is outside the recommended workbook range; the workbook note says to use 760 m/s.")
    }
  } else if (name == "BSSA14") {
    NS <- get_num("NS", 0)
    if (outside_range(M, 3.0, 8.5)) {
      warnings <- c(warnings, "BSSA14 magnitude is outside the workbook applicability range 3.0 to 8.5.")
    }
    if (!is.null(NS) && !is.na(NS) && NS == 1 && !is.null(M) && !is.na(M) && M > 7.0) {
      warnings <- c(warnings, "BSSA14 normal-fault magnitude is outside the workbook applicability maximum of 7.0.")
    }
    if (outside_range(Rjb, 0.0, 400.0)) {
      warnings <- c(warnings, "BSSA14 Rjb is outside the workbook applicability range 0 to 400 km.")
    }
    if (outside_range(Vs30, 150.0, 1500.0)) {
      warnings <- c(warnings, "BSSA14 Vs30 is outside the workbook applicability range 150 to 1500 m/s.")
    }
    Z1 <- get_num("Z1")
    if (!is_missing_optional(Z1) && outside_range(Z1, 0.0, 3.0)) {
      warnings <- c(warnings, "BSSA14 Z1 is outside the workbook applicability range 0 to 3 km.")
    }
  } else if (name == "CB14") {
    if (outside_range(M, 3.3, 8.5)) {
      warnings <- c(warnings, "CB14 magnitude is outside the workbook applicability range 3.3 to 8.5.")
    }
    if (outside_range(Rrup, 0.0, 300.0)) {
      warnings <- c(warnings, "CB14 Rrup is outside the workbook applicability range 0 to 300 km.")
    }
    if (outside_range(Vs30, 150.0, 1500.0)) {
      warnings <- c(warnings, "CB14 Vs30 is outside the workbook applicability range 150 to 1500 m/s.")
    }
    Fhw <- get_num("Fhw", 0)
    if (!is.null(Fhw) && !is.na(Fhw) && Fhw == 1 && !is.null(M) && !is.na(M) && M > 8.0) {
      warnings <- c(warnings, "CB14 hanging-wall term is outside the workbook applicability maximum magnitude of 8.0.")
    }
    dip <- get_num("dip")
    if (outside_range(dip, 15.0, 90.0)) {
      warnings <- c(warnings, "CB14 dip is outside the workbook applicability range 15 to 90 degrees.")
    }
    Ztor <- get_num("Ztor")
    if (!is_missing_optional(Ztor) && outside_range(Ztor, 0.0, 20.0)) {
      warnings <- c(warnings, "CB14 Ztor is outside the workbook applicability range 0 to 20 km.")
    }
    Z25 <- get_num("Z25")
    if (!is_missing_optional(Z25) && outside_range(Z25, 0.0, 20.0)) {
      warnings <- c(warnings, "CB14 Z25 is outside the workbook applicability range 0 to 20 km.")
    }
    Zhyp <- get_num("Zhyp")
    if (!is_missing_optional(Zhyp) && outside_range(Zhyp, 0.0, 10.0)) {
      warnings <- c(warnings, "CB14 Zhyp is outside the workbook applicability range 0 to 10 km.")
    }
  } else if (name == "CY14") {
    if (outside_range(M, 3.5, 8.5)) {
      warnings <- c(warnings, "CY14 magnitude is outside the workbook applicability range 3.5 to 8.5.")
    }
    fault_flags <- vapply(c("Frv", "Fnm", "Fhw"), function(key) identical(get_num(key, 0), 1), logical(1))
    if (any(fault_flags) && !is.null(M) && !is.na(M) && M > 8.0) {
      warnings <- c(warnings, "CY14 fault-specific terms are outside the workbook applicability maximum magnitude of 8.0.")
    }
    if (outside_range(Rrup, 0.0, 300.0)) {
      warnings <- c(warnings, "CY14 Rrup is outside the workbook applicability range 0 to 300 km.")
    }
    if (outside_range(Vs30, 180.0, 1500.0)) {
      warnings <- c(warnings, "CY14 Vs30 is outside the workbook applicability range 180 to 1500 m/s.")
    }
    Ztor <- get_num("Ztor")
    if (!is_missing_optional(Ztor) && !is.na(Ztor) && Ztor > 20.0) {
      warnings <- c(warnings, "CY14 Ztor is outside the workbook applicability maximum of 20 km.")
    }
    if (!is.null(Rrup) && !is_missing_optional(Ztor) && Rrup < Ztor) {
      warnings <- c(warnings, "CY14 Rrup cannot be less than Ztor.")
    }
  } else if (name == "I14") {
    if (!is.null(M) && !is.na(M) && M < 5.0) {
      warnings <- c(warnings, "I14 magnitude is below the workbook applicability minimum of 5.0.")
    }
    if (!is.null(Rrup) && !is.na(Rrup) && Rrup > 150.0) {
      warnings <- c(warnings, "I14 Rrup is above the workbook applicability maximum of 150 km.")
    }
    if (!is.null(Vs30) && !is.na(Vs30) && Vs30 < 450.0) {
      warnings <- c(warnings, "I14 Vs30 is below the workbook applicability minimum of 450 m/s.")
    }
  }

  warnings
}
