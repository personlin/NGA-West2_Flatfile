"""Small JSON CLI used by validation and automation workflows."""
from __future__ import annotations

import json
import sys

from .batch import predict_dataframe
from .models import ask14, bssa14, cb14, cy14, idriss14


MODEL_FUNCTIONS = {
    "ASK14": ask14,
    "BSSA14": bssa14,
    "CB14": cb14,
    "CY14": cy14,
    "I14": idriss14,
    "IDRISS14": idriss14,
}


def _result_dict(result):
    return {
        "model": result.model,
        "period_s": result.period,
        "median": result.median,
        "ln_median": result.ln_median,
        "sigma": result.sigma,
        "tau": result.tau,
        "phi": result.phi,
        "warnings": list(result.warnings),
    }


def main() -> int:
    request = json.load(sys.stdin)
    if request.get("kind", "scalar") == "dataframe":
        import pandas as pd

        frame = pd.DataFrame(request["rows"])
        out = predict_dataframe(frame, request["model"], request["periods"], request.get("column_map"))
        print(out.to_json(orient="records"))
        return 0

    model = request["model"].upper()
    args = request.get("args", {})
    result = MODEL_FUNCTIONS[model](**args)
    print(json.dumps(_result_dict(result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
