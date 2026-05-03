#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(data.table)
})

source("scripts/nga_west2_common.R")

dir.create("manifests", showWarnings = FALSE, recursive = TRUE)

files <- list_input_files(".")
files <- add_excel_counts(files)

field_catalog <- rbindlist(lapply(seq_len(nrow(files)), function(i) {
  hdr <- read_header_catalog(files$path[i], files$sheet_name[i])
  hdr[, `:=`(
    release_file_id = files$release_file_id[i],
    file_name = files$file_name[i],
    component = files$component[i],
    damping_percent = files$damping_percent[i],
    sheet_name = files$sheet_name[i]
  )]
  hdr
}), fill = TRUE)

fwrite(files, "manifests/nga_west2_input_files.csv")
fwrite(field_catalog, "manifests/nga_west2_field_catalog_draft.csv")

cat("Wrote manifests/nga_west2_input_files.csv\n")
cat("Wrote manifests/nga_west2_field_catalog_draft.csv\n")
print(files[, .(file_name, component, damping_percent, row_count, column_count)])

