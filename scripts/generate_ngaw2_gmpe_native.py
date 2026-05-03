#!/usr/bin/env python3
"""Generate native Python and R GMPE equations from audit-only VBA source.

The generated runtime module does not read or depend on VBA files.  VBA is used
only as a local porting reference to produce native source code.
"""
from __future__ import annotations

import argparse
import keyword
import re
from pathlib import Path


FUNC_RE = re.compile(r"(?ims)^Function\s+(\w+)\((.*?)\)\s*(.*?)(?=^End Function)", re.M)
MODEL_MAP = {
    "ASK14_Coeffs": "ASK14",
    "BSSA14_Coeffs": "BSSA14",
    "CB14_Coeffs": "CB14",
    "CY14_Coeffs": "CY14",
    "I14_Coeffs": "I14",
}
MATH_FUNCS = {
    "log": "math.log",
    "exp": "math.exp",
    "sqr": "math.sqrt",
    "sin": "math.sin",
    "cos": "math.cos",
    "tan": "math.tan",
    "atn": "math.atan",
    "abs": "abs",
}
R_MATH_FUNCS = {
    "log": "log",
    "exp": "exp",
    "sqr": "sqrt",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "atn": "atan",
    "abs": "abs",
}
FUNC_NAMES = {
    "A1100_CB": "a1100_cb",
    "CB_14": "cb_14_raw",
    "CY_14": "cy_14_raw",
    "CY14_stdev": "cy14_stdev_raw",
    "ASK_14": "ask_14_raw",
    "ASK14_Z1": "ask14_z1",
    "ASK14_stdev": "ask14_stdev_raw",
    "BSSA_14": "bssa_14_raw",
    "BSSA14_stdev": "bssa14_stdev_raw",
    "PGAr_calc": "pgar_calc",
    "dz1_calc": "dz1_calc",
    "I_14": "i_14_raw",
    "I_14_stdev": "i_14_stdev_raw",
}
MODULE_ORDER = [
    "Module5.bas",
    "Module6.bas",
    "Module7.bas",
    "Module4.bas",
    "Module1.bas",
    "Module2.bas",
    "Module3.bas",
]


def clean_comment(line: str) -> str:
    out = []
    in_quote = False
    for ch in line:
        if ch == '"':
            in_quote = not in_quote
        if ch == "'" and not in_quote:
            break
        out.append(ch)
    return "".join(out).strip()


def join_continuations(lines: list[str]) -> list[str]:
    out: list[str] = []
    buf = ""
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith("_"):
            buf += stripped[:-1] + " "
            continue
        out.append(buf + line)
        buf = ""
    if buf:
        out.append(buf)
    return out


def norm_ident(name: str) -> str:
    out = name.lower()
    if out == "del":
        out = "delta"
    if out == "lambda":
        out = "lambda_"
    if keyword.iskeyword(out):
        out += "_"
    return out


def expr(text: str) -> str:
    out = text.strip().replace("#", "")
    out = re.sub(r"(?i)^mz1\s*=\s*mz1\s*=\s*", "", out)
    out = re.sub(r"\bAnd\b", "and", out, flags=re.I)
    out = re.sub(r"\bOr\b", "or", out, flags=re.I)
    out = re.sub(r"\bNot\b", "not", out, flags=re.I)
    out = out.replace("<>", "!=")
    out = re.sub(r"(?<![<>!=])=(?!=)", "==", out)
    out = out.replace("^", "**")
    out = re.sub(r"\bCof\((\d+)\)", r"cof[\1]", out, flags=re.I)
    for vb_name, py_name in FUNC_NAMES.items():
        out = re.sub(r"\b" + re.escape(vb_name) + r"\b", py_name, out, flags=re.I)

    parts = re.split(r'("[^"]*")', out)
    for idx, part in enumerate(parts):
        if idx % 2:
            continue

        def repl(match: re.Match[str]) -> str:
            token = match.group(0)
            low = token.lower()
            if low in MATH_FUNCS:
                return MATH_FUNCS[low]
            if low in {"min", "max"}:
                return low
            if token in {"and", "or", "not"}:
                return token
            return norm_ident(token)

        parts[idx] = re.sub(r"\b[A-Za-z_]\w*\b", repl, part)
    return "".join(parts).replace("math.math.", "math.")


