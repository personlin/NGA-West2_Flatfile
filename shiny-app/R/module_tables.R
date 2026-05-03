tables_ui <- function(id) {
  ns <- NS(id)
  layout_sidebar(
    sidebar = sidebar(
      width = 300,
      selectInput(ns("table"), "Table", choices = valid_table_choices, selected = "vw_records_overview"),
      numericInput(ns("limit"), "Max Rows", value = 1000, min = 100, max = 20000, step = 100),
      downloadButton(ns("download"), "Download CSV")
    ),
    card(full_screen = TRUE, card_header(textOutput(ns("title"), inline = TRUE)), DT::DTOutput(ns("table_out")))
  )
}

tables_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    table_data <- reactive({
      db_query(table_sql(input$table, input$limit))
    })

    output$title <- renderText({
      paste(input$table, "preview")
    })

    output$table_out <- DT::renderDT({
      DT::datatable(
        table_data(),
        rownames = FALSE,
        filter = "top",
        options = list(pageLength = 25, scrollX = TRUE)
      )
    })

    output$download <- downloadHandler(
      filename = function() paste0(input$table, ".csv"),
      content = function(file) write.csv(table_data(), file, row.names = FALSE, na = "")
    )
  })
}

