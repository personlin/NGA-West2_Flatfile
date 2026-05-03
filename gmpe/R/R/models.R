region_codes <- c(
  global = 0,
  california = 0,
  ca = 0,
  taiwan = 0,
  tw = 0,
  new_zealand = 0,
  nz = 0,
  japan = 1,
  jp = 1,
  china = 3,
  ch = 3,
  italy = 4,
  it = 4,
  turkey = 5,
  tur = 5
)

region_code <- function(region = "global") {
  if (is.null(region)) {
    return(0)
  }
  if (is.numeric(region)) {
    return(as.integer(region))
  }
  key <- gsub("-", "_", gsub(" ", "_", tolower(trimws(region))), fixed = TRUE)
  if (!key %in% names(region_codes)) {
    stop(sprintf("Unknown GMPE region: %s", region), call. = FALSE)
  }
  unname(region_codes[[key]])
}

period_value <- function(period = NULL, T = NULL) {
  value <- if (!is.null(period)) period else T
  if (is.null(value)) {
    stop("period or T must be provided.", call. = FALSE)
  }
  as.numeric(value)
}

prediction_result <- function(model, period, median, sigma, tau = NULL, phi = NULL, warnings = character()) {
  if (is.null(tau)) {
    tau <- NA_real_
  }
  if (is.null(phi)) {
    phi <- NA_real_
  }
  list(
    model = model,
    period_s = period,
    median = median,
    ln_median = log(median),
    sigma = sigma,
    tau = tau,
    phi = phi,
    warnings = warnings
  )
}

ask14 <- function(
  M,
  Rrup,
  Rjb,
  Rx = 0,
  Frv = 0,
  Fnm = 0,
  Fhw = 0,
  FAS = 0,
  Ztor = 999,
  W = 999,
  dip = 90,
  Vs30 = 760,
  Vs30flag = 0,
  Z1 = 999,
  Ry0 = 999,
  region = "global",
  period = NULL,
  T = NULL,
  ...
) {
  t <- period_value(period, T)
  code <- region_code(region)
  Ztor <- workbook_missing(Ztor)
  W <- workbook_missing(W)
  Z1 <- workbook_missing(Z1)
  Ry0 <- workbook_missing(Ry0)
  warnings <- applicability_warnings(
    "ASK14",
    M = M, Rrup = Rrup, Rjb = Rjb, Vs30 = Vs30,
    Ztor = Ztor, W = W, Z1 = Z1, Ry0 = Ry0
  )
  median <- ask_14_raw(
    as.numeric(M), as.numeric(Rrup), as.numeric(Rjb), as.numeric(Rx),
    as.numeric(Frv), as.numeric(Fnm), as.numeric(Fhw), as.numeric(FAS),
    as.numeric(Ztor), as.numeric(W), as.numeric(dip), as.numeric(Vs30),
    as.numeric(Vs30flag), as.numeric(Z1), as.numeric(Ry0), code, t
  )
  sigma <- ask14_stdev_raw(
    as.numeric(M), as.numeric(Rrup), as.numeric(Rjb), as.numeric(Rx),
    as.numeric(Frv), as.numeric(Fnm), as.numeric(Fhw), as.numeric(FAS),
    as.numeric(Ztor), as.numeric(W), as.numeric(dip), as.numeric(Vs30),
    as.numeric(Vs30flag), as.numeric(Z1), as.numeric(Ry0), code, t
  )
  prediction_result("ASK14", t, median, sigma, warnings = warnings)
}

