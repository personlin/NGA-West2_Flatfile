"""Small shared utilities for NGA-West2 GMPE APIs."""
from __future__ import annotations


def period_key(period: float | int | str) -> str:
    """Return the stable key used for PGA, PGV, and SA periods."""
    value = float(period)
    if value == 0:
        return "pga"
    if value == -1:
        return "pgv"
    sign = "m" if value < 0 else "p"
    return f"{sign}{abs(value):.3f}".replace(".", "p")