def r_expr(text: str) -> str:
    out = text.strip().replace("#", "")
    out = re.sub(r"(?i)^mz1\s*=\s*mz1\s*=\s*", "", out)
    out = re.sub(r"\bAnd\b", "&&", out, flags=re.I)
    out = re.sub(r"\bOr\b", "||", out, flags=re.I)
    out = re.sub(r"\bNot\b", "!", out, flags=re.I)
    out = out.replace("<>", "!=")
    out = re.sub(r"(?<![<>!=])=(?!=)", "==", out)
    out = re.sub(
        r"\bCof\((\d+)\)",
        lambda match: f"cof[[{int(match.group(1)) + 1}]]",
        out,
        flags=re.I,
    )
    for vb_name, native_name in FUNC_NAMES.items():
        out = re.sub(r"\b" + re.escape(vb_name) + r"\b", native_name, out, flags=re.I)

    parts = re.split(r'("[^"]*")', out)
    for idx, part in enumerate(parts):
        if idx % 2:
            continue

        def repl(match: re.Match[str]) -> str:
            token = match.group(0)
            low = token.lower()
            if low in R_MATH_FUNCS:
                return R_MATH_FUNCS[low]
            if low in {"min", "max"}:
                return low
            return norm_ident(token)

        parts[idx] = re.sub(r"\b[A-Za-z_]\w*\b", repl, part)
    return "".join(parts)


def select_has_range(lines: list[str], idx: int) -> bool:
    for line in lines[idx + 1 :]:
        cleaned = clean_comment(line).lower()
        if cleaned.startswith("end select"):
            return False
        if "range(" in cleaned:
            return True
    return False


def lhs_names(body: str) -> list[str]:
    names: set[str] = set()
    for raw in join_continuations(body.splitlines()):
        line = clean_comment(raw)
        match = re.match(r"([A-Za-z_]\w*)\s*=\s*", line)
        if not match:
            continue
        name = match.group(1)
        if name.lower() not in {key.lower() for key in FUNC_NAMES} and not name.lower().startswith("cof"):
            names.add(norm_ident(name))
    return sorted(names)


def coefficient_model(body: str) -> str | None:
    match = re.search(r'Range\("(\w+_Coeffs)!', body)
    if not match:
        return None
    return MODEL_MAP[match.group(1)]


def translate_function(vb_name: str, args: str, body: str) -> str:
    py_name = FUNC_NAMES[vb_name]
    arglist = [norm_ident(arg.strip()) for arg in args.replace("\n", " ").split(",") if arg.strip()]
    lines = [f"def {py_name}({', '.join(arglist)}):"]
    init = [name for name in lhs_names(body) if name not in set(arglist)]
    for chunk_start in range(0, len(init), 8):
        chunk = init[chunk_start : chunk_start + 8]
        lines.append("    " + ", ".join(chunk) + " = " + ", ".join(["0"] * len(chunk)))
    model = coefficient_model(body)
    if model:
        lines.append(f"    cof = _cof({model!r}, t)")

    raw_lines = join_continuations(body.splitlines())
    indent = 1
    in_select = False
    skip_select = False
    select_var = ""
    first_case = True

    for idx, raw_line in enumerate(raw_lines):
        line = clean_comment(raw_line)
        if not line:
            continue
        low = line.lower().strip()
        if low.startswith(("attribute ", "public ")):
            continue
        if low.startswith("dim ") or low.startswith("counter") or low.startswith("for each"):
            continue
        if low.startswith("next ") or "cell.value" in low:
            continue
        if low.startswith("end select"):
            if in_select and not skip_select:
                indent = max(1, indent - 1)
            in_select = False
            skip_select = False
            select_var = ""
            first_case = True
            continue
        if low.startswith("select case"):
            if select_has_range(raw_lines, idx):
                in_select = True
                skip_select = True
                continue
            select_var = line.split(None, 2)[2]
            in_select = True
            skip_select = False
            first_case = True
            continue
        if in_select and skip_select:
            continue
        if in_select and low.startswith("case"):
            if not first_case:
                indent = max(1, indent - 1)
            rest = re.sub(r"(?i)^case\s+is\s*", "", line).strip()
            op = "=="
            for candidate in ("<=", ">=", "<", ">", "="):
                if rest.startswith(candidate):
                    op = "==" if candidate == "=" else candidate
                    value = rest[len(candidate) :].strip()
                    break
            else:
                value = rest
            prefix = "if" if first_case else "elif"
            lines.append("    " * indent + f"{prefix} {expr(select_var)} {op} {expr(value)}:")
            indent += 1
            first_case = False
            continue
        if low.startswith("end if"):
            indent = max(1, indent - 1)
            continue
        if low.startswith("else if") or low.startswith("elseif"):
            indent = max(1, indent - 1)
            condition = re.sub(r"(?i)^else\s*if|^elseif", "", line).strip()
            condition = re.sub(r"(?i)\s+then$", "", condition).strip()
            lines.append("    " * indent + f"elif {expr(condition)}:")
            indent += 1
            continue
        if low == "else":
            indent = max(1, indent - 1)
            lines.append("    " * indent + "else:")
            indent += 1
            continue

        single_if = False
        if low.startswith("if "):
            match = re.match(r"(?i)^if\s+(.*?)\s+then\s*(.*)$", line)
            if match:
                condition, rest = match.groups()
                lines.append("    " * indent + f"if {expr(condition)}:")
                indent += 1
                if not rest.strip():
                    continue
                line = rest.strip()
                single_if = True

        assignment = re.match(r"([A-Za-z_]\w*)\s*=\s*(.*)$", line)
        if assignment:
            lhs, rhs = assignment.groups()
            rhs = re.sub(r"(?i)^" + re.escape(lhs) + r"\s*=\s*", "", rhs.strip())
            if lhs.lower() == vb_name.lower():
                lines.append("    " * indent + f"return {expr(rhs)}")
            else:
                lines.append("    " * indent + f"{norm_ident(lhs)} = {expr(rhs)}")
            if single_if:
                indent = max(1, indent - 1)
            continue

        lines.append("    " * indent + "# UNTRANSLATED: " + line)
        if single_if:
            indent = max(1, indent - 1)

    if all("return " not in line for line in lines):
        lines.append("    return y")
    return "\n".join(lines) + "\n"


