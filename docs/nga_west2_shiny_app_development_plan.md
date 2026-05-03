# NGA-West2 Flatfile Data Processing and Shiny App Development Plan

本文件依據下列資料擬定 NGA-West2 flatfile 的整理與 Shiny app 開發計畫：

- 本專案 `data/` 中 11 個 RotD50 damping Excel flatfiles 與 1 個 vertical 5 percent damping Excel flatfile。
- 本專案 `docs/webpeer-2013-03-timothy_d._ancheta_robert_b._darragh_jonathan_p._stewart_emel_seyhan.pdf`。
- 參考專案 `personlin/NGA-West3_Flatfile` 的 `docs/shiny_app_development_plan.md`、`docs/sqlite_usage.md`、`docs/rds_usage.md` 與根目錄架構。

## 1. 參考案例摘要

NGA-West3 參考專案採用下列架構，可移植到 NGA-West2：

```text
scripts/
  build_*.py
  build_*.R
output/
  sqlite/
  rds/
docs/
  sqlite_usage.md
  rds_usage.md
  shiny_app_development_plan.md
shiny-app/
  app.R
  R/
  data/cache/
  www/
```

核心設計原則：

- SQLite 作為 canonical normalized database，支援互動查詢、server-side tables、地圖點位查詢與統計 aggregation。
- RDS 作為 R 使用者與 Shiny cache 的高效率資料格式，保留 wide flatfile 以利建模分析，也另存 normalized core list。
- Shiny app 啟動時只讀小型 summary/cache；大型 flatfile 或完整 spectra 在使用者進入分析頁或縮小篩選後再 lazy load。

## 2. NGA-West2 資料與報告重點

Ancheta et al. (2013) 報告說明 NGA-West2 metadata 來自四個主要資料表：

- Earthquake source table：地震事件、震源機制、震源幾何、finite fault 與分類資訊。
- Site database：測站座標、Vs30、site class、地質與 basin depth 資訊。
- Propagation path table：由震源幾何與測站位置計算的 distance metrics、hanging-wall indicator、directivity parameters。
- Record catalog：RSN、檔名、處理流程、filter corners、PGA/PGV/PGD、RotDnn spectra、quality flags。

報告第 7 章指出 NGA-West2 flatfiles 是上述四表的合併摘要，用於 GMPE regression 與資料發佈。RotD50 flatfiles 包含 PGA、PGV、PGD，以及 11 個 damping levels 的 pseudo spectral acceleration；periods 為 0.01 到 20 秒，共 111 個。Appendix D 提供 flatfile 欄位定義，Appendix E 提供 site classification definitions。

本專案目前資料盤點：

| 類別 | 檔案 | 初步觀察 |
|---|---|---|
| RotD50 | `Updated_NGA_West2_Flatfile_RotD50_d005_public_version.xlsx` 到 `d300` 共 11 檔 | 每檔 274 欄，sheet 名稱如 `ROTD50_d050` |
| Vertical | `Updated_NGAW2_Flatfile_Vertical_5percentdamping.xlsx` | 276 欄，sheet `As_Recorded_d050` |
| 5 percent RotD50 | `Updated_NGA_West2_Flatfile_RotD50_d050_public_version.xlsx` | 21,540 records、600 EQID、約 4,151 station sequence numbers |

`Mechanism Based on Rake Angle` 欄位可依 Appendix D 對應：

| Code | 類型 | Rake 範圍 |
|---|---|---|
| 0 | strike-slip | -180 到 -150、-30 到 30、150 到 180 |
| 1 | normal | -120 到 -60 |
| 2 | reverse | 60 到 120 |
| 3 | reverse-oblique | 30 到 60、120 到 150 |
| 4 | normal-oblique | -150 到 -120、-60 到 -30 |
| -999 或 blank | unknown | 缺值或未知 |

Shiny app 中的震源機制分類建議使用兩層欄位：

- `mechanism_class_original`：保留 0 到 4 與 unknown。
- `mechanism_class_simple`：`strike-slip`、`normal`、`reverse`、`oblique`、`unknown`。

## 3. 資料整理開發計畫

### 3.1 目標輸出

建立下列衍生資料：

