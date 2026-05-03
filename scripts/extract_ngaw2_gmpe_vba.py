#!/usr/bin/env python3
"""Extract the NGA-West2 GMPE VBA project for local audit use only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import zipfile
from pathlib import Path


WORKBOOK = Path("data/NGAW2_GMPE_Spreadsheets_v5.7_041415_ProtectedLocked.xlsm")
OUT_DIR = Path("output/gmpe_vba")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def extract_with_olevba(vba_bin: Path, out_dir: Path) -> list[Path]:
    try:
        from oletools.olevba import VBA_Parser
    except ImportError as exc:
        raise RuntimeError("oletools.olevba is required to export readable VBA source.") from exc

    parser = VBA_Parser(str(vba_bin))
    exported: list[Path] = []
    for _, stream_path, file_name, source in parser.extract_macros():
        if not source.strip():
            continue
        path = out_dir / file_name
        path.write_text(source, encoding="utf-8")
        exported.append(path)
    parser.close()
    return exported


def write_manifest(paths: list[Path], manifest_path: Path) -> None:
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["stream_path", "exported_file", "line_count", "function_names", "sha256"],
        )
        writer.writeheader()
        for path in sorted(paths):
            text = path.read_text(encoding="utf-8", errors="replace")
            functions = re.findall(r"(?im)^\s*(?:Public |Private )?(?:Function|Sub)\s+([A-Za-z0-9_]+)", text)
            writer.writerow(
                {
                    "stream_path": "xl/vbaProject.bin",
                    "exported_file": str(path),
                    "line_count": text.count("\n") + 1,
                    "function_names": ";".join(functions),
                    "sha256": sha256(path),
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=WORKBOOK)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    vba_bin = args.out_dir / "vbaProject.bin"
    with zipfile.ZipFile(args.workbook) as zf:
        zf.extract("xl/vbaProject.bin", args.out_dir)
    extracted = args.out_dir / "xl" / "vbaProject.bin"
    extracted.replace(vba_bin)
    try:
        (args.out_dir / "xl").rmdir()
    except OSError:
        pass

    exported = extract_with_olevba(vba_bin, args.out_dir)
    write_manifest(exported, args.out_dir / "vba_manifest.csv")
    print(f"Wrote audit-only VBA export to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
