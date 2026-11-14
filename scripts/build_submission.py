"""构建官方提交包（可重复执行）。

默认 stage 模式：允许 result2 占位，生成 PENDING/NOT_READY 包和 manifest。
--release 模式：必须通过严格校验且 result2 数据行数 > 0，否则阻断。

用法：
    python scripts/build_submission.py
    python scripts/build_submission.py --release
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "competition_submission"
RESULTS_SRC = ROOT / "results" / "final"
SCREENSHOTS_SRC = ROOT / "docs" / "research_stage3" / "stage3e3" / "screenshots"
VERSION_FILE = RESULTS_SRC / ".result_version.json"
MANIFEST_SCHEMA = "submission_manifest_v1"

SOURCE_ITEMS = (
    "app.py",
    "src/data_loader.py",
    "edumine/__init__.py",
    "edumine/__main__.py",
    "edumine/baselines.py",
    "edumine/cli.py",
    "edumine/competition.py",
    "edumine/core.py",
    "edumine/normalization.py",
    "edumine/stage3e2.py",
    "edumine/stage3e3.py",
    "config/official_headers.py",
    "scripts/validate_csv.py",
    "scripts/switch_official_results.py",
    "requirements.txt",
    "run_system.bat",
    "run_system.sh",
)

PUBLIC_README = """# 教育 AI 应用场景智能挖掘与机会评估系统

本提交包是第三届甘肃省大学生数据挖掘挑战赛本科组赛题作品的可运行工程包。
系统围绕教育 AI 场景，展示多源数据清洗、机会判别、主题聚类、价值评分与策划案生成流程。

## 快速启动

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\python -m pip install -r requirements.txt
run_system.bat

# Linux / macOS
.venv/bin/python -m pip install -r requirements.txt
bash run_system.sh
```

浏览器访问 <http://localhost:8501>。

## 数据与结果

- `results/result1.csv`：多源采集与清洗记录
- `results/result2.csv`：逐条机会判别（当前状态见 `submission_checklist.md`）
- `results/result3.csv`：主题聚类与簇内记录追溯
- `results/result4.csv`：机会价值评分与优先级
- `results/` 下文件名与官方四份 CSV 模板一致。

数据准备与重新生成：

```bash
python -m edumine competition-mvp --input results/result1.csv --output results
```

## 校验

```bash
python scripts/validate_csv.py --strict --results-dir results
```

正式提交前必须返回 `READY_FOR_SUBMISSION`，否则不得打包。

## 目录

```
competition_submission/
├── results/        # 官方四份 CSV
├── source/         # 最小可运行源码
├── docs/           # 启动、部署、切换、AI 使用说明
├── screenshots/    # 系统关键页面截图
├── README.md
├── submission_checklist.md
└── manifest.json
```

## 核心创新

1. 多源证据可追溯：每条机会记录保留来源与簇内记录编号；
2. 可解释价值评分：维度分数可独立重算，不依赖黑盒；
3. 人工审计旁路：机器结果与人工审核分层展示，不把人工结论伪装成新的机器聚类；
4. 正式结果原子切换：审批、哈希、严格校验和回滚形成完整发布闸门。

## 版本状态

本包版本与是否正式提交以 `manifest.json` 和 `submission_checklist.md` 为准。
当前若仍为 `NOT_READY`，表示 result2 的 REVIEW 政策尚未批准，禁止正式提交。
"""

PUBLIC_ENV = """# 环境与部署说明

## 环境

- Python 3.11+（验证版本 3.12）
- Windows 11 / Linux / macOS
- 依赖：streamlit、pandas、requests、beautifulsoup4、pytest

## 安装

```bash
python -m venv .venv
.venv\\Scripts\\python -m pip install -r requirements.txt   # Windows
.venv/bin/python -m pip install -r requirements.txt       # Linux/macOS
```

## 启动

```bash
run_system.bat   # Windows
bash run_system.sh
# 或
streamlit run app.py
```

## 部署边界

当前交付为本地运行模式，不包含长期稳定公网入口。若需公网演示，应由负责人评估并批准反代、认证和费用，不得擅自创建付费资源。

## 数据依赖

- `results/result1.csv` 必须有数据；
- `result3.csv`、`result4.csv` 用于主题与评分页面；
- 数据缺失时页面显示提示，不崩溃；
- 密钥只从本地 `.env` 读取，提交包不包含 `.env`。
"""

PUBLIC_SWITCH = """# 正式结果切换说明（摘要）

正式结果接入需要：

- `result2.csv`、`result3.csv`、`result4.csv`；
- 输入 `result1.csv` 的 SHA256；
- 算法版本、算法配置版本、负责人审批版本；
- 每份结果文件的 SHA256；
- `approval.submission_ready=true`。

切换命令：

```bash
python scripts/switch_official_results.py \\
  --candidate-dir path/to/candidate \\
  --manifest path/to/candidate/manifest.json
