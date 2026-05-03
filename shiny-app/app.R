suppressPackageStartupMessages({
  library(shiny)
  library(bslib)
  library(DBI)
  library(RSQLite)
  library(leaflet)
  library(DT)
  library(ggplot2)
})

for (file in list.files("R", "[.]R$", full.names = TRUE)) {
  source(file, local = FALSE)
}

theme <- bs_theme(
  version = 5,
  bootswatch = "flatly",
  primary = "#2f6f73",
  secondary = "#6e7d3f",
  success = "#6e7d3f",
  info = "#496f9e",
  warning = "#b8860b",
  danger = "#c84630"
)

ui <- page_navbar(
  title = "NGA-West2 Flatfile Explorer",
  theme = theme,
  nav_panel("Overview", overview_ui("overview")),
  nav_panel("Map", map_ui("map")),
  nav_panel("Tables", tables_ui("tables")),
  nav_panel("Statistics", stats_ui("stats")),
  nav_panel("Analysis", analysis_ui("analysis")),
  nav_panel("About", about_ui("about"))
)

server <- function(input, output, session) {
  overview_server("overview")
  map_server("map")
  tables_server("tables")
  stats_server("stats")
  analysis_server("analysis")
  about_server("about")
}

shinyApp(ui, server)

