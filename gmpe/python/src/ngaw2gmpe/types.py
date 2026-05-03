"""Shared return types for NGA-West2 GMPE predictions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionResult:
    """Scalar GMPE prediction result."""

    model: str
    period: float
    median: float
    ln_median: float
    sigma: float
    tau: float | None = None
    phi: float | None = None
    warnings: tuple[str, ...] = ()
