#!/usr/bin/env python3
"""Send a test email with current status from all monitoring daemons."""

import argparse
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Import sibling modules
sys.path.insert(0, str(Path(__file__).parent))
from health_check import SystemHealthChecker, Severity

# Import skill auditor
SKILL_AUDIT_PATH = Path.home() / ".agents" / "skills" / "lessons-learned" / "scripts"
sys.path.insert(0, str(SKILL_AUDIT_PATH))
from audit_skills import SkillAuditor, Severity as SkillSeverity


def bar(pct: int, width: int = 20) -> str:
    """ASCII progress bar."""
    filled = int(width * pct / 100)
    empty = width - filled
    if pct > 90:
        indicator = "🔴"
    elif pct > 75:
        indicator = "🟡"
    else:
        indicator = "🟢"
    return f"{indicator} [{'█' * filled}{'░' * empty}] {pct}%"


def get_ram_info() -> tuple:
    with open("/proc/meminfo") as f:
        meminfo = f.read()
    total = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1)) // 1024
    avail = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1)) // 1024
    used = total - avail
    pct = int(used / total * 100)
    return total, used, avail, pct


def get_swap_info() -> tuple:
    with open("/proc/meminfo") as f:
        meminfo = f.read()
    total = int(re.search(r"SwapTotal:\s+(\d+)", meminfo).group(1)) // 1024
    free = int(re.search(r"SwapFree:\s+(\d+)", meminfo).group(1)) // 1024
    used = total - free
    pct = int(used / total * 100) if total > 0 else 0
    return total, used, pct


def get_disk_info() -> tuple:
    st = os.statvfs("/")
    total_gb = (st.f_blocks * st.f_frsize) / (1024 ** 3)
    free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
    used_gb = total_gb - free_gb
    pct = int(used_gb / total_gb * 100)
    return total_gb, used_gb, free_gb, pct


