analysis_ui <- function(id) {
  ns <- NS(id)
  layout_sidebar(
    sidebar = sidebar(
      width = 320,
      selectInput(ns("rds_file"), "Wide RDS", choices = character()),
      sliderInput(ns("mag"), "Magnitude", min = 0, max = 10, value = c(5, 8), step = 0.1),
      sliderInput(ns("rjb"), "RJB (km)", min = 0, max = 500, value = c(0, 100), step = 5),
      selectInput(ns("yvar"), "Y Variable", choices = c("PGA" = "pga_g", "PGV" = "pgv_cm_sec", "PSA 0.2s" = "t0_200s", "PSA 1.0s" = "t1_000s", "PSA 3.0s" = "t3_000s")),
      selectInput(ns("xvar"), "X Variable", choices = c("Magnitude" = "earthquake_magnitude", "RJB" = "joyner_boore_dist_km", "Vs30" = "vs30_m_s_selected_for_analysis")),
      actionButton(ns("load"), "Load / Refresh")
    ),
    tagList(
      card(full_screen = TRUE, card_header("Selected Subset Plot"), plotOutput(ns("plot"), height = 420)),
      card(full_screen = TRUE, card_header("Preview"), DT::DTOutput(ns("preview")))
    )
  )
}

analysis_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    observe({
      rds_dir <- app_rds_dir()
      files <- if (dir.exists(rds_dir)) list.files(rds_dir, "flatfile[.]rds$", full.names = FALSE) else character()
      updateSelectInput(session, "rds_file", choices = files, selected = files[grepl("rotd50_d050", files)][1] %||% files[1])
    })

    selected_data <- eventReactive(input$load, {
      req(input$rds_file)
      path <- file.path(app_rds_dir(), input$rds_file)
      validate(need(file.exists(path), "RDS file not found. Run Rscript scripts/build_nga_west2_rds.R first."))
      dt <- as.data.frame(readRDS(path))
      if ("earthquake_magnitude" %in% names(dt)) {
        dt <- dt[dt$earthquake_magnitude >= input$mag[1] & dt$earthquake_magnitude <= input$mag[2], , drop = FALSE]
      }
      if ("joyner_boore_dist_km" %in% names(dt)) {
        dt <- dt[dt$joyner_boore_dist_km >= input$rjb[1] & dt$joyner_boore_dist_km <= input$rjb[2], , drop = FALSE]
      }
      dt
    }, ignoreInit = FALSE)

    output$plot <- renderPlot({
      dt <- selected_data()
      req(nrow(dt) > 0, input$xvar %in% names(dt), input$yvar %in% names(dt))
      ggplot(dt, aes(.data[[input$xvar]], .data[[input$yvar]])) +
        geom_point(alpha = 0.35, color = "#2f6f73", size = 1.2) +
        scale_y_continuous(trans = "log10") +
        labs(x = input$xvar, y = input$yvar) +
        theme_minimal(base_size = 12)
    })

    output$preview <- DT::renderDT({
      dt <- selected_data()
      keep <- intersect(
        c("record_sequence_number", "eqid", "earthquake_name", "station_sequence_number", "station_name",
          "earthquake_magnitude", "joyner_boore_dist_km", "campbell_r_dist_km",
          "vs30_m_s_selected_for_analysis", input$xvar, input$yvar),
        names(dt)
      )
      DT::datatable(head(dt[, keep, drop = FALSE], 2000), rownames = FALSE, options = list(pageLength = 15, scrollX = TRUE))
    })
  })
}

