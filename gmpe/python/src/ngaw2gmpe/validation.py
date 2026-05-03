"""Applicability checks mirroring workbook warning formulas."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


OPTIONAL_SENTINELS = {-999.0, 999.0}


def workbook_missing(value: Any, default: float = 999.0) -> float:
    """Return the workbook missing-value sentinel for optional numeric inputs."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if numeric in OPTIONAL_SENTINELS:
        return default
    return numeric


def _number(args: Mapping[str, Any], name: str, default: float | None = None) -> float | None:
    if name not in args or args[name] is None:
        return default
    try:
        return float(args[name])
    except (TypeError, ValueError):
        return default


def _outside(value: float | None, low: float, high: float) -> bool:
    return value is not None and (value < low or value > high)


def _missing(value: float | None) -> bool:
    return value is None or value in OPTIONAL_SENTINELS


def applicability_warnings(model: str, **kwargs: Any) -> tuple[str, ...]:
    """Return workbook-style applicability warnings for scalar inputs.

    These checks represent the warning formulas extracted from the workbook.
    They do not change the computed prediction; callers can decide whether to
    display, filter, or reject out-of-range cases.
    """
    name = model.upper()
    if name in {"IDRISS", "IDRISS14"}:
        name = "I14"

    warnings: list[str] = []
    m = _number(kwargs, "M")
    rrup = _number(kwargs, "Rrup")
    rjb = _number(kwargs, "Rjb")
    vs30 = _number(kwargs, "Vs30")

    if rrup is not None and rjb is not None and rrup < rjb:
        warnings.append("Rrup cannot be less than Rjb.")

    if name == "ASK14":
        if _outside(m, 3.0, 8.5):
            warnings.append("ASK14 magnitude is outside the workbook applicability range 3.0 to 8.5.")
        if _outside(rrup, 0.0, 300.0):
            warnings.append("ASK14 Rrup is outside the workbook applicability range 0 to 300 km.")
        if vs30 is not None and vs30 < 180:
            warnings.append("ASK14 Vs30 is below the workbook applicability minimum of 180 m/s.")
        elif vs30 is not None and vs30 > 1000:
            warnings.append("ASK14 Vs30 is outside the recommended workbook range; the workbook note says to use 760 m/s.")

    elif name == "BSSA14":
        ns = _number(kwargs, "NS", 0.0) or 0.0
        if _outside(m, 3.0, 8.5):
            warnings.append("BSSA14 magnitude is outside the workbook applicability range 3.0 to 8.5.")
        if ns == 1 and m is not None and m > 7.0:
            warnings.append("BSSA14 normal-fault magnitude is outside the workbook applicability maximum of 7.0.")
        if _outside(rjb, 0.0, 400.0):
            warnings.append("BSSA14 Rjb is outside the workbook applicability range 0 to 400 km.")
        if _outside(vs30, 150.0, 1500.0):
            warnings.append("BSSA14 Vs30 is outside the workbook applicability range 150 to 1500 m/s.")
        z1 = _number(kwargs, "Z1")
        if not _missing(z1) and _outside(z1, 0.0, 3.0):
            warnings.append("BSSA14 Z1 is outside the workbook applicability range 0 to 3 km.")

    elif name == "CB14":
        if _outside(m, 3.3, 8.5):
            warnings.append("CB14 magnitude is outside the workbook applicability range 3.3 to 8.5.")
        if _outside(rrup, 0.0, 300.0):
            warnings.append("CB14 Rrup is outside the workbook applicability range 0 to 300 km.")
        if _outside(vs30, 150.0, 1500.0):
            warnings.append("CB14 Vs30 is outside the workbook applicability range 150 to 1500 m/s.")
        fhw = _number(kwargs, "Fhw", 0.0) or 0.0
        if fhw == 1 and m is not None and m > 8.0:
            warnings.append("CB14 hanging-wall term is outside the workbook applicability maximum magnitude of 8.0.")
        dip = _number(kwargs, "dip")
        if _outside(dip, 15.0, 90.0):
            warnings.append("CB14 dip is outside the workbook applicability range 15 to 90 degrees.")
        ztor = _number(kwargs, "Ztor")
        if not _missing(ztor) and _outside(ztor, 0.0, 20.0):
            warnings.append("CB14 Ztor is outside the workbook applicability range 0 to 20 km.")
        z25 = _number(kwargs, "Z25")
        if not _missing(z25) and _outside(z25, 0.0, 20.0):
            warnings.append("CB14 Z25 is outside the workbook applicability range 0 to 20 km.")
        zhyp = _number(kwargs, "Zhyp")
        if not _missing(zhyp) and _outside(zhyp, 0.0, 10.0):
            warnings.append("CB14 Zhyp is outside the workbook applicability range 0 to 10 km.")

    elif name == "CY14":
        if _outside(m, 3.5, 8.5):
            warnings.append("CY14 magnitude is outside the workbook applicability range 3.5 to 8.5.")
        has_fault_flag = any((_number(kwargs, key, 0.0) or 0.0) == 1 for key in ("Frv", "Fnm", "Fhw"))
        if has_fault_flag and m is not None and m > 8.0:
            warnings.append("CY14 fault-specific terms are outside the workbook applicability maximum magnitude of 8.0.")
        if _outside(rrup, 0.0, 300.0):
            warnings.append("CY14 Rrup is outside the workbook applicability range 0 to 300 km.")
        if _outside(vs30, 180.0, 1500.0):
            warnings.append("CY14 Vs30 is outside the workbook applicability range 180 to 1500 m/s.")
        ztor = _number(kwargs, "Ztor")
        if not _missing(ztor) and ztor > 20.0:
            warnings.append("CY14 Ztor is outside the workbook applicability maximum of 20 km.")
        if rrup is not None and ztor is not None and not _missing(ztor) and rrup < ztor:
            warnings.append("CY14 Rrup cannot be less than Ztor.")

    elif name == "I14":
        if m is not None and m < 5.0:
            warnings.append("I14 magnitude is below the workbook applicability minimum of 5.0.")
        if rrup is not None and rrup > 150.0:
            warnings.append("I14 Rrup is above the workbook applicability maximum of 150 km.")
        if vs30 is not None and vs30 < 450.0:
            warnings.append("I14 Vs30 is below the workbook applicability minimum of 450 m/s.")

    return tuple(warnings)
