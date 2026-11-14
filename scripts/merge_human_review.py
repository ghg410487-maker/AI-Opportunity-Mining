"""合并郭的机会人工审核结果与 42 条机器机会审核表。

用法：python scripts/merge_human_review.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GUO_PATH = ROOT / "data" / "guo_opp42_submit.csv"
OUTPUT_DIR = ROOT / "results" / "stage3e1" / "integrated"
OUTPUT_CSV = OUTPUT_DIR / "opportunity_42_merged_v1.csv"
REPORT_PATH = OUTPUT_DIR / "merge_report.md"

KEY = "record_id"
HUMAN_PREFIX = "human_"
EXPECTED_ROWS = 42
HUMAN_REQUIRED = (
    "human_opportunity_decision",
    "human_review_reason",
    "human_evidence_quality",
    "review_status",
)
DECISION_ORDER = ("1", "0", "INSUFFICIENT")
REVIEW_NOTE = (
    "review_status=VERIFIED 代表人工已完成，"
    "human_evidence_quality 保持空值等待曹确认 Q 等级"
)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )


def find_machine_table(exclude_paths: set[Path]) -> Path:
    """搜索包含机器机会结论的 42 条审核表。"""
    candidates: list[tuple[int, str, Path]] = []
    for path in ROOT.rglob("*opportunity_42*.csv"):
        resolved = path.resolve()
        if resolved in exclude_paths:
            continue
        if OUTPUT_DIR.resolve() in resolved.parents:
            continue
        try:
            columns = pd.read_csv(
                path, encoding="utf-8-sig", nrows=0
            ).columns
        except Exception:
            continue
        if "machine_opportunity_result" not in columns:
            continue
        priority = 0 if "docs" in path.parts else 1
        candidates.append((priority, str(path), path))

    if not candidates:
        raise FileNotFoundError(
            "未找到包含 machine_opportunity_result 的 *opportunity_42*.csv"
        )
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def check_keys(machine: pd.DataFrame, human: pd.DataFrame) -> tuple[list[str], ...]:
    machine_ids = machine[KEY].astype(str).str.strip()
    human_ids = human[KEY].astype(str).str.strip()

    machine_dup = sorted(set(machine_ids[machine_ids.duplicated()].tolist()))
    human_dup = sorted(set(human_ids[human_ids.duplicated()].tolist()))
    machine_only = sorted(set(machine_ids) - set(human_ids))
    human_only = sorted(set(human_ids) - set(machine_ids))
    return machine_dup, human_dup, machine_only, human_only


def build_merged(machine: pd.DataFrame, human: pd.DataFrame) -> pd.DataFrame:
    prefilled = [
        column
        for column in machine.columns
        if column.startswith(HUMAN_PREFIX) or column == "review_status"
    ]
    machine_base = machine.drop(columns=prefilled)

    rename: dict[str, str] = {}
    for column in human.columns:
        if column == KEY:
            continue
        if column == "review_status" or column.startswith(HUMAN_PREFIX):
            rename[column] = column
        else:
            rename[column] = HUMAN_PREFIX + column

    human_renamed = human.rename(columns=rename)
    return pd.merge(
        machine_base,
        human_renamed,
        on=KEY,
        how="left",
        validate="one_to_one",
    )


def format_rows(rows: list[str]) -> str:
    return "无" if not rows else "、".join(rows)


def percent(count: int, total: int) -> str:
    return f"{count / total * 100:.1f}%" if total else "0.0%"


def build_report(
    machine_path: Path,
    machine_count: int,
    human_count: int,
    machine_dup: list[str],
    human_dup: list[str],
    machine_only: list[str],
    human_only: list[str],
    merged: pd.DataFrame,
    matched_count: int,
    counts: dict[str, int],
) -> str:
    total = sum(counts.values())
    rows = [
        f"| `{label}` | {counts.get(label, 0)} | {percent(counts.get(label, 0), total)} |"
        for label in DECISION_ORDER
    ]
    other_labels = [key for key in counts if key not in DECISION_ORDER]
    if other_labels:
        rows.extend(
            f"| `{label}` | {counts[label]} | {percent(counts[label], total)} |"
            for label in other_labels
        )

    confirmed = counts.get("1", 0)
    rejected = counts.get("0", 0)
    insufficient = counts.get("INSUFFICIENT", 0)
    machine_positive = int(
        (merged["machine_opportunity_result"].astype(str).str.strip() == "1").sum()
    )

    return f"""# 机会 42 条人工审核合并报告

生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 1. 输入与输出

- 机器审核表：`{machine_path.relative_to(ROOT)}`
- 人工结果表：`{GUO_PATH.relative_to(ROOT)}`
- 合并结果：`{OUTPUT_CSV.relative_to(ROOT)}`
- 合并方式：以 `record_id` 为键的 `pd.merge(..., how="left")`，严格一对一。
- 人工字段统一加 `human_` 前缀；`review_status` 保留原名以便状态核对。机器表中预置的空人工占位列已在合并前移除，机器原字段未被覆盖。

