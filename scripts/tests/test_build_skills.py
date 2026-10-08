from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build-skills.mjs"


class BuildSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lazycat-build-test-")
        self.root = Path(self.temporary.name)
        (self.root / "scripts").mkdir()
        (self.root / "skills").mkdir()
        shutil.copy2(BUILD_SCRIPT, self.root / "scripts" / "build-skills.mjs")

    def tearDown(self):
        self.temporary.cleanup()

    def make_skill(self, name="demo") -> Path:
        skill = self.root / "skills" / name
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: demo\ndescription: test\n---\n# Demo\n", encoding="utf-8"
        )
        return skill

    def run_build(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["node", "scripts/build-skills.mjs", *args],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_rejects_unknown_argument_without_writing(self):
        self.make_skill()
        result = self.run_build("--chek")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("未知参数", result.stderr)
        self.assertFalse((self.root / "skills" / "demo.skill").exists())

    def test_deterministic_utf8_and_normalized_permissions(self):
        skill = self.make_skill()
        (skill / "说明.md").write_text("中文文件名\n", encoding="utf-8")
        scripts = skill / "scripts"
        scripts.mkdir()
        executable = scripts / "run.sh"
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o711)
        (skill / "SKILL.md").chmod(0o600)

        first = self.run_build()
        self.assertEqual(first.returncode, 0, first.stderr)
        archive = self.root / "skills" / "demo.skill"
        first_bytes = archive.read_bytes()
        second = self.run_build()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first_bytes, archive.read_bytes())
        checked = self.run_build("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

        archive_bytes = archive.read_bytes()
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(package.namelist(), ["SKILL.md", "scripts/run.sh", "说明.md"])
            for info in package.infolist():
                self.assertTrue(info.flag_bits & 0x0800, info.filename)
                local_flags = int.from_bytes(
                    archive_bytes[info.header_offset + 6 : info.header_offset + 8], "little"
                )
                self.assertTrue(local_flags & 0x0800, info.filename)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
            modes = {
                info.filename: (info.external_attr >> 16) & 0xFFFF
                for info in package.infolist()
            }
            self.assertEqual(modes["SKILL.md"], stat.S_IFREG | 0o644)
            self.assertEqual(modes["说明.md"], stat.S_IFREG | 0o644)
            self.assertEqual(modes["scripts/run.sh"], stat.S_IFREG | 0o755)
            self.assertEqual(package.read("说明.md"), "中文文件名\n".encode())

    def test_rejects_empty_skills_directory(self):
        result = self.run_build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("没有可打包的技能目录", result.stderr)

    def test_rejects_directory_without_skill_before_any_write(self):
        self.make_skill("valid")
        invalid = self.root / "skills" / "invalid"
        invalid.mkdir()
        (invalid / "note.md").write_text("missing SKILL\n", encoding="utf-8")
        result = self.run_build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("缺少必需的 SKILL.md", result.stderr)
        self.assertFalse((self.root / "skills" / "valid.skill").exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "platform has no symlink")
    def test_rejects_recursive_and_top_level_symlinks(self):
        skill = self.make_skill()
        target = self.root / "outside.txt"
        target.write_text("outside\n", encoding="utf-8")
        os.symlink(target, skill / "linked.txt")
        result = self.run_build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("拒绝符号链接", result.stderr)
        self.assertFalse((self.root / "skills" / "demo.skill").exists())

        (skill / "linked.txt").unlink()
        os.symlink(skill, self.root / "skills" / "linked-skill")
        result = self.run_build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("顶层符号链接", result.stderr)


if __name__ == "__main__":
    unittest.main()
