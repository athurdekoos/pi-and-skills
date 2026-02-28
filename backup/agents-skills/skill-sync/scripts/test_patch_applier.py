import os
import subprocess
import pytest
from patch_applier import copy_upstream_files, backup_local, restore_backup


@pytest.fixture
def skill_dirs(tmp_path):
    local = tmp_path / "local"
    upstream = tmp_path / "upstream"
    backup = tmp_path / "backup"
    local.mkdir()
    upstream.mkdir()

    (local / "SKILL.md").write_text("# Skill\nLocal adapted version\n")
    (local / "old_file.txt").write_text("this only exists locally\n")
    (upstream / "SKILL.md").write_text("# Skill\nNew upstream version\n")
    (upstream / "new_script.py").write_text("print('new')\n")

    # Nested directory in upstream
    (upstream / "scripts").mkdir()
    (upstream / "scripts" / "helper.py").write_text("# helper\n")

    return {"local": str(local), "upstream": str(upstream), "backup": str(backup)}


def test_backup_local(skill_dirs):
    """Creates a full backup of the local skill directory."""
    backup_path = backup_local(skill_dirs["local"], skill_dirs["backup"])
    assert os.path.exists(os.path.join(backup_path, "SKILL.md"))
    with open(os.path.join(backup_path, "SKILL.md")) as f:
        assert "Local adapted" in f.read()
    # Original is untouched
    assert os.path.exists(os.path.join(skill_dirs["local"], "SKILL.md"))


def test_copy_upstream_files(skill_dirs):
    """Copies upstream files into local directory, including nested dirs."""
    copied = copy_upstream_files(skill_dirs["upstream"], skill_dirs["local"])
    with open(os.path.join(skill_dirs["local"], "SKILL.md")) as f:
        assert "New upstream version" in f.read()
    assert os.path.exists(os.path.join(skill_dirs["local"], "new_script.py"))
    assert os.path.exists(os.path.join(skill_dirs["local"], "scripts", "helper.py"))
    assert "SKILL.md" in copied
    assert os.path.join("scripts", "helper.py") in copied


def test_copy_preserves_local_only_files(skill_dirs):
    """Files that exist only locally are not removed by copy."""
    copy_upstream_files(skill_dirs["upstream"], skill_dirs["local"])
    assert os.path.exists(os.path.join(skill_dirs["local"], "old_file.txt"))


def test_restore_backup(skill_dirs):
    """Restoring a backup replaces the local directory entirely."""
    backup_path = backup_local(skill_dirs["local"], skill_dirs["backup"])
    # Mess up local
    with open(os.path.join(skill_dirs["local"], "SKILL.md"), "w") as f:
        f.write("BROKEN")
    # Restore
    restore_backup(backup_path, skill_dirs["local"])
    with open(os.path.join(skill_dirs["local"], "SKILL.md")) as f:
        assert "Local adapted" in f.read()


def test_cli_backup(skill_dirs):
    """CLI backup command works."""
    result = subprocess.run(
        ["python3", "patch_applier.py", "backup",
         "--local", skill_dirs["local"],
         "--backup-dir", skill_dirs["backup"]],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    assert result.returncode == 0
    assert "Backup saved" in result.stdout
