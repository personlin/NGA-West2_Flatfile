#!/usr/bin/env python3
"""Compatibility wrapper for the R-based NGA-West2 SQLite builder."""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    cmd = ["Rscript", "scripts/build_nga_west2_sqlite.R"]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())

