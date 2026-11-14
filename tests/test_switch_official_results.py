from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "switch_official_results.py"
SPEC = importlib.util.spec_from_file_location("switch_official_results", SCRIPT)
switch = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(switch)

RESULT1 = [
    "采集批次号",
    "记录编号",
    "来源网站名称",
    "来源链接",
    "内容",
    "采集时间",
    "热度指标（点赞数、评论数、收藏数、转发量等）",
]
RESULT2 = ["采集批次号", "记录编号", "是否构成机会", "机会置信度", "功能类别", "所属行业"]
RESULT3 = [
    "采集批次号",
    "主题簇编号",
    "主题簇名称",
    "功能类别",
    "所属行业",
    "簇内机会记录数",
    "来源网站数",
    "簇内机会记录编号",
]
RESULT4 = ["采集批次号", "主题簇编号", "主题簇名称", "功能类别", "所属行业", "机会价值分", "优先级"]

SYNTH_IDS = ["SYNTH-Z5-S00001", "SYNTH-Z5-S00002", "SYNTH-Z5-S00003"]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    pd.DataFrame(rows, columns=header).to_csv(path, index=False, encoding="utf-8-sig")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_candidate(
    base: Path,
    *,
    decisions: tuple[str, str, str] = ("1", "0", "1"),
    cluster_id: str = "SYNTH-C001",
    result3_ids: str | None = None,
    submission_ready: bool = True,
    version: str = "v2-synthetic-test",
) -> Path:
    candidate = base / "candidate"
    candidate.mkdir(parents=True)
    write_csv(
        candidate / "result1.csv",
        RESULT1,
        [
            ["SYNTH", SYNTH_IDS[0], "合成来源A", "https://example.invalid/a", "合成正文A", "2026-11-20", "{}"],
            ["SYNTH", SYNTH_IDS[1], "合成来源B", "https://example.invalid/b", "合成正文B", "2026-11-20", "{}"],
            ["SYNTH", SYNTH_IDS[2], "合成来源C", "https://example.invalid/c", "合成正文C", "2026-11-20", "{}"],
        ],
    )
    write_csv(
        candidate / "result2.csv",
        RESULT2,
        [
            ["SYNTH", SYNTH_IDS[index], decisions[index], "0.9", "文本生成", "教育"]
            for index in range(3)
        ],
    )
    record_ids = result3_ids or ";".join(
        SYNTH_IDS[index] for index, value in enumerate(decisions) if value == "1"
    )
    count = len([item for item in record_ids.split(";") if item])
    write_csv(
        candidate / "result3.csv",
        RESULT3,
        [["SYNTH", cluster_id, "合成主题", "文本生成", "教育", str(count), "2", record_ids]],
    )
    write_csv(
        candidate / "result4.csv",
        RESULT4,
        [["SYNTH", cluster_id, "合成主题", "文本生成", "教育", "88.0", "1"]],
    )
    manifest = {
        "schema_version": switch.SCHEMA_VERSION,
        "version": version,
        "algorithm_version": "synthetic-test-v2",
        "algorithm_config_version": "synthetic-config-v1",
        "result1_sha256": sha(candidate / "result1.csv"),
        "approval": {
            "approved_by": "synthetic-test",
            "approval_version": "synthetic-approval-v1",
            "submission_ready": submission_ready,
        },
        "files": [
            {
                "path": name,
                "sha256": sha(candidate / name),
                "rows": len(pd.read_csv(candidate / name, encoding="utf-8-sig")),
                "formal": True,
                "status": "READY",
            }
            for name in ("result2.csv", "result3.csv", "result4.csv")
        ],
    }
    (candidate / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return candidate


def make_target(base: Path) -> Path:
    target = base / "target"
    target.mkdir()
    write_csv(
        target / "result2.csv",
        RESULT2,
        [["SYNTH", SYNTH_IDS[0], "0", "0.1", "文本生成", "教育"]],
    )
    write_csv(
        target / "result3.csv",
        RESULT3,
        [["SYNTH", "OLD-C001", "旧主题", "文本生成", "教育", "1", "1", SYNTH_IDS[0]]],
    )
    write_csv(
        target / "result4.csv",
        RESULT4,
        [["SYNTH", "OLD-C001", "旧主题", "文本生成", "教育", "10.0", "1"]],
    )
    return target


def load(candidate: Path) -> dict:
    return switch.load_manifest(candidate / "manifest.json")


def run(candidate: Path, target: Path, base: Path, **kwargs) -> dict:
    return switch.publish(
        candidate,
        target,
        load(candidate),
        base / "backups",
        **kwargs,
    )


def test_publish_success(tmp_path):
    candidate = make_candidate(tmp_path)
    target = make_target(tmp_path)
    old_result3 = (target / "result3.csv").read_bytes()

    report = run(candidate, target, tmp_path, dry_run=False)

    assert report["status"] == "PUBLISHED", report
    assert "SYNTH-C001" in (target / "result3.csv").read_text(encoding="utf-8-sig")
    version = json.loads((target / ".result_version.json").read_text(encoding="utf-8"))
    assert version["version"] == "v2-synthetic-test"
    assert report["backup_dir"]
    assert old_result3 != (target / "result3.csv").read_bytes()


def test_dry_run_does_not_modify(tmp_path):
    candidate = make_candidate(tmp_path)
    target = make_target(tmp_path)
    before = {name: (target / name).read_bytes() for name in ("result2.csv", "result3.csv", "result4.csv")}

    report = run(candidate, target, tmp_path, dry_run=True)

    assert report["status"] == "DRY_RUN_READY", report
    for name, content in before.items():
        assert (target / name).read_bytes() == content
    assert not (target / ".result_version.json").exists()


def test_blocked_without_approval(tmp_path):
    candidate = make_candidate(tmp_path, submission_ready=False)
    target = make_target(tmp_path)
    before = (target / "result3.csv").read_bytes()

    report = run(candidate, target, tmp_path, dry_run=False)

    assert report["status"] == "BLOCKED_MANIFEST"
    assert any("submission_ready" in error for error in report["errors"])
    assert (target / "result3.csv").read_bytes() == before


def test_blocked_missing_result2(tmp_path):
    candidate = make_candidate(tmp_path)
    (candidate / "result2.csv").unlink()
    target = make_target(tmp_path)

    report = run(candidate, target, tmp_path, dry_run=False)

    assert report["status"] == "BLOCKED_MANIFEST"
    assert any("result2.csv" in error for error in report["errors"])


def test_blocked_review_in_result2(tmp_path):
    candidate = make_candidate(tmp_path)
    frame = pd.read_csv(candidate / "result2.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    frame.loc[0, "是否构成机会"] = "REVIEW"
    frame.to_csv(candidate / "result2.csv", index=False, encoding="utf-8-sig")
    manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        if item["path"] == "result2.csv":
            item["sha256"] = sha(candidate / "result2.csv")
            item["rows"] = len(frame)
    (candidate / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    report = run(candidate, make_target(tmp_path), tmp_path, dry_run=False)

    assert report["status"] == "BLOCKED_VALIDATION"
    ok, output = switch.run_strict_validation(candidate)
    assert not ok
    assert "REVIEW" in output


def test_blocked_result3_non_opportunity(tmp_path):
    candidate = make_candidate(tmp_path, result3_ids=f"{SYNTH_IDS[0]};{SYNTH_IDS[1]}")
    report = run(candidate, make_target(tmp_path), tmp_path, dry_run=False)
    assert report["status"] == "BLOCKED_VALIDATION"


def test_blocked_result4_cluster_mismatch(tmp_path):
    candidate = make_candidate(tmp_path)
    frame = pd.read_csv(candidate / "result4.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    frame.loc[0, "主题簇编号"] = "SYNTH-C999"
    frame.to_csv(candidate / "result4.csv", index=False, encoding="utf-8-sig")
    manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        if item["path"] == "result4.csv":
            item["sha256"] = sha(candidate / "result4.csv")
    (candidate / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    report = run(candidate, make_target(tmp_path), tmp_path, dry_run=False)

    assert report["status"] == "BLOCKED_VALIDATION"


def test_blocked_hash_mismatch(tmp_path):
    candidate = make_candidate(tmp_path)
    manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64
    (candidate / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    report = run(candidate, make_target(tmp_path), tmp_path, dry_run=False)

    assert report["status"] == "BLOCKED_MANIFEST"
    assert any("SHA256" in error for error in report["errors"])


def test_blocked_service_running(tmp_path, monkeypatch):
    candidate = make_candidate(tmp_path)
    target = make_target(tmp_path)
    before = (target / "result3.csv").read_bytes()
    monkeypatch.setattr(switch, "service_is_running", lambda *args, **kwargs: True)

    report = run(candidate, target, tmp_path, dry_run=False)

    assert report["status"] == "BLOCKED_SERVICE_RUNNING"
    assert (target / "result3.csv").read_bytes() == before


def test_publish_failure_rolls_back(tmp_path, monkeypatch):
    candidate = make_candidate(tmp_path)
    target = make_target(tmp_path)
    before = {name: (target / name).read_bytes() for name in ("result2.csv", "result3.csv", "result4.csv")}
    original_replace = os.replace
    state = {"failed": False}

    def flaky_replace(source, destination):
        destination = Path(destination)
        if (
            not state["failed"]
            and destination.name == "result3.csv"
            and Path(source).parent.name.startswith(".switch_tmp_")
        ):
            state["failed"] = True
            raise OSError("synthetic switch failure")
        return original_replace(source, destination)

    monkeypatch.setattr(switch.os, "replace", flaky_replace)

    report = run(candidate, target, tmp_path, dry_run=False)

    assert report["status"] == "ROLLED_BACK", report
    for name, content in before.items():
        assert (target / name).read_bytes() == content
    assert not (target / ".result_version.json").exists()