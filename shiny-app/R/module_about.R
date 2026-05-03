about_ui <- function(id) {
  ns <- NS(id)
  tagList(
    card(
      card_header("Data Products"),
      p("This app reads the normalized NGA-West2 SQLite database and optional RDS files generated from the public flatfiles."),
      tags$ul(
        tags$li(code("output/sqlite/nga_west2.sqlite")),
        tags$li(code("output/rds/nga_west2_core_normalized.rds")),
        tags$li(code("output/rds/*_flatfile.rds")),
        tags$li(code("shiny-app/data/cache/*.rds"))
      )
    ),
    card(
      card_header("Build Commands"),
      tags$pre("Rscript scripts/inspect_nga_west2_inputs.R\nRscript scripts/build_nga_west2_sqlite.R\nRscript scripts/build_nga_west2_rds.R\nRscript scripts/validate_nga_west2_outputs.R")
    ),
    card(
      card_header("Notes"),
      p("Country/region fields are derived from event names and broad station coordinate boxes. Treat them as browsing aids rather than official metadata."),
      p("Official missing values such as -999 are preserved in the database and RDS files.")
    )
  )
}

about_server <- function(id) {
  moduleServer(id, function(input, output, session) {})
}

