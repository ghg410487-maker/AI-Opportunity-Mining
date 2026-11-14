"""统一数据加载层。

只读官方 result1 CSV，并将官方中文字段映射为 competition_mvp_v1 统一字段。
对文件缺失、空数据、表头不符等情况做容错，不向上抛出未处理异常。
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

COL_BATCH = "采集批次号"
COL_ID = "记录编号"
COL_SOURCE = "来源网站名称"
COL_URL = "来源链接"
COL_CONTENT = "内容"
COL_TIME = "采集时间"
COL_HEAT = "热度指标（点赞数、评论数、收藏数、转发量等）"

REQUIRED_COLUMNS = (COL_ID, COL_CONTENT, COL_SOURCE, COL_URL)
OPTIONAL_COLUMNS = (COL_BATCH, COL_TIME, COL_HEAT)

DEFAULT_CSV_PATH = PROJECT_ROOT / "results" / "final" / "result1_Final_All.csv"

ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


def _read_csv_robust(path: str | os.PathLike) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ENCODINGS:
        try:
            return pd.read_csv(
                path,
                encoding=encoding,
                dtype=str,
                keep_default_na=False,
            )
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"无法识别文件编码：{path}（{last_error}）")


def _text_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column].astype(str)
    return pd.Series("", index=df.index, dtype="object")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in ("nan", "none"):
        return ""
    return text


def _derive_title(text: str, record_id: str) -> str:
    if not text:
        return record_id or "（无标题）"
    first_line = text.splitlines()[0].strip() or text.strip()
    compact = " ".join(first_line.split())
    return compact if len(compact) <= 60 else compact[:60] + "…"


def _parse_heat(raw: Any) -> dict[str, int | float]:
    text = _clean(raw)
    if not text or text in ("{}", "[]"):
        return {}
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return {}
    if not isinstance(value, dict):
        return {}
    metrics: dict[str, int | float] = {}
    for key, item in value.items():
        try:
            number = float(item)
        except (TypeError, ValueError):
            continue
        if number < 0:
            continue
        metrics[str(key)] = int(number) if number.is_integer() else number
    return metrics


def load_optional_csv(
    csv_path: str | os.PathLike,
    required_columns: tuple[str, ...] | list[str] | None = None,
) -> tuple[pd.DataFrame | None, str | None]:
    """读取可选结果表，返回 (DataFrame, 错误信息)。文件缺失或为空时不抛异常。"""
    path = Path(csv_path)
    if not path.exists():
        return None, f"未找到文件：{path}"
    try:
        df = _read_csv_robust(path)
    except Exception as exc:
        return None, f"读取失败：{path}（{exc}）"
    if df.empty:
        return None, f"文件为空：{path}"
    if required_columns:
        missing = [column for column in required_columns if column not in df.columns]
        if missing:
            return None, f"{path} 缺少字段：{', '.join(missing)}"
    return df, None


class DataLoader:
    """官方 result1 CSV 的统一读取与概览入口。"""

    def __init__(self, csv_path: str | os.PathLike | None = None):
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
        self.load_error: str | None = None
        self.missing_columns: list[str] = []
        self.df = self._load()

    @property
    def is_ready(self) -> bool:
        return (
            not self.df.empty
            and not self.missing_columns
            and self.load_error is None
        )

    def _load(self) -> pd.DataFrame:
        if not self.csv_path.exists():
            self.load_error = f"数据文件不存在：{self.csv_path}"
            return pd.DataFrame()
        try:
            df = _read_csv_robust(self.csv_path)
        except Exception as exc:
            self.load_error = f"读取数据文件失败：{self.csv_path}（{exc}）"
            return pd.DataFrame()
        self.missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in df.columns
        ]
        if self.missing_columns:
            self.load_error = f"数据文件缺少必需字段：{', '.join(self.missing_columns)}"
        return df

    def load_records(self, batch_id: str | None = None) -> list[dict[str, Any]]:
        """返回统一 Schema 记录列表；batch_id 为空时返回全部。"""
        df = self.df
        if df.empty:
            return []
        if batch_id not in (None, "", "全部"):
            if COL_BATCH not in df.columns:
                return []
            df = df[df[COL_BATCH].astype(str) == str(batch_id)]
        return [self._to_record(row) for _, row in df.iterrows()]

    def _to_record(self, row: pd.Series) -> dict[str, Any]:
        record_id = _clean(row.get(COL_ID, ""))
        text = _clean(row.get(COL_CONTENT, ""))
        return {
            "record_id": record_id,
            "batch_id": _clean(row.get(COL_BATCH, "")),
            "title": _derive_title(text, record_id),
            "text": text,
            "source_name": _clean(row.get(COL_SOURCE, "")),
            "source_url": _clean(row.get(COL_URL, "")),
            "collected_at": _clean(row.get(COL_TIME, "")),
            "heat_metrics": _parse_heat(row.get(COL_HEAT, "")),
            "has_text": bool(text),
        }

    def get_record_by_id(self, record_id: str) -> dict[str, Any] | None:
        if self.df.empty or COL_ID not in self.df.columns:
            return None
        matched = self.df[self.df[COL_ID].astype(str) == str(record_id)]
        if matched.empty:
            return None
        return self._to_record(matched.iloc[0])

    def get_batches(self) -> list[str]:
        values = _text_series(self.df, COL_BATCH).str.strip()
        return sorted(value for value in set(values) if value)

    def get_source_distribution(self) -> pd.Series:
        values = _text_series(self.df, COL_SOURCE).str.strip().replace("", "未知来源")
        if values.empty:
            return pd.Series(dtype="int64")
        return values.value_counts()

    def get_stats(self) -> dict[str, Any]:
        df = self.df
        total = int(len(df))
        text_ok = _text_series(df, COL_CONTENT).str.strip().ne("")
        source_distribution = self.get_source_distribution()
        return {
            "total_records": total,
            "source_count": int(source_distribution.size),
            "batch_count": int(_text_series(df, COL_BATCH).str.strip().nunique()) if total else 0,
            "non_empty_text": int(text_ok.sum()) if total else 0,
            "source_distribution": source_distribution.to_dict() if total else {},
            "is_ready": self.is_ready,
            "load_error": self.load_error,
            "missing_columns": list(self.missing_columns),
        }

    def get_funnel(self) -> list[dict[str, Any]]:
        df = self.df
        total = int(len(df))
        if total == 0:
            return []

        text_ok = _text_series(df, COL_CONTENT).str.strip().ne("")
        source_ok = (
            _text_series(df, COL_SOURCE).str.strip().ne("")
            & _text_series(df, COL_URL).str.strip().ne("")
        )
        id_values = _text_series(df, COL_ID).str.strip()
        id_ok = id_values.ne("")
        unique_ok = id_ok & ~id_values.duplicated()
        analyzable = text_ok & source_ok & unique_ok

        stages = [
            ("原始采集记录", pd.Series(True, index=df.index, dtype="bool")),
            ("正文非空", text_ok),
            ("来源信息完整", text_ok & source_ok),
            ("记录编号唯一", text_ok & source_ok & unique_ok),
            ("可进入机会判别", analyzable),
        ]
        funnel: list[dict[str, Any]] = []
        for name, mask in stages:
            count = int(mask.sum())
            funnel.append(
                {
                    "stage": name,
                    "count": count,
                    "ratio": round(count / total, 4),
                }
            )
        return funnel