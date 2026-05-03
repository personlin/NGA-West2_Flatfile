"""Batch prediction helpers for NGA-West2 flatfile workflows."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from .models import ask14, bssa14, cb14, cy14, idriss14


DEFAULT_COLUMN_MAP = {
    "earthquake_magnitude": "M",
    "campbell_r_dist_km": "Rrup",
    "joyner_boore_dist_km": "Rjb",
    "rx": "Rx",
    "vs30_m_s_selected_for_analysis": "Vs30",
    "depth_to_top_of_fault_rupture_model": "Ztor",
    "fault_rupture_width_km": "W",
    "dip_deg": "dip",
    "hypocenter_depth_km": "Zhyp",
}

MODEL_FUNCTIONS = {
    "ASK14": ask14,
    "BSSA14": bssa14,
    "CB14": cb14,
    "CY14": cy14,
    "I14": idriss14,
    "IDRISS14": idriss14,
}


def predict_dataframe(
    df: pd.DataFrame,
    model: str,
    periods: Iterable[float],
    column_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Return tidy predictions for rows in a dataframe."""
    fn = MODEL_FUNCTIONS[model.upper()]
    mapping = {**DEFAULT_COLUMN_MAP, **(column_map or {})}
    out: list[dict[str, Any]] = []
    for index, row in df.iterrows():
        base = {target: row[source] for source, target in mapping.items() if source in row.index}
        for period in periods:
            result = fn(**base, period=period)
            out.append(
                {
                    "row_index": index,
                    "model": result.model,
                    "period_s": result.period,
                    "median": result.median,
                    "ln_median": result.ln_median,
                    "sigma": result.sigma,
                    "tau": result.tau,
                    "phi": result.phi,
                    "warnings": "; ".join(result.warnings),
                }
            )
    return pd.DataFrame(out)
