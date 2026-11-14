"""正式结果原子切换工具。

默认 dry-run，只有显式 --publish 且 manifest 审批通过、严格校验通过、
哈希一致、服务未占用时才替换 results/final 下的 result2/result3/result4。
任何中途失败都会从备份完整回滚。

用法：
    python scripts/switch_official_results.py \
        --candidate-dir path/to/official_candidate \
        --manifest path/to/official_candidate/manifest.json

    # 正式发布
    python scripts/switch_official_results.py \
        --candidate-dir path/to/official_candidate \
        --manifest path/to/official_candidate/manifest.json --publish
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "results" / "final"
DEFAULT_BACKUP = ROOT / "results" / "_switch_backups"
SCHEMA_VERSION = "official_result_switch_v1"
REQUIRED_FILES = ("result2.csv", "result3.csv", "result4.csv")
VERSION_FILE = ".result_version.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"manifest 不存在：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest JSON 解析失败：{exc}") from exc
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"manifest schema_version 必须为 {SCHEMA_VERSION}，实际为 {data.get('schema_version')!r}"
        )
    return data


def _candidate_result1(candidate_dir: Path) -> Path | None:
    for name in ("result1.csv", "result1_Final_All.csv"):
        path = candidate_dir / name
        if path.exists():
            return path
    return None


def verify_candidate(candidate_dir: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    approval = manifest.get("approval") or {}
    if approval.get("submission_ready") is not True:
        errors.append(
            "审批标志 submission_ready 不为 true（当前为 "
            f"{approval.get('submission_ready')!r}），禁止发布"
        )
    if not str(manifest.get("version") or "").strip():
        errors.append("manifest 缺少 version")
    if not str(manifest.get("algorithm_version") or "").strip():
        errors.append("manifest 缺少 algorithm_version")

    result1 = _candidate_result1(candidate_dir)
    expected_r1 = str(manifest.get("result1_sha256") or "")
    if result1 is None:
        errors.append("候选目录缺少 result1.csv / result1_Final_All.csv")
    elif not expected_r1:
        errors.append("manifest 缺少 result1_sha256")
    elif sha256_file(result1) != expected_r1:
        errors.append("result1 SHA256 与 manifest 不一致")

    files = {str(item.get("path")): item for item in manifest.get("files", [])}
    for name in REQUIRED_FILES:
        item = files.get(name)
        path = candidate_dir / name
        if item is None:
            errors.append(f"manifest 缺少文件条目：{name}")
            continue
        if not path.exists():
            errors.append(f"候选文件不存在：{name}")
            continue
        if item.get("formal") is not True:
            errors.append(f"{name} 未标记为正式提交件")
        if str(item.get("status") or "") != "READY":
            errors.append(f"{name} 状态不是 READY（{item.get('status')!r}）")
        expected = str(item.get("sha256") or "")
        if expected and sha256_file(path) != expected:
            errors.append(f"{name} SHA256 与 manifest 不一致")
        try:
            rows = int(item.get("rows", 0))
        except (TypeError, ValueError):
            rows = 0
        if rows <= 0:
            errors.append(f"{name} 数据行数为 0，占位文件禁止发布")
    return errors


def run_strict_validation(candidate_dir: Path) -> tuple[bool, str]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    command = [
        sys.executable,
        str(ROOT / "scripts" / "validate_csv.py"),
        "--strict",
        "--results-dir",
        str(candidate_dir),
    ]
    process = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    output = (process.stdout or "") + (process.stderr or "")
    return process.returncode == 0, output.strip()


def service_is_running(host: str = "127.0.0.1", port: int = 8501) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def current_version(target_dir: Path) -> dict[str, Any]:
    path = target_dir / VERSION_FILE
    if not path.exists():
        return {"version": "v1-experimental", "source": "implicit"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": "unknown", "source": "invalid"}


def backup_current(target_dir: Path, backup_root: Path) -> Path | None:
    existing = {name: target_dir / name for name in REQUIRED_FILES if (target_dir / name).exists()}
    if not existing:
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = backup_root / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name, path in existing.items():
        shutil.copy2(path, backup_dir / name)
    for extra in (VERSION_FILE, "result2_resolved_subset.csv", "result2_export_blockers.csv"):
        source = target_dir / extra
        if source.exists():
            shutil.copy2(source, backup_dir / extra)
    return backup_dir


def rollback(target_dir: Path, backup_dir: Path | None) -> None:
    if backup_dir is None:
        return
    for name in REQUIRED_FILES:
        backup_file = backup_dir / name
        target_file = target_dir / name
        if backup_file.exists():
            os.replace(backup_file, target_file)
        elif target_file.exists():
            target_file.unlink()
    version_backup = backup_dir / VERSION_FILE
    version_target = target_dir / VERSION_FILE
    if version_backup.exists():
        os.replace(version_backup, version_target)
    elif version_target.exists():
        version_target.unlink()


def publish(
    candidate_dir: Path,
    target_dir: Path,
    manifest: dict[str, Any],
    backup_root: Path,
    *,
    dry_run: bool = True,
    allow_service_running: bool = False,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_dir": str(candidate_dir),
        "target_dir": str(target_dir),
        "mode": "dry-run" if dry_run else "publish",
        "status": "UNKNOWN",
        "errors": [],
        "warnings": [],
        "files": [],
    }

    report["errors"].extend(verify_candidate(candidate_dir, manifest))
    if report["errors"]:
        report["status"] = "BLOCKED_MANIFEST"
        return report

    ok, output = run_strict_validation(candidate_dir)
    report["strict_validation"] = {
        "passed": ok,
        "output_tail": "\n".join(output.splitlines()[-8:]),
    }
    if not ok:
        report["errors"].append("严格校验未通过，禁止发布")
        report["status"] = "BLOCKED_VALIDATION"
        return report

    previous = current_version(target_dir)
    if previous.get("version") == manifest.get("version"):
        for name in REQUIRED_FILES:
            item = next(
                (entry for entry in manifest["files"] if entry.get("path") == name), {}
            )
            target_file = target_dir / name
            if target_file.exists() and item.get("sha256") != sha256_file(target_file):
                report["errors"].append(
                    f"同版本 {manifest.get('version')} 但 {name} 哈希不同，禁止覆盖"
                )
    report["previous_version"] = previous.get("version")
    report["new_version"] = manifest.get("version")
    if report["errors"]:
        report["status"] = "BLOCKED_VERSION"
        return report

    if not dry_run and service_is_running() and not allow_service_running:
        report["errors"].append(
            "检测到 127.0.0.1:8501 服务正在运行；请先停止服务再发布，"
            "或显式使用 --allow-service-running"
        )
        report["status"] = "BLOCKED_SERVICE_RUNNING"
        return report

    report["files"] = [
        {
            "path": name,
            "candidate": str(candidate_dir / name),
            "target": str(target_dir / name),
            "sha256": sha256_file(candidate_dir / name),
        }
        for name in REQUIRED_FILES
    ]

    if dry_run:
        report["status"] = "DRY_RUN_READY"
        return report

    backup_dir = backup_current(target_dir, backup_root)
    report["backup_dir"] = str(backup_dir) if backup_dir else None
    target_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=".switch_tmp_", dir=str(target_dir)))
    replaced: list[str] = []
    try:
        staged: dict[str, Path] = {}
        for name in REQUIRED_FILES:
            staged_path = temp_dir / name
            shutil.copy2(candidate_dir / name, staged_path)
            expected = sha256_file(candidate_dir / name)
            if sha256_file(staged_path) != expected:
                raise RuntimeError(f"暂存文件哈希校验失败：{name}")
            staged[name] = staged_path

        for name in REQUIRED_FILES:
            os.replace(staged[name], target_dir / name)
            replaced.append(name)

        version_payload = {
            "version": manifest.get("version"),
            "algorithm_version": manifest.get("algorithm_version"),
            "algorithm_config_version": manifest.get("algorithm_config_version"),
            "approval_version": (manifest.get("approval") or {}).get("approval_version"),
            "switched_at": datetime.now().isoformat(timespec="seconds"),
            "source_manifest": str(candidate_dir),
            "files": {
                entry["path"]: entry["sha256"] for entry in manifest.get("files", [])
            },
        }
        version_path = target_dir / VERSION_FILE
        temp_version = temp_dir / VERSION_FILE
        temp_version.write_text(
            json.dumps(version_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temp_version, version_path)
        report["status"] = "PUBLISHED"
    except Exception as exc:
        report["errors"].append(f"切换失败：{exc}")
        rollback(target_dir, backup_dir)
        report["status"] = "ROLLED_BACK"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    report["replaced_files"] = replaced
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="正式结果原子切换工具")
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--target-dir", default=DEFAULT_TARGET, type=Path)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP, type=Path)
    parser.add_argument("--publish", action="store_true", help="实际替换；默认 dry-run")
    parser.add_argument("--allow-service-running", action="store_true")
    parser.add_argument("--report", type=Path, default=None, help="输出 JSON 报告路径")
    args = parser.parse_args(argv)

    candidate = args.candidate_dir.resolve()
    manifest_path = args.manifest or (candidate / "manifest.json")
    try:
        manifest = load_manifest(manifest_path)
    except ValueError as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED_MANIFEST",
            "errors": [str(exc)],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    report = publish(
        candidate,
        args.target_dir.resolve(),
        manifest,
        args.backup_dir.resolve(),
        dry_run=not args.publish,
        allow_service_running=args.allow_service_running,
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")

    if report["status"] in {"DRY_RUN_READY", "PUBLISHED"}:
        return 0
    if report["status"].startswith("BLOCKED"):
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())