period_key <- function(period) {
  value <- as.numeric(period)
  if (length(value) != 1L || is.na(value)) {
    stop("period must be a single numeric value", call. = FALSE)
  }
  if (value == 0) {
    return("pga")
  }
  if (value == -1) {
    return("pgv")
  }
  sign <- if (value < 0) "m" else "p"
  gsub(".", "p", sprintf("%s%.3f", sign, abs(value)), fixed = TRUE)
}

