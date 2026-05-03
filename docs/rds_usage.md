# NGA-West2 RDS Files Usage

RDS 輸出提供 R 使用者直接讀取 NGA-West2 flatfiles 的方式。SQLite 適合互動查詢與 Shiny app；RDS 適合 R/data.table 的建模、繪圖、篩選與 wide flatfile 工作流。

輸出位置：

```text
output/rds/
```

## 建置

```bash
Rscript scripts/build_nga_west2_rds.R
```

## 檔案

| File | 說明 |
|---|---|
| `nga_west2_core_normalized.rds` | named list，包含 normalized events、sources、stations、sites、paths、records、field catalog 等 |
| `nga_west2_rotd50_d005_flatfile.rds` 到 `nga_west2_rotd50_d300_flatfile.rds` | 11 個 RotD50 damping wide flatfiles |
| `nga_west2_vertical_d050_flatfile.rds` | vertical 5% damping wide flatfile |
| `nga_west2_rds_manifest.rds` / `.csv` | RDS 檔案 manifest |

## 基本讀取

```r
library(data.table)

core <- readRDS("output/rds/nga_west2_core_normalized.rds")
manifest <- readRDS("output/rds/nga_west2_rds_manifest.rds")
rotd50 <- readRDS("output/rds/nga_west2_rotd50_d050_flatfile.rds")

names(core)
manifest
nrow(rotd50)
```

## Core Object

`nga_west2_core_normalized.rds` 是 named list：

```text
release_files
field_catalog
damping_levels
spectral_periods
mechanism_classes
events
event_sources
networks
stations
sites
records
paths
record_quality_flags
class2_distances
```

## 範例：建立 GMPE 子集

```r
library(data.table)

rotd50 <- as.data.table(readRDS("output/rds/nga_west2_rotd50_d050_flatfile.rds"))

model_dt <- rotd50[
  earthquake_magnitude >= 5 &
    joyner_boore_dist_km >= 0 &
    joyner_boore_dist_km <= 100 &
    vs30_m_s_selected_for_analysis > 0,
  .(
    record_sequence_number,
    eqid,
    station_sequence_number,
    earthquake_magnitude,
    joyner_boore_dist_km,
    campbell_r_dist_km,
    vs30_m_s_selected_for_analysis,
    pga_g,
    pgv_cm_sec,
    t1_000s
  )
]

summary(model_dt)
```

## 範例：轉 PSA 欄位為 long format

```r
library(data.table)

rotd50 <- as.data.table(readRDS("output/rds/nga_west2_rotd50_d050_flatfile.rds"))
psa_cols <- grep("^t[0-9]+_[0-9]+s$", names(rotd50), value = TRUE)

psa_long <- melt(
  rotd50,
  id.vars = c(
    "record_sequence_number",
    "eqid",
    "station_sequence_number",
    "earthquake_magnitude",
    "joyner_boore_dist_km",
    "vs30_m_s_selected_for_analysis"
  ),
  measure.vars = psa_cols,
  variable.name = "period_field",
  value.name = "psa_g"
)

psa_long[, period_s := as.numeric(
  gsub("_", ".", sub("^t", "", sub("s$", "", period_field)))
)]
```

## Shiny Cache

`scripts/build_nga_west2_sqlite.R` 與 `scripts/build_nga_west2_rds.R` 會建立：

```text
shiny-app/data/cache/
  events_map.rds
  stations_map.rds
  overview_counts.rds
  event_summary.rds
  station_summary.rds
  network_summary.rds
```

這些 cache 是 app 啟動與地圖瀏覽用的小型資料，不是 canonical source。

## 注意事項

- 欄位名稱已轉為 snake_case，原始 Excel 欄名保存在 object attributes 與 `core$field_catalog`。
- 官方缺值代碼如 `-999` 原樣保存。
- Vertical 目前只有 5% damping 檔案。