def r_line(indent: int, text: str) -> str:
    return "  " * indent + text


def translate_function_r(vb_name: str, args: str, body: str) -> str:
    r_name = FUNC_NAMES[vb_name]
    arglist = [norm_ident(arg.strip()) for arg in args.replace("\n", " ").split(",") if arg.strip()]
    lines = [f"{r_name} <- function({', '.join(arglist)}) {{"]
    init = [name for name in lhs_names(body) if name not in set(arglist)]
    for name in init:
        lines.append(r_line(1, f"{name} <- 0"))
    model = coefficient_model(body)
    if model:
        lines.append(r_line(1, f'cof <- .cof("{model}", t)'))

    raw_lines = join_continuations(body.splitlines())
    indent = 1
    in_select = False
    skip_select = False
    select_var = ""
    first_case = True

    for idx, raw_line in enumerate(raw_lines):
        line = clean_comment(raw_line)
        if not line:
            continue
        low = line.lower().strip()
        if low.startswith(("attribute ", "public ")):
            continue
        if low.startswith("dim ") or low.startswith("counter") or low.startswith("for each"):
            continue
        if low.startswith("next ") or "cell.value" in low:
            continue
        if low.startswith("end select"):
            if in_select and not skip_select:
                lines.append(r_line(max(1, indent - 1), "}"))
                indent = max(1, indent - 1)
            in_select = False
            skip_select = False
            select_var = ""
            first_case = True
            continue
        if low.startswith("select case"):
            if select_has_range(raw_lines, idx):
                in_select = True
                skip_select = True
                continue
            select_var = line.split(None, 2)[2]
            in_select = True
            skip_select = False
            first_case = True
            continue
        if in_select and skip_select:
            continue
        if in_select and low.startswith("case"):
            rest = re.sub(r"(?i)^case\s+is\s*", "", line).strip()
            op = "=="
            for candidate in ("<=", ">=", "<", ">", "="):
                if rest.startswith(candidate):
                    op = "==" if candidate == "=" else candidate
                    value = rest[len(candidate) :].strip()
                    break
            else:
                value = rest
            condition = f"{r_expr(select_var)} {op} {r_expr(value)}"
            if first_case:
                lines.append(r_line(indent, f"if ({condition}) {{"))
            else:
                lines.append(r_line(max(1, indent - 1), f"}} else if ({condition}) {{"))
            indent += 1 if first_case else 0
            first_case = False
            continue
        if low.startswith("end if"):
            indent = max(1, indent - 1)
            lines.append(r_line(indent, "}"))
            continue
        if low.startswith("else if") or low.startswith("elseif"):
            indent = max(1, indent - 1)
            condition = re.sub(r"(?i)^(else\s*if|elseif)", "", line).strip()
            condition = re.sub(r"(?i)\s+then$", "", condition).strip()
            lines.append(r_line(indent, f"}} else if ({r_expr(condition)}) {{"))
            indent += 1
            continue
        if low == "else":
            indent = max(1, indent - 1)
            lines.append(r_line(indent, "} else {"))
            indent += 1
            continue

        single_if = False
        if low.startswith("if "):
            match = re.match(r"(?i)^if\s+(.*?)\s+then\s*(.*)$", line)
            if match:
                condition, rest = match.groups()
                lines.append(r_line(indent, f"if ({r_expr(condition)}) {{"))
                indent += 1
                if not rest.strip():
                    continue
                line = rest.strip()
                single_if = True

        assignment = re.match(r"([A-Za-z_]\w*)\s*=\s*(.*)$", line)
        if assignment:
            lhs, rhs = assignment.groups()
            rhs = re.sub(r"(?i)^" + re.escape(lhs) + r"\s*=\s*", "", rhs.strip())
            if lhs.lower() == vb_name.lower():
                lines.append(r_line(indent, f"return({r_expr(rhs)})"))
            else:
                lines.append(r_line(indent, f"{norm_ident(lhs)} <- {r_expr(rhs)}"))
            if single_if:
                indent = max(1, indent - 1)
                lines.append(r_line(indent, "}"))
            continue

        lines.append(r_line(indent, "# UNTRANSLATED: " + line))
        if single_if:
            indent = max(1, indent - 1)
            lines.append(r_line(indent, "}"))

    if all("return(" not in line for line in lines):
        lines.append(r_line(1, "return(y)"))
    lines.append("}")
    return "\n".join(lines) + "\n"