```text
output/sqlite/nga_west2.sqlite
output/rds/nga_west2_core_normalized.rds
output/rds/nga_west2_rotd50_d005_flatfile.rds
output/rds/nga_west2_rotd50_d010_flatfile.rds
output/rds/nga_west2_rotd50_d020_flatfile.rds
output/rds/nga_west2_rotd50_d030_flatfile.rds
output/rds/nga_west2_rotd50_d050_flatfile.rds
output/rds/nga_west2_rotd50_d070_flatfile.rds
output/rds/nga_west2_rotd50_d100_flatfile.rds
output/rds/nga_west2_rotd50_d150_flatfile.rds
output/rds/nga_west2_rotd50_d200_flatfile.rds
output/rds/nga_west2_rotd50_d250_flatfile.rds
output/rds/nga_west2_rotd50_d300_flatfile.rds
output/rds/nga_west2_vertical_d050_flatfile.rds
output/rds/nga_west2_rds_manifest.rds
output/rds/nga_west2_rds_manifest.csv
```

建立下列程式與文件：

```text
scripts/
  inspect_nga_west2_inputs.R
  build_nga_west2_sqlite.py
  build_nga_west2_rds.R
  validate_nga_west2_outputs.R
docs/
  sqlite_usage.md
  rds_usage.md
  data_processing_notes.md
```

所有資料整理與驗證程式需保留於 `scripts/`，不可只在 notebook 或互動 console 中完成。

### 3.2 前處理原則

1. 以 5 percent RotD50 flatfile 作為 normalized metadata 的主要來源，因其含有完整 metadata、PGA/PGV/PGD 與 111 個 5 percent RotD50 PSA periods。
2. 其他 RotD50 damping files 只新增 damping-specific spectral values，不重複建立事件、測站、path metadata。
3. Vertical 5 percent damping flatfile 建成獨立 component 的 intensity measures 與 response spectra，metadata 則用 RSN/EQID/SSN 與 core tables 關聯。
4. 保留原始欄位名稱於 `field_catalog`，同時建立 snake_case 欄位供程式使用。
5. 官方缺值代碼如 `-999` 先原樣保存，另在文件說明；若建立分析用 view，再轉換為 SQL `NULL`。
6. 對於重複欄名與 Excel 特殊欄名，例如多個 `CRjb`、`Unused Column`、換行欄名，建立穩定 machine-readable name。
7. 以 RSN 作為 record 主鍵、EQID 作為 event key、Station Sequence Number 作為 station key。
8. 依報告與 Appendix D 建立欄位分類：source、path、site、record/processing、intensity、spectra、quality flags。

### 3.3 SQLite schema

建議資料表如下。

| Table | 主鍵 | 說明 |
|---|---|---|
| `release_files` | `release_file_id` | 原始 Excel 檔名、component、damping、sheet、row count、column count、SHA-256 |
| `field_catalog` | `field_id` | 原始欄名、snake_case 名稱、來源欄位字母、單位、欄位群組、Appendix D 說明 |
| `damping_levels` | `damping_id` | 0.5、1、2、3、5、7、10、15、20、25、30 percent |
| `spectral_periods` | `period_id` | 111 個 period，0.01 到 20 秒 |
| `mechanism_classes` | `mechanism_code` | 0 到 4、unknown 的原始與簡化分類 |
| `events` | `eqid` | 地震名稱、時間、Mw、magnitude uncertainty、hypocenter、mechanism、surface rupture、finite rupture flag |
| `event_sources` | `eqid` | strike、dip、rake、rupture length/width/area、ZTOR、fault name、slip rate、stress drop 等震源幾何與 kinematic metadata |
| `stations` | `station_sequence_number` | 測站名稱、station id、owner/network provider、座標、recording type、instrument metadata |
| `sites` | `site_id` | station FK、Vs30、Vs30 class、NEHRP、Geomatrix、geology、basin、site visited、site proxies |
| `networks` | `network_id` | 由 `Owner`、station id 或後續 mapping 檔整理出的觀測網/資料來源 |
| `paths` | `path_id` | RSN FK、EpiD、HypD、RJB、RRUP/Campbell R、Rx、Ry、azimuth、hanging wall、directivity metrics |
| `records` | `rsn` | EQID FK、station FK、file names、component azimuth、processing flags、filter parameters、quality flags |
| `intensity_measures` | `im_id` | RSN、component、damping、PGA、PGV、PGD |
| `response_spectra` | `spectrum_id` | RSN、component、damping、PSA JSON array 或 long table 值 |
| `response_spectra_long` | composite | 可選，若效能允許則存 RSN、component、damping、period、psa |
| `record_quality_flags` | `rsn` | quality flag、spectra quality flag、late S/P trigger |
| `class2_distances` | `class2_distance_id` | TYPE/CRjb at 0、2、5、10、20、40 km |
| `build_manifest` | `build_id` | 建置時間、script version、row counts、驗證結果 |

`response_spectra` 儲存策略需在實作前以檔案大小測試決定：

