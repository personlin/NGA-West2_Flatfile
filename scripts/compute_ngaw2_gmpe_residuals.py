#!/usr/bin/env python3
"""Compute NGA-West2 observed/predicted GMPE residuals from the SQLite view."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from ngaw2gmpe import predict_dataframe


DEFAULT_DB = Path("output/sqlite/nga_west2.sqlite")


def psa_column(period: float) -> str:
    if period == 0:
        return "pga_g"
    return f"psa_{str(period).replace('.', '_')}_s".replace("_0_s", "_s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_DB)
    parser.add_argument("--model", required=True, choices=["ASK14", "BSSA14", "CB14", "CY14", "I14"])
    parser.add_argument("--period", type=float, required=True)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    observed_col = psa_column(args.period)
    query = f"""
      SELECT *
      FROM vw_ground_motion_rotd50_d050
      WHERE {observed_col} > 0
        AND earthquake_magnitude > 0
        AND rrup_km > 0
        AND rjb_km >= 0
        AND vs30_m_s > 0
      LIMIT ?
    """
    with sqlite3.connect(args.sqlite) as con:
        df = pd.read_sql_query(query, con, params=(args.limit,))

    pred = predict_dataframe(
        df,
        args.model,
        [args.period],
        column_map={"rrup_km": "Rrup", "rjb_km": "Rjb", "rx_km": "Rx", "vs30_m_s": "Vs30"},
    )
    out = pd.concat([df.reset_index(drop=True), pred.reset_index(drop=True)], axis=1)
    out["observed"] = out[observed_col]
    out["ln_observed"] = out["observed"].map(lambda x: __import__("math").log(x))
    out["residual_ln"] = out["ln_observed"] - out["ln_median"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out)} residual rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
