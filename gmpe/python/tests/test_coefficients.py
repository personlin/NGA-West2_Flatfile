import json
import math
from pathlib import Path

import pytest

from ngaw2gmpe import (
    ask14,
    applicability_warnings,
    available_periods,
    bssa14,
    cb14,
    cy14,
    idriss14,
    load_coefficients,
    period_key,
    predict_dataframe,
)
from ngaw2gmpe.coefficients import CSV_SCHEMA, coefficients_dir


def test_period_key():
    assert period_key(0) == "pga"
    assert period_key(-1) == "pgv"
    assert period_key(0.01) == "p0p010"
    assert period_key(1) == "p1p000"


@pytest.mark.parametrize("model", ["ASK14", "BSSA14", "CB14", "CY14", "I14"])
def test_coefficients_load(model):
    data = load_coefficients(model)
    assert list(data.columns) == list(CSV_SCHEMA)
    assert set(data["model"]) == {model}
    assert len(available_periods(model)) > 0


def test_coefficients_are_shared_not_vba():
    assert coefficients_dir().name == "coefficients"
    assert "vba" not in str(coefficients_dir()).lower()


def test_coefficient_manifest_expected_ranges():
    manifest_path = coefficients_dir() / "coefficient_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    ranges = {sheet["model"]: sheet["used_range"] for sheet in manifest["sheets"]}
    assert ranges == {
        "ASK14": "A1:AT28",
        "BSSA14": "A1:AK27",
        "CB14": "A1:AR27",
        "CY14": "A1:AT30",
        "I14": "A1:M26",
    }


@pytest.mark.parametrize(
    ("fn", "args"),
    [
        (idriss14, dict(M=6.5, Rrup=20, Vs30=760, F=1, period=1.0)),
        (bssa14, dict(M=6.5, Rjb=20, Vs30=760, RS=1, period=1.0)),
        (
            cb14,
            dict(M=6.5, Rrup=20, Rjb=18, Rx=5, Frv=1, Fhw=1, Ztor=2, W=15, dip=30, Vs30=760, period=1.0),
        ),
        (
            ask14,
            dict(M=6.5, Rrup=20, Rjb=18, Rx=5, Frv=1, Fhw=1, Ztor=2, W=15, dip=30, Vs30=760, period=1.0),
        ),
        (
            cy14,
            dict(M=6.5, Rrup=20, Rjb=18, Rx=5, Frv=1, Fhw=1, Ztor=2, dip=30, Vs30=760, period=1.0),
        ),
    ],
)
def test_model_scalar_predictions(fn, args):
    result = fn(**args)
    assert result.median > 0
    assert result.sigma >= 0


def test_predict_dataframe_batch():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame(
        [
            {
                "earthquake_magnitude": 6.5,
                "campbell_r_dist_km": 20,
                "joyner_boore_dist_km": 18,
                "rx": 5,
                "vs30_m_s_selected_for_analysis": 760,
                "depth_to_top_of_fault_rupture_model": 2,
                "fault_rupture_width_km": 15,
                "dip_deg": 30,
            }
        ]
    )
    out = predict_dataframe(df, "ASK14", [0.2, 1.0])
    assert list(out["period_s"]) == [0.2, 1.0]
    assert (out["median"] > 0).all()
    assert "warnings" in out.columns


def test_applicability_warnings_are_exposed():
    warnings = applicability_warnings("I14", M=4.5, Rrup=175, Vs30=300)
    assert len(warnings) == 3
    result = idriss14(M=4.5, Rrup=175, Vs30=300, period=1.0)
    assert result.warnings == warnings


def test_flatfile_missing_sentinel_is_normalized():
    with_negative = ask14(M=6.5, Rrup=20, Rjb=18, Vs30=760, Ztor=-999, W=-999, Z1=-999, period=1.0)
    with_workbook = ask14(M=6.5, Rrup=20, Rjb=18, Vs30=760, Ztor=999, W=999, Z1=999, period=1.0)
    assert math.isclose(with_negative.median, with_workbook.median, rel_tol=1e-12)


def test_golden_outputs_match_python():
    pd = pytest.importorskip("pandas")
    from ngaw2gmpe import ask14, bssa14, cb14, cy14, idriss14

    root = coefficients_dir().parents[0]
    cases = pd.read_csv(root / "validation" / "golden_cases.csv")
    golden = pd.read_csv(root / "validation" / "golden_outputs.csv")
    fns = {"ASK14": ask14, "BSSA14": bssa14, "CB14": cb14, "CY14": cy14, "I14": idriss14}
    for _, expected in golden.iterrows():
        case = cases[cases["case_id"] == expected["case_id"]].iloc[0].dropna().to_dict()
        model = case.pop("model")
        case.pop("case_id")
        case.pop("description")
        case["period"] = case.pop("period_s")
        result = fns[model](**case)
        assert math.isclose(result.ln_median, expected["ln_median"], abs_tol=1e-6)
        assert math.isclose(result.median, expected["median"], rel_tol=1e-5)
        assert math.isclose(result.sigma, expected["sigma"], abs_tol=1e-6)
