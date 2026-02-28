"""
Backup, copy, and rollback utilities for skill updates.
The agent handles intelligent merge decisions — these helpers handle file operations.

CLI usage:
    python patch_applier.py backup --local DIR --backup-dir DIR
    python patch_applier.py copy --upstream DIR --local DIR
    python patch_applier.py restore --backup DIR --local DIR
"""
import argparse
import os
import shutil
import sys
from datetime import datetime


def backup_local(local_dir: str, backup_base: str) -> str:
    """
    Create a timestamped backup of the local skill directory.
    Returns the backup path.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    skill_name = os.path.basename(local_dir.rstrip("/"))
    backup_path = os.path.join(backup_base, f"{skill_name}-{timestamp}")
    shutil.copytree(local_dir, backup_path)
    return backup_path


def copy_upstream_files(upstream_dir: str, local_dir: str) -> list:
    """
    Copy all files from upstream into local, overwriting existing ones.
    Does NOT delete local-only files (the agent decides what to do with those).
    Returns list of relative paths copied.
    """
    copied = []
    for root, _, files in os.walk(upstream_dir):
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(src, upstream_dir)
            dst = os.path.join(local_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel)
    return copied


def restore_backup(backup_path: str, local_dir: str) -> None:
    """Restore local skill from backup (full rollback)."""
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
    shutil.copytree(backup_path, local_dir)


def main():
    parser = argparse.ArgumentParser(description="Backup, copy, and rollback for skill updates")
    sub = parser.add_subparsers(dest="command", required=True)

    # backup
    bk_p = sub.add_parser("backup", help="Backup local skill directory")
    bk_p.add_argument("--local", required=True, help="Local skill directory to back up")
    bk_p.add_argument("--backup-dir", required=True, help="Directory to store backups")

    # copy
    cp_p = sub.add_parser("copy", help="Copy upstream files into local directory")
    cp_p.add_argument("--upstream", required=True, help="Upstream skill directory (from clone)")
    cp_p.add_argument("--local", required=True, help="Local skill directory to update")

    # restore
    rs_p = sub.add_parser("restore", help="Restore local skill from backup")
    rs_p.add_argument("--backup", required=True, help="Backup directory to restore from")
    rs_p.add_argument("--local", required=True, help="Local skill directory to overwrite")

    args = parser.parse_args()

    if args.command == "backup":
        path = backup_local(args.local, args.backup_dir)
        print(f"Backup saved to: {path}")

    elif args.command == "copy":
        copied = copy_upstream_files(args.upstream, args.local)
        print(f"Copied {len(copied)} files:")
        for f in copied:
            print(f"  {f}")

    elif args.command == "restore":
        restore_backup(args.backup, args.local)
        print(f"✓ Restored from {args.backup}")


if __name__ == "__main__":
    main()
