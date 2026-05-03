# NGA-West2 SQLite Database Usage

本資料庫由本專案 `data/` 中的 NGA-West2 public flatfiles 建立。它依據 Ancheta et al. (2013) 報告對四個 metadata tables 的說明，將 flatfile 反向整理為較適合查詢與 Shiny app 使用的 normalized application database。

輸出檔案：

```text
output/sqlite/nga_west2.sqlite
```

## 建置

```bash
Rscript scripts/inspect_nga_west2_inputs.R
Rscript scripts/build_nga_west2_sqlite.R
Rscript scripts/validate_nga_west2_outputs.R
```

也可使用相容入口：

```bash
python3 scripts/build_nga_west2_sqlite.py
```

## 資料表

| Table | 說明 |
|---|---|
| `release_files` | 原始 Excel 檔案、component、damping、sheet、row/column count、SHA-256 |
| `field_catalog` | 5% RotD50 flatfile 欄位名稱、clean name、欄位群組 |
| `damping_levels` | RotD50 11 個 damping levels 與 vertical 5% |
| `spectral_periods` | 111 個 response spectrum periods |
| `mechanism_classes` | mechanism code 對應 strike-slip、normal、reverse、oblique、unknown |
| `events`, `event_sources` | 地震事件與震源幾何、finite rupture、mechanism metadata |
| `networks`, `stations`, `sites` | 測網/owner、測站與場址條件 |
| `records`, `record_quality_flags` | RSN、檔名、processing/filter metadata、quality flags |
| `paths`, `class2_distances` | RJB/RRUP/Rx/Ry/directivity 與 C1/C2 distances |
| `intensity_measures` | 每個 RSN + component + damping 的 PGA、PGV、PGD |
| `response_spectra` | 每個 RSN + component + damping 的 111-period PSA JSON array |
| `response_spectra_common_periods` | Shiny 常用 period helper table |
| `build_manifest` | 建置時間、row counts、integrity check |

## Views

| View | 用途 |
|---|---|
| `vw_events_map` | 震央地圖與 event filters |
| `vw_stations_map` | 測站地圖與 station/network filters |
| `vw_records_overview` | records table 的常用欄位 |
| `vw_ground_motion_rotd50_d050` | 5% RotD50 常用 GMPE 欄位與 PGA/PGV/PSA |

## SQL 範例

資料量與 integrity：

```sql
SELECT * FROM build_manifest;
PRAGMA integrity_check;
```

查 5% RotD50 常用欄位：

```sql
SELECT
  rsn,
  earthquake_name,
  earthquake_magnitude,
  mechanism_class_simple,
  station_name,
  rjb_km,
  rrup_km,
  vs30_m_s,
  pga_g,
  pgv_cm_sec,
  psa_1_s
FROM vw_ground_motion_rotd50_d050
WHERE earthquake_magnitude >= 6.5
  AND rjb_km BETWEEN 0 AND 50
LIMIT 20;
```

查地圖點位：

```sql
SELECT eqid, earthquake_name, hypocenter_latitude, hypocenter_longitude, earthquake_magnitude
FROM vw_events_map
WHERE mechanism_class_simple = 'reverse';
```

查某個 period 的 JSON PSA：

```sql
WITH axis AS (
  SELECT period_id - 1 AS json_index
  FROM spectral_periods
  WHERE period_s = 1.0
)
SELECT
  rs.rsn,
  json_extract(rs.psa_json, '$[' || axis.json_index || ']') AS psa_1s
FROM response_spectra rs
CROSS JOIN axis
WHERE rs.component = 'RotD50'
  AND rs.damping_percent = 5
LIMIT 20;
```

## 注意事項

- SQLite 是由 public flatfiles 建立的 application database，不是官方完整內部 database dump。
- `-999` 等官方缺值代碼原樣保存；分析時可自行轉為 `NULL` 或 `NA`。
- `event_region_derived` 與 `station_region_derived` 是瀏覽輔助欄位，分別由 event name keywords 與粗略座標範圍推估，不是官方 metadata。
- `response_spectra` 使用 JSON array 保存 111 個 PSA values，以避免建立過大的 long table。