- JSON array：表格較小，適合 Shiny 預覽與指定 period 查詢。
- Long table：SQL aggregation 較直覺，但資料列數約為 `records * components * damping * 111`，需確認 SQLite 大小與查詢速度。

初版建議同時建立：

- Canonical `response_spectra` JSON table。
- 常用 periods 的 materialized helper table，例如 0.01、0.2、1.0、3.0 秒，供 Shiny 統計與圖表快速使用。

### 3.4 SQLite views and indexes

建議建立 Shiny 專用 views：

| View | 用途 |
|---|---|
| `vw_events_map` | 震央地圖，含 EQID、名稱、座標、規模、時間、震源機制、record count |
| `vw_stations_map` | 測站地圖，含 SSN、名稱、座標、network、Vs30、record count |
| `vw_records_overview` | records table 預設欄位，避免直接載入所有 spectra |
| `vw_ground_motion_rotd50_d050` | 常用 GMPE 欄位與 5 percent RotD50 PGA/PGV/PGD/常用 PSA |
| `vw_summary_counts` | overview value boxes 與基本統計 |

建議 indexes：

```sql
CREATE INDEX idx_records_eqid ON records(eqid);
CREATE INDEX idx_records_station ON records(station_sequence_number);
CREATE INDEX idx_events_mechanism ON events(mechanism_class_simple);
CREATE INDEX idx_events_mag ON events(earthquake_magnitude);
CREATE INDEX idx_stations_network ON stations(network_id);
CREATE INDEX idx_paths_rjb ON paths(rjb_km);
CREATE INDEX idx_paths_rrup ON paths(campbell_r_dist_km);
CREATE INDEX idx_im_rsn_component_damping ON intensity_measures(rsn, component, damping_percent);
CREATE INDEX idx_spectra_rsn_component_damping ON response_spectra(rsn, component, damping_percent);
```

### 3.5 RDS outputs

RDS 應支援兩種使用情境：

1. R 使用者直接讀入 wide flatfile 進行 GMPE、統計或繪圖。
2. Shiny app 讀取小型 cache，以避免每次啟動都連接大型 Excel 或完整 RDS。

建議 `nga_west2_core_normalized.rds` 結構：

```r
list(
  events = data.table(...),
  event_sources = data.table(...),
  mechanism_classes = data.table(...),
  networks = data.table(...),
  stations = data.table(...),
  sites = data.table(...),
  paths = data.table(...),
  records = data.table(...),
  record_quality_flags = data.table(...),
  field_catalog = data.table(...),
  release_files = data.table(...)
)
```

保留每個原始 component/damping 的 wide flatfile RDS：

- 欄位名稱採 snake_case。
- attributes 保留原始 Excel 檔名、sheet name、damping、component、SHA-256、原始欄名對照。
- 不在 wide RDS 中移除 `-999`，但可提供 `na_codes = c(-999)` 說明。

另建立 Shiny cache：

```text
shiny-app/data/cache/
  events_map.rds
  stations_map.rds
  overview_counts.rds
  event_summary.rds
  station_summary.rds
  network_summary.rds
  motion_summary.rds
  rotd50_d050_common_periods.rds
```

### 3.6 資料處理文件

`docs/sqlite_usage.md` 需包含：

- SQLite 檔案位置與重建指令。
- schema diagram 或 table list。
- 常用 SQL 範例：查事件、測站、地圖點位、RotD50 PGA/PGV/PSA、距離與 Vs30 篩選。
- 缺值代碼、單位、damping 與 period 查詢方式。
- row counts、integrity check、SHA-256 驗證摘要。

`docs/rds_usage.md` 需包含：

- RDS 檔案清單與用途。
- `readRDS()` 範例。
- wide flatfile 欄位選取範例。
- core normalized list 的 join 範例。
- PSA wide-to-long 範例。
- Shiny cache 與完整 RDS 的差異。

`docs/data_processing_notes.md` 需包含：

- 原始 Excel 讀取與欄位清理規則。
- 欄位到資料表的 mapping。
- `-999`、blank、重複欄名、Excel 換行欄名處理方式。
- 使用報告 Appendix D/E 的欄位定義整理方式。
- 驗證清單與已知限制。

## 4. Shiny App 開發計畫

### 4.1 App backend strategy

採用 hybrid backend：

- SQLite：主要查詢、server-side tables、地圖進階篩選、資料下載。
- RDS cache：地圖初始資料、overview counts、常用 summary charts。
- Wide RDS：進階分析頁 lazy load，讓 R 使用者可以直接使用完整 flatfile 形狀。

不要在 app 啟動時讀取所有 Excel 或所有 wide RDS。

### 4.2 Project layout

