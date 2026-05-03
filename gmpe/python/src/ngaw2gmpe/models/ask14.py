"""ASK14 NGA-West2 GMPE."""
from __future__ import annotations

import math

from ngaw2gmpe.regions import region_code
from ngaw2gmpe.types import PredictionResult
from ngaw2gmpe.validation import applicability_warnings, workbook_missing

from . import _native


def ask14(
    *,
    M: float,
    Rrup: float,
    Rjb: float,
    Rx: float = 0,
    Frv: float = 0,
    Fnm: float = 0,
    Fhw: float = 0,
    FAS: float = 0,
    Ztor: float = 999,
    W: float = 999,
    dip: float = 90,
    Vs30: float = 760,
    Vs30flag: float = 0,
    Z1: float = 999,
    Ry0: float = 999,
    region: str | int | float | None = "global",
    period: float | None = None,
    T: float | None = None,
    **_: float,
) -> PredictionResult:
    """Return ASK14 median and sigma."""
    t = float(period if period is not None else T)
    code = region_code(region)
    Ztor = workbook_missing(Ztor)
    W = workbook_missing(W)
    Z1 = workbook_missing(Z1)
    Ry0 = workbook_missing(Ry0)
    warnings = applicability_warnings(
        "ASK14", M=M, Rrup=Rrup, Rjb=Rjb, Vs30=Vs30, Ztor=Ztor, W=W, Z1=Z1, Ry0=Ry0
    )
    median = _native.ask_14_raw(
        float(M), float(Rrup), float(Rjb), float(Rx), float(Frv), float(Fnm), float(Fhw),
        float(FAS), float(Ztor), float(W), float(dip), float(Vs30), float(Vs30flag),
        float(Z1), float(Ry0), code, t,
    )
    sigma = _native.ask14_stdev_raw(
        float(M), float(Rrup), float(Rjb), float(Rx), float(Frv), float(Fnm), float(Fhw),
        float(FAS), float(Ztor), float(W), float(dip), float(Vs30), float(Vs30flag),
        float(Z1), float(Ry0), code, t,
    )
    return PredictionResult("ASK14", t, median, math.log(median), sigma, warnings=warnings)


def ask14_z1(Vs30: float, region: str | int | float = "global", Z1: float = 999) -> float:
    """Return ASK14 basin-depth helper."""
    return _native.ask14_z1(float(Vs30), region_code(region), float(Z1))
