"""Region-code helpers matching the NGA-West2 GMPE workbook conventions."""
from __future__ import annotations


REGION_CODES = {
    "global": 0,
    "california": 0,
    "ca": 0,
    "taiwan": 0,
    "tw": 0,
    "new_zealand": 0,
    "nz": 0,
    "japan": 1,
    "jp": 1,
    "china": 3,
    "ch": 3,
    "italy": 4,
    "it": 4,
    "turkey": 5,
    "tur": 5,
}


def region_code(region: str | int | float | None) -> int:
    """Return the workbook numeric region code."""
    if region is None:
        return 0
    if isinstance(region, (int, float)):
        return int(region)
    key = region.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in REGION_CODES:
        raise ValueError(f"Unknown GMPE region: {region}")
    return REGION_CODES[key]

