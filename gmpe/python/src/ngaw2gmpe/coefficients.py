"""Coefficient loading utilities for NGA-West2 GMPE models."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd


MODELS = ("ASK14", "BSSA14", "CB14", "CY14", "I14")
CSV_SCHEMA = (
    "model",
    "period_s",
    "period_key",
    "imt",
    "row_index",
    "coefficient",
    "value",
    "cached_value",
    "formula",
    "source_sheet",
    "source_cell",
    "source_workbook",
)


def coefficients_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "coefficients"


def normalize_model(model: str) -> str:
    name = model.upper()
    aliases = {"IDRISS14": "I14", "IDRISS": "I14"}
    name = aliases.get(name, name)
    if name not in MODELS:
        raise ValueError(f"Unknown GMPE model: {model}")
    return name


@lru_cache(maxsize=None)
def load_coefficients(model: str) -> pd.DataFrame:
    """Load one model's normalized coefficient table."""
    name = normalize_model(model)
    path = coefficients_dir() / f"{name.lower()}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    data = pd.read_csv(path)
    missing = [col for col in CSV_SCHEMA if col not in data.columns]
    if missing:
        raise ValueError(f"Coefficient file {path} is missing columns: {missing}")
    return data.loc[:, CSV_SCHEMA].copy()


def available_periods(model: str) -> list[float]:
    """Return sorted period values available for a model."""
    data = load_coefficients(model)
    return sorted(data["period_s"].dropna().astype(float).unique().tolist())