def get_uptime() -> str:
    with open("/proc/uptime") as f:
        secs = float(f.read().split()[0])
    days = int(secs // 86400)
    hours = int((secs % 86400) // 3600)
    mins = int((secs % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    return f"{hours}h {mins}m"


def get_pi_sessions() -> list:
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
        sessions = []
        for line in result.stdout.splitlines():
            if "/pi" in line or line.endswith(" pi"):
                parts = line.split()
                mem_mb = int(parts[5]) // 1024 if len(parts) > 5 else 0
                if mem_mb > 50:  # Filter out tiny grep matches
                    sessions.append(mem_mb)
        return sorted(sessions, reverse=True)
    except Exception:
        return []


def get_git_repos() -> list:
    repos = []
    dev = Path.home() / "dev"
    try:
        for git_dir in dev.rglob(".git"):
            if git_dir.is_dir() and len(git_dir.parts) <= len(dev.parts) + 3:
                repo = git_dir.parent
                name = repo.name
                # Branch
                branch_result = subprocess.run(
                    ["git", "-C", str(repo), "branch", "--show-current"],
                    capture_output=True, text=True, timeout=5,
                )
                branch = branch_result.stdout.strip() or "detached"
                # Dirty files
                status_result = subprocess.run(
                    ["git", "-C", str(repo), "status", "--porcelain"],
                    capture_output=True, text=True, timeout=5,
                )
                dirty = len([l for l in status_result.stdout.splitlines() if l.strip()])
                # Last commit
                log_result = subprocess.run(
                    ["git", "-C", str(repo), "log", "-1", "--format=%ar"],
                    capture_output=True, text=True, timeout=5,
                )
                last_commit = log_result.stdout.strip()
                repos.append((name, branch, dirty, last_commit))
    except Exception:
        pass
    return repos


def get_node_modules_size() -> list:
    sizes = []
    try:
        # Only top-level node_modules (not nested ones inside other node_modules)
        result = subprocess.run(
            ["find", str(Path.home() / "dev"), "-maxdepth", "4", "-name", "node_modules", "-type", "d",
             "-not", "-path", "*/node_modules/*/node_modules*"],
            capture_output=True, text=True, timeout=10,
        )
        for nm_path in result.stdout.strip().splitlines():
            if not nm_path:
                continue
            nm = Path(nm_path)
            du_result = subprocess.run(
                ["du", "-sh", str(nm)], capture_output=True, text=True, timeout=10,
            )
            if du_result.returncode == 0:
                size = du_result.stdout.split()[0]
                # Show relative path from ~/dev
                rel = str(nm.relative_to(Path.home() / "dev"))
                sizes.append((rel, size))
    except Exception:
        pass
    return sizes


def get_listening_ports() -> list:
    ports = []
    try:
        result = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                addr = parts[3]
                port = addr.rsplit(":", 1)[-1]
                proc_info = parts[-1] if "users:" in parts[-1] else ""
                proc_name = re.search(r'"([^"]+)"', proc_info)
                proc_name = proc_name.group(1) if proc_name else "unknown"
                if port not in ("53",):  # Skip DNS
                    ports.append((port, proc_name))
    except Exception:
        pass
    return ports


def get_docker_usage() -> str:
    try:
        result = subprocess.run(
            ["docker", "system", "df", "--format", "{{.Type}}\t{{.Size}}\t{{.Reclaimable}}"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = []
            for line in result.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) >= 3:
                    lines.append(f"    {parts[0]:<15} {parts[1]:<12} ({parts[2]} reclaimable)")
            return "\n".join(lines)
    except Exception:
        pass
    return "    Not available"


def build_email(to_addr: str) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M UTC")
    hostname = socket.gethostname()

    # Gather all data
    ram_total, ram_used, ram_avail, ram_pct = get_ram_info()
    swap_total, swap_used, swap_pct = get_swap_info()
    disk_total, disk_used, disk_free, disk_pct = get_disk_info()
    load1, load5, load15 = os.getloadavg()
    uptime = get_uptime()
    pi_sessions = get_pi_sessions()
    repos = get_git_repos()
    nm_sizes = get_node_modules_size()
    ports = get_listening_ports()
    docker_usage = get_docker_usage()

    # Skill audit
    auditor = SkillAuditor(str(Path.home() / ".agents" / "skills"))
    skill_findings = auditor.audit()
    skill_errors = [f for f in skill_findings if f.severity == SkillSeverity.ERROR]
    skill_warns = [f for f in skill_findings if f.severity == SkillSeverity.WARN]
    skill_infos = [f for f in skill_findings if f.severity == SkillSeverity.INFO]

    # System health
    checker = SystemHealthChecker()
    health_alerts = checker.run_all()
    health_emergencies = [a for a in health_alerts if a.severity == Severity.EMERGENCY]
    health_warnings = [a for a in health_alerts if a.severity == Severity.WARNING]

    # Overall vibe
    total_issues = len(health_emergencies) + len(skill_errors)
    if total_issues > 0:
        vibe = "🔥 NEEDS ATTENTION"
        vibe_line = "Something needs fixing. Check the details below."
    elif len(health_warnings) + len(skill_warns) > 0:
        vibe = "⚡ MOSTLY GOOD"
        vibe_line = "Nothing critical, but a few things to keep an eye on."
    else:
        vibe = "✨ VIBES ARE IMMACULATE"
        vibe_line = "Everything's running smooth. Ship that code."

    # Build the email
    lines = []
    w = lines.append

    w("╔══════════════════════════════════════════════════════════╗")
    w("║          ⚠️  THIS IS A TEST — THIS IS A TEST ⚠️         ║")
    w("╚══════════════════════════════════════════════════════════╝")
    w("")
    w(f"  📡 {hostname} — {date_str}")
    w(f"  ⏱  Uptime: {uptime}")
    w(f"  🎯 Status: {vibe}")
    w(f"     {vibe_line}")
    w("")
    w("──────────────────────────────────────────────────────────")
    w("  💻  SYSTEM VITALS")
    w("──────────────────────────────────────────────────────────")
    w("")
    w(f"  RAM     {bar(ram_pct)}")
    w(f"          {ram_used} MB used / {ram_total} MB total ({ram_avail} MB free)")
    w("")
    w(f"  DISK    {bar(disk_pct)}")
    w(f"          {disk_used:.1f} GB used / {disk_total:.1f} GB total ({disk_free:.1f} GB free)")
    w("")
    w(f"  SWAP    {bar(swap_pct)}")
    w(f"          {swap_used} MB used / {swap_total} MB total")
    w("")
    w(f"  LOAD    {load1:.2f} / {load5:.2f} / {load15:.2f}  (1m / 5m / 15m)")
    ncpu = os.cpu_count() or 1
    load_status = "🟢 chill" if load5 < ncpu * 0.7 else ("🟡 busy" if load5 < ncpu else "🔴 saturated")
    w(f"          {ncpu} cores — {load_status}")
    w("")

    # Pi sessions
    w("──────────────────────────────────────────────────────────")
    w("  🤖  AGENT SESSIONS")
    w("──────────────────────────────────────────────────────────")
    w("")
    if pi_sessions:
        total_mem = sum(pi_sessions)
        w(f"  {len(pi_sessions)} active pi sessions — {total_mem} MB total")
        for i, mem in enumerate(pi_sessions, 1):
            bar_len = min(mem // 10, 25)
            w(f"    Session {i}:  {'█' * bar_len} {mem} MB")
        if len(pi_sessions) >= 4:
            w(f"  ⚡ Tip: {len(pi_sessions)} sessions on {ram_total} MB RAM — watch for memory pressure")
    else:
        w("  No active sessions")
    w("")

    # Git repos
    w("──────────────────────────────────────────────────────────")
    w("  📦  GIT REPOS")
    w("──────────────────────────────────────────────────────────")
    w("")
    if repos:
        for name, branch, dirty, last_commit in repos:
            dirty_flag = f" ⚠️  {dirty} uncommitted" if dirty > 0 else " ✅"
            w(f"  {name}")
            w(f"    ├─ branch: {branch}")
            w(f"    ├─ last commit: {last_commit}")
            w(f"    └─ status:{dirty_flag}")
        w("")
        dirty_repos = [(n, d) for n, _, d, _ in repos if d > 0]
        if dirty_repos:
            w(f"  💡 {len(dirty_repos)} repo(s) have uncommitted work — don't lose it!")
    else:
        w("  No repos found")
    w("")

    # Listening ports
    w("──────────────────────────────────────────────────────────")
    w("  🌐  NETWORK")
    w("──────────────────────────────────────────────────────────")
    w("")
    if ports:
        for port, proc in ports:
            w(f"    :{port:<6} → {proc}")
    else:
        w("  No listening ports")
    w("")

    # Docker
    w("──────────────────────────────────────────────────────────")
    w("  🐳  DOCKER")
    w("──────────────────────────────────────────────────────────")
    w("")
    w(docker_usage)
    w("")

    # node_modules
    if nm_sizes:
        w("──────────────────────────────────────────────────────────")
        w("  📁  DISK HOGS")
        w("──────────────────────────────────────────────────────────")
        w("")
        for rel_path, size in nm_sizes:
            w(f"    {size:<8} {rel_path}")
        w("")

    # Skill health
    w("──────────────────────────────────────────────────────────")
    w(f"  🔧  SKILL HEALTH ({len(skill_findings)} issues)")
    w("──────────────────────────────────────────────────────────")
    w("")
    if skill_errors:
        w(f"  🔴 ERRORS ({len(skill_errors)})")
        for f in skill_errors:
            w(f"    ✗ {f.skill_name}: {f.message}")
        w("")
    if skill_warns:
        w(f"  🟡 WARNINGS ({len(skill_warns)})")
        for f in skill_warns:
            w(f"    ⚡ {f.skill_name}: {f.message}")
        w("")
    if skill_infos:
        w(f"  ℹ️  INFO ({len(skill_infos)})")
        for f in skill_infos:
            w(f"    · {f.skill_name}: {f.message}")
        w("")
    if not skill_findings:
        w("  ✨ All skills healthy")
        w("")

    # System alerts
    if health_emergencies or health_warnings:
        w("──────────────────────────────────────────────────────────")
        w("  🚨  SYSTEM ALERTS")
        w("──────────────────────────────────────────────────────────")
        w("")
        for a in health_emergencies:
            w(f"  🚨 [{a.check_id}] {a.message}")
        for a in health_warnings:
            w(f"  🟡 [{a.check_id}] {a.message}")
        w("")

    # Log locations
    w("──────────────────────────────────────────────────────────")
    w("  📋  LOG LOCATIONS")
    w("──────────────────────────────────────────────────────────")
    w("")
    logs = [
        ("/tmp/skill-audit-cron.log", "Skill audit daemon"),
        ("/tmp/system-health-digest.log", "System health daily digest"),
        ("/tmp/system-health-emergency.log", "Emergency check (every 5 min)"),
        ("/tmp/system-health-cooldowns.json", "Alert cooldown state"),
        ("/home/mia/.msmtp.log", "Email send log"),
        ("/var/log/syslog", "System log"),
        ("/var/log/auth.log", "SSH / auth log"),
    ]
    for path, desc in logs:
        exists = "✅" if Path(path).exists() else "❌"
        w(f"    {exists} {desc}")
        w(f"       {path}")
    w("")

    # Footer
    w("──────────────────────────────────────────────────────────")
    w("  🛠  QUICK COMMANDS")
    w("──────────────────────────────────────────────────────────")
    w("")
    w("  # Run full health check")
    w("  python3 ~/.agents/skills/system-health/scripts/health_check.py")
    w("")
    w("  # Audit all skills")
    w("  python3 ~/.agents/skills/lessons-learned/scripts/audit_skills.py")
    w("")
    w("  # Send this test email again")
    w("  python3 ~/.agents/skills/system-health/scripts/send_test.py")
    w("")
    w("  # Check what cron is running")
    w("  crontab -l")
    w("")
    w("╔══════════════════════════════════════════════════════════╗")
    w("║          ⚠️  THIS IS A TEST — THIS IS A TEST ⚠️         ║")
    w("╚══════════════════════════════════════════════════════════╝")

    body = "\n".join(lines)

    # Subject line
    if total_issues > 0:
        subject = f"🔥 [TEST] {hostname} — {total_issues} issues — {date_str}"
    else:
        subject = f"✨ [TEST] {hostname} — All clear — {date_str}"

    msg = f"Subject: {subject}\nTo: {to_addr}\nContent-Type: text/plain; charset=utf-8\n\n{body}"
    return msg, body


def main():
    parser = argparse.ArgumentParser(description="Send a test email with current monitoring status")
    parser.add_argument(
        "--email",
        default="skynetwasdumb@gmail.com",
        help="Email address to send test to (default: skynetwasdumb@gmail.com)",
    )
    args = parser.parse_args()

    print(f"Building test email for {args.email}...\n")
    msg, body = build_email(args.email)

    print(body)

    try:
        proc = subprocess.run(
            ["msmtp", args.email],
            input=msg,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            print(f"\n✅ Test email sent to {args.email}")
        else:
            print(f"\n❌ msmtp failed: {proc.stderr}", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("\n❌ msmtp not installed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
