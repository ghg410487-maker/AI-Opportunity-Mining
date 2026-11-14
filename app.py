from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.data_loader import DataLoader, load_optional_csv

st.set_page_config(
    page_title="AI 应用场景智能挖掘系统",
    page_icon="🎓",
    layout="wide",
)

DATA_CSV = BASE_DIR / "results" / "final" / "result1_Final_All.csv"

RESULT3_CANDIDATES = (
    BASE_DIR / "results" / "final" / "result3.csv",
    BASE_DIR / "results" / "stage3e1" / "result3.csv",
)
RESULT4_CANDIDATES = (
    BASE_DIR / "results" / "final" / "result4.csv",
    BASE_DIR / "results" / "stage3e1" / "result4.csv",
)

RESULT3_REQUIRED = ("主题簇编号", "主题簇名称")
RESULT4_REQUIRED = ("主题簇编号", "主题簇名称", "机会价值分")

AUDIT_CSV = BASE_DIR / "experiments" / "stage3e3" / "cluster5_guo_initial_audit.csv"
PAUSED_CLUSTER_FALLBACK = ("T3-C004",)

MOCK_NOTE = (
    "【Mock 数据测试】当前为演示数据，非算法端真实结果，"
    "禁止用于正式导出、验收或对外汇报。"
)


@st.cache_data(show_spinner=False, ttl=300)
def load_dataset(csv_path: str) -> dict:
    loader = DataLoader(csv_path)
    distribution = loader.get_source_distribution()
    return {
        "records": loader.load_records(),
        "stats": loader.get_stats(),
        "funnel": loader.get_funnel(),
        "batches": loader.get_batches(),
        "sources": list(distribution.index),
        "error": loader.load_error,
        "missing": list(loader.missing_columns),
        "path": str(loader.csv_path),
    }


def _find_result(
    candidates: tuple[Path, ...],
    required_columns: tuple[str, ...],
) -> tuple[pd.DataFrame | None, str | None, str]:
    for candidate in candidates:
        if candidate.exists():
            frame, error = load_optional_csv(candidate, required_columns)
            if frame is not None:
                return frame, None, str(candidate)
            return None, error, str(candidate)
    return None, "算法端尚未产出结果文件", ""


@st.cache_data(show_spinner=False, ttl=60)
def load_paused_clusters(audit_path: str) -> list[str]:
    fallback = list(PAUSED_CLUSTER_FALLBACK)
    path = Path(audit_path)
    if not path.exists():
        return fallback
    try:
        frame = pd.read_csv(
            path, encoding="utf-8-sig", dtype=str, keep_default_na=False
        )
    except Exception:
        return fallback
    required = {"cluster_id", "human_confirmed_1", "human_rejected_0"}
    if not required.issubset(frame.columns):
        return fallback
    confirmed = pd.to_numeric(frame["human_confirmed_1"], errors="coerce").fillna(0)
    rejected = pd.to_numeric(frame["human_rejected_0"], errors="coerce").fillna(0)
    paused = frame.loc[(confirmed == 0) & (rejected > 0), "cluster_id"].tolist()
    paused.extend(fallback)
    return sorted({item for item in paused if item})


def pause_rejected_clusters(
    table: pd.DataFrame, paused: list[str]
) -> tuple[pd.DataFrame, list[str]]:
    if table.empty or not paused:
        return table, []
    ids = table["主题簇编号"].astype(str)
    matched: list[str] = []
    for cluster_id in ids:
        for item in paused:
            short = item.replace("T3-", "")
            if (
                cluster_id == item
                or cluster_id.endswith(item)
                or cluster_id.endswith(short)
            ):
                matched.append(cluster_id)
                break
    if not matched:
        return table, []
    kept = table.loc[~ids.isin(matched)].reset_index(drop=True)
    removed = list(dict.fromkeys(item.replace("T3-", "") for item in matched))
    return kept, removed


def render_paused_notice(removed: list[str]) -> None:
    if not removed:
        return
    labels = "、".join(removed)
    st.caption(
        f"{labels} 簇因人工核验全否，已在推荐视图中暂停展示（保留机器实验历史）"
    )


def _pick(frame: pd.DataFrame, *names: str) -> pd.Series:
    for name in names:
        if name in frame.columns:
            return frame[name].astype(str)
    return pd.Series("", index=frame.index, dtype="object")



