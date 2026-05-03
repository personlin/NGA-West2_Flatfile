test_that("R native outputs match golden fixtures", {
  gmpe_dir <- normalizePath(file.path(coefficients_dir(), ".."), mustWork = TRUE)
  cases <- data.table::fread(file.path(gmpe_dir, "validation", "golden_cases.csv"))
  golden <- data.table::fread(file.path(gmpe_dir, "validation", "golden_outputs.csv"))
  fns <- list(
    ASK14 = ask14,
    BSSA14 = bssa14,
    CB14 = cb14,
    CY14 = cy14,
    I14 = idriss14
  )

  for (i in seq_len(nrow(golden))) {
    expected <- golden[i]
    case <- cases[case_id == expected$case_id]
    args <- as.list(case[, setdiff(names(case), c("case_id", "description", "model", "period_s")), with = FALSE])
    args <- args[!vapply(args, function(x) length(x) == 0L || is.na(x), logical(1))]
    args$period <- as.numeric(case$period_s)

    result <- do.call(fns[[case$model]], args)
    expect_equal(result$ln_median, expected$ln_median, tolerance = 1e-6)
    expect_equal(result$median, expected$median, tolerance = 1e-5)
    expect_equal(result$sigma, expected$sigma, tolerance = 1e-6)
    if (!is.na(expected$tau)) {
      expect_equal(result$tau, expected$tau, tolerance = 1e-6)
    }
    if (!is.na(expected$phi)) {
      expect_equal(result$phi, expected$phi, tolerance = 1e-6)
    }
  }
})
