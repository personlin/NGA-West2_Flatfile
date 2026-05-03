# NGA-West2 Flatfile Explorer

本專案將 NGA-West2 public flatfile Excel 檔整理為可重建的 SQLite 與 RDS 資料產品，並提供一個 Shiny app，用來互動檢視地震、測站、records、地動資料與基本統計。

英文版說明請見 [README.md](README.md)。

## 專案內容

```text
data/        原始 NGA-West2 public flatfile Excel 檔
docs/        開發計畫、資料處理說明、SQLite/RDS 使用文件、來源報告
manifests/   scripts 產生的輸入與驗證清單
scripts/     可重建的資料盤點、建置與驗證程式
shiny-app/   互動式 Shiny dashboard
```

下列輸出檔案可由 scripts 重建，故不納入 Git：

```text
output/sqlite/nga_west2.sqlite
output/rds/
shiny-app/data/cache/
```

## 資料來源

本專案包含：

- 11 個 RotD50 damping flatfiles，damping 從 0.5% 到 30%。
- 1 個 vertical 5% damping flatfile。
- NGA-West2 database 報告：`docs/webpeer-2013-03-timothy_d._ancheta_robert_b._darragh_jonathan_p._stewart_emel_seyhan.pdf`。

資料處理計畫依據報告中四個 metadata tables 的概念：

- earthquake source table
- site database
- propagation path table
- record catalog

Public flatfiles 是上述表格的合併摘要。本專案建立的 SQLite 是由 public release files 反推整理的 application-oriented normalized database，不是 PEER 官方內部資料庫 dump。

## 需求套件

目前資料管線與 Shiny app 使用的 R packages：

- `readxl`
- `data.table`
- `DBI`
- `RSQLite`
- `jsonlite`
- `digest`
- `shiny`
- `bslib`
- `leaflet`
- `DT`
- `ggplot2`
- `dplyr`
- `dbplyr`

開發計畫中提到的 optional packages，例如 `bsicons` 與 `shinycssloaders`，目前 app 不需要。

## 建置資料產品

在專案根目錄執行：

```bash
Rscript scripts/inspect_nga_west2_inputs.R
Rscript scripts/build_nga_west2_sqlite.R
Rscript scripts/build_nga_west2_rds.R
Rscript scripts/validate_nga_west2_outputs.R
```

SQLite builder 也提供 Python wrapper：

```bash
python3 scripts/build_nga_west2_sqlite.py
```

## 驗證摘要

目前建置結果已通過：

```text
SQLite integrity_check: ok
events: 600
stations: 4151
records: 21540
spectral_periods: 111
intensity_measures: 258480
response_spectra: 258480
```

驗證輸出位於：

```text
manifests/nga_west2_validation_summary.csv
```

## 執行 Shiny App

先建立 SQLite database 與 cache files，然後執行：

```bash
Rscript -e 'shiny::runApp("shiny-app", host = "127.0.0.1", port = 3838, launch.browser = FALSE)'
```

接著開啟：

```text
http://127.0.0.1:3838
```

目前 app 包含：

- Overview counts 與統計圖。
- 震央與測站互動地圖。
- server-side table previews。
- 基本統計圖表。
- 以 lazy loading 讀取 wide RDS 的分析頁。

## 資料產品

SQLite：

```text
output/sqlite/nga_west2.sqlite
```

重要 SQLite tables 與 views：

- `events`, `event_sources`
- `stations`, `sites`, `networks`
- `records`, `paths`, `record_quality_flags`
- `intensity_measures`
- `response_spectra`
- `response_spectra_common_periods`
- `vw_events_map`
- `vw_stations_map`
- `vw_records_overview`
- `vw_ground_motion_rotd50_d050`

RDS：

```text
output/rds/nga_west2_core_normalized.rds
output/rds/nga_west2_rotd50_d005_flatfile.rds
...
output/rds/nga_west2_rotd50_d300_flatfile.rds
output/rds/nga_west2_vertical_d050_flatfile.rds
output/rds/nga_west2_rds_manifest.csv
```

詳細說明請見 [docs/sqlite_usage.md](docs/sqlite_usage.md)、[docs/rds_usage.md](docs/rds_usage.md)、[docs/data_processing_notes.md](docs/data_processing_notes.md)。

## 注意事項

- 官方缺值代碼如 `-999` 會原樣保存。
- SQLite 中的 response spectra 以 JSON array 保存，以避免建立過大的 long-format spectra table。
- `event_region_derived` 與 `station_region_derived` 是由事件名稱與測站粗略座標框推估的瀏覽輔助欄位，不是官方 metadata。
- `station_region_derived` 已將 Taiwan 測站座標從 broad China coordinate rule 中分開。

## 引用

主要文件來源：

Ancheta, T. D., Darragh, R. B., Stewart, J. P., Seyhan, E., Silva, W. J., Chiou, B. S.-J., Wooddell, K. E., Graves, R. W., Kottke, A. R., Boore, D. M., Kishida, T., and Donahue, J. L. (2013). *PEER NGA-West2 Database*. PEER Report 2013/03.

