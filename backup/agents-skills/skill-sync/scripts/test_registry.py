import json
import os
import subprocess
import tempfile
import pytest
from registry import Registry

@pytest.fixture
def tmp_registry(tmp_path):
    path = tmp_path / "skill-registry.json"
    return Registry(str(path))

def test_creates_registry_file_if_missing(tmp_registry):
    """Registry initializes empty file on first access."""
    entries = tmp_registry.list()
    assert entries == []
    assert os.path.exists(tmp_registry.path)

def test_add_entry(tmp_registry):
    """Can add a new skill entry."""
    tmp_registry.add(
        name="test-skill",
        github_repo="https://github.com/user/repo",
        repo_subpath="skills/test-skill",
        local_path="/home/user/.agents/skills/test-skill",
        last_checked_commit="abc123",
        baseline_commit="abc123",
        adaptation_notes="No changes needed",
        adaptation_diff=""
    )
    entries = tmp_registry.list()
    assert len(entries) == 1
    assert entries[0]["name"] == "test-skill"
    assert entries[0]["github_repo"] == "https://github.com/user/repo"

def test_add_duplicate_raises(tmp_registry):
    """Adding a skill with the same name raises ValueError."""
    tmp_registry.add(name="dup", github_repo="https://github.com/a/b",
                     repo_subpath="", local_path="/tmp/dup",
                     last_checked_commit="abc", baseline_commit="abc",
                     adaptation_notes="", adaptation_diff="")
    with pytest.raises(ValueError, match="already registered"):
        tmp_registry.add(name="dup", github_repo="https://github.com/a/b",
                         repo_subpath="", local_path="/tmp/dup",
                         last_checked_commit="abc", baseline_commit="abc",
                         adaptation_notes="", adaptation_diff="")

def test_get_entry(tmp_registry):
    """Can retrieve a specific entry by name."""
    tmp_registry.add(name="my-skill", github_repo="https://github.com/x/y",
                     repo_subpath="", local_path="/tmp/my-skill",
                     last_checked_commit="def456", baseline_commit="def456",
                     adaptation_notes="Adjusted paths", adaptation_diff="diff here")
    entry = tmp_registry.get("my-skill")
    assert entry["adaptation_notes"] == "Adjusted paths"

def test_get_missing_returns_none(tmp_registry):
    """Getting a non-existent skill returns None."""
    assert tmp_registry.get("nope") is None

def test_remove_entry(tmp_registry):
    """Can remove a skill by name."""
    tmp_registry.add(name="removable", github_repo="https://github.com/a/b",
                     repo_subpath="", local_path="/tmp/rm",
                     last_checked_commit="xyz", baseline_commit="xyz",
                     adaptation_notes="", adaptation_diff="")
    tmp_registry.remove("removable")
    assert tmp_registry.list() == []

def test_remove_nonexistent_is_noop(tmp_registry):
    """Removing a skill that doesn't exist doesn't raise."""
    tmp_registry.remove("ghost")  # Should not raise
    assert tmp_registry.list() == []

def test_update_entry(tmp_registry):
    """Can update fields on an existing entry."""
    tmp_registry.add(name="updatable", github_repo="https://github.com/a/b",
                     repo_subpath="", local_path="/tmp/up",
                     last_checked_commit="old", baseline_commit="old",
                     adaptation_notes="old notes", adaptation_diff="old diff")
    tmp_registry.update("updatable", last_checked_commit="new", adaptation_notes="new notes")
    entry = tmp_registry.get("updatable")
    assert entry["last_checked_commit"] == "new"
    assert entry["adaptation_notes"] == "new notes"

def test_update_nonexistent_raises(tmp_registry):
    """Updating a skill that doesn't exist raises KeyError."""
    with pytest.raises(KeyError, match="not found"):
        tmp_registry.update("ghost", adaptation_notes="nope")

def test_cli_list_empty(tmp_path):
    """CLI list command works on empty registry."""
    reg_path = str(tmp_path / "skill-registry.json")
    result = subprocess.run(
        ["python3", "registry.py", "list", "--registry", reg_path],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    assert result.returncode == 0
    assert "No skills registered" in result.stdout or "[]" in result.stdout
