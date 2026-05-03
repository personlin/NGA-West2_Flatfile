gmpe_models <- c("ASK14", "BSSA14", "CB14", "CY14", "I14")

csv_schema <- c(
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

normalize_model <- function(model) {
  name <- toupper(model)
  if (name %in% c("IDRISS", "IDRISS14")) {
    name <- "I14"
  }
  if (!name %in% gmpe_models) {
    stop(sprintf("Unknown GMPE model: %s", model), call. = FALSE)
  }
  name
}

coefficients_dir <- function() {
  env <- Sys.getenv("NGAW2GMPE_COEFF_DIR", unset = NA_character_)
  if (!is.na(env) && nzchar(env)) {
    return(normalizePath(env, mustWork = FALSE))
  }

  candidates <- c(
    file.path(getwd(), "gmpe", "coefficients"),
    file.path(getwd(), "..", "coefficients"),
    file.path(getwd(), "..", "..", "coefficients"),
    file.path(getwd(), "..", "..", "..", "coefficients")
  )
  for (candidate in candidates) {
    if (dir.exists(candidate)) {
      return(normalizePath(candidate, mustWork = TRUE))
    }
  }
  stop("Cannot locate gmpe/coefficients; set NGAW2GMPE_COEFF_DIR.", call. = FALSE)
}

load_coefficients <- function(model) {
  name <- normalize_model(model)
  path <- file.path(coefficients_dir(), paste0(tolower(name), ".csv"))
  if (!file.exists(path)) {
    stop(sprintf("Coefficient file not found: %s", path), call. = FALSE)
  }
  data <- data.table::fread(path, na.strings = c("", "NA"))
  missing <- setdiff(csv_schema, names(data))
  if (length(missing) > 0L) {
    stop(
      sprintf("Coefficient file is missing columns: %s", paste(missing, collapse = ", ")),
      call. = FALSE
    )
  }
  data[, ..csv_schema]
}

available_periods <- function(model) {
  data <- load_coefficients(model)
  sort(unique(as.numeric(data$period_s)))
}