## 2. 对账结果

| 检查项 | 结果 |
|---|---|
| 机器表记录数 | {machine_count} |
| 人工表记录数 | {human_count} |
| 期望记录数 | {EXPECTED_ROWS} |
| 机器表重复 record_id | {len(machine_dup)}（{format_rows(machine_dup)}） |
| 人工表重复 record_id | {len(human_dup)}（{format_rows(human_dup)}） |
| 仅存在于机器表 | {len(machine_only)}（{format_rows(machine_only)}） |
| 仅存在于人工表 | {len(human_only)}（{format_rows(human_only)}） |
| 成功匹配 | {matched_count} / {machine_count} |
| 合并后行数 | {len(merged)} |

结论：{"42 条记录完全匹配，无重复、无多余、无遗漏。" if matched_count == machine_count == EXPECTED_ROWS else "存在未匹配或数量异常，请人工复核。"}

## 3. 人工结果统计

| human_opportunity_decision | 数量 | 占比 |
|---|---:|---:|
{chr(10).join(rows)}
| **合计** | **{total}** | **100.0%** |

- 人工确认机会（1）：{confirmed}
- 人工否定机会（0）：{rejected}
- 证据不足（INSUFFICIENT）：{insufficient}
- 机器机会结论为 1：{machine_positive}
- 人工推翻机器机会结论：{rejected + insufficient}

## 4. 字段说明

- `review_status`：{REVIEW_NOTE}。
- `human_evidence_quality`：本次合并保持空值，等待曹确认 Q 等级。
- `human_reviewer`、`human_reviewed_at`：由原 `reviewer`、`reviewed_at` 加前缀得到。

## 5. 产物

- 合并 CSV：`{OUTPUT_CSV}`
- 本报告：`{REPORT_PATH}`
"""


def main() -> int:
    if not GUO_PATH.exists():
        print(f"[错误] 未找到人工结果文件：{GUO_PATH}")
        return 1

    try:
        machine_path = find_machine_table({GUO_PATH.resolve()})
    except FileNotFoundError as exc:
        print(f"[错误] {exc}")
        return 1

    machine = read_csv(machine_path)
    human = read_csv(GUO_PATH)

    missing_columns = [column for column in HUMAN_REQUIRED if column not in human.columns]
    if missing_columns:
        print(f"[错误] 人工结果表缺少字段：{', '.join(missing_columns)}")
        return 1
    if KEY not in machine.columns or KEY not in human.columns:
        print(f"[错误] 两张表都必须包含主键 {KEY}")
        return 1

    machine_dup, human_dup, machine_only, human_only = check_keys(machine, human)

    print("=== 合并对账 ===")
    print(f"机器审核表：{machine_path.relative_to(ROOT)}")
    print(f"人工结果表：{GUO_PATH.relative_to(ROOT)}")
    print(f"机器记录数：{len(machine)}")
    print(f"人工记录数：{len(human)}")
    print(f"机器重复 record_id：{len(machine_dup)} {format_rows(machine_dup)}")
    print(f"人工重复 record_id：{len(human_dup)} {format_rows(human_dup)}")
    print(f"仅机器表存在：{len(machine_only)} {format_rows(machine_only)}")
    print(f"仅人工表存在：{len(human_only)} {format_rows(human_only)}")

    if machine_dup or human_dup or machine_only or human_only:
        print("[错误] 主键不满足严格一对一，已终止，未生成合并文件。")
        return 1

    merged = build_merged(machine, human)

    matched_mask = (
        merged["human_opportunity_decision"].astype(str).str.strip().ne("")
    )
    matched_count = int(matched_mask.sum())
    print(f"成功匹配：{matched_count} / {len(machine)}")
    print(f"合并后行数：{len(merged)}")

    if matched_count != len(machine):
        unmatched = merged.loc[~matched_mask, KEY].tolist()
        print(f"[错误] 存在未匹配记录：{format_rows(unmatched)}")
        return 1

    decision = human["human_opportunity_decision"].astype(str).str.strip()
    raw_counts = {key: int(value) for key, value in decision.value_counts().items()}
    counts = {label: raw_counts.get(label, 0) for label in DECISION_ORDER}
    counts.update(
        {key: value for key, value in raw_counts.items() if key not in counts}
    )

    total = sum(counts.values())
    print("=== 人工结果分布 ===")
    for label in DECISION_ORDER:
        print(f"{label}: {counts[label]} ({percent(counts[label], total)})")
    for label, value in counts.items():
        if label not in DECISION_ORDER:
            print(f"{label}: {value} ({percent(value, total)})")
    print(f"合计: {total}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    report = build_report(
        machine_path,
        len(machine),
        len(human),
        machine_dup,
        human_dup,
        machine_only,
        human_only,
        merged,
        matched_count,
        counts,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("=== 输出 ===")
    print(f"合并 CSV：{OUTPUT_CSV}")
    print(f"合并报告：{REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())