"""
Check upstream GitHub repos for skill updates.
Shallow-clones to /tmp, compares HEAD SHA against stored commit.
Can retrieve commit log to show what changed.

CLI usage:
    python upstream_check.py check --repo URL --last-sha SHA [--subpath PATH]
    python upstream_check.py check-all --registry PATH
    python upstream_check.py log --repo URL --since-sha SHA [--depth N]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def clone_to_temp(repo_url: str, depth: int = 1) -> str:
    """Shallow-clone a repo to a temp directory. Returns clone path."""
    tmp_dir = tempfile.mkdtemp(prefix="skill-sync-")
    subprocess.run(
        ["git", "clone", "--depth", str(depth), repo_url, tmp_dir],
        check=True, capture_output=True, text=True
    )
    return tmp_dir


def get_head_sha(repo_path: str) -> str:
    """Get HEAD SHA of a local git repo."""
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_commit_log(clone_path: str, since_sha: str) -> str:
    """
    Get commit messages since a given SHA.
    If the SHA is not in the shallow clone history, returns all available commits.
    """
    try:
        # Try to get log since the specific commit
        result = subprocess.run(
            ["git", "-C", clone_path, "log", f"{since_sha}..HEAD", "--oneline"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            return result.stdout.strip()
    except subprocess.CalledProcessError:
        pass

    # Fallback: show all available commits (shallow clone may not have old SHA)
    result = subprocess.run(
        ["git", "-C", clone_path, "log", "--oneline"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def check_upstream(repo_url: str, repo_subpath: str, last_checked_commit: str) -> dict:
    """
    Check if upstream repo has updates since last_checked_commit.

    Returns dict:
      has_updates: bool (or None on error)
      old_sha: str
      new_sha: str
      clone_path: str (temp dir, caller must clean up)
      error: str (only present on failure)
    """
    try:
        clone_path = clone_to_temp(repo_url)
    except subprocess.CalledProcessError as e:
        return {
            "has_updates": None,
            "old_sha": last_checked_commit,
            "new_sha": None,
            "clone_path": None,
            "error": f"Failed to clone: {e.stderr or str(e)}",
        }

    new_sha = get_head_sha(clone_path)
    has_updates = new_sha != last_checked_commit

    result = {
        "has_updates": has_updates,
        "old_sha": last_checked_commit,
        "new_sha": new_sha,
        "clone_path": clone_path,
        "skill_path_in_clone": os.path.join(clone_path, repo_subpath) if repo_subpath else clone_path,
    }

    # If updates found, try to get the commit log for context
    if has_updates:
        # Re-clone with more depth to get meaningful log
        cleanup(clone_path)
        try:
            clone_path = clone_to_temp(repo_url, depth=50)
            result["clone_path"] = clone_path
            result["skill_path_in_clone"] = os.path.join(clone_path, repo_subpath) if repo_subpath else clone_path
            result["commit_log"] = get_commit_log(clone_path, last_checked_commit)
        except subprocess.CalledProcessError:
            # Fall back to shallow clone
            clone_path = clone_to_temp(repo_url)
            result["clone_path"] = clone_path
            result["skill_path_in_clone"] = os.path.join(clone_path, repo_subpath) if repo_subpath else clone_path
            result["commit_log"] = "(could not retrieve commit log)"

    return result


def check_all(registry_entries: list) -> list:
    """Check all registered skills for updates. Returns list of results."""
    results = []
    for entry in registry_entries:
        result = check_upstream(
            entry["github_repo"],
            entry.get("repo_subpath", ""),
            entry["last_checked_commit"]
        )
        result["name"] = entry["name"]
        result["local_path"] = entry["local_path"]
        results.append(result)
    return results


def cleanup(clone_path: str) -> None:
    """Remove a temp clone directory."""
    if clone_path and os.path.exists(clone_path) and clone_path.startswith(tempfile.gettempdir()):
        shutil.rmtree(clone_path)


def main():
    parser = argparse.ArgumentParser(description="Check upstream repos for skill updates")
    sub = parser.add_subparsers(dest="command", required=True)

    # check single
    check_p = sub.add_parser("check", help="Check one repo for updates")
    check_p.add_argument("--repo", required=True, help="GitHub repo URL")
    check_p.add_argument("--last-sha", required=True, help="Last known commit SHA")
    check_p.add_argument("--subpath", default="", help="Subpath within repo")

    # check-all
    all_p = sub.add_parser("check-all", help="Check all registered skills")
    all_p.add_argument("--registry", required=True, help="Path to registry JSON")

    # log
    log_p = sub.add_parser("log", help="Get commit log since a SHA")
    log_p.add_argument("--repo", required=True, help="GitHub repo URL")
    log_p.add_argument("--since-sha", required=True, help="SHA to get commits since")
    log_p.add_argument("--depth", type=int, default=50, help="Clone depth for log")

    args = parser.parse_args()

    if args.command == "check":
        result = check_upstream(args.repo, args.subpath, args.last_sha)
        print(json.dumps(result, indent=2, default=str))
        if result.get("clone_path"):
            cleanup(result["clone_path"])

    elif args.command == "check-all":
        # Import registry from same directory
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import registry as reg_mod
        r = reg_mod.Registry(args.registry)
        entries = r.list()
        if not entries:
            print("No skills registered.")
            return
        results = check_all(entries)
        for res in results:
            clone = res.pop("clone_path", None)
            res.pop("skill_path_in_clone", None)
            if clone:
                cleanup(clone)
        print(json.dumps(results, indent=2, default=str))

    elif args.command == "log":
        clone_path = clone_to_temp(args.repo, depth=args.depth)
        try:
            log = get_commit_log(clone_path, args.since_sha)
            print(log)
        finally:
            cleanup(clone_path)


if __name__ == "__main__":
    main()