```text
shiny-app/
  app.R
  R/
    db.R
    cache.R
    filters.R
    module_overview.R
    module_map.R
    module_tables.R
    module_stats.R
    module_analysis.R
    module_about.R
  data/
    cache/
  www/
  _brand.yml
```

建議套件：

- Core：`shiny`、`bslib`、`DBI`、`RSQLite`、`dplyr`、`dbplyr`、`data.table`。
- 地圖：`leaflet`、`leaflet.extras`。
- 表格：初版用 `DT` server-side；若摘要表需要較佳呈現，可加 `reactable`。
- 統計圖：`ggplot2`；需要 hover/zoom 時再使用 `plotly`。
- UX：`shinycssloaders`、`bsicons`、`memoise`、`cachem`。

### 4.3 Navigation

建議使用 `bslib::page_navbar()`：

1. Overview
2. Map
3. Tables
4. Statistics
5. Analysis
6. About

### 4.4 Overview page

顯示整體資料狀態：

- Events、stations、records、networks、damping levels、spectral periods。
- Records by component/damping。
- Events by mechanism class。
- Stations by network or data owner。
- Magnitude range、RJB/RRUP range、Vs30 range。

資料來源：

- 優先讀 `overview_counts.rds`。
- 若 cache 不存在，從 SQLite aggregation 即時計算並提示可重建 cache。

### 4.5 Interactive map

地圖需支援三種模式：

- 震央。
- 測站。
- 震央與測站。

必要 filters：

- 震源機制：normal、reverse、strike-slip、oblique、unknown；保留 original code 與 simple class。
- 資料來源：network/owner、station id prefix、recording type。
- 國家或區域：NGA-West2 flatfile 未明確提供完整 country 欄位時，初版可用事件名稱解析與測站座標反查的 derived country 欄位；需在文件標明 derived 欄位來源。
- 規模範圍。
- 年份或日期範圍。
- 距離範圍：RJB、RRUP/Campbell R、HypD、EpiD。
- Vs30 範圍與 measured/inferred class。
- Damping/component。

效能策略：

- 預設不顯示所有點，先用 marker clustering 且限制最大點數。
- 提供明確的 `Show all` 開關；開啟後先顯示估計點數。
- 對點位查詢只取地圖所需欄位。
- 對 5,000 點以上的結果使用 cluster 或 aggregated grid。
- 地圖 popup 只顯示精簡資訊，詳細資料連到 tables tab 的 filtered view。

### 4.6 Data tables

表格頁依 normalized schema 分組：

| Group | Tables |
|---|---|
| Earthquakes | `events`、`event_sources`、`mechanism_classes` |
| Stations and sites | `stations`、`sites`、`networks` |
| Paths | `paths`、`class2_distances` |
| Records | `records`、`record_quality_flags` |
| Ground motions | `intensity_measures`、`response_spectra` 或常用 period helper table |
| Documentation | `release_files`、`field_catalog`、`build_manifest` |

功能需求：

- 使用 `DT` server-side processing。
- 預設只顯示常用欄位，提供 advanced column selector。
- 支援依 map filters 同步篩選。
- 支援下載目前 filtered result，不下載整個大型 spectra table。
- 大型 spectra 不直接展開所有 periods；提供 period selector 後查詢。

### 4.7 Statistics page

初版統計圖表：

- Event counts by mechanism class。
- Event counts by year and magnitude bin。
- Station counts by network/owner。
- Station counts by Vs30 bin and measured/inferred class。
- Record counts by damping/component。
- Record counts by mechanism class and distance bin。
- RJB、RRUP、Vs30、magnitude histograms。
- PGA/PGV distribution for selected component/damping。
- PSA at selected periods distribution。

實作策略：

- counts 與 histograms 優先用 SQLite aggregation。
- 常用統計可保存於 `shiny-app/data/cache/*.rds`。
- `plotly` 僅用於需要 hover 或 zoom 的圖，避免全頁互動圖拖慢速度。

### 4.8 Analysis page

提供 R/GMPE 使用者的簡單互動分析：

- 選擇 component：RotD50 或 Vertical。
- 選擇 damping：0.5 到 30 percent；vertical 初版僅 5 percent。
- 選擇 periods：PGA、PGV、PGD、0.2s、1.0s、3.0s 或任一 period。
- 篩選 magnitude、RJB/RRUP、Vs30、mechanism、network。
- 預覽 wide flatfile 子集。
- 繪製 PGA/PGV/PSA 與 magnitude/distance/Vs30 的簡單散佈圖或分布圖。
- 匯出 filtered modeling subset。

