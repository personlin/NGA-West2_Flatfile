`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0) y else x
}

app_project_root <- function() {
  wd <- normalizePath(getwd(), mustWork = TRUE)
  if (basename(wd) == "shiny-app") dirname(wd) else wd
}

app_db_path <- function() {
  Sys.getenv(
    "NGA_WEST2_SQLITE",
    file.path(app_project_root(), "output/sqlite/nga_west2.sqlite")
  )
}

app_rds_dir <- function() {
  Sys.getenv("NGA_WEST2_RDS_DIR", file.path(app_project_root(), "output/rds"))
}

app_cache_dir <- function() {
  file.path(app_project_root(), "shiny-app/data/cache")
}

app_load_gmpe <- local({
  loaded <- FALSE
  function() {
    if (loaded) {
      return(invisible(TRUE))
    }
    root <- app_project_root()
    gmpe_dir <- file.path(root, "gmpe/R/R")
    coeff_dir <- file.path(root, "gmpe/coefficients")
    validate_msg <- "GMPE R source not found. Build or restore gmpe/R before using GMPE analysis."
    if (!dir.exists(gmpe_dir)) {
      stop(validate_msg, call. = FALSE)
    }
    if (!nzchar(Sys.getenv("NGAW2GMPE_COEFF_DIR", unset = "")) && dir.exists(coeff_dir)) {
      Sys.setenv(NGAW2GMPE_COEFF_DIR = normalizePath(coeff_dir, mustWork = TRUE))
    }
    for (file in c("utils.R", "coefficients.R", "native.R", "validation.R", "models.R", "batch.R")) {
      path <- file.path(gmpe_dir, file)
      if (!file.exists(path)) {
        stop(validate_msg, call. = FALSE)
      }
      source(path, local = FALSE)
    }
    loaded <<- TRUE
    invisible(TRUE)
  }
})

db_connect <- function() {
  path <- app_db_path()
  if (!file.exists(path)) {
    stop("SQLite database not found. Run Rscript scripts/build_nga_west2_sqlite.R first.")
  }
  DBI::dbConnect(RSQLite::SQLite(), path)
}

db_query <- function(sql, params = NULL) {
  con <- db_connect()
  on.exit(DBI::dbDisconnect(con), add = TRUE)
  if (is.null(params)) DBI::dbGetQuery(con, sql) else DBI::dbGetQuery(con, sql, params = params)
}

cache_read <- function(name, fallback_sql = NULL) {
  path <- file.path(app_cache_dir(), name)
  if (file.exists(path)) {
    return(readRDS(path))
  }
  if (!is.null(fallback_sql)) {
    return(db_query(fallback_sql))
  }
  NULL
}

format_count <- function(x) {
  format(as.integer(x %||% 0), big.mark = ",")
}
