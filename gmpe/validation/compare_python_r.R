#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
})

`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0) y else x
}

script_path <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", script_path[grepl("^--file=", script_path)])
script_dir <- dirname(normalizePath(script_path %||% "gmpe/validation/compare_python_r.R"))
repo_root <- normalizePath(file.path(script_dir, "..", ".."))
cases_path <- file.path(repo_root, "gmpe", "validation", "golden_cases.csv")
python_src <- file.path(repo_root, "gmpe", "python", "src")
python <- Sys.getenv(
  "NGAW2GMPE_PYTHON",
  "/Users/person/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
)

pkgload::load_all(file.path(repo_root, "gmpe", "R"), quiet = TRUE)

models <- c("ASK14", "BSSA14", "CB14", "CY14", "I14")
cases <- fread(cases_path)
missing_models <- setdiff(unique(cases$model), models)
if (length(missing_models) > 0) {
  stop("Unknown models in golden cases: ", paste(missing_models, collapse = ", "))
}

case_args <- function(row) {
  args <- as.list(row[, setdiff(names(row), c("case_id", "description", "model", "period_s")), with = FALSE])
  args <- args[!vapply(args, function(x) is.na(x) || identical(x, ""), logical(1))]
  args$period <- as.numeric(row$period_s)
  args
}

predict_python <- function(row) {
  request <- toJSON(list(kind = "scalar", model = row$model, args = case_args(row)), auto_unbox = TRUE)
  output <- system2(
    python,
    c("-m", "ngaw2gmpe.cli"),
    input = request,
    stdout = TRUE,
    stderr = TRUE,
    env = paste0("PYTHONPATH=", python_src)
  )
  status <- attr(output, "status")
  if (!is.null(status) && status != 0) {
    stop(paste(output, collapse = "\n"))
  }
  result <- fromJSON(paste(output, collapse = "\n"))
  data.table(
    model = result$model,
    period_s = result$period_s,
    median = result$median,
    ln_median = result$ln_median,
    sigma = result$sigma,
    tau = result$tau %||% NA_real_,
    phi = result$phi %||% NA_real_,
    warnings = paste(result$warnings %||% character(), collapse = "; ")
  )
}

predict_r <- function(row) {
  fns <- list(
    ASK14 = ask14,
    BSSA14 = bssa14,
    CB14 = cb14,
    CY14 = cy14,
    I14 = idriss14
  )
  result <- do.call(fns[[row$model]], case_args(row))
  data.table(
    model = result$model,
    period_s = result$period_s,
    median = result$median,
    ln_median = result$ln_median,
    sigma = result$sigma,
    tau = result$tau,
    phi = result$phi,
    warnings = paste(result$warnings, collapse = "; ")
  )
}

python_pred <- rbindlist(lapply(seq_len(nrow(cases)), function(i) {
  cbind(case_id = cases$case_id[i], predict_python(cases[i]))
}), fill = TRUE)

r_pred <- rbindlist(lapply(seq_len(nrow(cases)), function(i) {
  cbind(case_id = cases$case_id[i], predict_r(cases[i]))
}), fill = TRUE)

merged <- merge(python_pred, r_pred, by = c("case_id", "model", "period_s"), suffixes = c("_python", "_r"))
if (nrow(merged) != nrow(cases)) {
  stop("Python/R prediction row mismatch.")
}

check_close <- function(name, atol = 1e-6, rtol = 1e-5) {
  p <- merged[[paste0(name, "_python")]]
  r <- merged[[paste0(name, "_r")]]
  ok <- is.na(p) & is.na(r) | abs(p - r) <= atol + rtol * pmax(abs(p), abs(r))
  if (any(!ok, na.rm = TRUE)) {
    stop(name, " mismatch for cases: ", paste(merged$case_id[!ok], collapse = ", "))
  }
}

check_close("ln_median")
check_close("median")
check_close("sigma")
check_close("tau")
check_close("phi")

if (!identical(merged$warnings_python, merged$warnings_r)) {
  bad <- merged$case_id[merged$warnings_python != merged$warnings_r]
  stop("warning mismatch for cases: ", paste(bad, collapse = ", "))
}

cat("Python native and R native GMPE parity checks passed.\n")
