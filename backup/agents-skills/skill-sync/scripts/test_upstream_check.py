import subprocess
import os
import pytest
from upstream_check import check_upstream, clone_to_temp, get_commit_log, cleanup


GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "t@t",
}


@pytest.fixture
def fake_repo(tmp_path):
    """Create a bare git repo with one commit to simulate upstream."""
    repo = tmp_path / "upstream.git"
    work = tmp_path / "work"
    repo.mkdir()
    work.mkdir()
    subprocess.run(["git", "init", "--bare", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(repo), str(work)], check=True, capture_output=True)
    # Create initial commit
    skill_file = work / "SKILL.md"
    skill_file.write_text("# Test Skill\nVersion 1")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "init: first commit"],
                   check=True, capture_output=True, env=GIT_ENV)
    subprocess.run(["git", "-C", str(work), "push"], check=True, capture_output=True)
    sha = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return {"repo_url": str(repo), "sha": sha, "work": str(work)}


def test_clone_to_temp(fake_repo):
    """Clones a repo to a temp directory and returns the path."""
    clone_path = clone_to_temp(fake_repo["repo_url"])
    try:
        assert os.path.exists(os.path.join(clone_path, "SKILL.md"))
    finally:
        cleanup(clone_path)


def test_check_upstream_no_changes(fake_repo):
    """Returns up-to-date when SHA matches."""
    result = check_upstream(fake_repo["repo_url"], "", fake_repo["sha"])
    try:
        assert result["has_updates"] is False
    finally:
        cleanup(result.get("clone_path", ""))


def test_check_upstream_with_changes(fake_repo):
    """Returns has_updates when upstream has new commits."""
    work = fake_repo["work"]
    with open(os.path.join(work, "SKILL.md"), "w") as f:
        f.write("# Test Skill\nVersion 2")
    subprocess.run(["git", "-C", work, "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", work, "commit", "-m", "feat: update to v2"],
                   check=True, capture_output=True, env=GIT_ENV)
    subprocess.run(["git", "-C", work, "push"], check=True, capture_output=True)

    result = check_upstream(fake_repo["repo_url"], "", fake_repo["sha"])
    try:
        assert result["has_updates"] is True
        assert result["old_sha"] == fake_repo["sha"]
        assert result["new_sha"] != fake_repo["sha"]
    finally:
        cleanup(result.get("clone_path", ""))


def test_get_commit_log(fake_repo):
    """Gets commit messages between two SHAs."""
    work = fake_repo["work"]
    old_sha = fake_repo["sha"]

    # Add two more commits
    for i in range(2):
        with open(os.path.join(work, "SKILL.md"), "a") as f:
            f.write(f"\nChange {i}")
        subprocess.run(["git", "-C", work, "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", work, "commit", "-m", f"feat: change {i}"],
                       check=True, capture_output=True, env=GIT_ENV)
    subprocess.run(["git", "-C", work, "push"], check=True, capture_output=True)

    clone_path = clone_to_temp(fake_repo["repo_url"], depth=10)
    try:
        log = get_commit_log(clone_path, old_sha)
        assert "change 0" in log.lower()
        assert "change 1" in log.lower()
    finally:
        cleanup(clone_path)


def test_check_upstream_bad_url():
    """Reports error for unreachable repos instead of crashing."""
    result = check_upstream("/tmp/nonexistent-repo-that-does-not-exist", "", "abc")
    assert result["has_updates"] is None
    assert "error" in result
