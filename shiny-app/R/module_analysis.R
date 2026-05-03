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
      hr(),
      selectInput(ns("gmpe_model"), "GMPE Model", choices = c("ASK14", "BSSA14", "CB14", "CY14", "I14")),
      selectInput(
        ns("gmpe_im"),
        "GMPE Intensity",
        choices = c("PGA" = "pga_g", "PSA 0.2s" = "t0_200s", "PSA 1.0s" = "t1_000s", "PSA 3.0s" = "t3_000s", "PSA 10s" = "t10_000s"),
        selected = "t1_000s"
      ),
      numericInput(ns("gmpe_limit"), "GMPE Rows", value = 1000, min = 50, max = 5000, step = 50),
      actionButton(ns("load"), "Load / Refresh")
    ),
    tagList(
      layout_column_wrap(
        width = "220px",
        fill = FALSE,
        value_box("Subset Records", textOutput(ns("n_records")), theme = "primary"),
        value_box("GMPE Rows", textOutput(ns("n_gmpe")), theme = "info"),
        value_box("Median Residual", textOutput(ns("median_residual")), theme = "secondary")
      ),
      navset_card_underline(
        full_screen = TRUE,
        nav_panel("Subset", plotOutput(ns("plot"), height = 420)),
        nav_panel("Observed vs Predicted", plotOutput(ns("gmpe_scatter"), height = 420)),
        nav_panel("Residuals", plotOutput(ns("gmpe_residuals"), height = 420)),
        nav_panel("Table", DT::DTOutput(ns("gmpe_table"))),
        nav_panel("Preview", DT::DTOutput(ns("preview")))
      )
    )
  )
}

gmpe_period_for_column <- function(column) {
  switch(column,
    pga_g = 0,
    t0_200s = 0.2,
    t1_000s = 1.0,
    t3_000s = 3.0,
    t10_000s = 10.0,
    NA_real_
  )
}

gmpe_column_map <- function() {
  c(
    joyner_boore_dist_km = "Rjb",
    campbell_r_dist_km = "Rrup",
    rx = "Rx",
    vs30_m_s_selected_for_analysis = "Vs30",
    depth_to_top_of_fault_rupture_model = "Ztor",
    fault_rupture_width_km = "W",
    dip_deg = "dip",
    hypocenter_depth_km = "Zhyp"
  )
}

gmpe_prepare_subset <- function(dt, observed_col, limit) {
  required <- c(
    "earthquake_magnitude",
    "joyner_boore_dist_km",
    "campbell_r_dist_km",
    "vs30_m_s_selected_for_analysis",
    observed_col
  )
  missing <- setdiff(required, names(dt))
  shiny::validate(shiny::need(length(missing) == 0, paste("Missing columns:", paste(missing, collapse = ", "))))
  dt <- dt[
    is.finite(dt$earthquake_magnitude) &
      is.finite(dt$joyner_boore_dist_km) &
      is.finite(dt$campbell_r_dist_km) &
      is.finite(dt$vs30_m_s_selected_for_analysis) &
      is.finite(dt[[observed_col]]) &
      dt$earthquake_magnitude > 0 &
      dt$joyner_boore_dist_km >= 0 &
      dt$campbell_r_dist_km > 0 &
      dt$vs30_m_s_selected_for_analysis > 0 &
      dt[[observed_col]] > 0, ,
    drop = FALSE
  ]
  head(dt, limit)
}