```

默认只做 dry-run；只有全部审批与严格校验通过后才允许追加 `--publish`。
发布前必须停止服务，发布后重启并执行页面验收；失败会自动回滚到上一版本。
"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return len(pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False))


def current_version() -> str:
    if VERSION_FILE.exists():
        try:
            return json.loads(VERSION_FILE.read_text(encoding="utf-8")).get("version", "v1-experimental")
        except json.JSONDecodeError:
            pass
    return "v1-experimental"


def copy_tree_files(destination: Path) -> None:
    for relative in SOURCE_ITEMS:
        source = ROOT / relative
        if not source.exists():
            continue
        target = destination / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def reset_package() -> None:
    for name in ("results", "source", "docs", "screenshots"):
        path = PACKAGE / name
        if path.exists():
            shutil.rmtree(path)
    for legacy in ("result1.csv", "result2.csv", "result3.csv", "result4.csv"):
        path = PACKAGE / legacy
        if path.exists():
            path.unlink()
    (PACKAGE / "results").mkdir(parents=True, exist_ok=True)
    (PACKAGE / "source").mkdir(parents=True, exist_ok=True)
    (PACKAGE / "docs").mkdir(parents=True, exist_ok=True)
    (PACKAGE / "screenshots").mkdir(parents=True, exist_ok=True)


def prepare_results() -> dict[str, Any]:
    results = PACKAGE / "results"
    mapping = {
        "result1.csv": RESULTS_SRC / "result1_Final_All.csv",
        "result3.csv": RESULTS_SRC / "result3.csv",
        "result4.csv": RESULTS_SRC / "result4.csv",
    }
    info: dict[str, Any] = {}
    for name, source in mapping.items():
        if source.exists():
            shutil.copy2(source, results / name)
        info[name] = read_rows(results / name)

    full_result2 = RESULTS_SRC / "result2.csv"
    if full_result2.exists() and read_rows(full_result2) > 0:
        shutil.copy2(full_result2, results / "result2.csv")
        info["result2.csv"] = read_rows(results / "result2.csv")
        info["result2_mode"] = "official_full"
    else:
        with (results / "result2.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            import csv

            csv.writer(handle).writerow(
                ["采集批次号", "记录编号", "是否构成机会", "机会置信度", "功能类别", "所属行业"]
            )
        info["result2.csv"] = 0
        info["result2_mode"] = "placeholder_header_only"
    return info


def prepare_docs() -> None:
    docs = PACKAGE / "docs"
    (PACKAGE / "README.md").write_text(PUBLIC_README, encoding="utf-8")
    (docs / "environment_and_deployment.md").write_text(PUBLIC_ENV, encoding="utf-8")
    (docs / "official_result_switch_contract.md").write_text(PUBLIC_SWITCH, encoding="utf-8")
    source_docs = {
        "demo_guide.md": ROOT / "docs" / "demo_guide.md",
        "AI_usage_log.md": ROOT / "docs" / "AI_usage_log.md",
    }
    for name, source in source_docs.items():
        if source.exists():
            content = source.read_text(encoding="utf-8")
            if name == "demo_guide.md":
                content = content.replace(
                    "(research_stage3/stage3e3/screenshots/",
                    "(../screenshots/",
                )
            (docs / name).write_text(content, encoding="utf-8")


def prepare_screenshots() -> None:
    for name in ("overview.png", "topics.png", "ranking.png", "plan.png"):
        source = SCREENSHOTS_SRC / name
        if source.exists():
            shutil.copy2(source, PACKAGE / "screenshots" / name)


def validate_package() -> tuple[bool, str]:
    env = {"PYTHONUTF8": "1"}
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_csv.py"),
            "--strict",
            "--results-dir",
            str(PACKAGE / "results"),
        ],
        cwd=str(ROOT),
        env={**dict(__import__("os").environ), **env},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    return process.returncode == 0, (process.stdout or process.stderr or "").strip()


def build_manifest(results_info: dict[str, Any], validation: tuple[bool, str]) -> dict[str, Any]:
    version = current_version()
    result2_ready = results_info.get("result2.csv", 0) > 0
    passed, output = validation
    overall = "READY" if passed and result2_ready else "NOT_READY"
    blockers: list[str] = []
    if not result2_ready:
        blockers.append("result2.csv 数据行数为 0（占位文件）")
    if not passed:
        blockers.append("严格校验未通过")
    files = []
    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(PACKAGE).as_posix()
        if relative.startswith("results/"):
            purpose = "官方结果 CSV"
            formal = True
            status = "READY"
            if relative == "results/result2.csv" and not result2_ready:
                formal = False
                status = "NOT_READY"
        elif relative.startswith("source/"):
            purpose, formal, status = "运行源码", True, "READY"
        elif relative.startswith("docs/"):
            purpose, formal, status = "公开文档", True, "READY"
        elif relative.startswith("screenshots/"):
            purpose, formal, status = "系统截图", True, "READY"
        else:
            purpose, formal, status = "包说明", True, "READY"
        files.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
                "purpose": purpose,
                "version": version,
                "formal": formal,
                "status": status,
            }
        )
    return {
        "schema_version": MANIFEST_SCHEMA,
        "version": version,
        "algorithm_version": "v1-rule-baseline",
        "algorithm_config_version": "competition-mvp-v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": overall,
        "submission_ready": overall == "READY",
        "blockers": blockers,
        "result1_sha256": sha256_file(PACKAGE / "results" / "result1.csv")
        if (PACKAGE / "results" / "result1.csv").exists()
        else "",
        "results": results_info,
        "validation": {"passed": passed, "output_tail": "\n".join(output.splitlines()[-8:])},
        "files": files,
    }


def build_checklist(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{item['path']}` | {item['size']} | `{item['sha256'][:16]}…` | {item['status']} |"
        for item in manifest["files"]
    )
    return f"""# 官方提交包核对清单

- 包版本：`{manifest['version']}`
- 总体状态：**{manifest['overall_status']}**
- `submission_ready`：`{manifest['submission_ready']}`
- 生成时间：{manifest['generated_at']}

## 1. 阻断项

{chr(10).join(f'- {item}' for item in manifest['blockers']) or '- 无'}

## 2. 官方材料核对

| 材料 | 状态 | 说明 |
|---|---|---|
| 四份官方 CSV | {'PASS' if manifest['submission_ready'] else 'NOT_READY'} | 见 `results/` 与 manifest |
| 源代码 | PASS | `source/` 最小可运行源码 |
| 运行环境说明 | PASS | `docs/environment_and_deployment.md` |
| 系统部署说明 | PASS | 本地运行，公网入口待负责人批准 |
| 系统关键截图 | PASS | `screenshots/` 4 张 |
| AI 使用说明 | PARTIAL | `docs/AI_usage_log.md` 为记录模板，实际记录待团队补填 |
| 论文 Word/PDF | MISSING | 本包未包含论文，需团队另行提交 |
| 附件1标签映射文件 | 待核实 | 官方附件1标签需在最终算法配置中核对 |
| 其他官方材料 | 待核实 | 以赛题 PDF 最终清单为准 |

## 3. 文件清单

| 相对路径 | 大小 | SHA256 前缀 | 状态 |
|---|---:|---|---|
{rows}

## 4. 正式发布闸门

```bash
python scripts/build_submission.py --release
python scripts/validate_csv.py --strict --results-dir competition_submission/results
python scripts/security_gate.py --target competition_submission
```

release 模式在 result2 仍为占位、或严格校验未通过时必须返回非零退出码。

## 5. 排除项

- `.env`、`.env.*`、密钥、SSH 私钥
- `.venv/`、`__pycache__/`、`.pytest_cache/`
- `data/`、`results/` 中间产物、`experiments/datasets/`
- 私有盲审文件、受控人工审核原件
- 本地大文件（`cloudflared.exe`、审计 zip）
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建官方提交包")
    parser.add_argument("--release", action="store_true", help="正式发布模式，未 READY 则阻断")
    args = parser.parse_args(argv)

    PACKAGE.mkdir(exist_ok=True)
    reset_package()
    results_info = prepare_results()
    copy_tree_files(PACKAGE)
    prepare_docs()
    prepare_screenshots()
    validation = validate_package()
    manifest = build_manifest(results_info, validation)
    (PACKAGE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PACKAGE / "submission_checklist.md").write_text(
        build_checklist(manifest), encoding="utf-8"
    )

    print(json.dumps(
        {
            "overall_status": manifest["overall_status"],
            "submission_ready": manifest["submission_ready"],
            "blockers": manifest["blockers"],
            "results": results_info,
            "files": len(manifest["files"]),
            "validation_passed": manifest["validation"]["passed"],
        },
        ensure_ascii=False,
        indent=2,
    ))
    if args.release and not manifest["submission_ready"]:
        print("RELEASE_BLOCKED：提交包仍为 NOT_READY，禁止正式打包。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())