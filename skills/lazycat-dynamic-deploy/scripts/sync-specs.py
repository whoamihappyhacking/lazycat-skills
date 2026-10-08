#!/usr/bin/env python3
"""安全拉取懒猫官方规范，并生成可审计的来源与 SHA-256 记录。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPOSITORY = "https://gitee.com/lazycatcloud/lzc-developer-doc"
RAW_TEMPLATE = REPOSITORY + "/raw/{ref}/docs/{path}.md"
SITE_TEMPLATE = "https://developer.lazycat.cloud/{path}.html"
MAX_BYTES = 5 * 1024 * 1024
USER_AGENT = "lazycat-skills-spec-sync/1.0 (+https://github.com/whoamihappyhacking/lazycat-skills)"
VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


@dataclass(frozen=True)
class Page:
    topic: str
    path: str | None
    title: str
    core: bool = False
    site_url: str | None = None
    site_kind: str = "site"
    aipod_required: bool = False


PAGES = (
    Page("package", "spec/package", "package.yml", True),
    Page("manifest", "spec/manifest", "lzc-manifest.yml", True),
    Page("build", "spec/build", "lzc-build.yml", True),
    Page("deploy-params", "spec/deploy-params", "lzc-deploy-params.yml", True),
    Page("lpk-format", "spec/lpk-format", "LPK 包格式", True),
    Page("route", "advanced-route", "HTTP 路由"),
    Page("secondary-domains", "advanced-secondary-domains", "应用多域名"),
    Page("l4forward", "advanced-l4forward", "TCP/UDP 四层转发"),
    Page("public-api", "advanced-public-api", "独立鉴权与 public_path"),
    Page("oidc", "advanced-oidc", "OIDC 单点登录"),
    Page("headers", "http-request-headers", "HTTP 身份 Header"),
    Page("injects", "advanced-injects", "脚本注入"),
    Page("passwordless-login", "advanced-inject-passwordless-login", "免密登录专题"),
    Page("inject-dev-cookbook", "advanced-inject-request-dev-cookbook", "开发态注入 Cookbook"),
    Page("manifest-render", "advanced-manifest-render", "manifest 模板渲染"),
    Page("setup-script", "advanced-setupscript", "初始化脚本"),
    Page("envs", "advanced-envs", "部署时环境变量"),
    Page("api-auth-token", "advanced-api-auth-token", "API Auth Token"),
    Page("app-interconnect", "advanced-app-interconnect", "应用间访问"),
    Page("compose-override", "advanced-compose-override", "Compose override"),
    Page("entries", "advanced-entries", "应用 entries"),
    Page("vt", "advanced-vt", "VT 图形应用"),
    Page("skill-mcp", "resource-skill-mcp", "Skill / MCP 资源"),
    Page("resource-export", "spec/resource-export", "资源导出规范"),
    Page("store-submission", "store-submission-guide", "上架审核规则"),
    Page("gpu", "advanced-gpu", "GPU 加速"),
    Page("multi-instance", "advanced-multi-instance", "多实例"),
    # AI Pod 规范不在通用 Gitee 文档仓库中，只能从官方专页取得并用 digest 固定。
    Page(
        "aipod-package-spec",
        None,
        "AI Pod package 专页",
        site_url="https://developer.lazycat.cloud/aipod/package/spec.html",
        aipod_required=True,
    ),
    Page(
        "aipod-llms-full",
        None,
        "AI Pod 完整文档文本",
        site_url="https://developer.lazycat.cloud/aipod/llms-full.txt",
        site_kind="site-text",
        aipod_required=True,
    ),
)
PAGE_BY_TOPIC = {page.topic: page for page in PAGES}


class ValidationError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_version(value: str) -> str:
    if not VERSION_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("必须是明确的语义版本，如 1.6.1（不能写 latest/unknown）")
    return value.removeprefix("v")


def validate_commit(value: str) -> str:
    if not COMMIT_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("必须是 7–40 位十六进制官方 commit")
    return value.lower()


def _read_limited(response, limit: int = MAX_BYTES) -> bytes:
    length = response.headers.get("Content-Length")
    if length:
        try:
            if int(length) > limit:
                raise ValidationError(f"正文超过 {limit} bytes")
        except ValueError:
            pass
    chunks = []
    total = 0
    while True:
        chunk = response.read(min(65536, limit + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > limit:
            raise ValidationError(f"正文超过 {limit} bytes")
    return b"".join(chunks)


def _obvious_error_title(title: str) -> bool:
    normalized = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", title)).strip(" #`*_~-:：").lower()
    exact_errors = {
        "error",
        "not found",
        "page not found",
        "access denied",
        "forbidden",
        "bad gateway",
        "service unavailable",
        "login",
        "sign in",
        "captcha",
        "错误",
        "页面不存在",
        "访问被拒绝",
    }
    return normalized in exact_errors or bool(re.match(r"^(?:4\d\d|5\d\d)(?:\b|\s|[-:：])", normalized))


def validate_body(body: bytes, content_type: str, kind: str) -> None:
    if not body.strip():
        raise ValidationError("正文为空")
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError(f"正文不是有效 UTF-8：{error}") from error

    media_type = content_type.split(";", 1)[0].strip().lower()
    sample = text[:16384].lstrip()
    sample_lower = sample.lower()
    looks_html = bool(re.match(r"(?:<!doctype\s+html|<html(?:\s|>))", sample_lower))

    if kind in {"raw", "site-text"}:
        label = "raw" if kind == "raw" else "官方文本页"
        if media_type in {"text/html", "application/xhtml+xml"} or looks_html:
            raise ValidationError(f"{label}返回 HTML，疑似错误页/登录页")
        if media_type and media_type not in {
            "text/plain",
            "text/markdown",
            "text/x-markdown",
            "application/octet-stream",
        }:
            raise ValidationError(f"{label} Content-Type 异常：{media_type}")
        heading = re.search(r"(?m)^\s{0,3}#{1,6}[ \t]+(.+?)\s*$", text)
        if heading is None:
            raise ValidationError(f"{label}缺少 Markdown 标题结构，疑似纯文本错误页")
        if _obvious_error_title(heading.group(1)):
            raise ValidationError(f"{label}首个 Markdown 标题是明显错误页标题")
        return

    if media_type not in {"text/html", "application/xhtml+xml"} and not looks_html:
        raise ValidationError(f"文档站未返回 HTML：{media_type or '无 Content-Type'}")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", sample, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1) if title_match else ""
    waf_markers = ("cf-chl-", "just a moment...</title>", "challenge-platform")
    if any(marker in sample_lower for marker in waf_markers) or _obvious_error_title(title):
        raise ValidationError("文档站返回明显错误页/登录页/验证页")

    html_lower = text.lower()
    has_vitepress = bool(re.search(r'class=["\'][^"\']*(?:vp-doc|vpcontent)\b', html_lower))
    has_main = bool(re.search(r"<main(?:\s|>)", html_lower))
    has_article = bool(re.search(r"<article(?:\s|>)", html_lower))
    has_heading = bool(re.search(r"<h[12](?:\s|>)", html_lower))
    visible_text = re.sub(r"<[^>]+>", " ", text)
    reasonable_main = has_main and has_article and has_heading and len(visible_text.strip()) >= 200
    if not ((has_vitepress and has_heading) or reasonable_main):
        raise ValidationError("文档站 HTML 缺少 VitePress/正文标题结构，疑似 200 占位页")


def download_url(url: str, kind: str, timeout: float, *, allow_http: bool = False) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" and not (allow_http and parsed.scheme == "http"):
        raise ValidationError("只允许 HTTPS 官方来源")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/plain,text/markdown"
                if kind in {"raw", "site-text"}
                else "text/html,application/xhtml+xml"
            ),
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", response.getcode())
        if status != 200:
            raise ValidationError(f"HTTP {status}")
        final_url = response.geturl()
        final_scheme = urllib.parse.urlparse(final_url).scheme
        if final_scheme != "https" and not (allow_http and final_scheme == "http"):
            raise ValidationError("重定向到了非 HTTPS 地址")
        content_type = response.headers.get("Content-Type", "")
        body = _read_limited(response)
    validate_body(body, content_type, kind)
    return body, final_url, content_type


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".sync-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def source_urls(page: Page, official_commit: str | None) -> tuple[tuple[str, str], ...]:
    candidates = []
    if page.path is not None:
        ref = official_commit or "master"
        raw = RAW_TEMPLATE.format(ref=urllib.parse.quote(ref, safe=""), path=page.path)
        site = SITE_TEMPLATE.format(path=page.path)
        candidates.extend((("raw", raw), ("site", site)))
    if page.site_url is not None:
        candidates.append((page.site_kind, page.site_url))
    return tuple(candidates)


def sync_pages(
    pages: Iterable[Page],
    task_dir: Path,
    timeout: float,
    official_commit: str | None,
    *,
    allow_http: bool = False,
    url_factory=source_urls,
) -> tuple[list[dict], list[dict]]:
    successes = []
    failures = []
    for page in pages:
        attempts = []
        for kind, url in url_factory(page, official_commit):
            try:
                body, final_url, content_type = download_url(
                    url, kind, timeout, allow_http=allow_http
                )
                suffix = {"raw": ".md", "site": ".html", "site-text": ".txt"}[kind]
                filename = page.topic + suffix
                atomic_write(task_dir / filename, body)
                successes.append(
                    {
                        "topic": page.topic,
                        "title": page.title,
                        "status": "downloaded",
                        "source_kind": kind,
                        "official_commit": official_commit if kind == "raw" else None,
                        "requested_url": url,
                        "source_url": final_url,
                        "content_type": content_type,
                        "local_file": filename,
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "attempt_errors": attempts,
                    }
                )
                print(f"OK    {page.topic:<22} {kind:<9} {len(body):>7} bytes")
                break
            except urllib.error.HTTPError as error:
                # HTTPError 同时是可读响应对象；显式关闭，避免批量失败时泄漏连接。
                error.close()
                attempts.append({"source_kind": kind, "url": url, "error": str(error)})
            except (OSError, urllib.error.URLError, ValidationError) as error:
                attempts.append({"source_kind": kind, "url": url, "error": str(error)})
        else:
            failure = {
                "topic": page.topic,
                "title": page.title,
                "status": "offline-unavailable",
                "attempt_errors": attempts,
            }
            failures.append(failure)
            print(f"FAIL  {page.topic:<22} 所有配置的官方来源均不可用", file=sys.stderr)
    return successes, failures


def select_pages(all_requested: bool, topics: list[str] | None, skill_name: str) -> list[Page]:
    if all_requested:
        selected = list(PAGES)
    elif topics:
        selected = [PAGE_BY_TOPIC[topic] for topic in dict.fromkeys(topics)]
    else:
        selected = [page for page in PAGES if page.core]

    # AI Pod 的权威专页在通用仓库之外；从 Pod 技能运行时不可只校准通用五篇。
    if skill_name == "lazycat-aipod-developer":
        selected_topics = {page.topic for page in selected}
        selected.extend(
            page for page in PAGES if page.aipod_required and page.topic not in selected_topics
        )
    return selected


def create_task_dir(output_root: Path | None) -> Path:
    prefix = "lzc-spec-" + datetime.now().strftime("%Y%m%d-%H%M%S-")
    if output_root is not None:
        output_root.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix=prefix, dir=output_root))
    return Path(tempfile.mkdtemp(prefix=prefix))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="按 raw → 官方文档站顺序拉取规范；任一页失败即非零退出。"
    )
    parser.add_argument("--lzcos-version", required=True, type=validate_version, help="目标 lzcos 明确版本")
    parser.add_argument("--cli-version", required=True, type=validate_version, help="目标 lzc-cli 明确版本")
    parser.add_argument(
        "--topic",
        action="append",
        choices=sorted(PAGE_BY_TOPIC),
        help="只拉取指定专题，可重复；默认拉取 5 篇核心规范（AI Pod 技能会强制附加专页）",
    )
    parser.add_argument("--all", action="store_true", help="拉取核心与全部专题")
    parser.add_argument("--official-commit", type=validate_commit, help="固定官方仓库 commit；否则逐页记录原文 SHA-256")
    parser.add_argument("--timeout", type=float, default=15.0, help="每次 HTTP 操作超时秒数（1–60，默认 15）")
    parser.add_argument("--output-root", type=Path, help="任务独立目录的父目录；默认使用系统临时目录")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.all and args.topic:
        parser.error("--all 与 --topic 不能同时使用")
    if not 1 <= args.timeout <= 60:
        parser.error("--timeout 必须在 1–60 秒之间")

    skill_name = Path(__file__).resolve().parents[1].name
    pages = select_pages(args.all, args.topic, skill_name)

    print(f"目标版本核验：lzcos={args.lzcos_version}，lzc-cli={args.cli_version}")
    if skill_name == "lazycat-aipod-developer":
        print("AI Pod 校准：已强制加入官方 package 专页与 llms-full.txt")
    task_dir = create_task_dir(args.output_root)
    print(f"任务目录：{task_dir}")
    successes, failures = sync_pages(pages, task_dir, args.timeout, args.official_commit)

    record = {
        "schema_version": 1,
        "created_at": utc_now(),
        "repository": REPOSITORY,
        "requested_official_commit": args.official_commit,
        "target_versions": {"lzcos": args.lzcos_version, "lzc_cli": args.cli_version},
        "result": "success" if not failures else "incomplete-offline",
        "source_policy": [
            "gitee-raw",
            "developer-site",
            "aipod-official-site-only",
            "explicit-offline-declaration",
        ],
        "documents": successes + failures,
    }
    if failures:
        record["offline_declaration"] = (
            "官方 raw 与文档站仍有页面不可用；未把本地快照或错误页记为成功。"
            "如改用技能内 references，必须向用户声明可能过期，并在网络恢复后重跑。"
        )
    atomic_write(
        task_dir / "calibration.json",
        (json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    if failures:
        print("\n失败汇总：", file=sys.stderr)
        for failure in failures:
            print(f"- {failure['topic']}", file=sys.stderr)
            for attempt in failure["attempt_errors"]:
                print(
                    f"  {attempt['source_kind']}: {attempt['url']} -> {attempt['error']}",
                    file=sys.stderr,
                )
        print(
            "⚠️ 校准未完成（离线/来源异常），不得把本次结果声明为校准成功。",
            file=sys.stderr,
        )
        print(f"审计记录：{task_dir / 'calibration.json'}", file=sys.stderr)
        return 2

    print(f"\n校准下载完成；来源与 SHA-256：{task_dir / 'calibration.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
