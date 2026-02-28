"""
Generate unified diffs between local and upstream skill files.
Handles binary files safely by detecting and skipping them.

CLI usage:
    python diff_generator.py file --local PATH --upstream PATH
    python diff_generator.py dir --local DIR --upstream DIR [--json]
"""
import argparse
import difflib
import json
import os
import sys


def is_binary_file(filepath: str, check_bytes: int = 8192) -> bool:
    """
    Check if a file is binary by reading the first N bytes and looking for
    null bytes or decode failures.
    """
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(check_bytes)
        if b'\x00' in chunk:
            return True
        chunk.decode("utf-8")
        return False
    except (UnicodeDecodeError, OSError):
        return True


def generate_diff(local_file: str, upstream_file: str) -> str:
    """Generate a unified diff between two text files."""
    local_lines = []
    upstream_lines = []

    if os.path.exists(local_file):
        with open(local_file, "r", errors="replace") as f:
            local_lines = f.readlines()

    if os.path.exists(upstream_file):
        with open(upstream_file, "r", errors="replace") as f:
            upstream_lines = f.readlines()

    diff = difflib.unified_diff(
        local_lines, upstream_lines,
        fromfile=f"local/{os.path.basename(local_file)}",
        tofile=f"upstream/{os.path.basename(upstream_file)}",
        lineterm=""
    )
    return "\n".join(diff)


def diff_directories(local_dir: str, upstream_dir: str) -> list:
    """
    Compare two skill directories file-by-file.

    Returns list of dicts:
      file: relative filename
      status: "modified" | "new" | "deleted" | "binary_changed" | "binary_new"
      diff: unified diff string (for text files) or descriptive note (for binary)
    """
    local_files = set()
    upstream_files = set()

    for root, _, files in os.walk(local_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), local_dir)
            local_files.add(rel)

    for root, _, files in os.walk(upstream_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), upstream_dir)
            upstream_files.add(rel)

    results = []

    # Files in both directories
    for f in sorted(local_files & upstream_files):
        local_path = os.path.join(local_dir, f)
        upstream_path = os.path.join(upstream_dir, f)

        if is_binary_file(local_path) or is_binary_file(upstream_path):
            # Check if binary files differ by size or content
            local_size = os.path.getsize(local_path)
            upstream_size = os.path.getsize(upstream_path)
            if local_size != upstream_size:
                results.append({
                    "file": f,
                    "status": "binary_changed",
                    "diff": f"Binary file changed: {local_size} bytes → {upstream_size} bytes"
                })
            else:
                with open(local_path, "rb") as lf, open(upstream_path, "rb") as uf:
                    if lf.read() != uf.read():
                        results.append({
                            "file": f,
                            "status": "binary_changed",
                            "diff": f"Binary file changed (same size: {local_size} bytes)"
                        })
        else:
            diff = generate_diff(local_path, upstream_path)
            if diff:
                results.append({"file": f, "status": "modified", "diff": diff})

    # New files (only in upstream)
    for f in sorted(upstream_files - local_files):
        upstream_path = os.path.join(upstream_dir, f)
        if is_binary_file(upstream_path):
            size = os.path.getsize(upstream_path)
            results.append({
                "file": f,
                "status": "binary_new",
                "diff": f"New binary file: {size} bytes"
            })
        else:
            with open(upstream_path, "r", errors="replace") as fh:
                content = fh.read()
            results.append({"file": f, "status": "new", "diff": f"+++ new file: {f}\n{content}"})

    # Deleted files (only in local)
    for f in sorted(local_files - upstream_files):
        results.append({"file": f, "status": "deleted", "diff": f"--- deleted: {f}"})

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate diffs between local and upstream skills")
    sub = parser.add_subparsers(dest="command", required=True)

    # Single file diff
    file_p = sub.add_parser("file", help="Diff two files")
    file_p.add_argument("--local", required=True, help="Local file path")
    file_p.add_argument("--upstream", required=True, help="Upstream file path")

    # Directory diff
    dir_p = sub.add_parser("dir", help="Diff two directories")
    dir_p.add_argument("--local", required=True, help="Local skill directory")
    dir_p.add_argument("--upstream", required=True, help="Upstream skill directory")
    dir_p.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "file":
        if is_binary_file(args.local) or is_binary_file(args.upstream):
            print("Binary file — cannot generate text diff")
            sys.exit(0)
        print(generate_diff(args.local, args.upstream))

    elif args.command == "dir":
        results = diff_directories(args.local, args.upstream)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print("No differences found.")
            for r in results:
                print(f"\n{'='*60}")
                print(f"[{r['status'].upper()}] {r['file']}")
                print(f"{'='*60}")
                print(r["diff"])


if __name__ == "__main__":
    main()
