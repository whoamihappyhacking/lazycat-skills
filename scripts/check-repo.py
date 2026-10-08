#!/usr/bin/env python3
"""零依赖仓库静态筛选；严格 YAML 验证由 tests/test_examples.py 负责。"""

from __future__ import annotations

import argparse
import os
import re
import stat
import struct
import sys
import zipfile
from pathlib import Path

CALIBRATION_SKILLS = (
    "lazycat-advanced-routing",
    "lazycat-aipod-developer",
    "lazycat-auth-integration",
    "lazycat-developer-expert",
    "lazycat-dynamic-deploy",
    "lazycat-lpk-builder",
)
SHARED_GROUPS = (
    (
        "skills/lazycat-developer-expert/references/build-spec.md",
        "skills/lazycat-lpk-builder/references/build-spec.md",
    ),
    (
        "skills/lazycat-developer-expert/references/manifest-spec.md",
        "skills/lazycat-lpk-builder/references/manifest-spec.md",
    ),
    (
        "skills/lazycat-developer-expert/references/package-spec.md",
        "skills/lazycat-lpk-builder/references/package-spec.md",
    ),
    (
        "skills/lazycat-developer-expert/references/store-publish.md",
        "skills/lazycat-lpk-builder/references/store-publish.md",
    ),
    (
        "skills/lazycat-developer-expert/references/troubleshooting.md",
        "skills/lazycat-lpk-builder/references/troubleshooting.md",
    ),
    (
        "skills/lazycat-developer-expert/references/resource-export.md",
        "skills/lazycat-lpk-builder/references/resource-export.md",
    ),
    (
        "skills/lazycat-auth-integration/references/app-interconnect.md",
        "skills/lazycat-developer-expert/references/app-interconnect.md",
    ),
    tuple(f"skills/{name}/references/spec-sync.md" for name in CALIBRATION_SKILLS),
    tuple(f"skills/{name}/scripts/sync-specs.py" for name in CALIBRATION_SKILLS),
)
TEXT_SUFFIXES = {".md", ".py", ".mjs", ".js", ".yml", ".yaml", ".json", ".txt"}
INLINE_MD_RE = re.compile(r"`([^`\n]+\.md(?:#[^`\n]+)?)`")
MARKDOWN_LINK_RE = re.compile(r"\]\(([^)\s]+)")
REAL_BOX_RE = re.compile(r"(?<![\w${<{])([A-Za-z0-9-]+)\.heiyu\.space", re.IGNORECASE)
SAFE_BOX_LABELS = {"xx", "xxx", "devicename", "your-box-name"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def source_skill_dirs(root: Path) -> list[Path]:
    skills = root / "skills"
    return sorted(
        (path for path in skills.iterdir() if path.is_dir() and not path.is_symlink()),
        key=lambda path: path.name,
    )


def check_source_types(root: Path) -> list[str]:
    errors = []
    for top in (root / "scripts", root / "skills", root / ".github"):
        if not top.exists():
            continue
        for current, dirs, files in os.walk(top, followlinks=False):
            current_path = Path(current)
            for name in list(dirs):
                path = current_path / name
                if path.is_symlink():
                    errors.append(f"符号链接目录不允许：{rel(path, root)}")
                    dirs.remove(name)
            for name in files:
                path = current_path / name
                if path.is_symlink():
                    errors.append(f"符号链接文件不允许：{rel(path, root)}")
                elif not path.is_file():
                    errors.append(f"非普通文件不允许：{rel(path, root)}")
    return errors


def parse_frontmatter(path: Path) -> tuple[dict[str, str] | None, str | None]:
    """只筛选平坦必填字段；不声称实现 YAML，严格解析在 test_examples.py。"""
    lines = path.read_text("utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None, "缺少起始 ---"
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None, "缺少结束 ---"

    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#") or line.startswith((" ", "\t")):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in fields:
            return None, f"重复的顶层字段 {key!r}"
        fields[key] = value.strip().strip('"\'')
    return fields, None


def check_skills_and_readme(root: Path) -> list[str]:
    errors = []
    dirs = source_skill_dirs(root)
    names = {path.name for path in dirs}
    for skill_dir in dirs:
        skill = skill_dir / "SKILL.md"
        if not skill.is_file() or skill.is_symlink():
            errors.append(f"技能缺少普通文件 SKILL.md：{rel(skill_dir, root)}")
            continue
        fields, frontmatter_error = parse_frontmatter(skill)
        if frontmatter_error is not None:
            errors.append(f"frontmatter 无效：{rel(skill, root)}（{frontmatter_error}）")
            continue
        assert fields is not None
        if fields.get("name") != skill_dir.name:
            errors.append(f"frontmatter name 必须是与目录名相同的字符串：{rel(skill, root)}")
        description = fields.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"frontmatter description 必须是非空字符串：{rel(skill, root)}")

    readme = (root / "README.md").read_text("utf-8")
    listed = set(re.findall(r"(?m)^- `((?:lazycat-)[^`]+)`: ", readme))
    if listed != names:
        errors.append(
            "README 技能表与目录不一致："
            f"缺少={sorted(names - listed)}，多余={sorted(listed - names)}"
        )
    return errors


def check_shared_copies(root: Path) -> list[str]:
    errors = []
    for group in SHARED_GROUPS:
        paths = [root / item for item in group]
        missing = [rel(path, root) for path in paths if not path.is_file()]
        if missing:
            errors.append(f"共享副本缺失：{', '.join(missing)}")
            continue
        baseline = paths[0].read_bytes()
        different = [rel(path, root) for path in paths[1:] if path.read_bytes() != baseline]
        if different:
            errors.append(f"共享副本不一致：{rel(paths[0], root)} != {', '.join(different)}")

    for name in CALIBRATION_SKILLS:
        helper = root / "skills" / name / "scripts" / "sync-specs.py"
        if helper.is_file() and not helper.stat().st_mode & 0o111:
            errors.append(f"校准 helper 必须可执行：{rel(helper, root)}")
    return errors


def resolve_reference(
    skill_dir: Path, document: Path, target: str, all_skills: list[Path], context_line: str
) -> bool:
    target = target.split("#", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:", "#")):
        return True
    candidates = []
    if target.startswith(("references/", "scripts/")):
        candidates.append(skill_dir / target)
    else:
        candidates.extend((document.parent / target, skill_dir / "references" / target))
    if any(path.is_file() for path in candidates):
        return True
    # 明确写成跨技能说明时，允许解析到被点名技能；不允许静默依赖任意技能。
    line_candidates = [path for path in all_skills if f"`{path.name}`" in context_line]
    return any((path / "references" / Path(target).name).is_file() for path in line_candidates)


def check_references(root: Path) -> list[str]:
    errors = []
    skills = source_skill_dirs(root)
    for skill_dir in skills:
        for document in sorted(skill_dir.rglob("*.md")):
            text = document.read_text("utf-8")
            for line_number, line in enumerate(text.splitlines(), 1):
                targets = [match.group(1) for match in INLINE_MD_RE.finditer(line)]
                targets += [match.group(1) for match in MARKDOWN_LINK_RE.finditer(line)]
                for target in targets:
                    if target.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    # “官方 advanced-*.md”是上游源文件名，不是本技能的相对引用。
                    if "/" not in target and target.startswith("advanced-") and "官方" in line:
                        continue
                    if not resolve_reference(skill_dir, document, target, skills, line):
                        errors.append(
                            f"引用不存在：{rel(document, root)}:{line_number} -> {target}"
                        )
    return sorted(set(errors))


def iter_text_files(root: Path):
    for top_name in ("README.md", "AGENTS.md", "scripts", "skills", ".github"):
        top = root / top_name
        if top.is_file():
            yield top
        elif top.is_dir():
            for path in sorted(top.rglob("*")):
                if path.is_file() and not path.is_symlink() and path.suffix.lower() in TEXT_SUFFIXES:
                    yield path


def check_safety(root: Path) -> list[str]:
    errors = []
    for path in iter_text_files(root):
        text = path.read_text("utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"疑似真实凭据/私钥：{rel(path, root)} ({pattern.pattern})")
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in REAL_BOX_RE.finditer(line):
                label = match.group(1).lower()
                if label not in SAFE_BOX_LABELS:
                    errors.append(
                        f"疑似真实微服域名：{rel(path, root)}:{line_number} ({match.group(0)})"
                    )
    return errors


def yaml_regions(path: Path, text: str):
    if path.suffix.lower() in {".yml", ".yaml"}:
        yield 1, text
    fence = re.compile(r"(?ms)^```(?:ya?ml)\s*\n(.*?)^```\s*$", re.IGNORECASE)
    for match in fence.finditer(text):
        yield text.count("\n", 0, match.start(1)) + 1, match.group(1)


def find_v2_bad_patterns(path: Path, text: str) -> list[tuple[int, str]]:
    found = []
    for start_line, block in yaml_regions(path, text):
        checks = (
            (r"(?mi)^\s*apiVersion\s*:\s*lzc-sdk/v1\s*$", "LPK V1 apiVersion"),
            (r"(?mi)^\s*secondary_domains\s*:", "无官方依据的 secondary_domains"),
            (r"(?mi)^\s*pkg_id\s*:", "过时的 build.pkg_id"),
            (r"(?mi)^\s*backend\s*:\s*exec://", "upstreams.backend 不支持 exec://"),
            (r"(?mi)^\s*-?\s*/lzcapp/run/mnt/home(?:/|:|\s|$)", "V2 示例使用旧文稿挂载路径"),
        )
        for pattern, label in checks:
            for match in re.finditer(pattern, block):
                line = start_line + block.count("\n", 0, match.start())
                found.append((line, label))

        top_keys = set(re.findall(r"(?m)^([A-Za-z_][\w-]*)\s*:", block))
        if {"package", "version", "name"}.issubset(top_keys) and top_keys & {"application", "services"}:
            found.append((start_line, "V2 manifest 混入 package 元数据"))
        if re.search(r"(?mi)^\s*injects\s*:", block):
            for match in re.finditer(r"(?mi)^\s*-?\s*(include|exclude|mode|scripts)\s*:", block):
                line = start_line + block.count("\n", 0, match.start())
                found.append((line, f"injects 使用旧字段 {match.group(1)}"))
        if re.search(r"(?mi)^\s*buildscript\s*:", block) and re.search(
            r"lzc-cli\s+project\s+build", block
        ):
            found.append((start_line, "buildscript 递归调用 lzc-cli project build"))
    return found


def check_v2_patterns(root: Path) -> list[str]:
    errors = []
    for path in iter_text_files(root):
        if "skills" not in path.parts:
            continue
        text = path.read_text("utf-8", errors="replace")
        for line, label in find_v2_bad_patterns(path, text):
            errors.append(f"V2 坏模式：{rel(path, root)}:{line} ({label})")
    return errors


def normalized_mode(path: Path) -> int:
    return 0o100755 if path.stat().st_mode & 0o111 else 0o100644


def check_distributions(root: Path) -> list[str]:
    errors = []
    skill_dirs = source_skill_dirs(root)
    expected_archives = {f"{path.name}.skill" for path in skill_dirs}
    actual_archives = {path.name for path in (root / "skills").glob("*.skill")}
    if actual_archives != expected_archives:
        errors.append(
            "分发件集合与技能目录不一致："
            f"缺少={sorted(expected_archives - actual_archives)}，孤儿={sorted(actual_archives - expected_archives)}"
        )

    for skill_dir in skill_dirs:
        archive = root / "skills" / f"{skill_dir.name}.skill"
        if not archive.is_file() or archive.is_symlink():
            continue
        source_files = sorted(
            (path for path in skill_dir.rglob("*") if path.is_file() and not path.is_symlink()),
            key=lambda path: path.relative_to(skill_dir).as_posix(),
        )
        source_names = [path.relative_to(skill_dir).as_posix() for path in source_files]
        try:
            archive_bytes = archive.read_bytes()
            with zipfile.ZipFile(archive) as package:
                infos = package.infolist()
                names = [info.filename for info in infos]
                if len(names) != len(set(names)):
                    errors.append(f"ZIP 含重复成员：{rel(archive, root)}")
                if names != source_names:
                    errors.append(f"ZIP 成员/顺序与源目录不一致：{rel(archive, root)}")
                    continue
                for source, info in zip(source_files, infos):
                    name = info.filename
                    pure_parts = Path(name).parts
                    if name.startswith(("/", "\\")) or ".." in pure_parts or "\\" in name:
                        errors.append(f"ZIP 不安全路径：{rel(archive, root)} -> {name}")
                    if not info.flag_bits & 0x0800:
                        errors.append(f"ZIP central 成员未设置 UTF-8 标志：{rel(archive, root)} -> {name}")
                    if len(archive_bytes) < info.header_offset + 8 or struct.unpack_from(
                        "<I", archive_bytes, info.header_offset
                    )[0] != 0x04034B50:
                        errors.append(f"ZIP local header 无效：{rel(archive, root)} -> {name}")
                    else:
                        local_flags = struct.unpack_from("<H", archive_bytes, info.header_offset + 6)[0]
                        if not local_flags & 0x0800:
                            errors.append(
                                f"ZIP local 成员未设置 UTF-8 标志：{rel(archive, root)} -> {name}"
                            )
                    if info.date_time != (1980, 1, 1, 0, 0, 0):
                        errors.append(f"ZIP 时间戳不确定：{rel(archive, root)} -> {name}")
                    archive_mode = (info.external_attr >> 16) & 0xFFFF
                    if archive_mode != normalized_mode(source):
                        errors.append(
                            f"ZIP 权限不一致：{rel(archive, root)} -> {name} "
                            f"({archive_mode:o} != {normalized_mode(source):o})"
                        )
                    if stat.S_ISLNK(archive_mode):
                        errors.append(f"ZIP 不允许符号链接：{rel(archive, root)} -> {name}")
                    if package.read(info) != source.read_bytes():
                        errors.append(f"ZIP 内容与源文件不同：{rel(archive, root)} -> {name}")
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            errors.append(f"无法校验分发件 {rel(archive, root)}：{error}")
    return errors


def run_checks(root: Path, *, skip_distributions: bool = False) -> list[str]:
    checks = (
        check_source_types,
        check_skills_and_readme,
        check_shared_copies,
        check_references,
        check_safety,
        check_v2_patterns,
    )
    errors = []
    for check in checks:
        errors.extend(check(root))
    if not skip_distributions:
        errors.extend(check_distributions(root))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--skip-distributions",
        action="store_true",
        help="仅供修改源码、尚未由主流程重建 .skill 时做其余检查；CI 不得使用",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = run_checks(root, skip_distributions=args.skip_distributions)
    if errors:
        print(f"✗ 仓库检查失败（{len(errors)} 项）：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("✓ 仓库结构、共享副本、引用、分发件、安全与 V2 坏模式检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