def adapt_result3(frame: pd.DataFrame) -> pd.DataFrame:
    if "来源覆盖" in frame.columns:
        source_label = "来源覆盖"
    elif "来源网站数" in frame.columns:
        source_label = "来源网站数"
    else:
        source_label = "来源覆盖"
    table = pd.DataFrame(
        {
            "主题簇编号": _pick(frame, "主题簇编号", "cluster_id"),
            "主题簇名称": _pick(frame, "主题簇名称", "主题名称", "cluster_name"),
            "功能类别": _pick(frame, "功能类别", "function_category"),
            "所属行业": _pick(frame, "所属行业", "industry"),
            "机会记录数": _pick(frame, "簇内机会记录数", "机会记录数"),
            source_label: _pick(frame, "来源覆盖", "来源网站数", "来源数量"),
            "簇内记录": _pick(frame, "簇内机会记录", "簇内机会记录编号", "记录编号"),
        }
    )
    table["机会记录数"] = (
        pd.to_numeric(table["机会记录数"], errors="coerce").fillna(0).astype(int)
    )
    table = table.sort_values("机会记录数", ascending=False).reset_index(drop=True)
    return table


def adapt_result4(frame: pd.DataFrame) -> pd.DataFrame:
    scores = pd.to_numeric(
        _pick(frame, "机会价值分", "机会价值评分", "score"), errors="coerce"
    )
    table = pd.DataFrame(
        {
            "主题簇编号": _pick(frame, "主题簇编号", "cluster_id"),
            "主题簇名称": _pick(frame, "主题簇名称", "主题名称", "cluster_name"),
            "功能类别": _pick(frame, "功能类别", "function_category"),
            "所属行业": _pick(frame, "所属行业", "industry"),
            "机会价值分": scores,
            "优先级": _pick(frame, "优先级", "priority"),
        }
    )
    table = table.sort_values(
        "机会价值分", ascending=False, na_position="last"
    ).reset_index(drop=True)
    table.insert(0, "排名", range(1, len(table) + 1))
    return table


def mock_result3() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "主题簇编号": "T3-MOCK-001",
                "主题簇名称": "AI 辅助备课",
                "功能类别": "文本生成",
                "所属行业": "教育",
                "机会记录数": 15,
                "来源覆盖": "哔哩哔哩 / 掘金 / GitHub",
                "簇内记录": "演示记录",
            },
            {
                "主题簇编号": "T3-MOCK-002",
                "主题簇名称": "论文自动润色",
                "功能类别": "文本生成",
                "所属行业": "教育",
                "机会记录数": 12,
                "来源覆盖": "教育论坛 / 教育官方新闻",
                "簇内记录": "演示记录",
            },
            {
                "主题簇编号": "T3-MOCK-003",
                "主题簇名称": "实验错误排查",
                "功能类别": "智能诊断",
                "所属行业": "教育",
                "机会记录数": 8,
                "来源覆盖": "V2EX / GitHub",
                "簇内记录": "演示记录",
            },
        ]
    )


def mock_result4() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "排名": 1,
                "主题簇编号": "T3-MOCK-001",
                "主题簇名称": "AI 辅助备课",
                "功能类别": "文本生成",
                "所属行业": "教育",
                "机会价值分": 88.5,
                "优先级": 1,
            },
            {
                "排名": 2,
                "主题簇编号": "T3-MOCK-002",
                "主题簇名称": "论文自动润色",
                "功能类别": "文本生成",
                "所属行业": "教育",
                "机会价值分": 82.0,
                "优先级": 2,
            },
            {
                "排名": 3,
                "主题簇编号": "T3-MOCK-003",
                "主题簇名称": "实验错误排查",
                "功能类别": "智能诊断",
                "所属行业": "教育",
                "机会价值分": 75.2,
                "优先级": 3,
            },
        ]
    )


