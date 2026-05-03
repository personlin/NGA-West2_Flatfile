stats_ui <- function(id) {
  ns <- NS(id)
  tagList(
    layout_columns(
      col_widths = c(6, 6),
      card(full_screen = TRUE, card_header("Records by Mechanism"), plotOutput(ns("records_mech"), height = 340)),
      card(full_screen = TRUE, card_header("Distance Distribution"), plotOutput(ns("distance_hist"), height = 340))
    ),
    layout_columns(
      col_widths = c(6, 6),
      card(full_screen = TRUE, card_header("Vs30 Distribution"), plotOutput(ns("vs30_hist"), height = 340)),
      card(full_screen = TRUE, card_header("RotD50 5% PGA Distribution"), plotOutput(ns("pga_hist"), height = 340))
    )
  )
}

stats_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    output$records_mech <- renderPlot({
      dt <- db_query("
        SELECT mechanism_class_simple, COUNT(*) AS n
        FROM vw_records_overview
        GROUP BY mechanism_class_simple
        ORDER BY n DESC
      ")
      ggplot(dt, aes(reorder(mechanism_class_simple, n), n)) +
        geom_col(fill = "#496f9e") +
        coord_flip() +
        labs(x = NULL, y = "Records") +
        theme_minimal(base_size = 12)
    })

    output$distance_hist <- renderPlot({
      dt <- db_query("SELECT rjb_km, rrup_km FROM paths WHERE rjb_km >= 0 OR rrup_km >= 0")
      ggplot(dt, aes(rjb_km)) +
        geom_histogram(binwidth = 10, fill = "#8b5a2b", color = "white") +
        coord_cartesian(xlim = c(0, 300)) +
        labs(x = "RJB (km)", y = "Records") +
        theme_minimal(base_size = 12)
    })

    output$vs30_hist <- renderPlot({
      dt <- db_query("SELECT vs30_m_s FROM sites WHERE vs30_m_s > 0")
      ggplot(dt, aes(vs30_m_s)) +
        geom_histogram(binwidth = 50, fill = "#2f6f73", color = "white") +
        coord_cartesian(xlim = c(0, 1500)) +
        labs(x = "Vs30 (m/s)", y = "Stations") +
        theme_minimal(base_size = 12)
    })

    output$pga_hist <- renderPlot({
      dt <- db_query("SELECT pga_g FROM intensity_measures WHERE component = 'RotD50' AND damping_percent = 5 AND pga_g > 0")
      ggplot(dt, aes(pga_g)) +
        geom_histogram(bins = 60, fill = "#6e7d3f", color = "white") +
        scale_x_log10() +
        labs(x = "PGA (g, log scale)", y = "Records") +
        theme_minimal(base_size = 12)
    })
  })
}

