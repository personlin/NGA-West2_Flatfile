# NGA-West2 Data Processing Notes

## Source Files

本專案處理 12 個 Excel flatfiles：

- 11 個 RotD50 damping files：0.5、1、2、3、5、7、10、15、20、25、30 percent。
- 1 個 vertical 5 percent damping file。

每個檔案目前皆為 21,540 rows；RotD50 files 為 274 columns，vertical file 為 276 columns。

## Processing Scripts

| Script | 用途 |
|---|---|
| `scripts/inspect_nga_west2_inputs.R` | 建立 input file manifest 與欄位 catalog draft |
| `scripts/build_nga_west2_sqlite.R` | 建立 normalized SQLite、views、indexes、Shiny cache |
| `scripts/build_nga_west2_sqlite.py` | 呼叫 R SQLite builder 的相容 wrapper |
| `scripts/build_nga_west2_rds.R` | 建立 core normalized RDS 與 wide flatfile RDS |
| `scripts/validate_nga_west2_outputs.R` | SQLite integrity 與資料量驗證 |

## Column Cleaning

Excel 欄名處理規則：

1. 將換行、標點、括號與單位轉為 `_`。
2. 轉為小寫 snake_case。
3. 重複欄名以 `make.unique(..., sep = "_")` 產生穩定後綴。
4. 原始欄名保留於 `field_catalog$original_name` 與 RDS attributes。

範例：

| Original | Clean |
|---|---|
| `Record Sequence Number` | `record_sequence_number` |
| `Earthquake Magnitude` | `earthquake_magnitude` |
| `Joyner-Boore Dist. (km)` | `joyner_boore_dist_km` |
| `T1.000S` | `t1_000s` |

## Normalization Rules

- 以 5% RotD50 flatfile 建立 canonical event/station/site/path/record metadata。
- 以 `EQID` 建立 `events` 與 `event_sources`。
- 以 `Station Sequence Number` 建立 `stations` 與 `sites`。
- 以 `Record Sequence Number` 建立 `records`、`paths`、`record_quality_flags`。
- 所有 RotD50 damping files 與 vertical 5% file 皆寫入 `intensity_measures` 與 `response_spectra`。
- 111 個 PSA periods 寫入 `spectral_periods`，每筆 response spectrum 以 JSON array 保存。

## Mechanism Classification

`Mechanism Based on Rake Angle` 依報告 Appendix D 對應：

| Code | Original | Simple |
|---|---|---|
| 0 | strike-slip | strike-slip |
| 1 | normal | normal |
| 2 | reverse | reverse |
| 3 | reverse-oblique | oblique |
| 4 | normal-oblique | oblique |
| -999 / blank | unknown | unknown |

## Derived Region Fields

`event_region_derived` 由 earthquake name keyword 推估。`station_region_derived` 由 broad latitude/longitude bounding boxes 推估。這兩個欄位只作為 Shiny map filters 的瀏覽輔助，不應取代官方 metadata。

## Missing Values

官方缺值代碼如 `-999` 原樣保存。SQLite views 目前不自動轉為 `NULL`，以避免改變原始 public flatfile 語意。分析程式可視需求轉換。

## Validation Summary

目前建置結果：

```text
events: 600
stations: 4151
records: 21540
intensity_measures: 258480
response_spectra: 258480
spectral_periods: 111
SQLite integrity_check: ok
```