def generated_header() -> str:
    return '''"""Native NGA-West2 GMPE equations generated from audit-only VBA."""
from __future__ import annotations

import math

from ngaw2gmpe.coefficients import load_coefficients


def _excel_col_number(label: str) -> int:
    out = 0
    for ch in label:
        out = out * 26 + ord(ch) - 64
    return out


def _cof(model: str, period: float) -> list[float]:
    lookup_period = 0.001 if model == "CB14" and float(period) == 0 else float(period)
    data = load_coefficients(model)
    rows = data[abs(data["period_s"].astype(float) - lookup_period) < 1e-9].copy()
    if rows.empty:
        raise ValueError(f"No coefficients for {model} period {period}")
    rows["source_col"] = rows["source_cell"].str.extract(r"([A-Z]+)")[0].map(_excel_col_number)
    values = []
    for _, row in rows.sort_values("source_col").iterrows():
        value = row["value"]
        if str(value) == "nan":
            value = row["cached_value"]
        values.append(float(value))
    return values


'''


def generated_r_header() -> str:
    return '''# Native NGA-West2 GMPE equations generated from audit-only VBA.
# This file is generated by scripts/generate_ngaw2_gmpe_native.py.

.excel_col_number <- function(label) {
  chars <- strsplit(label, "", fixed = TRUE)[[1]]
  out <- 0
  for (ch in chars) {
    out <- out * 26 + utf8ToInt(ch) - 64
  }
  out
}

.cof <- function(model, period) {
  lookup_period <- if (model == "CB14" && as.numeric(period) == 0) 0.001 else as.numeric(period)
  data <- load_coefficients(model)
  rows <- data[abs(as.numeric(data$period_s) - lookup_period) < 1e-9, ]
  if (nrow(rows) == 0L) {
    stop(sprintf("No coefficients for %s period %s", model, period), call. = FALSE)
  }
  labels <- sub("^([A-Z]+).*$", "\\\\1", rows$source_cell)
  rows$source_col <- vapply(labels, .excel_col_number, numeric(1))
  rows <- rows[order(rows$source_col), ]
  values <- rows$value
  missing <- is.na(values)
  values[missing] <- rows$cached_value[missing]
  as.numeric(values)
}

'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vba-dir", type=Path, default=Path("output/gmpe_vba"))
    parser.add_argument(
        "--python-out",
        type=Path,
        default=Path("gmpe/python/src/ngaw2gmpe/models/_native.py"),
    )
    parser.add_argument(
        "--r-out",
        type=Path,
        default=Path("gmpe/R/R/native.R"),
    )
    args = parser.parse_args()

    py_code = generated_header()
    r_code = generated_r_header()
    for module in MODULE_ORDER:
        source = (args.vba_dir / module).read_text(encoding="utf-8", errors="replace")
        for name, func_args, body in FUNC_RE.findall(source):
            py_code += translate_function(name, func_args, body) + "\n"
            r_code += translate_function_r(name, func_args, body) + "\n"

    args.python_out.parent.mkdir(parents=True, exist_ok=True)
    args.python_out.write_text(py_code, encoding="utf-8")
    print(f"Wrote {args.python_out}")
    args.r_out.parent.mkdir(parents=True, exist_ok=True)
    args.r_out.write_text(r_code, encoding="utf-8")
    print(f"Wrote {args.r_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
