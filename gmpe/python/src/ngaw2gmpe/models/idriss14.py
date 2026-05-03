"""Idriss 2014 NGA-West2 GMPE."""
from __future__ import annotations

import math

from ngaw2gmpe.types import PredictionResult
from ngaw2gmpe.validation import applicability_warnings

from . import _native


def idriss14(
    *,
    M: float,
    Rrup: float,
    Vs30: float,
    F: float = 0,
    period: float | None = None,
    T: float | None = None,
    **_: float,
) -> PredictionResult:
    """Return Idriss 2014 median and sigma."""
    t = float(period if period is not None else T)
    warnings = applicability_warnings("I14", M=M, Rrup=Rrup, Vs30=Vs30)
    median = _native.i_14_raw(float(M), float(Rrup), float(F), float(Vs30), t)
    sigma = _native.i_14_stdev_raw(float(M), t)
    return PredictionResult("I14", t, median, math.log(median), sigma, warnings=warnings)
