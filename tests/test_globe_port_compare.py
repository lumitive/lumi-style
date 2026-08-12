"""_compare_port's length guard on the golden grid.

zip() truncates silently, so a backend returning a short (or empty) result
list once compared a prefix — or nothing — and still printed agreement on all
1300 samples (PR #87 review). These tests pin the length checks; full
numeric agreement is what CI's --node run covers, so no tolerances are
re-derived here.
"""
import json
import pathlib

import check_globe

GOLDEN = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "fixtures"
     / "globe-golden.json").read_text(encoding="utf-8"))


def _exact_result():
    """What a perfectly agreeing backend would return, copied from the grid."""
    out = [[px, py, pvis] for (_, _, _, px, py, pvis) in GOLDEN["samples"]]
    rt = [{"lon": lon, "lat": lat} if pvis else None
          for (_, lon, lat, _, _, pvis) in GOLDEN["samples"]]
    return {"out": out, "rt": rt}


def test_exact_copy_of_the_grid_passes():
    assert check_globe._compare_port(GOLDEN, _exact_result()) == []


def test_empty_result_lists_error_instead_of_vacuous_agreement():
    errors = check_globe._compare_port(GOLDEN, {"out": [], "rt": []})
    assert errors
    assert "not covered" in errors[0]


def test_one_short_out_list_errors():
    result = _exact_result()
    result["out"] = result["out"][:-1]
    errors = check_globe._compare_port(GOLDEN, result)
    assert errors
    assert "not covered" in errors[0]


def test_one_short_rt_list_errors():
    result = _exact_result()
    result["rt"] = result["rt"][:-1]
    errors = check_globe._compare_port(GOLDEN, result)
    assert errors
    assert "not covered" in errors[0]
