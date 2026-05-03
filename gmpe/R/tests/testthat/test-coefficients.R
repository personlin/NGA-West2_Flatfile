test_that("period_key uses stable keys", {
  expect_equal(period_key(0), "pga")
  expect_equal(period_key(-1), "pgv")
  expect_equal(period_key(0.01), "p0p010")
  expect_equal(period_key(1), "p1p000")
})

test_that("coefficient files load", {
  expected_schema <- c(
    "model",
    "period_s",
    "period_key",
    "imt",
    "row_index",
    "coefficient",
    "value",
    "cached_value",
    "formula",
    "source_sheet",
    "source_cell",
    "source_workbook"
  )
  for (model in c("ASK14", "BSSA14", "CB14", "CY14", "I14")) {
    data <- load_coefficients(model)
    expect_named(data, expected_schema)
    expect_equal(unique(data$model), model)
    expect_gt(length(available_periods(model)), 0)
  }
})

test_that("model scalar predictions run", {
  expect_gt(idriss14(M = 6.5, Rrup = 20, Vs30 = 760, F = 1, period = 1.0)$median, 0)
  expect_gt(bssa14(M = 6.5, Rjb = 20, Vs30 = 760, RS = 1, period = 1.0)$median, 0)
  expect_gt(cb14(M = 6.5, Rrup = 20, Rjb = 18, Rx = 5, Frv = 1, Fhw = 1, Ztor = 2, W = 15, dip = 30, Vs30 = 760, period = 1.0)$median, 0)
  expect_gt(ask14(M = 6.5, Rrup = 20, Rjb = 18, Rx = 5, Frv = 1, Fhw = 1, Ztor = 2, W = 15, dip = 30, Vs30 = 760, period = 1.0)$median, 0)
  expect_gt(cy14(M = 6.5, Rrup = 20, Rjb = 18, Rx = 5, Frv = 1, Fhw = 1, Ztor = 2, dip = 30, Vs30 = 760, period = 1.0)$median, 0)
})

test_that("batch predictions run", {
  df <- data.frame(
    earthquake_magnitude = 6.5,
    campbell_r_dist_km = 20,
    joyner_boore_dist_km = 18,
    rx = 5,
    vs30_m_s_selected_for_analysis = 760,
    depth_to_top_of_fault_rupture_model = 2,
    fault_rupture_width_km = 15,
    dip_deg = 30
  )
  out <- predict_dataframe(df, "ASK14", c(0.2, 1.0))
  expect_equal(out$period_s, c(0.2, 1.0))
  expect_equal(all(out$median > 0), TRUE)
  expect_named(out, c("row_index", "model", "period_s", "median", "ln_median", "sigma", "tau", "phi", "warnings"))
})

test_that("applicability warnings are exposed", {
  warnings <- applicability_warnings("I14", M = 4.5, Rrup = 175, Vs30 = 300)
  expect_length(warnings, 3)
  result <- idriss14(M = 4.5, Rrup = 175, Vs30 = 300, period = 1.0)
  expect_equal(result$warnings, warnings)
})

test_that("flatfile missing sentinel is normalized", {
  with_negative <- ask14(M = 6.5, Rrup = 20, Rjb = 18, Vs30 = 760, Ztor = -999, W = -999, Z1 = -999, period = 1.0)
  with_workbook <- ask14(M = 6.5, Rrup = 20, Rjb = 18, Vs30 = 760, Ztor = 999, W = 999, Z1 = 999, period = 1.0)
  expect_equal(with_negative$median, with_workbook$median, tolerance = 1e-12)
})
