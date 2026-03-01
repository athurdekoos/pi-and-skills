"""Tests for skill health auditor."""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from audit_skills import SkillAuditor, Finding, Severity


class TestSkillAuditor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.auditor = SkillAuditor(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _make_skill(self, name, content=None):
        """Helper: create a skill dir with optional SKILL.md content."""
        skill_dir = os.path.join(self.tmpdir, name)
        os.makedirs(skill_dir, exist_ok=True)
        if content is not None:
            with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
                f.write(content)
        return skill_dir

    # --- ORPHAN check ---
    def test_orphan_dir_no_skill_md(self):
        self._make_skill("broken-skill")  # no SKILL.md
        findings = self.auditor.audit()
        errors = [f for f in findings if f.check_id == "ORPHAN"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].severity, Severity.ERROR)

    # --- NAME check ---
    def test_missing_name_in_frontmatter(self):
        self._make_skill("no-name", "---\ndescription: hello world this is long enough\n---\n# Body")
        findings = self.auditor.audit()
        errors = [f for f in findings if f.check_id == "NAME"]
        self.assertEqual(len(errors), 1)

    # --- DESC check ---
    def test_short_description_warns(self):
        self._make_skill("short-desc", "---\nname: short-desc\ndescription: hi\n---\n# Body")
        findings = self.auditor.audit()
        warns = [f for f in findings if f.check_id == "DESC"]
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0].severity, Severity.WARN)

    # --- Healthy skill ---
    def test_healthy_skill_no_findings(self):
        good = "---\nname: good-skill\ndescription: A perfectly fine skill that does useful things for the user\n---\n# Good Skill\nDoes stuff."
        self._make_skill("good-skill", good)
        findings = self.auditor.audit()
        serious = [f for f in findings if f.skill_name == "good-skill" and f.severity in (Severity.ERROR, Severity.WARN)]
        self.assertEqual(len(serious), 0)

    # --- SIZE check ---
    def test_oversized_skill_warns(self):
        body = "---\nname: big\ndescription: A big skill with lots of content inside it\n---\n" + ("line\n" * 501)
        self._make_skill("big", body)
        findings = self.auditor.audit()
        warns = [f for f in findings if f.check_id == "SIZE"]
        self.assertEqual(len(warns), 1)

    # --- REF_BROKEN check ---
    def test_broken_reference_errors(self):
        content = '---\nname: reftest\ndescription: Skill that references nonexistent files in refs\n---\n# Ref\nRead `references/missing.md` for details.'
        self._make_skill("reftest", content)
        findings = self.auditor.audit()
        errors = [f for f in findings if f.check_id == "REF_BROKEN"]
        self.assertEqual(len(errors), 1)

    # --- EMPTY_DIR check ---
    def test_empty_subdir_info(self):
        good = "---\nname: with-empty\ndescription: A skill with empty subdirectories inside it\n---\n# Body"
        skill_dir = self._make_skill("with-empty", good)
        os.makedirs(os.path.join(skill_dir, "scripts"))
        findings = self.auditor.audit()
        infos = [f for f in findings if f.check_id == "EMPTY_DIR"]
        self.assertEqual(len(infos), 1)

    # --- JSON output ---
    def test_json_output(self):
        self._make_skill("broken")  # orphan
        findings = self.auditor.audit()
        json_out = json.loads(self.auditor.to_json(findings))
        self.assertIn("findings", json_out)
        self.assertIn("summary", json_out)

    # --- Report output ---
    def test_report_output(self):
        self._make_skill("broken")  # orphan
        findings = self.auditor.audit()
        report = self.auditor.to_report(findings)
        self.assertIn("ORPHAN", report)
        self.assertIn("broken", report)

    # --- No skills dir ---
    def test_nonexistent_dir_returns_empty(self):
        auditor = SkillAuditor("/nonexistent/path")
        findings = auditor.audit()
        self.assertEqual(findings, [])

    # --- All clear report ---
    def test_all_clear_report(self):
        good = "---\nname: perfect\ndescription: A perfectly working skill with a good description\n---\n# Perfect"
        self._make_skill("perfect", good)
        findings = self.auditor.audit()
        serious = [f for f in findings if f.severity in (Severity.ERROR, Severity.WARN)]
        self.assertEqual(len(serious), 0)


if __name__ == "__main__":
    unittest.main()