bssa14 <- function(
  M,
  Rjb,
  Vs30,
  U = 0,
  RS = 0,
  NS = 0,
  Z1 = 999,
  region = "global",
  period = NULL,
  T = NULL,
  ...
) {
  t <- period_value(period, T)
  code <- region_code(region)
  Z1 <- workbook_missing(Z1)
  warnings <- applicability_warnings("BSSA14", M = M, Rjb = Rjb, Vs30 = Vs30, U = U, RS = RS, NS = NS, Z1 = Z1)
  pgar <- pgar_calc(as.numeric(M), as.numeric(Rjb), as.numeric(U), as.numeric(RS), as.numeric(NS), code, 0)
  median <- bssa_14_raw(
    as.numeric(M), as.numeric(Rjb), as.numeric(U), as.numeric(RS),
    as.numeric(NS), as.numeric(Vs30), code, as.numeric(Z1), pgar, t
  )
  sigma <- bssa14_stdev_raw(as.numeric(M), as.numeric(Rjb), as.numeric(Vs30), t)
  prediction_result("BSSA14", t, median, sigma, warnings = warnings)
}

cb_coeffs <- function(period) {
  lookup <- if (as.numeric(period) == 0) 0.001 else as.numeric(period)
  rows <- load_coefficients("CB14")
  rows <- rows[abs(as.numeric(rows$period_s) - lookup) < 1e-9, ]
  labels <- sub("^([A-Z]+).*$", "\\1", rows$source_cell)
  rows$source_col <- vapply(labels, .excel_col_number, numeric(1))
  rows <- rows[order(rows$source_col), ]
  values <- rows$value
  missing <- is.na(values)
  values[missing] <- rows$cached_value[missing]
  out <- as.numeric(values)
  names(out) <- rows$coefficient
  out
}

mag_interp <- function(M, low, high) {
  if (M < 4.5) {
    return(low)
  }
  if (M > 5.5) {
    return(high)
  }
  high + (low - high) * (5.5 - M) * (5.5 - 4.5)
}

cb_sigma <- function(M, Vs30, a1100, period) {
  c <- cb_coeffs(period)
  pga <- cb_coeffs(0)
  q <- 0
  if (Vs30 < c[["k1"]]) {
    q <- c[["k2"]] * a1100 * (
      (a1100 + c[["c"]] * (Vs30 / c[["k1"]])^c[["n"]])^-1 -
        (a1100 + c[["c"]])^-1
    )
  }
  phi_base <- mag_interp(M, c[["f1"]], c[["f2"]])
  tau_base <- mag_interp(M, c[["t1"]], c[["t2"]])
  phi_pga <- mag_interp(M, pga[["f1"]], pga[["f2"]])
  tau_pga <- mag_interp(M, pga[["t1"]], pga[["t2"]])
  phi <- sqrt(
    (phi_base^2 - c[["flnAF"]]^2) +
      c[["flnAF"]]^2 +
      q^2 * (phi_pga^2 - pga[["flnAF"]]^2) +
      2 * q * c[["rlnPGA,lnY"]] *
        sqrt(max(phi_base^2 - c[["flnAF"]]^2, 0)) *
        sqrt(max(phi_pga^2 - pga[["flnAF"]]^2, 0))
  )
  tau <- sqrt(tau_base^2 + q^2 * tau_pga^2 + 2 * q * c[["rlnPGA,lnY"]] * tau_base * tau_pga)
  sigma <- sqrt(c[["fC"]]^2 + phi^2 + tau^2)
  list(sigma = sigma, tau = tau, phi = phi)
}

