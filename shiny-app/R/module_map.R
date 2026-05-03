map_ui <- function(id) {
  ns <- NS(id)
  layout_sidebar(
    sidebar = sidebar(
      width = 310,
      radioButtons(ns("mode"), "Map Mode", choices = c("Epicenters" = "events", "Stations" = "stations", "Both" = "both"), selected = "events"),
      selectInput(ns("mechanism"), "Source Mechanism", choices = NULL, multiple = TRUE),
      selectInput(ns("event_region"), "Event Region (Derived)", choices = NULL, multiple = TRUE),
      selectInput(ns("station_region"), "Station Region (Derived)", choices = NULL, multiple = TRUE),
      selectInput(ns("network"), "Network / Owner", choices = NULL, multiple = TRUE),
      sliderInput(ns("magnitude"), "Magnitude", min = 0, max = 10, value = c(0, 10), step = 0.1),
      checkboxInput(ns("show_all"), "Show all matching points", FALSE)
    ),
    card(
      full_screen = TRUE,
      card_header(textOutput(ns("map_title"), inline = TRUE)),
      leaflet::leafletOutput(ns("map"), height = 680)
    )
  )
}

map_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    events <- reactive({
      cache_read("events_map.rds", "SELECT * FROM vw_events_map")
    })
    stations <- reactive({
      cache_read("stations_map.rds", "SELECT * FROM vw_stations_map")
    })

    observe({
      ev <- events()
      st <- stations()
      updateSelectInput(session, "mechanism", choices = safe_choices(ev$mechanism_class_simple), selected = safe_choices(ev$mechanism_class_simple))
      updateSelectInput(session, "event_region", choices = safe_choices(ev$event_region_derived))
      updateSelectInput(session, "station_region", choices = safe_choices(st$station_region_derived))
      updateSelectInput(session, "network", choices = head(safe_choices(st$network_name), 200))
      rng <- range(ev$earthquake_magnitude, na.rm = TRUE)
      updateSliderInput(session, "magnitude", min = floor(rng[1]), max = ceiling(rng[2]), value = rng)
    })

    filtered_events <- reactive({
      dt <- events()
      dt <- dt[!is.na(dt$hypocenter_latitude) & !is.na(dt$hypocenter_longitude), , drop = FALSE]
      if (length(input$mechanism)) dt <- dt[dt$mechanism_class_simple %in% input$mechanism, , drop = FALSE]
      if (length(input$event_region)) dt <- dt[dt$event_region_derived %in% input$event_region, , drop = FALSE]
      dt <- dt[dt$earthquake_magnitude >= input$magnitude[1] & dt$earthquake_magnitude <= input$magnitude[2], , drop = FALSE]
      limit_points(dt, input$show_all)
    })

    filtered_stations <- reactive({
      dt <- stations()
      lat_col <- if ("station_latitude" %in% names(dt)) "station_latitude" else "station_latitude.x"
      lon_col <- if ("station_longitude" %in% names(dt)) "station_longitude" else "station_longitude.x"
      dt <- dt[!is.na(dt[[lat_col]]) & !is.na(dt[[lon_col]]), , drop = FALSE]
      if (length(input$station_region)) dt <- dt[dt$station_region_derived %in% input$station_region, , drop = FALSE]
      if (length(input$network)) dt <- dt[dt$network_name %in% input$network, , drop = FALSE]
      limit_points(dt, input$show_all)
    })

    output$map_title <- renderText({
      paste(
        "Showing",
        if (input$mode %in% c("events", "both")) nrow(filtered_events()) else 0,
        "events and",
        if (input$mode %in% c("stations", "both")) nrow(filtered_stations()) else 0,
        "stations"
      )
    })

    output$map <- leaflet::renderLeaflet({
      m <- leaflet::leaflet() |>
        leaflet::addProviderTiles(leaflet::providers$CartoDB.Positron)

      if (input$mode %in% c("events", "both")) {
        ev <- filtered_events()
        if (nrow(ev)) {
          m <- m |>
            leaflet::addCircleMarkers(
              data = ev,
              lng = ~hypocenter_longitude,
              lat = ~hypocenter_latitude,
              radius = ~pmax(4, pmin(12, earthquake_magnitude)),
              stroke = FALSE,
              fillOpacity = 0.75,
              color = "#c84630",
              clusterOptions = leaflet::markerClusterOptions(),
              popup = ~paste0(
                "<strong>", earthquake_name, "</strong><br>",
                "EQID: ", eqid, "<br>",
                "Mw: ", earthquake_magnitude, "<br>",
                "Mechanism: ", mechanism_class_simple, "<br>",
                "Records: ", record_count
              )
            )
        }
      }

      if (input$mode %in% c("stations", "both")) {
        st <- filtered_stations()
        lat_col <- if ("station_latitude" %in% names(st)) "station_latitude" else "station_latitude.x"
        lon_col <- if ("station_longitude" %in% names(st)) "station_longitude" else "station_longitude.x"
        if (nrow(st)) {
          st$.lat <- st[[lat_col]]
          st$.lon <- st[[lon_col]]
          m <- m |>
            leaflet::addCircleMarkers(
              data = st,
              lng = ~.lon,
              lat = ~.lat,
              radius = 4,
              stroke = FALSE,
              fillOpacity = 0.65,
              color = "#2f6f73",
              clusterOptions = leaflet::markerClusterOptions(),
              popup = ~paste0(
                "<strong>", station_name, "</strong><br>",
                "SSN: ", station_sequence_number, "<br>",
                "Network: ", network_name, "<br>",
                "Vs30: ", round(vs30_m_s, 1), "<br>",
                "Records: ", record_count
              )
            )
        }
      }
      m
    })
  })
}

