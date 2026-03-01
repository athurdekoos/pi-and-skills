#!/usr/bin/env python3
"""Skill health auditor — scans installed skills for common problems."""

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


@dataclass
class Finding:
    check_id: str
    severity: Severity
    skill_name: str
    message: str
    file_path: Optional[str] = None


class SkillAuditor:
    """Audits a directory of skills for health issues."""

    STALE_DAYS = 90
    MAX_LINES = 500
    MIN_DESC_LEN = 20

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)

    def audit(self) -> list:
        findings: list = []
        if not self.skills_dir.is_dir():
            return findings

        skill_names: list = []

        for entry in sorted(self.skills_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue

            skill_md = entry / "SKILL.md"
            if not skill_md.exists():
                findings.append(Finding(
                    check_id="ORPHAN",
                    severity=Severity.ERROR,
                    skill_name=entry.name,
                    message="Directory exists but has no SKILL.md",
                    file_path=str(entry),
                ))
                continue

            # Parse frontmatter
            frontmatter = self._parse_frontmatter(skill_md)
            name = frontmatter.get("name", "")
            desc = frontmatter.get("description", "")

            # NAME check
            if not name:
                findings.append(Finding(
                    check_id="NAME",
                    severity=Severity.ERROR,
                    skill_name=entry.name,
                    message="Missing 'name' in SKILL.md frontmatter",
                    file_path=str(skill_md),
                ))

            # DESC check
            if not desc or len(desc.strip()) < self.MIN_DESC_LEN:
                findings.append(Finding(
                    check_id="DESC",
                    severity=Severity.WARN,
                    skill_name=entry.name,
                    message=f"Description is missing or too short ({len(desc.strip())} chars, min {self.MIN_DESC_LEN})",
                    file_path=str(skill_md),
                ))

            # SIZE check
            body_lines = self._count_body_lines(skill_md)
            if body_lines > self.MAX_LINES:
                findings.append(Finding(
                    check_id="SIZE",
                    severity=Severity.WARN,
                    skill_name=entry.name,
                    message=f"SKILL.md body is {body_lines} lines (recommended max {self.MAX_LINES})",
                    file_path=str(skill_md),
                ))

            # REF_BROKEN check
            findings.extend(self._check_broken_refs(entry, skill_md))

            # SCRIPT_ERR check
            findings.extend(self._check_scripts(entry))

            # STALE check
            findings.extend(self._check_staleness(entry))

            # EMPTY_DIR check
            findings.extend(self._check_empty_dirs(entry))

            skill_names.append((name or entry.name, entry))

        # CONFLICT check (near-duplicate names)
        findings.extend(self._check_conflicts(skill_names))

        return findings

    def _parse_frontmatter(self, skill_md: Path) -> dict:
        """Parse YAML frontmatter from SKILL.md (simple parser, no PyYAML dep)."""
        text = skill_md.read_text(errors="replace")
        if not text.startswith("---"):
            return {}
        end = text.find("---", 3)
        if end == -1:
            return {}
        fm_text = text[3:end].strip()
        result = {}
        current_key = None
        current_val_lines = []

        for line in fm_text.split("\n"):
            m = re.match(r"^(\w[\w-]*):\s*(.*)", line)
            if m:
                if current_key:
                    result[current_key] = " ".join(current_val_lines).strip()
                current_key = m.group(1)
                val = m.group(2).strip()
                if val == ">":
                    current_val_lines = []
                else:
                    current_val_lines = [val]
            elif current_key and line.startswith("  "):
                current_val_lines.append(line.strip())

        if current_key:
            result[current_key] = " ".join(current_val_lines).strip()

        return result

    def _count_body_lines(self, skill_md: Path) -> int:
        text = skill_md.read_text(errors="replace")
        if not text.startswith("---"):
            return len(text.splitlines())
        end = text.find("---", 3)
        if end == -1:
            return len(text.splitlines())
        body = text[end + 3:]
        return len(body.strip().splitlines())

    def _check_broken_refs(self, skill_dir: Path, skill_md: Path) -> list:
        findings = []
        text = skill_md.read_text(errors="replace")
        refs = re.findall(r'`((?:references|scripts|assets)/[^`]+)`', text)
        for ref in refs:
            ref_path = skill_dir / ref
            if not ref_path.exists():
                findings.append(Finding(
                    check_id="REF_BROKEN",
                    severity=Severity.ERROR,
                    skill_name=skill_dir.name,
                    message=f"Referenced file does not exist: {ref}",
                    file_path=str(ref_path),
                ))
        return findings

    def _check_scripts(self, skill_dir: Path) -> list:
        findings = []
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.is_dir():
            return findings
        for py_file in scripts_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                findings.append(Finding(
                    check_id="SCRIPT_ERR",
                    severity=Severity.WARN,
                    skill_name=skill_dir.name,
                    message=f"Script compilation error: {e}",
                    file_path=str(py_file),
                ))
        return findings

    def _check_staleness(self, skill_dir: Path) -> list:
        findings = []
        cutoff = datetime.now().timestamp() - (self.STALE_DAYS * 86400)
        newest = 0
        for f in skill_dir.rglob("*"):
            if f.is_file():
                newest = max(newest, f.stat().st_mtime)
        if newest > 0 and newest < cutoff:
            days_ago = int((datetime.now().timestamp() - newest) / 86400)
            findings.append(Finding(
                check_id="STALE",
                severity=Severity.INFO,
                skill_name=skill_dir.name,
                message=f"No files modified in {days_ago} days",
            ))
        return findings

    def _check_empty_dirs(self, skill_dir: Path) -> list:
        findings = []
        for subdir_name in ("scripts", "references", "assets"):
            subdir = skill_dir / subdir_name
            if subdir.is_dir() and not any(subdir.iterdir()):
                findings.append(Finding(
                    check_id="EMPTY_DIR",
                    severity=Severity.INFO,
                    skill_name=skill_dir.name,
                    message=f"Empty directory: {subdir_name}/",
                ))
        return findings

    def _check_conflicts(self, skill_names: list) -> list:
        findings = []
        names = [(n.lower(), d) for n, d in skill_names]
        for i, (name_a, dir_a) in enumerate(names):
            for name_b, dir_b in names[i + 1:]:
                dist = self._levenshtein(name_a, name_b)
                if 0 < dist <= 2:
                    findings.append(Finding(
                        check_id="CONFLICT",
                        severity=Severity.WARN,
                        skill_name=dir_a.name,
                        message=f"Name '{dir_a.name}' is very similar to '{dir_b.name}' (edit distance {dist})",
                    ))
        return findings

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return SkillAuditor._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
            prev = curr
        return prev[len(s2)]

    def to_json(self, findings: list) -> str:
        summary = {
            "errors": sum(1 for f in findings if f.severity == Severity.ERROR),
            "warnings": sum(1 for f in findings if f.severity == Severity.WARN),
            "info": sum(1 for f in findings if f.severity == Severity.INFO),
            "total": len(findings),
        }
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "skills_dir": str(self.skills_dir),
            "summary": summary,
            "findings": [
                {
                    "check_id": f.check_id,
                    "severity": f.severity.value,
                    "skill_name": f.skill_name,
                    "message": f.message,
                    "file_path": f.file_path,
                }
                for f in findings
            ],
        }, indent=2)

    def to_report(self, findings: list) -> str:
        if not findings:
            return "✅ All skills healthy — no issues found."

        lines = [
            "=" * 60,
            "  SKILL HEALTH REPORT",
            f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
        ]

        for severity in (Severity.ERROR, Severity.WARN, Severity.INFO):
            group = [f for f in findings if f.severity == severity]
            if not group:
                continue
            icon = {"ERROR": "🔴", "WARN": "🟡", "INFO": "ℹ️"}[severity.value]
            lines.append(f"{icon} {severity.value} ({len(group)})")
            lines.append("-" * 40)
            for f in group:
                lines.append(f"  [{f.check_id}] {f.skill_name}: {f.message}")
            lines.append("")

        summary_errors = sum(1 for f in findings if f.severity == Severity.ERROR)
        summary_warns = sum(1 for f in findings if f.severity == Severity.WARN)
        lines.append(f"Total: {len(findings)} issues ({summary_errors} errors, {summary_warns} warnings)")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit installed skills for health issues")
    parser.add_argument(
        "--skills-dir",
        default=os.path.expanduser("~/.agents/skills"),
        help="Path to skills directory (default: ~/.agents/skills)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--email", type=str, help="Email address to send report to (via msmtp)")
    args = parser.parse_args()

    auditor = SkillAuditor(args.skills_dir)
    findings = auditor.audit()

    if args.json:
        output = auditor.to_json(findings)
    else:
        output = auditor.to_report(findings)

    print(output)

    if args.email:
        _send_email(args.email, findings, auditor)


def _send_email(to_addr: str, findings: list, auditor: SkillAuditor):
    """Send report via msmtp."""
    n_issues = len(findings)
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = (
        f"[Skill Health] {date_str} — {n_issues} issues found"
        if n_issues
        else f"[Skill Health] {date_str} — All clear"
    )
    body = auditor.to_report(findings)

    msg = f"Subject: {subject}\nTo: {to_addr}\nContent-Type: text/plain; charset=utf-8\n\n{body}"

    try:
        proc = subprocess.run(
            ["msmtp", to_addr],
            input=msg,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            print(f"Warning: msmtp failed: {proc.stderr}", file=sys.stderr)
            _fallback_save(body, date_str)
    except FileNotFoundError:
        print("Warning: msmtp not installed. Report not sent.", file=sys.stderr)
        _fallback_save(body, date_str)


def _fallback_save(body: str, date_str: str):
    """Save report to /tmp when email fails."""
    fallback = f"/tmp/skill-health-report-{date_str}.txt"
    with open(fallback, "w") as f:
        f.write(body)
    print(f"Report saved to {fallback}", file=sys.stderr)


if __name__ == "__main__":
    main()