analysis_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    observe({
      rds_dir <- app_rds_dir()
      files <- if (dir.exists(rds_dir)) list.files(rds_dir, "flatfile[.]rds$", full.names = FALSE) else character()
      updateSelectInput(session, "rds_file", choices = files, selected = files[grepl("rotd50_d050", files)][1] %||% files[1])
    })

    selected_data <- eventReactive(input$load,
      {
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
      },
      ignoreInit = FALSE
    )

    gmpe_results <- reactive({
      app_load_gmpe()
      dt <- selected_data()
      period <- gmpe_period_for_column(input$gmpe_im)
      validate(need(!is.na(period), "Select a PGA or PSA intensity for GMPE prediction."))
      validate(need(nrow(dt) > 0, "No records match the current filters."))

      observed_col <- input$gmpe_im
      subset <- gmpe_prepare_subset(dt, observed_col, input$gmpe_limit)
      validate(need(nrow(subset) > 0, "No positive observed values are available for the selected GMPE intensity."))

      pred <- predict_dataframe(
        subset,
        input$gmpe_model,
        c(period),
        column_map = gmpe_column_map()
      )
      out <- cbind(subset[seq_len(nrow(pred)), , drop = FALSE], as.data.frame(pred))
      out$observed <- out[[observed_col]]
      out$ln_observed <- log(out$observed)
      out$residual_ln <- out$ln_observed - out$ln_median
      out
    })

    output$plot <- renderPlot({
      dt <- selected_data()
      req(nrow(dt) > 0, input$xvar %in% names(dt), input$yvar %in% names(dt))
      ggplot(dt, aes(.data[[input$xvar]], .data[[input$yvar]])) +
        geom_point(alpha = 0.35, color = "#2f6f73", size = 1.2) +
        scale_y_continuous(trans = "log10") +
        labs(x = input$xvar, y = input$yvar) +
        theme_minimal(base_size = 12)
    })

    output$n_records <- renderText({
      format_count(nrow(selected_data()))
    })

    output$n_gmpe <- renderText({
      format_count(nrow(gmpe_results()))
    })

    output$median_residual <- renderText({
      dt <- gmpe_results()
      sprintf("%.3f", stats::median(dt$residual_ln, na.rm = TRUE))
    })

    output$gmpe_scatter <- renderPlot({
      dt <- gmpe_results()
      ggplot(dt, aes(median, observed)) +
        geom_abline(slope = 1, intercept = 0, color = "#6e7d3f", linewidth = 0.8) +
        geom_point(aes(color = residual_ln), alpha = 0.55, size = 1.4) +
        scale_x_log10() +
        scale_y_log10() +
        scale_color_gradient2(low = "#496f9e", mid = "#666666", high = "#c84630", midpoint = 0) +
        labs(x = "Predicted median", y = "Observed", color = "ln residual") +
        theme_minimal(base_size = 12)
    })

    output$gmpe_residuals <- renderPlot({
      dt <- gmpe_results()
      xvar <- input$xvar
      validate(need(xvar %in% names(dt), "Selected x variable is not available."))
      ggplot(dt, aes(.data[[xvar]], residual_ln)) +
        geom_hline(yintercept = 0, color = "#6e7d3f", linewidth = 0.8) +
        geom_point(alpha = 0.45, color = "#2f6f73", size = 1.3) +
        geom_smooth(method = "loess", formula = y ~ x, se = FALSE, color = "#c84630", linewidth = 0.9) +
        labs(x = xvar, y = "ln(observed) - ln(predicted)") +
        theme_minimal(base_size = 12)
    })

    output$gmpe_table <- DT::renderDT({
      dt <- gmpe_results()
      keep <- intersect(
        c(
          "record_sequence_number", "eqid", "earthquake_name", "station_name",
          "earthquake_magnitude", "joyner_boore_dist_km", "campbell_r_dist_km",
          "vs30_m_s_selected_for_analysis", "model", "period_s", "observed",
          "median", "sigma", "residual_ln", "warnings"
        ),
        names(dt)
      )
      DT::datatable(dt[, keep, drop = FALSE], rownames = FALSE, options = list(pageLength = 15, scrollX = TRUE))
    })

    output$preview <- DT::renderDT({
      dt <- selected_data()
      keep <- intersect(
        c(
          "record_sequence_number", "eqid", "earthquake_name", "station_sequence_number", "station_name",
          "earthquake_magnitude", "joyner_boore_dist_km", "campbell_r_dist_km",
          "vs30_m_s_selected_for_analysis", input$xvar, input$yvar
        ),
        names(dt)
      )
      DT::datatable(head(dt[, keep, drop = FALSE], 2000), rownames = FALSE, options = list(pageLength = 15, scrollX = TRUE))
    })
  })
}