def render_data_overview(data: dict) -> None:
    st.header("📊 数据漏斗与来源分布")

    stats = data["stats"]
    if data["error"]:
        st.error(f"数据加载异常：{data['error']}")
        if data["missing"]:
            st.caption(f"缺失字段：{', '.join(data['missing'])}")

    if stats["total_records"] == 0:
        st.info("当前没有可用记录，请确认官方 CSV 存在且表头未被修改。")
        st.caption(f"期望路径：{data['path']}")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总记录数", f"{stats['total_records']:,}")
    col2.metric("来源网站数", f"{stats['source_count']}")
    col3.metric("采集批次数", f"{stats['batch_count']}")
    ratio = stats["non_empty_text"] / stats["total_records"] * 100
    col4.metric("正文非空", f"{stats['non_empty_text']:,}", f"{ratio:.1f}%")

    st.subheader("🧭 数据漏斗")
    funnel = data["funnel"]
    if not funnel:
        st.warning("暂无漏斗数据。")
    else:
        funnel_table = pd.DataFrame(funnel).rename(
            columns={"stage": "阶段", "count": "记录数", "ratio": "占比"}
        )
        funnel_table["占比"] = (
            (funnel_table["占比"] * 100).round(1).astype(str) + "%"
        )
        st.dataframe(funnel_table, hide_index=True, width="stretch")
        st.bar_chart(
            pd.DataFrame(funnel).set_index("stage")["count"], horizontal=True
        )
        st.caption("相邻阶段数值相同，表示该维度在数据中没有缺失。")

    st.subheader("🌐 来源分布")
    distribution = stats["source_distribution"]
    if not distribution:
        st.warning("暂无来源分布数据。")
    else:
        distribution_table = pd.DataFrame(
            sorted(distribution.items(), key=lambda item: item[1], reverse=True),
            columns=["来源", "记录数"],
        )
        total = int(distribution_table["记录数"].sum())
        distribution_table["占比"] = (
            (distribution_table["记录数"] / total * 100).round(1).astype(str) + "%"
        )
        st.bar_chart(
            distribution_table.set_index("来源")["记录数"], horizontal=True
        )
        st.dataframe(distribution_table, hide_index=True, width="stretch")

    st.subheader("📄 记录浏览")
    filter_col1, filter_col2 = st.columns(2)
    batch_options = ["全部"] + data["batches"]
    source_options = ["全部"] + data["sources"]
    batch = filter_col1.selectbox("采集批次", batch_options, key="overview_batch")
    source = filter_col2.selectbox("来源网站", source_options, key="overview_source")

    records = data["records"]
    if batch != "全部":
        records = [item for item in records if item["batch_id"] == batch]
    if source != "全部":
        records = [item for item in records if item["source_name"] == source]

    if not records:
        st.info("当前筛选条件下没有记录。")
        return

    preview = pd.DataFrame(
        [
            {
                "记录编号": item["record_id"],
                "标题": item["title"],
                "来源": item["source_name"],
                "正文": (
                    item["text"][:160] + "…"
                    if len(item["text"]) > 160
                    else item["text"]
                ),
                "采集时间": item["collected_at"],
                "来源链接": item["source_url"],
            }
            for item in records[:200]
        ]
    )
    st.dataframe(preview, hide_index=True, width="stretch")
    st.caption(f"筛选结果 {len(records)} 条，仅展示前 {min(200, len(records))} 条。")


def render_topics() -> None:
    st.header("🔍 机会主题发现")

    frame, error, path = _find_result(RESULT3_CANDIDATES, RESULT3_REQUIRED)
    is_mock = frame is None

    if is_mock:
        st.info("⏳ 待算法端输出 result3.csv，以下先以 Mock 数据占位。")
        if error:
            st.caption(f"读取说明：{error}")
        st.warning(MOCK_NOTE)
        table = mock_result3()
        st.caption("⚠️ [Mock 数据测试]")
    else:
        st.warning("⚠️ 【实验候选版本】当前展示的聚类与评分基于算法的早期结果（v1）。由于 result2 的最终政策尚未确定，本页面数据仅用于展示算法能力，非正式提交版。")
        st.success(f"已加载算法端真实结果：{path}")
        table, removed = pause_rejected_clusters(
            adapt_result3(frame), load_paused_clusters(str(AUDIT_CSV))
        )
        render_paused_notice(removed)

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("主题簇数量", f"{len(table)}")
    metric_col2.metric("覆盖机会记录数", f"{int(table['机会记录数'].sum()):,}")

    st.dataframe(table, hide_index=True, width="stretch")
    if table["机会记录数"].sum() > 0:
        chart = table.assign(
            主题标签=table["主题簇编号"] + " " + table["主题簇名称"]
        ).set_index("主题标签")["机会记录数"]
        st.bar_chart(chart, horizontal=True)


def render_ranking() -> None:
    st.header("🏆 机会价值综合排行")

    frame, error, path = _find_result(RESULT4_CANDIDATES, RESULT4_REQUIRED)
    is_mock = frame is None

    if is_mock:
        st.info("⏳ 待算法端输出 result4.csv，以下先以 Mock 数据占位。")
        if error:
            st.caption(f"读取说明：{error}")
        st.warning(MOCK_NOTE)
        table = mock_result4()
        st.caption("⚠️ [Mock 数据测试]")
    else:
        st.warning("⚠️ 【实验候选版本】当前展示的聚类与评分基于算法的早期结果（v1）。由于 result2 的最终政策尚未确定，本页面数据仅用于展示算法能力，非正式提交版。")
        st.success(f"已加载算法端真实结果：{path}")
        table, removed = pause_rejected_clusters(
            adapt_result4(frame), load_paused_clusters(str(AUDIT_CSV))
        )
        if removed:
            table["排名"] = range(1, len(table) + 1)
        render_paused_notice(removed)

    st.dataframe(table, hide_index=True, width="stretch")

    scored = table.dropna(subset=["机会价值分"]).head(10).assign(
        主题标签=lambda frame: frame["主题簇编号"] + " " + frame["主题簇名称"]
    )
    if not scored.empty:
        st.bar_chart(
            scored.set_index("主题标签")["机会价值分"], horizontal=True
        )


