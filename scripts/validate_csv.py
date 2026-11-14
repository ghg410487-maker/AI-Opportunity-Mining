"""官方四份 CSV 核对脚本。

result2 采用“已决子集 + REVIEW 阻断表”的形态；存在 REVIEW 时输出
“部分通过 / 待 REVIEW 审批”，不将 REVIEW 映射为 0 或 1，也不中断脚本。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "final"

RESULT1_FILE = "result1_Final_All.csv"
RESULT2_RESOLVED_FILE = "result2_resolved_subset.csv"
RESULT2_BLOCKERS_FILE = "result2_export_blockers.csv"
RESULT3_FILE = "result3.csv"
RESULT4_FILE = "result4.csv"

RESULT2_COLUMNS = {
    "采集批次号",
    "记录编号",
    "是否构成机会",
    "机会置信度",
    "功能类别",
    "所属行业",
}
RESULT3_COLUMNS = {
    "采集批次号",
    "主题簇编号",
    "主题簇名称",
    "功能类别",
    "所属行业",
    "簇内机会记录数",
}
RESULT4_COLUMNS = {
    "采集批次号",
    "主题簇编号",
    "主题簇名称",
    "功能类别",
    "所属行业",
    "机会价值分",
    "优先级",
}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path, encoding="utf-8-sig", dtype=str, keep_default_na=False
    )


def clean_ids(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in str(value).split(";") if item.strip()]


def validate_official_csvs() -> int:
    print("=== 官方四份 CSV 核对 ===")
    print(f"目录：{RESULTS_DIR}")

    errors: list[str] = []
    warnings: list[str] = []
    statuses: list[str] = []

    def passed(message: str) -> None:
        print(f"✅ {message}")

    def warning(message: str) -> None:
        warnings.append(message)
        print(f"⚠️ {message}")

    def failed(message: str) -> None:
        errors.append(message)
        print(f"❌ {message}")

    result1_path = RESULTS_DIR / RESULT1_FILE
    if not result1_path.exists():
        failed(f"缺少 result1：{result1_path}")
        print("校验结果：失败（result1 缺失，无法继续）")
        return 1

    result1 = read_csv(result1_path)
    if "记录编号" not in result1.columns:
        failed("result1 缺少字段：记录编号")
        print("校验结果：失败")
        return 1

    result1_ids = clean_ids(result1["记录编号"])
    if result1_ids.duplicated().any():
        duplicates = sorted(set(result1_ids[result1_ids.duplicated()].tolist()))
        failed(f"result1 记录编号重复 {len(duplicates)} 个：{', '.join(duplicates[:10])}")
    else:
        passed(f"result1 行数 {len(result1)}，记录编号唯一")
    result1_id_set = set(result1_ids)

    resolved: pd.DataFrame | None = None
    blockers: pd.DataFrame | None = None
    resolved_path = RESULTS_DIR / RESULT2_RESOLVED_FILE
    blockers_path = RESULTS_DIR / RESULT2_BLOCKERS_FILE
    resolved_ids: set[str] = set()
    blocker_ids: set[str] = set()

    if resolved_path.exists():
        resolved = read_csv(resolved_path)
        missing = sorted(RESULT2_COLUMNS - set(resolved.columns))
        if missing:
            failed(f"result2 已决子集缺少字段：{', '.join(missing)}")
        else:
            resolved_ids = set(clean_ids(resolved["记录编号"]))
            if len(resolved_ids) != len(resolved):
                failed("result2 已决子集记录编号不唯一")
            invalid_values = sorted(
                set(clean_ids(resolved["是否构成机会"])) - {"0", "1"}
            )
            if invalid_values:
                failed(
                    "result2 已决子集出现非 0/1 状态："
                    + ", ".join(invalid_values)
                    + "（REVIEW 不得映射为 0 或 1）"
                )
            passed(f"result2 已决子集 {len(resolved)} 条，记录编号唯一，状态仅 0/1")
    else:
        warning(f"缺少 result2 已决子集：{resolved_path}")

    if blockers_path.exists():
        blockers = read_csv(blockers_path)
        if "记录编号" not in blockers.columns:
            failed("result2 阻断表缺少字段：记录编号")
        else:
            blocker_ids = set(clean_ids(blockers["记录编号"]))
            if len(blocker_ids) != len(blockers):
                failed("result2 阻断表记录编号不唯一")
            if "内部状态" in blockers.columns:
                invalid = sorted(
                    set(clean_ids(blockers["内部状态"])) - {"REVIEW"}
                )
                if invalid:
                    failed(f"result2 阻断表出现非 REVIEW 状态：{', '.join(invalid)}")
            passed(f"result2 REVIEW 阻断表 {len(blockers)} 条，记录编号唯一")
    else:
        warning(f"缺少 result2 阻断表：{blockers_path}")

    if resolved is None and blockers is None:
        statuses.append("result2：待算法接入（未生成已决子集与阻断表）")
    else:
        overlap = resolved_ids & blocker_ids
        if overlap:
            failed(f"result2 已决子集与阻断表存在 {len(overlap)} 条重叠记录")

        combined = resolved_ids | blocker_ids
        missing_from_result2 = sorted(result1_id_set - combined)
        extra_in_result2 = sorted(combined - result1_id_set)
        if missing_from_result2:
            failed(
                f"result2 未覆盖 result1 的 {len(missing_from_result2)} 条记录："
                + ", ".join(missing_from_result2[:10])
            )
        if extra_in_result2:
            failed(
                f"result2 出现 result1 之外的 {len(extra_in_result2)} 条记录："
                + ", ".join(extra_in_result2[:10])
            )
        if not missing_from_result2 and not extra_in_result2:
            passed(
                f"result2 与 result1 对账一致："
                f"{len(resolved_ids)} 已决 + {len(blocker_ids)} REVIEW = {len(result1_ids)}"
            )

        if blocker_ids:
            statuses.append(
                f"result2：部分通过（已决 {len(resolved_ids)} 条，"
                f"待 REVIEW 审批 {len(blocker_ids)} 条），"
                "REVIEW 保持阻断，禁止正式全量导出"
            )
        elif resolved is not None and len(resolved_ids) == len(result1_ids):
            statuses.append("result2：完全通过")
        else:
            statuses.append("result2：待补充已决记录")

    result3: pd.DataFrame | None = None
    result3_path = RESULTS_DIR / RESULT3_FILE
    if not result3_path.exists():
        warning(f"缺少 result3：{result3_path}")
    else:
        result3 = read_csv(result3_path)
        missing = sorted(RESULT3_COLUMNS - set(result3.columns))
        if missing:
            failed(f"result3 缺少字段：{', '.join(missing)}")
        cluster_ids = clean_ids(result3["主题簇编号"]) if "主题簇编号" in result3.columns else pd.Series(dtype=str)
        if cluster_ids.duplicated().any():
            failed("result3 主题簇编号重复")
        else:
            passed(f"result3 共 {len(result3)} 个主题簇，主题簇编号唯一")

        record_column = next(
            (
                name
                for name in ("簇内机会记录编号", "簇内机会记录")
                if name in result3.columns
            ),
            None,
        )
        if record_column is None:
            failed("result3 缺少簇内记录字段")
        else:
            cluster_records = [
                record
                for value in result3[record_column]
                for record in split_ids(value)
            ]
            if len(cluster_records) != len(set(cluster_records)):
                failed("result3 簇内记录存在重复")
            else:
                passed(f"result3 簇内记录 {len(cluster_records)} 条，无重复")

            if resolved is not None and "是否构成机会" in resolved.columns:
                opportunity_ids = set(
                    clean_ids(
                        resolved.loc[
                            clean_ids(resolved["是否构成机会"]) == "1", "记录编号"
                        ]
                    )
                )
                if set(cluster_records) == opportunity_ids:
                    passed(
                        f"result3 与 result2 机会记录对账一致：{len(opportunity_ids)} 条"
                    )
                else:
                    failed(
                        "result3 簇内记录与 result2 机会=1 记录不一致："
                        f"result3 {len(set(cluster_records))} 条，"
                        f"result2 {len(opportunity_ids)} 条"
                    )

    result4_path = RESULTS_DIR / RESULT4_FILE
    if not result4_path.exists():
        warning(f"缺少 result4：{result4_path}")
    else:
        result4 = read_csv(result4_path)
        missing = sorted(RESULT4_COLUMNS - set(result4.columns))
        if missing:
            failed(f"result4 缺少字段：{', '.join(missing)}")
        cluster_ids4 = clean_ids(result4["主题簇编号"]) if "主题簇编号" in result4.columns else pd.Series(dtype=str)
        if cluster_ids4.duplicated().any():
            failed("result4 主题簇编号重复")
        else:
            passed(f"result4 共 {len(result4)} 条评分记录，主题簇编号唯一")

        if result3 is not None and "主题簇编号" in result3.columns:
            if set(cluster_ids4) == set(clean_ids(result3["主题簇编号"])):
                passed("result4 与 result3 主题簇集合一致")
            else:
                failed("result4 与 result3 主题簇集合不一致")
            if len(result4) == len(result3):
                passed("result4 与 result3 行数一致")
            else:
                failed(f"result4 行数 {len(result4)} 与 result3 {len(result3)} 不一致")

        if "机会价值分" in result4.columns:
            scores = pd.to_numeric(result4["机会价值分"], errors="coerce")
            if scores.isna().any():
                failed("result4 机会价值分存在非数值")
            elif ((scores < 0) | (scores > 100)).any():
                failed("result4 机会价值分超出 0-100")
            else:
                passed(f"result4 机会价值分范围 {scores.min():.2f}-{scores.max():.2f}")

        if "优先级" in result4.columns:
            priorities = pd.to_numeric(result4["优先级"], errors="coerce")
            if priorities.isna().any() or priorities.duplicated().any():
                failed("result4 优先级存在空值或重复")
            else:
                passed("result4 优先级唯一")

    print("\n=== 校验摘要 ===")
    for status in statuses:
        print(f"• {status}")
    partial = any(
        ("部分通过" in status) or ("待 REVIEW" in status) for status in statuses
    )
    if errors:
        print(f"校验结果：失败（{len(errors)} 项错误，{len(warnings)} 项警告）")
        return 1
    if partial:
        print("校验结果：部分通过（result2 待 REVIEW 审批，其余 CSV 核对通过）")
        return 0
    if warnings:
        print(f"校验结果：通过（含 {len(warnings)} 项警告/待办）")
        return 0
    print("校验结果：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(validate_official_csvs())