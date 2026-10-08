from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check-repo.py"

spec = importlib.util.spec_from_file_location("check_repo", CHECKER)
check_repo = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check_repo)


class CheckRepoTests(unittest.TestCase):
    def test_detects_v2_yaml_bad_patterns(self):
        text = """Example:
```yaml
package: old.example
version: 1.0.0
name: Old
application:
  secondary_domains:
    - extra
  injects:
    - include: /login
      scripts: []
services: {}
```
"""
        found = check_repo.find_v2_bad_patterns(Path("example.md"), text)
        labels = {label for _line, label in found}
        self.assertIn("V2 manifest 混入 package 元数据", labels)
        self.assertIn("无官方依据的 secondary_domains", labels)
        self.assertIn("injects 使用旧字段 include", labels)
        self.assertIn("injects 使用旧字段 scripts", labels)

    def test_deprecation_prose_outside_yaml_is_not_a_bad_example(self):
        text = "旧路径 `/lzcapp/run/mnt/home` 只能作为历史说明，不要用于 V2。\n"
        self.assertEqual(check_repo.find_v2_bad_patterns(Path("note.md"), text), [])

    def test_readme_skill_table_must_match_directories(self):
        with tempfile.TemporaryDirectory(prefix="lazycat-check-test-") as temporary:
            root = Path(temporary)
            skill = root / "skills" / "lazycat-demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: lazycat-demo\ndescription: demo\n---\n", encoding="utf-8"
            )
            (root / "README.md").write_text("# Missing table\n", encoding="utf-8")
            errors = check_repo.check_skills_and_readme(root)
            self.assertTrue(any("README 技能表" in error for error in errors))

    def test_ignored_external_agent_skills_are_not_core_skills(self):
        with tempfile.TemporaryDirectory(prefix="lazycat-check-test-") as temporary:
            root = Path(temporary)
            core = root / "skills" / "lazycat-demo"
            external = root / ".agents" / "skills" / "third-party"
            core.mkdir(parents=True)
            external.mkdir(parents=True)
            (core / "SKILL.md").write_text(
                "---\nname: lazycat-demo\ndescription: demo\n---\n", encoding="utf-8"
            )
            (external / "SKILL.md").write_text(
                "---\nname: third-party\ndescription: external\n---\n", encoding="utf-8"
            )
            (root / "README.md").write_text("- `lazycat-demo`: demo\n", encoding="utf-8")
            self.assertEqual(check_repo.check_skills_and_readme(root), [])

    def test_lightweight_frontmatter_filter_rejects_repeated_top_level_field(self):
        with tempfile.TemporaryDirectory(prefix="lazycat-check-test-") as temporary:
            skill = Path(temporary) / "SKILL.md"
            skill.write_text(
                "---\nname: first\nname: second\ndescription: demo\n---\n",
                encoding="utf-8",
            )
            fields, error = check_repo.parse_frontmatter(skill)
            self.assertIsNone(fields)
            self.assertIn("重复", error)

    def test_lightweight_frontmatter_filter_requires_closing_delimiter(self):
        with tempfile.TemporaryDirectory(prefix="lazycat-check-test-") as temporary:
            skill = Path(temporary) / "SKILL.md"
            skill.write_text("---\nname: demo\ndescription: demo\n", encoding="utf-8")
            fields, error = check_repo.parse_frontmatter(skill)
            self.assertIsNone(fields)
            self.assertIn("结束", error)

    def test_real_box_domain_is_rejected_but_placeholders_are_allowed(self):
        with tempfile.TemporaryDirectory(prefix="lazycat-check-test-") as temporary:
            root = Path(temporary)
            (root / "skills").mkdir()
            suffix = ".heiyu" + ".space"
            real_domain = "sensitivebox" + suffix
            (root / "README.md").write_text(
                f"{real_domain}\nxx{suffix}\nyour-box-name{suffix}\n",
                encoding="utf-8",
            )
            errors = check_repo.check_safety(root)
            self.assertEqual(len(errors), 1)
            self.assertIn(real_domain, errors[0])


if __name__ == "__main__":
    unittest.main()
