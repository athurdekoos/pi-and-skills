"""
Registry manager for skill-sync.
Handles CRUD operations on ~/.agents/skill-registry.json

CLI usage:
    python registry.py list [--registry PATH]
    python registry.py add --name NAME --repo URL --subpath PATH --local-path PATH --sha SHA [--notes TEXT] [--diff TEXT] [--registry PATH]
    python registry.py get --name NAME [--registry PATH]
    python registry.py remove --name NAME [--registry PATH]
    python registry.py update --name NAME [--set FIELD VALUE ...] [--registry PATH]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone


REGISTRY_PATH = os.path.expanduser("~/.agents/skill-registry.json")


class Registry:
    def __init__(self, path: str = REGISTRY_PATH):
        self.path = path

    def _read(self) -> dict:
        if not os.path.exists(self.path):
            return {"version": 1, "skills": []}
        with open(self.path, "r") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def list(self) -> list:
        data = self._read()
        if not os.path.exists(self.path):
            self._write(data)
        return data["skills"]

    def get(self, name: str) -> dict | None:
        for entry in self._read()["skills"]:
            if entry["name"] == name:
                return entry
        return None

    def add(self, *, name: str, github_repo: str, repo_subpath: str,
            local_path: str, last_checked_commit: str, baseline_commit: str,
            adaptation_notes: str, adaptation_diff: str) -> dict:
        data = self._read()
        for entry in data["skills"]:
            if entry["name"] == name:
                raise ValueError(f"Skill '{name}' is already registered")
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "name": name,
            "github_repo": github_repo,
            "repo_subpath": repo_subpath,
            "local_path": local_path,
            "last_checked_commit": last_checked_commit,
            "baseline_commit": baseline_commit,
            "adaptation_notes": adaptation_notes,
            "adaptation_diff": adaptation_diff,
            "registered_at": now,
            "last_updated_at": now,
        }
        data["skills"].append(entry)
        self._write(data)
        return entry

    def update(self, name: str, **fields) -> dict:
        data = self._read()
        for entry in data["skills"]:
            if entry["name"] == name:
                for k, v in fields.items():
                    if k not in entry:
                        raise KeyError(f"Unknown field: {k}")
                    entry[k] = v
                entry["last_updated_at"] = datetime.now(timezone.utc).isoformat()
                self._write(data)
                return entry
        raise KeyError(f"Skill '{name}' not found")

    def remove(self, name: str) -> None:
        data = self._read()
        data["skills"] = [e for e in data["skills"] if e["name"] != name]
        self._write(data)


def main():
    parser = argparse.ArgumentParser(description="Skill registry manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared registry arg added to each subparser
    def add_registry_arg(p):
        p.add_argument("--registry", default=REGISTRY_PATH, help="Path to registry JSON file")

    # list
    list_p = sub.add_parser("list", help="List all registered skills")
    add_registry_arg(list_p)

    # add
    add_p = sub.add_parser("add", help="Register a new skill")
    add_registry_arg(add_p)
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--repo", required=True, help="GitHub repo URL")
    add_p.add_argument("--subpath", default="", help="Subpath within repo")
    add_p.add_argument("--local-path", required=True, help="Local skill directory")
    add_p.add_argument("--sha", required=True, help="Current upstream HEAD SHA")
    add_p.add_argument("--notes", default="", help="Adaptation notes")
    add_p.add_argument("--diff", default="", help="Adaptation diff")

    # get
    get_p = sub.add_parser("get", help="Get details for a skill")
    add_registry_arg(get_p)
    get_p.add_argument("--name", required=True)

    # remove
    rm_p = sub.add_parser("remove", help="Remove a skill from registry")
    add_registry_arg(rm_p)
    rm_p.add_argument("--name", required=True)

    # update
    up_p = sub.add_parser("update", help="Update fields on a registered skill")
    add_registry_arg(up_p)
    up_p.add_argument("--name", required=True)
    up_p.add_argument("--set", nargs=2, action="append", metavar=("FIELD", "VALUE"),
                      help="Field and value to update (repeatable)")

    args = parser.parse_args()
    reg = Registry(args.registry)

    if args.command == "list":
        entries = reg.list()
        if not entries:
            print("No skills registered.")
        else:
            for e in entries:
                status = f"  {e['name']}: {e['github_repo']}"
                if e.get("repo_subpath"):
                    status += f" (subpath: {e['repo_subpath']})"
                print(status)

    elif args.command == "add":
        try:
            entry = reg.add(
                name=args.name, github_repo=args.repo, repo_subpath=args.subpath,
                local_path=args.local_path, last_checked_commit=args.sha,
                baseline_commit=args.sha, adaptation_notes=args.notes,
                adaptation_diff=args.diff
            )
            print(f"✓ Registered '{args.name}'")
        except ValueError as e:
            print(f"✗ {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "get":
        entry = reg.get(args.name)
        if entry:
            print(json.dumps(entry, indent=2))
        else:
            print(f"✗ Skill '{args.name}' not found", file=sys.stderr)
            sys.exit(1)

    elif args.command == "remove":
        reg.remove(args.name)
        print(f"✓ Removed '{args.name}'")

    elif args.command == "update":
        if not args.set:
            print("✗ No fields to update. Use --set FIELD VALUE", file=sys.stderr)
            sys.exit(1)
        try:
            fields = {k: v for k, v in args.set}
            reg.update(args.name, **fields)
            print(f"✓ Updated '{args.name}'")
        except KeyError as e:
            print(f"✗ {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
