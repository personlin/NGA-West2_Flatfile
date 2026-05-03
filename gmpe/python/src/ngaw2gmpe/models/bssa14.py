"""BSSA14 NGA-West2 GMPE."""
from __future__ import annotations

import math

from ngaw2gmpe.regions import region_code
from ngaw2gmpe.types import PredictionResult
from ngaw2gmpe.validation import applicability_warnings, workbook_missing

from . import _native


def bssa14(
    *,
    M: float,
    Rjb: float,
    Vs30: float,
    U: float = 0,
    RS: float = 0,
    NS: float = 0,
    Z1: float = 999,
    region: str | int | float | None = "global",
    period: float | None = None,
    T: float | None = None,
    **_: float,
) -> PredictionResult:
    """Return BSSA14 median and sigma."""
    t = float(period if period is not None else T)
    code = region_code(region)
    Z1 = workbook_missing(Z1)
    warnings = applicability_warnings("BSSA14", M=M, Rjb=Rjb, Vs30=Vs30, U=U, RS=RS, NS=NS, Z1=Z1)
    pgar = _native.pgar_calc(float(M), float(Rjb), float(U), float(RS), float(NS), code, 0)
    median = _native.bssa_14_raw(
        float(M), float(Rjb), float(U), float(RS), float(NS), float(Vs30), code, float(Z1), pgar, t
    )
    sigma = _native.bssa14_stdev_raw(float(M), float(Rjb), float(Vs30), t)
    return PredictionResult("BSSA14", t, median, math.log(median), sigma, warnings=warnings)


def pgar_calc(M: float, Rjb: float, U: float, RS: float, NS: float, region: str | int | float = "global") -> float:
    """Return BSSA14 reference PGA helper."""
    return _native.pgar_calc(float(M), float(Rjb), float(U), float(RS), float(NS), region_code(region), 0)


def dz1_calc(Vs30: float, Z1: float, region: str | int | float = "global") -> float:
    """Return BSSA14 basin-depth residual helper."""
    return _native.dz1_calc(float(Vs30), float(Z1), region_code(region), 0)
