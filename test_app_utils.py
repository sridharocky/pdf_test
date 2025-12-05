# test_app_utils.py
import pandas as pd
import numpy as np

from apputil import normalize_and_transform

def test_normalize_and_transform_basic():
    # Create a tiny fake dataset that mimics our real schema
    raw = pd.DataFrame({
        "Region": ["AFR", "AFR", "EMR"],
        "Country": ["CountryA", "CountryA", "CountryB"],
        "Year": [2020, 2021, 2020],
        "Measles_Cases": [100, 150, 200],
        "Rubella_Cases": [10, 15, 20],
        "Population": [1_000_000, 1_000_000, 2_000_000],
    })

    base_wide, base_long = normalize_and_transform(raw)

    # Basic shape checks
    assert not base_wide.empty, "base_wide should not be empty"
    assert not base_long.empty, "base_long should not be empty"

    # Column normalization checks
    expected_cols = {"region", "country", "year", "measles", "rubella", "population"}
    assert expected_cols.issubset(set(base_wide.columns)), "Expected columns missing in base_wide"

    # Long format checks
    assert set(base_long["disease"].unique()) == {"Measles", "Rubella"}, "Unexpected diseases in base_long"

    # Rolling columns added
    for col in ["roll3", "roll5", "yoy"]:
        assert col in base_long.columns, f"{col} should be present in base_long"

if __name__ == "__main__":
    # Simple manual runner: python test_app_utils.py
    try:
        test_normalize_and_transform_basic()
        print("test_normalize_and_transform_basic: PASSED")
    except AssertionError as e:
        print(f"test_normalize_and_transform_basic: FAILED - {e}")
