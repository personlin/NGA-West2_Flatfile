overview_ui <- function(id) {
  ns <- NS(id)
  tagList(
    layout_column_wrap(
      width = "220px",
      fill = FALSE,
      value_box(title = "Events", value = textOutput(ns("events"), inline = TRUE), theme = "primary"),
      value_box(title = "Stations", value = textOutput(ns("stations"), inline = TRUE), theme = "success"),
      value_box(title = "Records", value = textOutput(ns("records"), inline = TRUE), theme = "info"),
      value_box(title = "Spectra Rows", value = textOutput(ns("spectra"), inline = TRUE), theme = "warning")
    ),
    layout_columns(
      col_widths = c(6, 6),
      card(full_screen = TRUE, card_header("Events by Mechanism"), plotOutput(ns("mechanism_plot"), height = 320)),
      card(full_screen = TRUE, card_header("Stations by Derived Region"), plotOutput(ns("station_region_plot"), height = 320))
    ),
    layout_columns(
      col_widths = c(6, 6),
      card(full_screen = TRUE, card_header("Magnitude Distribution"), plotOutput(ns("magnitude_plot"), height = 320)),
      card(full_screen = TRUE, card_header("Top Networks"), plotOutput(ns("network_plot"), height = 320))
    )
  )
}

overview_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    manifest <- reactive({
      db_query("SELECT * FROM build_manifest ORDER BY build_time_utc DESC LIMIT 1")
    })
    output$events <- renderText(format_count(manifest()$events[[1]]))
    output$stations <- renderText(format_count(manifest()$stations[[1]]))
    output$records <- renderText(format_count(manifest()$records[[1]]))
    output$spectra <- renderText(format_count(manifest()$response_spectra[[1]]))

    output$mechanism_plot <- renderPlot({
      dt <- db_query("SELECT mechanism_class_simple, COUNT(*) AS n FROM events GROUP BY mechanism_class_simple ORDER BY n DESC")
      ggplot(dt, aes(reorder(mechanism_class_simple, n), n)) +
        geom_col(fill = "#2f6f73") +
        coord_flip() +
        labs(x = NULL, y = "Events") +
        theme_minimal(base_size = 12)
    })

    output$station_region_plot <- renderPlot({
      dt <- db_query("SELECT station_region_derived, COUNT(*) AS n FROM stations GROUP BY station_region_derived ORDER BY n DESC")
      ggplot(dt, aes(reorder(station_region_derived, n), n)) +
        geom_col(fill = "#8b5a2b") +
        coord_flip() +
        labs(x = NULL, y = "Stations") +
        theme_minimal(base_size = 12)
    })

    output$magnitude_plot <- renderPlot({
      dt <- db_query("SELECT earthquake_magnitude FROM events WHERE earthquake_magnitude > 0")
      ggplot(dt, aes(earthquake_magnitude)) +
        geom_histogram(binwidth = 0.25, fill = "#496f9e", color = "white") +
        labs(x = "Magnitude", y = "Events") +
        theme_minimal(base_size = 12)
    })

    output$network_plot <- renderPlot({
      dt <- db_query("
        SELECT n.network_name, COUNT(*) AS n
        FROM stations s
        LEFT JOIN networks n ON n.network_id = s.network_id
        GROUP BY n.network_name
        ORDER BY n DESC
        LIMIT 12
      ")
      ggplot(dt, aes(reorder(network_name, n), n)) +
        geom_col(fill = "#6e7d3f") +
        coord_flip() +
        labs(x = NULL, y = "Stations") +
        theme_minimal(base_size = 12)
    })
  })
}

