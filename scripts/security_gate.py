"""发布前安全门禁。

扫描敏感文件、密钥、绝对路径、团队姓名、受控材料和异常大文件。
日志只输出脱敏片段，不输出密钥全文。

用法：
    python scripts/security_gate.py --target competition_submission
    python scripts/security_gate.py --target competition_submission --report out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "competition_submission"
MAX_FILE_BYTES = 10 * 1024 * 1024
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".sh", ".bat", ".html", ".js", ".css", ".xml",
}

SENSITIVE_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_dsa",
    "credentials.json", "secrets.json", "secret.json",
}
SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db")
CONTROLLED_TOKENS = (
    "locked_evaluation", "blinded", "private_handoff", "audit_package",
    "guo_handoff", "official_materials", "competition_materials",
)

SECRET_PATTERNS = (
    ("deepseek_or_openai_key", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("assigned_secret", re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{12,}")),
)
PATH_PATTERNS = (
    ("windows_user_home", re.compile(r"[A-Za-z]:\\Users\\[^\\\s\"']+")),
    ("linux_user_home", re.compile(r"/home/[^/\s\"']+")),
    ("local_project_path", re.compile(r"[A-Za-z]:\\AIjiaoyu[^\\\s\"']*")),
    ("windows_username", re.compile(r"\b86136\b")),
)
ANONYMITY_PATTERNS = (
    ("team_member_name", re.compile(r"(曹哥|郭哥|赵哥|曹负责|赵负责|郭负责)")),
    ("author_metadata", re.compile(r"(?i)(author|作者)\s*[:=]\s*\S+")),
)


def mask(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    visible = value[:4] if len(value) > 4 else value[:1]
    return f"{visible}***"


def read_text(path: Path) -> str | None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def scan_file(path: Path, root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    relative = path.relative_to(root).as_posix()
    lower_name = path.name.lower()
    if lower_name in SENSITIVE_NAMES or path.suffix.lower() in SENSITIVE_SUFFIXES:
        issues.append(
            {"severity": "HIGH", "type": "sensitive_file", "path": relative, "evidence": path.name}
        )
    if any(token in relative.lower() for token in CONTROLLED_TOKENS):
        issues.append(
            {"severity": "HIGH", "type": "controlled_material", "path": relative, "evidence": "受控目录/文件"}
        )
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        issues.append(
            {"severity": "HIGH", "type": "oversized_file", "path": relative, "evidence": f"{size} bytes"}
        )
    text = read_text(path)
    if text is None:
        return issues
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule_name, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                issues.append(
                    {
                        "severity": "HIGH",
                        "type": rule_name,
                        "path": relative,
                        "line": line_number,
                        "evidence": mask(match.group(0)),
                    }
                )
        for rule_name, pattern in PATH_PATTERNS:
            match = pattern.search(line)
            if match:
                issues.append(
                    {
                        "severity": "HIGH",
                        "type": rule_name,
                        "path": relative,
                        "line": line_number,
                        "evidence": mask(match.group(0)),
                    }
                )
        for rule_name, pattern in ANONYMITY_PATTERNS:
            match = pattern.search(line)
            if match:
                issues.append(
                    {
                        "severity": "MEDIUM",
                        "type": rule_name,
                        "path": relative,
                        "line": line_number,
                        "evidence": mask(match.group(0)),
                    }
                )
    return issues


def scan(targets: list[Path]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "targets": [str(path) for path in targets],
        "files_scanned": 0,
        "issues": [],
        "summary": {},
    }
    for target in targets:
        if not target.exists():
            report["issues"].append(
                {"severity": "HIGH", "type": "missing_target", "path": str(target), "evidence": "目录不存在"}
            )
            continue
        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue
            report["files_scanned"] += 1
            report["issues"].extend(scan_file(path, target))
    counts: dict[str, int] = {}
    for issue in report["issues"]:
        counts[issue["severity"]] = counts.get(issue["severity"], 0) + 1
    report["summary"] = counts
    report["passed"] = counts.get("HIGH", 0) == 0
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="发布前安全门禁")
    parser.add_argument("--target", action="append", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)
    targets = args.target or [DEFAULT_TARGET]
    report = scan([path.resolve() for path in targets])
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())