此頁可 lazy load `output/rds/*_flatfile.rds`，並顯示 loading state 與記憶體提示。

### 4.9 About page

包含：

- 原始資料檔案清單。
- 報告引用與資料版本說明。
- SQLite/RDS usage docs 連結。
- 目前 app 使用的 SQLite/RDS/cache 檔案與 build time。
- 缺值代碼與 derived country/network 欄位限制。

## 5. 實作階段

### Phase 1: Input inspection and field mapping

- 建立 `scripts/inspect_nga_west2_inputs.R`。
- 讀取所有 Excel sheet、欄位、列數、SHA-256。
- 建立欄位 mapping draft，分成 source/site/path/record/intensity/spectra/quality。
- 從 Appendix D 整理欄位說明到 `field_catalog`。
- 輸出 `docs/data_processing_notes.md` 初版。

### Phase 2: SQLite builder

- 建立 `scripts/build_nga_west2_sqlite.py`。
- 讀入 5 percent RotD50 metadata 建立 normalized core tables。
- 讀入所有 damping flatfiles 建立 intensity 與 spectra tables。
- 建立 views、indexes、manifest 與驗證摘要。
- 撰寫 `docs/sqlite_usage.md`。

### Phase 3: RDS builder

- 建立 `scripts/build_nga_west2_rds.R`。
- 輸出 core normalized RDS。
- 輸出各 component/damping wide flatfile RDS。
- 輸出 RDS manifest。
- 建立 Shiny cache RDS。
- 撰寫 `docs/rds_usage.md`。

### Phase 4: Shiny skeleton and overview

- 建立 `shiny-app/` 架構。
- 實作 SQLite connection helper 與 cache loader。
- 建立 overview value boxes 與基本資料健康檢查。
- 加入 app README。

### Phase 5: Map and filters

- 建立 map module。
- 加入 mechanism、network/owner、country/region、magnitude、date、distance、Vs30 filters。
- 實作 marker clustering、point count safeguard、show-all mode。
- 支援點擊地圖後連動 tables filter。

### Phase 6: Tables and statistics

- 建立 server-side DT tables。
- 加入 table group selector 與 common/advanced columns。
- 建立 summary charts 與 histograms。
- 加入 filtered download。

### Phase 7: Analysis and polish

- 實作 wide RDS lazy loading。
- 加入 selected period plotting 與 modeling subset export。
- 補齊 loading/empty/error states。
- 測試 local run、常用查詢效能、地圖大量點位情境。

## 6. 驗證清單

資料驗證：

- SQLite `PRAGMA integrity_check` 為 `ok`。
- 5 percent RotD50 筆數應與 Excel RSN 數一致，目前初步盤點為 21,540。
- normalized events 數量應約 600。
- station sequence number 數量應約 4,151。
- 每個 damping file 的 RSN set 應一致；若不一致需寫入 validation report。
- `mechanism_code` 僅允許 0、1、2、3、4、-999、NULL。
- Spectral periods 應為 111 個。
- 每個 output 檔案建立 SHA-256。

Shiny 驗證：

- App 可在無網路環境啟動。
- Overview 不載入完整 wide RDS。
- Map 預設載入時間可接受，且 show-all 有明確提示。
- Tables 使用 server-side pagination。
- Statistics 使用 aggregation 或 cache，不直接 collect 大表。
- Analysis 頁 lazy load 後可產生至少 PGA、PGV、PSA 1.0s 的圖與匯出。

## 7. 已知限制與待確認事項

- NGA-West2 public flatfiles 是四個 metadata tables 的合併摘要，並非完整原始 database dump；normalized SQLite 是 application database，不應宣稱完全重建官方內部資料庫。
- 國家與觀測網分類可能需由 `Earthquake Name`、`Owner`、station id 或座標反查補強；此類 derived 欄位需保留方法說明與信心等級。
- Vertical 檔案只有 5 percent damping；app filter 需避免使用者選擇不存在的 vertical damping。
- Excel 欄名含重複名稱與換行，需以穩定欄名 mapping 控制，不可依 readxl 自動加上的 `...248` 等名稱作為永久 API。
- Spectra 的 JSON 或 long table 儲存方式需在 Phase 2 以實際 SQLite 大小與查詢效能決定。

## 8. 建議初版交付順序

1. 先完成 SQLite、RDS 與 usage docs。
2. 再完成 Shiny app skeleton、overview、map。
3. 接著完成 tables 與 statistics。
4. 最後加入 analysis 頁與資料匯出。

這個順序可以先讓資料模型穩定，再逐步增加互動介面，避免 Shiny app 被原始 Excel 的寬表與重複欄名綁住。