cb14 <- function(
  M,
  Rrup,
  Rjb,
  Rx = 0,
  Frv = 0,
  Fnm = 0,
  Fhw = 0,
  Ztor = 999,
  W = 999,
  dip = 90,
  Vs30 = 760,
  Z25 = 999,
  Zhyp = 999,
  Ztord = 999,
  Wd = 999,
  Zhypd = 999,
  A = 0,
  region = "global",
  period = NULL,
  T = NULL,
  ...
) {
  t <- period_value(period, T)
  code <- region_code(region)
  Ztor <- workbook_missing(Ztor)
  W <- workbook_missing(W)
  Z25 <- workbook_missing(Z25)
  Zhyp <- workbook_missing(Zhyp)
  Ztord <- workbook_missing(Ztord)
  Wd <- workbook_missing(Wd)
  Zhypd <- workbook_missing(Zhypd)
  warnings <- applicability_warnings(
    "CB14",
    M = M, Rrup = Rrup, Rjb = Rjb, Vs30 = Vs30,
    Fhw = Fhw, dip = dip, Ztor = Ztor, Z25 = Z25, Zhyp = Zhyp
  )
  a1100 <- a1100_cb(
    as.numeric(M), as.numeric(Rrup), as.numeric(Rjb), as.numeric(Rx),
    as.numeric(Frv), as.numeric(Fnm), as.numeric(Fhw), as.numeric(W),
    as.numeric(dip), as.numeric(Ztor), as.numeric(Z25), as.numeric(Zhyp),
    as.numeric(Ztord), as.numeric(Wd), as.numeric(Zhypd), code, 0
  )
  median <- cb_14_raw(
    as.numeric(M), as.numeric(Rrup), as.numeric(Rjb), as.numeric(Rx),
    as.numeric(Frv), as.numeric(Fnm), as.numeric(Fhw), as.numeric(Ztor),
    as.numeric(W), as.numeric(dip), as.numeric(Vs30), as.numeric(Z25),
    as.numeric(Zhyp), as.numeric(Ztord), as.numeric(Wd), as.numeric(Zhypd),
    code, as.numeric(A), t
  )
  parts <- cb_sigma(as.numeric(M), as.numeric(Vs30), a1100, t)
  prediction_result("CB14", t, median, parts$sigma, tau = parts$tau, phi = parts$phi, warnings = warnings)
}

cy14 <- function(
  M,
  Rrup,
  Rjb,
  Vs30,
  Rx = 0,
  Frv = 0,
  Fnm = 0,
  Fhw = 0,
  dip = 90,
  Ztor = 999,
  Z1 = 999,
  Z1r = 999,
  DDPP = 0,
  Vs30flag = 0,
  region = "global",
  period = NULL,
  T = NULL,
  ...
) {
  t <- period_value(period, T)
  code <- region_code(region)
  Ztor <- workbook_missing(Ztor)
  Z1 <- workbook_missing(Z1)
  Z1r <- workbook_missing(Z1r)
  warnings <- applicability_warnings(
    "CY14",
    M = M, Rrup = Rrup, Rjb = Rjb, Vs30 = Vs30,
    Frv = Frv, Fnm = Fnm, Fhw = Fhw, Ztor = Ztor
  )
  median <- cy_14_raw(
    as.numeric(M), as.numeric(Rrup), as.numeric(Rjb), as.numeric(Rx),
    as.numeric(Vs30), as.numeric(Frv), as.numeric(Fnm), as.numeric(Fhw),
    as.numeric(dip), as.numeric(Ztor), code, as.numeric(Z1), as.numeric(Z1r),
    as.numeric(DDPP), t
  )
  sigma <- cy14_stdev_raw(
    as.numeric(M), as.numeric(Rrup), as.numeric(Rjb), as.numeric(Rx),
    as.numeric(Vs30), as.numeric(Frv), as.numeric(Fnm), as.numeric(Fhw),
    as.numeric(dip), as.numeric(Ztor), code, as.numeric(Z1), as.numeric(DDPP),
    as.numeric(Vs30flag), t
  )
  prediction_result("CY14", t, median, sigma, warnings = warnings)
}

idriss14 <- function(
  M,
  Rrup,
  Vs30,
  F = 0,
  period = NULL,
  T = NULL,
  ...
) {
  t <- period_value(period, T)
  warnings <- applicability_warnings("I14", M = M, Rrup = Rrup, Vs30 = Vs30)
  median <- i_14_raw(as.numeric(M), as.numeric(Rrup), as.numeric(F), as.numeric(Vs30), t)
  sigma <- i_14_stdev_raw(as.numeric(M), t)
  prediction_result("I14", t, median, sigma, warnings = warnings)
}
