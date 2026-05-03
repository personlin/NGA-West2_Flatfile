"""CY14 NGA-West2 GMPE."""
from __future__ import annotations

import math

from ngaw2gmpe.regions import region_code
from ngaw2gmpe.types import PredictionResult
from ngaw2gmpe.validation import applicability_warnings, workbook_missing

from . import _native


def cy14(
    *,
    M: float,
    Rrup: float,
    Rjb: float,
    Rx: float = 0,
    Vs30: float,
    Frv: float = 0,
    Fnm: float = 0,
    Fhw: float = 0,
    dip: float = 90,
    Ztor: float = 999,
    Z1: float = 999,
    Z1r: float = 999,
    DDPP: float = 0,
    Vs30flag: float = 0,
    region: str | int | float | None = "global",
    period: float | None = None,
    T: float | None = None,
    **_: float,
) -> PredictionResult:
    """Return CY14 median and sigma."""
    t = float(period if period is not None else T)
    code = region_code(region)
    Ztor = workbook_missing(Ztor)
    Z1 = workbook_missing(Z1)
    Z1r = workbook_missing(Z1r)
    warnings = applicability_warnings(
        "CY14", M=M, Rrup=Rrup, Rjb=Rjb, Vs30=Vs30, Frv=Frv, Fnm=Fnm, Fhw=Fhw, Ztor=Ztor
    )
    median = _native.cy_14_raw(
        float(M), float(Rrup), float(Rjb), float(Rx), float(Vs30), float(Frv), float(Fnm),
        float(Fhw), float(dip), float(Ztor), code, float(Z1), float(Z1r), float(DDPP), t,
    )
    sigma = _native.cy14_stdev_raw(
        float(M), float(Rrup), float(Rjb), float(Rx), float(Vs30), float(Frv), float(Fnm),
        float(Fhw), float(dip), float(Ztor), code, float(Z1), float(DDPP), float(Vs30flag), t,
    )
    return PredictionResult("CY14", t, median, math.log(median), sigma, warnings=warnings)