def render_plan() -> None:
    st.header("📄 机会策划案")
    st.warning("⚠️ 【实验候选版本】当前展示的聚类与评分基于算法的早期结果（v1）。由于 result2 的最终政策尚未确定，本页面数据仅用于展示算法能力，非正式提交版。")

    frame, error, path = _find_result(RESULT4_CANDIDATES, RESULT4_REQUIRED)
    if frame is None:
        st.info("⏳ 待算法端输出 result4.csv，以下策划案基于 Mock 主题演示。")
        if error:
            st.caption(f"读取说明：{error}")
        st.warning(MOCK_NOTE)
        table = mock_result4()
        st.caption("⚠️ [Mock 数据测试]")
    else:
        table, removed = pause_rejected_clusters(
            adapt_result4(frame), load_paused_clusters(str(AUDIT_CSV))
        )
        st.caption(f"数据来源：{path}")
        render_paused_notice(removed)

    topic_rows = table[table["主题簇名称"].astype(str).str.strip().ne("")]
    if topic_rows.empty:
        st.info("暂无可展示主题。")
        return

    options = [
        f"{item['主题簇编号']} {item['主题簇名称']}"
        for _, item in topic_rows.iterrows()
    ]
    selected = st.selectbox("选择目标主题", options)
    cluster_id = selected.split(" ", 1)[0]
    matched = table[table["主题簇编号"] == cluster_id]
    if matched.empty:
        st.info("未找到该主题的明细。")
        return
    row = matched.iloc[0]

    plan_markdown = f"""
### 1. 目标用户与痛点
- 主题：{row['主题簇名称']}（{row['主题簇编号']}）
- 功能类别：{row['功能类别'] or '待核'}
- 所属行业：{row['所属行业'] or '待核'}
- 机会价值分：{row['机会价值分'] if pd.notna(row['机会价值分']) else '待算法端输出'}

### 2. 核心功能
围绕「{row['功能类别'] or '待核'}」建立最小可验证功能，优先解决主题簇内高频出现的问题。

### 3. 验证路径
- 第 1 周：核对簇内机会记录与原文证据，确认需求真实性。
- 第 2 周：完成原型与离线指标，收集目标用户反馈。
- 复核通过后再进入正式方案评审。

> 依据：{path or 'Mock 数据'}。{'本策划案为 Mock 占位内容，不可用于正式汇报。' if frame is None else ''}
"""

    if st.button("生成 Markdown 策划案"):
        st.markdown(plan_markdown)
        st.success("策划案生成完毕。")

    st.download_button(
        label="⬇️ 下载 Markdown 文件",
        data=plan_markdown.encode("utf-8"),
        file_name=f"plan_{cluster_id}.md",
        mime="text/markdown",
        key="plan_download",
    )


def render_sidebar() -> str:
    with st.sidebar:
        st.header("系统导航")
        menu = st.selectbox(
            "功能页面",
            ["数据概览", "机会主题发现", "机会价值排行", "机会策划案"],
        )
        if st.button("🔄 刷新数据"):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.caption("数据源状态")
        st.write(f"主数据 result1：{'✅ 已找到' if DATA_CSV.exists() else '❌ 缺失'}")
        result3 = next((item for item in RESULT3_CANDIDATES if item.exists()), None)
        result4 = next((item for item in RESULT4_CANDIDATES if item.exists()), None)
        st.write(
            f"result3：{'✅ ' + result3.name if result3 else '⏳ 待算法端输出'}"
        )
        st.write(
            f"result4：{'✅ ' + result4.name if result4 else '⏳ 待算法端输出'}"
        )
        st.divider()
        st.caption("只读官方 CSV，不修改任何官方表头。")
    return menu


def main() -> None:
    st.title("🎓 教育 AI 应用场景智能挖掘与机会评估系统")
    st.caption("数据概览使用 result1 真实数据；主题与排行在算法端结果缺失时明确标注 Mock。")

    menu = render_sidebar()
    data = load_dataset(str(DATA_CSV))

    try:
        if menu == "数据概览":
            render_data_overview(data)
        elif menu == "机会主题发现":
            render_topics()
        elif menu == "机会价值排行":
            render_ranking()
        else:
            render_plan()
    except Exception as exc:
        st.error("页面渲染异常已被拦截，应用不会中断。请检查数据文件或联系维护人员。")
        with st.expander("查看异常详情"):
            st.exception(exc)


main()