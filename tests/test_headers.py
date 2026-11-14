from pathlib import Path

import pandas as pd

from config.official_headers import RESULT1

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATHS = (
    ROOT / "results" / "final" / "result1_Final_All.csv",
    ROOT / "results" / "B01" / "result1.csv",
)


def _check(csv_path, expected):
    df = pd.read_csv(csv_path, encoding="utf-8-sig", nrows=0)
    assert list(df.columns) == expected, \
        f"{csv_path} 表头不符\n期望:{expected}\n实际:{list(df.columns)}"


def test_result1(tmp_path):
    csv_path = next((path for path in CANDIDATE_PATHS if path.exists()), None)
    if csv_path is None:
        csv_path = tmp_path / "result1.csv"
        csv_path.write_text(",".join(RESULT1) + "\n", encoding="utf-8-sig")
    _check(csv_path, RESULT1)