import os
import pytest
from diff_generator import generate_diff, diff_directories, is_binary_file


@pytest.fixture
def skill_dirs(tmp_path):
    """Create two skill directories with slight differences."""
    local = tmp_path / "local"
    upstream = tmp_path / "upstream"
    local.mkdir()
    upstream.mkdir()

    (local / "SKILL.md").write_text("# My Skill\n\nLocal version with pi adaptations\n")
    (upstream / "SKILL.md").write_text("# My Skill\n\nUpstream version with new features\n")

    (local / "helper.py").write_text("def hello():\n    return 'local'\n")
    (upstream / "helper.py").write_text("def hello():\n    return 'upstream'\n")

    # File only in upstream (new file)
    (upstream / "new_file.md").write_text("# New upstream file\n")

    return {"local": str(local), "upstream": str(upstream)}


@pytest.fixture
def dirs_with_binary(tmp_path):
    """Create directories with binary files."""
    local = tmp_path / "local"
    upstream = tmp_path / "upstream"
    local.mkdir()
    upstream.mkdir()

    (local / "SKILL.md").write_text("# Skill\nv1\n")
    (upstream / "SKILL.md").write_text("# Skill\nv2\n")

    # Binary files (PNG header bytes)
    (local / "icon.png").write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    (upstream / "icon.png").write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 200)

    return {"local": str(local), "upstream": str(upstream)}


def test_generate_diff_single_file(skill_dirs):
    """Generates unified diff between two files."""
    diff = generate_diff(
        os.path.join(skill_dirs["local"], "SKILL.md"),
        os.path.join(skill_dirs["upstream"], "SKILL.md")
    )
    assert "Local version" in diff
    assert "Upstream version" in diff
    assert "---" in diff


def test_diff_directories(skill_dirs):
    """Generates diffs for all changed files between two directories."""
    results = diff_directories(skill_dirs["local"], skill_dirs["upstream"])
    filenames = [r["file"] for r in results]
    assert "SKILL.md" in filenames
    assert "helper.py" in filenames


def test_diff_directories_detects_new_files(skill_dirs):
    """Detects files that exist upstream but not locally."""
    results = diff_directories(skill_dirs["local"], skill_dirs["upstream"])
    new_files = [r for r in results if r["status"] == "new"]
    assert any(r["file"] == "new_file.md" for r in new_files)


def test_is_binary_file(dirs_with_binary):
    """Correctly identifies binary files."""
    assert is_binary_file(os.path.join(dirs_with_binary["local"], "icon.png")) is True
    assert is_binary_file(os.path.join(dirs_with_binary["local"], "SKILL.md")) is False


def test_diff_directories_skips_binary(dirs_with_binary):
    """Binary files are flagged but not diffed."""
    results = diff_directories(dirs_with_binary["local"], dirs_with_binary["upstream"])
    binary_results = [r for r in results if r["status"] == "binary_changed"]
    text_results = [r for r in results if r["status"] == "modified"]
    assert any(r["file"] == "icon.png" for r in binary_results)
    assert any(r["file"] == "SKILL.md" for r in text_results)


def test_diff_no_changes(tmp_path):
    """Returns empty list when directories are identical."""
    local = tmp_path / "local"
    upstream = tmp_path / "upstream"
    local.mkdir()
    upstream.mkdir()
    (local / "SKILL.md").write_text("identical\n")
    (upstream / "SKILL.md").write_text("identical\n")
    results = diff_directories(str(local), str(upstream))
    assert results == []
