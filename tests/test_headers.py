import pandas as pd
from config.official_headers import RESULT1


def _check(csv_path, expected):
    df = pd.read_csv(csv_path, encoding="utf-8-sig", nrows=0)
    assert list(df.columns) == expected, \
        f"{csv_path} 表头不符\n期望:{expected}\n实际:{list(df.columns)}"


def test_result1():
    _check("results/B01/result1.csv", RESULT1)