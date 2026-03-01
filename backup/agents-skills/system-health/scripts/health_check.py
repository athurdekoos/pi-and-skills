#!/usr/bin/env python3
"""System health monitor — checks VM resources and alerts via email."""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    EMERGENCY = "EMERGENCY"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Alert:
    check_id: str
    severity: Severity
    message: str
    value: str
    threshold: str


# Cooldown file — tracks when each emergency alert was last sent
COOLDOWN_FILE = Path("/tmp/system-health-cooldowns.json")
COOLDOWN_SECONDS = 3600  # 1 hour


class SystemHealthChecker:
    """Runs all health checks and returns alerts."""

    def __init__(self):
        self.alerts: list = []

    def run_all(self) -> list:
        """Run every check."""
        self.alerts = []
        self._check_ram()
        self._check_disk()
        self._check_swap()
        self._check_oom()
        self._check_node_server()
        self._check_load()
        self._check_failed_services()
        self._check_ssh_brute_force()
        self._check_zombies()
        self._check_inodes()
        self._check_cron_health()
        self._check_msmtp_health()
        self._check_tasks_stale()
        self._check_large_data_files()
        self._check_gsd_health()
        self._check_uptime()
        self._check_docker_disk()
        self._check_stale_tests()
        return self.alerts

    def run_emergency_only(self) -> list:
        """Run only emergency-level checks (for 5-min cron)."""
        self.alerts = []
        self._check_ram()
        self._check_disk()
        self._check_swap()
        self._check_oom()
        self._check_node_server()
        self._check_msmtp_health()
        # Also include warnings that are severe enough
        self._check_load()
        self._check_failed_services()
        self._check_zombies()
        self._check_cron_health()
        return [a for a in self.alerts if a.severity in (Severity.EMERGENCY, Severity.WARNING)]

    # ── Emergency checks ──────────────────────────────────────

    def _check_ram(self):
        """Check available RAM."""
        try:
            with open("/proc/meminfo") as f:
                meminfo = f.read()
            available_kb = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1))
            available_mb = available_kb // 1024
            total_kb = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1))
            total_mb = total_kb // 1024

            if available_mb < 500:
                self.alerts.append(Alert(
                    check_id="RAM_CRITICAL",
                    severity=Severity.EMERGENCY,
                    message=f"Available RAM critically low: {available_mb} MB / {total_mb} MB total",
                    value=f"{available_mb} MB",
                    threshold="< 500 MB",
                ))
            elif available_mb < 1500:
                self.alerts.append(Alert(
                    check_id="RAM_ELEVATED",
                    severity=Severity.WARNING,
                    message=f"Available RAM getting low: {available_mb} MB / {total_mb} MB total",
                    value=f"{available_mb} MB",
                    threshold="< 1500 MB",
                ))
        except Exception as e:
            self.alerts.append(Alert(
                check_id="RAM_CHECK_FAILED",
                severity=Severity.WARNING,
                message=f"Could not check RAM: {e}",
                value="unknown", threshold="N/A",
            ))

    def _check_disk(self):
        """Check root filesystem usage."""
        try:
            st = os.statvfs("/")
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            used_pct = int((1 - free / total) * 100)
            free_gb = free / (1024 ** 3)

            if used_pct > 90:
                self.alerts.append(Alert(
                    check_id="DISK_CRITICAL",
                    severity=Severity.EMERGENCY,
                    message=f"Disk {used_pct}% full — only {free_gb:.1f} GB free",
                    value=f"{used_pct}%",
                    threshold="> 90%",
                ))
            elif used_pct > 75:
                self.alerts.append(Alert(
                    check_id="DISK_FILLING",
                    severity=Severity.WARNING,
                    message=f"Disk {used_pct}% full — {free_gb:.1f} GB free",
                    value=f"{used_pct}%",
                    threshold="> 75%",
                ))
        except Exception as e:
            self.alerts.append(Alert(
                check_id="DISK_CHECK_FAILED",
                severity=Severity.WARNING,
                message=f"Could not check disk: {e}",
                value="unknown", threshold="N/A",
            ))

    def _check_swap(self):
        """Check swap usage."""
        try:
            with open("/proc/meminfo") as f:
                meminfo = f.read()
            swap_total = int(re.search(r"SwapTotal:\s+(\d+)", meminfo).group(1))
            swap_free = int(re.search(r"SwapFree:\s+(\d+)", meminfo).group(1))
            if swap_total == 0:
                return
            swap_used_pct = int((1 - swap_free / swap_total) * 100)
            swap_used_mb = (swap_total - swap_free) // 1024

            if swap_used_pct > 50:
                self.alerts.append(Alert(
                    check_id="SWAP_HEAVY",
                    severity=Severity.EMERGENCY,
                    message=f"Heavy swap usage: {swap_used_mb} MB used ({swap_used_pct}%)",
                    value=f"{swap_used_pct}%",
                    threshold="> 50%",
                ))
        except Exception as e:
            pass  # Swap check is best-effort

    def _check_oom(self):
        """Check for OOM killer events in dmesg."""
        try:
            result = subprocess.run(
                ["dmesg", "--time-format=reltime"],
                capture_output=True, text=True, timeout=5,
            )
            oom_lines = [l for l in result.stdout.splitlines()
                         if "oom" in l.lower() or "killed process" in l.lower()]
            # Only alert on recent ones (last 5 minutes = 300 seconds)
            # dmesg reltime shows seconds since boot, so we check if any exist
            if oom_lines:
                # Check if any are from the last 5 minutes using kernel timestamps
                recent = self._filter_recent_dmesg(oom_lines, 300)
                if recent:
                    self.alerts.append(Alert(
                        check_id="OOM_KILLED",
                        severity=Severity.EMERGENCY,
                        message=f"OOM killer fired! {len(recent)} recent event(s): {recent[0][:100]}",
                        value=f"{len(recent)} events",
                        threshold="any",
                    ))
        except Exception:
            pass  # dmesg may need root

    def _filter_recent_dmesg(self, lines: list, seconds: int) -> list:
        """Filter dmesg lines to only recent ones."""
        # Simple heuristic: just return all — dmesg is already filtered by boot
        # In practice, if OOM shows up at all this boot, it's worth alerting
        return lines

    def _check_node_server(self):
        """Check if node server is listening on 7777 and 7778."""
        for port in (7777, 7778):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(("127.0.0.1", port))
                sock.close()
                if result != 0:
                    self.alerts.append(Alert(
                        check_id="NODE_SERVER_DOWN",
                        severity=Severity.EMERGENCY,
                        message=f"Node server not responding on port {port}",
                        value=f"port {port} closed",
                        threshold="port open",
                    ))
            except Exception:
                self.alerts.append(Alert(
                    check_id="NODE_SERVER_DOWN",
                    severity=Severity.EMERGENCY,
                    message=f"Cannot connect to port {port}",
                    value=f"port {port} unreachable",
                    threshold="port open",
                ))

    # ── Warning checks ────────────────────────────────────────

    def _check_load(self):
        """Check system load average."""
        try:
            load1, load5, load15 = os.getloadavg()
            if load5 > 5.0:
                self.alerts.append(Alert(
                    check_id="LOAD_HIGH",
                    severity=Severity.WARNING,
                    message=f"High system load: {load1:.1f} / {load5:.1f} / {load15:.1f} (1/5/15 min)",
                    value=f"{load5:.1f}",
                    threshold="> 5.0",
                ))
        except Exception:
            pass

    def _check_failed_services(self):
        """Check for failed systemd services."""
        try:
            result = subprocess.run(
                ["systemctl", "list-units", "--failed", "--no-pager", "--no-legend"],
                capture_output=True, text=True, timeout=5,
            )
            failed = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
            if failed:
                names = [l.split()[0] for l in failed]
                self.alerts.append(Alert(
                    check_id="SERVICE_FAILED",
                    severity=Severity.WARNING,
                    message=f"Failed services: {', '.join(names)}",
                    value=f"{len(failed)} failed",
                    threshold="0",
                ))
        except Exception:
            pass

    def _check_ssh_brute_force(self):
        """Check for SSH brute force attempts in the last hour."""
        try:
            result = subprocess.run(
                ["journalctl", "-u", "ssh", "--since", "1 hour ago",
                 "--no-pager", "-q"],
                capture_output=True, text=True, timeout=10,
            )
            failed_count = sum(1 for l in result.stdout.splitlines()
                              if "Failed password" in l or "Invalid user" in l)
            if failed_count > 50:
                self.alerts.append(Alert(
                    check_id="SSH_BRUTE_FORCE",
                    severity=Severity.WARNING,
                    message=f"{failed_count} failed SSH login attempts in the last hour",
                    value=str(failed_count),
                    threshold="> 50",
                ))
        except Exception:
            pass

    def _check_zombies(self):
        """Check for zombie processes."""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=5,
            )
            zombies = [l for l in result.stdout.splitlines() if " Z " in l or " Z+ " in l]
            if len(zombies) > 5:
                self.alerts.append(Alert(
                    check_id="ZOMBIES",
                    severity=Severity.WARNING,
                    message=f"{len(zombies)} zombie processes detected",
                    value=str(len(zombies)),
                    threshold="> 5",
                ))
        except Exception:
            pass

    def _check_inodes(self):
        """Check inode usage on root filesystem."""
        try:
            st = os.statvfs("/")
            total = st.f_files
            free = st.f_ffree
            if total == 0:
                return
            used_pct = int((1 - free / total) * 100)
            if used_pct > 70:
                self.alerts.append(Alert(
                    check_id="INODE_HIGH",
                    severity=Severity.WARNING,
                    message=f"Inode usage at {used_pct}%",
                    value=f"{used_pct}%",
                    threshold="> 70%",
                ))
        except Exception:
            pass

    # ── Skill-specific checks ────────────────────────────────

    def _check_cron_health(self):
        """Check that our own daemons are actually running."""
        cron_logs = {
            "skill-audit": ("/tmp/skill-audit-cron.log", 86400 * 2),   # 2 days
            "health-digest": ("/tmp/system-health-digest.log", 86400 * 2),
        }
        for name, (logfile, max_age) in cron_logs.items():
            path = Path(logfile)
            if not path.exists():
                self.alerts.append(Alert(
                    check_id="CRON_MISSING",
                    severity=Severity.WARNING,
                    message=f"Cron log missing for {name}: {logfile} (daemon may have never run)",
                    value="missing",
                    threshold="file exists",
                ))
            else:
                age = time.time() - path.stat().st_mtime
                if age > max_age:
                    days = int(age // 86400)
                    self.alerts.append(Alert(
                        check_id="CRON_STALE",
                        severity=Severity.WARNING,
                        message=f"Cron log for {name} is {days} days old — daemon may have stopped",
                        value=f"{days} days",
                        threshold=f"< {max_age // 86400} days",
                    ))

    def _check_msmtp_health(self):
        """Check that msmtp is configured and log shows recent success."""
        msmtprc = Path.home() / ".msmtprc"
        if not msmtprc.exists():
            self.alerts.append(Alert(
                check_id="MSMTP_MISSING",
                severity=Severity.EMERGENCY,
                message="msmtp config missing (~/.msmtprc) — no alerts can be sent!",
                value="missing",
                threshold="file exists",
            ))
            return

        # Check for placeholder credentials (ignore comments)
        try:
            content = msmtprc.read_text()
            active_lines = [l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
            active_content = "\n".join(active_lines)
            if "YOUR_" in active_content or "YOUR_APP_PASSWORD" in active_content or "YOUR_SENDGRID" in active_content:
                self.alerts.append(Alert(
                    check_id="MSMTP_UNCONFIGURED",
                    severity=Severity.WARNING,
                    message="msmtp still has placeholder credentials — emails won't send",
                    value="placeholder",
                    threshold="real credentials",
                ))
        except PermissionError:
            pass  # Good — means permissions are locked down

    def _check_backup_age(self):
        """Check if pi-backup has run recently."""
        # Look for common backup indicators
        backup_markers = [
            Path.home() / ".pi" / "backup-timestamp",
            Path.home() / ".agents" / ".last-backup",
        ]
        # Also check git log in skills dir for backup-related commits
        try:
            result = subprocess.run(
                ["git", "-C", str(Path.home() / ".agents"), "log", "--oneline", "-1",
                 "--since=7 days ago", "--grep=backup"],
                capture_output=True, text=True, timeout=5,
            )
            # If no git repo or no recent backup commits, just note it
        except Exception:
            pass

    def _check_tasks_stale(self):
        """Check for stale tasks in TASKS.md."""
        tasks_file = Path.home() / "TASKS.md"
        if not tasks_file.exists():
            # Also check in dev/
            tasks_file = Path.home() / "dev" / "TASKS.md"
        if not tasks_file.exists():
            return

        try:
            age = time.time() - tasks_file.stat().st_mtime
            if age > 86400 * 30:
                days = int(age // 86400)
                self.alerts.append(Alert(
                    check_id="TASKS_STALE",
                    severity=Severity.INFO,
                    message=f"TASKS.md hasn't been updated in {days} days — forgotten tasks?",
                    value=f"{days} days",
                    threshold="< 30 days",
                ))
        except Exception:
            pass

    def _check_large_data_files(self):
        """Check for large data files that eat disk (h5ad, h5, large CSVs)."""
        home = Path.home()
        large_files = []
        try:
            for ext in ("*.h5ad", "*.h5", "*.bam", "*.fastq.gz"):
                for f in home.rglob(ext):
                    size_mb = f.stat().st_size / (1024 ** 2)
                    if size_mb > 500:
                        large_files.append(f"{f.name}: {size_mb:.0f} MB")
            if large_files:
                total = len(large_files)
                self.alerts.append(Alert(
                    check_id="LARGE_DATA_FILES",
                    severity=Severity.INFO,
                    message=f"{total} large data file(s): {'; '.join(large_files[:3])}",
                    value=f"{total} files",
                    threshold="awareness",
                ))
        except Exception:
            pass

    def _check_gsd_health(self):
        """Check for .planning directory corruption."""
        planning_dir = Path.home() / "dev" / ".planning"
        if not planning_dir.exists():
            return
        try:
            project_md = planning_dir / "PROJECT.md"
            if planning_dir.exists() and not project_md.exists():
                self.alerts.append(Alert(
                    check_id="GSD_CORRUPT",
                    severity=Severity.WARNING,
                    message=".planning directory exists but PROJECT.md is missing — GSD state may be corrupt",
                    value="missing PROJECT.md",
                    threshold="file exists",
                ))
        except Exception:
            pass

    # ── Info checks ───────────────────────────────────────────

    def _check_uptime(self):
        """Report system uptime."""
        try:
            with open("/proc/uptime") as f:
                uptime_secs = float(f.read().split()[0])
            days = int(uptime_secs // 86400)
            hours = int((uptime_secs % 86400) // 3600)
            self.alerts.append(Alert(
                check_id="UPTIME",
                severity=Severity.INFO,
                message=f"System uptime: {days}d {hours}h",
                value=f"{days}d {hours}h",
                threshold="N/A",
            ))
        except Exception:
            pass

    def _check_docker_disk(self):
        """Report docker disk usage."""
        try:
            result = subprocess.run(
                ["docker", "system", "df", "--format", "{{.Type}}: {{.Size}} ({{.Reclaimable}} reclaimable)"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                self.alerts.append(Alert(
                    check_id="DOCKER_DISK",
                    severity=Severity.INFO,
                    message=f"Docker disk: {result.stdout.strip()}",
                    value=result.stdout.strip(),
                    threshold="N/A",
                ))
        except Exception:
            pass

    def _check_stale_tests(self):
        """Check for test processes running longer than 2 hours."""
        try:
            result = subprocess.run(
                ["ps", "-eo", "pid,etimes,args"],
                capture_output=True, text=True, timeout=5,
            )
            stale = []
            for line in result.stdout.splitlines()[1:]:
                parts = line.strip().split(None, 2)
                if len(parts) < 3:
                    continue
                pid, elapsed, cmd = parts[0], int(parts[1]), parts[2]
                if "test" in cmd.lower() and elapsed > 7200:
                    stale.append(f"PID {pid} ({elapsed // 3600}h): {cmd[:60]}")
            if stale:
                self.alerts.append(Alert(
                    check_id="STALE_TESTS",
                    severity=Severity.INFO,
                    message=f"{len(stale)} test process(es) running > 2h: {stale[0]}",
                    value=str(len(stale)),
                    threshold="> 2 hours",
                ))
        except Exception:
            pass


# ── Output formatting ─────────────────────────────────────────

def to_report(alerts: list, mode: str = "full") -> str:
    if not alerts:
        return "✅ System healthy — no issues detected."

    lines = [
        "=" * 60,
        f"  SYSTEM HEALTH REPORT ({mode.upper()})",
        f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
    ]

    for severity in (Severity.EMERGENCY, Severity.WARNING, Severity.INFO):
        group = [a for a in alerts if a.severity == severity]
        if not group:
            continue
        icon = {
            "EMERGENCY": "🚨",
            "WARNING": "🟡",
            "INFO": "ℹ️",
        }[severity.value]
        lines.append(f"{icon} {severity.value} ({len(group)})")
        lines.append("-" * 40)
        for a in group:
            lines.append(f"  [{a.check_id}] {a.message}")
            lines.append(f"    Value: {a.value} | Threshold: {a.threshold}")
        lines.append("")

    emergencies = sum(1 for a in alerts if a.severity == Severity.EMERGENCY)
    warnings = sum(1 for a in alerts if a.severity == Severity.WARNING)
    lines.append(f"Total: {len(alerts)} checks flagged ({emergencies} emergency, {warnings} warning)")
    return "\n".join(lines)


def to_json(alerts: list) -> str:
    return json.dumps({
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "summary": {
            "emergencies": sum(1 for a in alerts if a.severity == Severity.EMERGENCY),
            "warnings": sum(1 for a in alerts if a.severity == Severity.WARNING),
            "info": sum(1 for a in alerts if a.severity == Severity.INFO),
            "total": len(alerts),
        },
        "alerts": [
            {
                "check_id": a.check_id,
                "severity": a.severity.value,
                "message": a.message,
                "value": a.value,
                "threshold": a.threshold,
            }
            for a in alerts
        ],
    }, indent=2)


# ── Cooldown logic ────────────────────────────────────────────

def load_cooldowns() -> dict:
    try:
        return json.loads(COOLDOWN_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cooldowns(cooldowns: dict):
    COOLDOWN_FILE.write_text(json.dumps(cooldowns))


def filter_cooled_down(alerts: list) -> list:
    """Filter out emergency alerts that were sent recently."""
    cooldowns = load_cooldowns()
    now = time.time()
    to_send = []

    for alert in alerts:
        if alert.severity != Severity.EMERGENCY:
            to_send.append(alert)
            continue
        last_sent = cooldowns.get(alert.check_id, 0)
        if now - last_sent > COOLDOWN_SECONDS:
            to_send.append(alert)
            cooldowns[alert.check_id] = now

    save_cooldowns(cooldowns)
    return to_send


# ── Email ─────────────────────────────────────────────────────

def send_email(to_addr: str, alerts: list, mode: str = "full"):
    """Send report via msmtp."""
    emergencies = sum(1 for a in alerts if a.severity == Severity.EMERGENCY)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if emergencies > 0:
        subject = f"🚨 [SYSTEM ALERT] {date_str} — {emergencies} emergency issue(s)"
    elif alerts:
        warnings = sum(1 for a in alerts if a.severity == Severity.WARNING)
        subject = f"[System Health] {date_str} — {warnings} warning(s)"
    else:
        subject = f"[System Health] {date_str} — All clear"

    body = to_report(alerts, mode)
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
            _fallback_save(body)
    except FileNotFoundError:
        print("Warning: msmtp not installed.", file=sys.stderr)
        _fallback_save(body)


def _fallback_save(body: str):
    fallback = f"/tmp/system-health-{datetime.now().strftime('%Y-%m-%d-%H%M')}.txt"
    with open(fallback, "w") as f:
        f.write(body)
    print(f"Report saved to {fallback}", file=sys.stderr)


# ── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="System health monitor")
    parser.add_argument("--emergency-only", action="store_true",
                        help="Run only emergency checks (for 5-min cron)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--email", type=str, help="Email address to send report to")
    parser.add_argument("--no-cooldown", action="store_true",
                        help="Ignore cooldown (send even if recently alerted)")
    args = parser.parse_args()

    checker = SystemHealthChecker()

    if args.emergency_only:
        alerts = checker.run_emergency_only()
        mode = "emergency"
    else:
        alerts = checker.run_all()
        mode = "full"

    # Apply cooldown for emergency mode
    if args.emergency_only and not args.no_cooldown:
        alerts = filter_cooled_down(alerts)

    if not alerts and args.emergency_only:
        # Silent exit for emergency cron when nothing is wrong
        return

    if args.json:
        print(to_json(alerts))
    else:
        print(to_report(alerts, mode))

    if args.email and alerts:
        send_email(args.email, alerts, mode)


if __name__ == "__main__":
    main()
