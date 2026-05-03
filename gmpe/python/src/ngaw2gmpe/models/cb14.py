"""CB14 NGA-West2 GMPE."""
from __future__ import annotations

import math

from ngaw2gmpe.coefficients import load_coefficients
from ngaw2gmpe.regions import region_code
from ngaw2gmpe.types import PredictionResult
from ngaw2gmpe.validation import applicability_warnings, workbook_missing

from . import _native


def _cb_coeffs(period: float) -> dict[str, float]:
    lookup = 0.001 if float(period) == 0 else float(period)
    rows = load_coefficients("CB14")
    rows = rows[abs(rows["period_s"].astype(float) - lookup) < 1e-9].copy()
    rows["source_col"] = rows["source_cell"].str.extract(r"([A-Z]+)")[0].map(
        lambda label: sum((ord(ch) - 64) * 26**idx for idx, ch in enumerate(reversed(label)))
    )
    out = {}
    for _, row in rows.sort_values("source_col").iterrows():
        value = row["value"]
        if str(value) == "nan":
            value = row["cached_value"]
        out[row["coefficient"]] = float(value)
    return out


def _mag_interp(M: float, low: float, high: float) -> float:
    if M < 4.5:
        return low
    if M > 5.5:
        return high
    return high + (low - high) * (5.5 - M) * (5.5 - 4.5)


def _cb_sigma(M: float, Vs30: float, a1100: float, period: float) -> tuple[float, float, float]:
    c = _cb_coeffs(period)
    pga = _cb_coeffs(0)
    q = 0.0
    if Vs30 < c["k1"]:
        q = c["k2"] * a1100 * (
            (a1100 + c["c"] * (Vs30 / c["k1"]) ** c["n"]) ** -1 - (a1100 + c["c"]) ** -1
        )
    phi_base = _mag_interp(M, c["f1"], c["f2"])
    tau_base = _mag_interp(M, c["t1"], c["t2"])
    phi_pga = _mag_interp(M, pga["f1"], pga["f2"])
    tau_pga = _mag_interp(M, pga["t1"], pga["t2"])
    phi = math.sqrt(
        (phi_base**2 - c["flnAF"] ** 2)
        + c["flnAF"] ** 2
        + q**2 * (phi_pga**2 - pga["flnAF"] ** 2)
        + 2
        * q
        * c["rlnPGA,lnY"]
        * math.sqrt(max(phi_base**2 - c["flnAF"] ** 2, 0))
        * math.sqrt(max(phi_pga**2 - pga["flnAF"] ** 2, 0))
    )
    tau = math.sqrt(tau_base**2 + q**2 * tau_pga**2 + 2 * q * c["rlnPGA,lnY"] * tau_base * tau_pga)
    sigma = math.sqrt(c["fC"] ** 2 + phi**2 + tau**2)
    return sigma, tau, phi


def cb14(
    *,
    M: float,
    Rrup: float,
    Rjb: float,
    Rx: float = 0,
    Frv: float = 0,
    Fnm: float = 0,
    Fhw: float = 0,
    Ztor: float = 999,
    W: float = 999,
    dip: float = 90,
    Vs30: float = 760,
    Z25: float = 999,
    Zhyp: float = 999,
    Ztord: float = 999,
    Wd: float = 999,
    Zhypd: float = 999,
    A: float = 0,
    region: str | int | float | None = "global",
    period: float | None = None,
    T: float | None = None,
    **_: float,
) -> PredictionResult:
    """Return CB14 median and approximate workbook sigma."""
    t = float(period if period is not None else T)
    code = region_code(region)
    Ztor = workbook_missing(Ztor)
    W = workbook_missing(W)
    Z25 = workbook_missing(Z25)
    Zhyp = workbook_missing(Zhyp)
    Ztord = workbook_missing(Ztord)
    Wd = workbook_missing(Wd)
    Zhypd = workbook_missing(Zhypd)
    warnings = applicability_warnings(
        "CB14", M=M, Rrup=Rrup, Rjb=Rjb, Vs30=Vs30, Fhw=Fhw, dip=dip, Ztor=Ztor, Z25=Z25, Zhyp=Zhyp
    )
    a1100 = _native.a1100_cb(
        float(M), float(Rrup), float(Rjb), float(Rx), float(Frv), float(Fnm), float(Fhw),
        float(W), float(dip), float(Ztor), float(Z25), float(Zhyp),
        float(Ztord), float(Wd), float(Zhypd), code, 0,
    )
    median = _native.cb_14_raw(
        float(M), float(Rrup), float(Rjb), float(Rx), float(Frv), float(Fnm), float(Fhw),
        float(Ztor), float(W), float(dip), float(Vs30), float(Z25), float(Zhyp),
        float(Ztord), float(Wd), float(Zhypd), code, float(A), t,
    )
    sigma, tau, phi = _cb_sigma(float(M), float(Vs30), a1100, t)
    return PredictionResult("CB14", t, median, math.log(median), sigma, tau=tau, phi=phi, warnings=warnings)


def a1100_cb(**kwargs: float) -> float:
    """Return CB14 A1100 helper using CB14 keyword arguments."""
    code = region_code(kwargs.get("region", "global"))
    return _native.a1100_cb(
        float(kwargs["M"]), float(kwargs["Rrup"]), float(kwargs["Rjb"]), float(kwargs["Rx"]),
        float(kwargs.get("Frv", 0)), float(kwargs.get("Fnm", 0)), float(kwargs.get("Fhw", 0)),
        float(kwargs.get("W", 999)), float(kwargs.get("dip", 90)), float(kwargs.get("Ztor", 999)),
        float(kwargs.get("Z25", 999)), float(kwargs.get("Zhyp", 999)), float(kwargs.get("Ztord", 999)),
        float(kwargs.get("Wd", 999)), float(kwargs.get("Zhypd", 999)), code, 0,
    )
