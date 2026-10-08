from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "skills" / "lazycat-lpk-builder" / "scripts" / "sync-specs.py"

spec = importlib.util.spec_from_file_location("sync_specs", HELPER)
sync_specs = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = sync_specs
spec.loader.exec_module(sync_specs)


class RouteHandler(BaseHTTPRequestHandler):
    routes = {}

    def do_GET(self):
        status, content_type, body = self.routes.get(
            self.path, (404, "text/plain", b"not found")
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        pass


class SyncSpecsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lazycat-sync-test-")
        self.task_dir = Path(self.temporary.name) / "task"
        self.task_dir.mkdir()
        handler = type("IsolatedRouteHandler", (RouteHandler,), {"routes": {}})
        self.handler = handler
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def factory(self, page, _commit):
        return (
            ("raw", f"{self.base}/raw/{page.topic}"),
            ("site", f"{self.base}/site/{page.topic}"),
        )

    def run_sync(self, pages, official_commit=None):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return sync_specs.sync_pages(
                pages,
                self.task_dir,
                2,
                official_commit,
                allow_http=True,
                url_factory=self.factory,
            )

    def test_html_masquerading_as_raw_falls_back_to_site(self):
        page = sync_specs.Page("example", "unused", "Example")
        self.handler.routes.update(
            {
                "/raw/example": (200, "text/plain", b"\xef\xbb\xbf<!doctype html><html>login</html>"),
                "/site/example": (
                    200,
                    "text/html; charset=utf-8",
                    b'<!doctype html><html><head><title>Docs</title></head>'
                    b'<body><main class="VPContent"><div class="vp-doc">'
                    b'<h1>Official Docs</h1><p>official</p></div></main></body></html>',
                ),
            }
        )
        successes, failures = self.run_sync([page])
        self.assertFalse(failures)
        self.assertEqual(successes[0]["source_kind"], "site")
        self.assertIsNone(successes[0]["official_commit"])
        self.assertIn("raw返回 HTML", successes[0]["attempt_errors"][0]["error"])
        self.assertTrue((self.task_dir / "example.html").is_file())

    def test_site_login_page_is_rejected_even_with_http_200(self):
        with self.assertRaises(sync_specs.ValidationError):
            sync_specs.validate_body(
                b"<!doctype html><html><head><title>Sign In</title></head></html>",
                "text/html",
                "site",
            )

    def test_plain_text_error_and_invalid_utf8_are_rejected(self):
        for body in (b"temporary backend error", b"# 503 Service Unavailable\n", b"# Docs\n\xff"):
            with self.subTest(body=body), self.assertRaises(sync_specs.ValidationError):
                sync_specs.validate_body(body, "text/plain", "raw")

    def test_document_login_content_is_not_mistaken_for_error(self):
        sync_specs.validate_body(
            "# Passwordless Login\n\n本文讨论 password 与 login。\n".encode(),
            "text/markdown; charset=utf-8",
            "raw",
        )
        sync_specs.validate_body(
            b'<!doctype html><html><head><title>Passwordless Login Guide</title></head>'
            b'<body><main class="VPContent"><article class="vp-doc">'
            b'<h1>Passwordless Login</h1><p>password and login guide</p>'
            b'</article></main></body></html>',
            "text/html; charset=utf-8",
            "site",
        )

    def test_minimal_hello_html_is_not_a_document_page(self):
        with self.assertRaises(sync_specs.ValidationError):
            sync_specs.validate_body(
                b"<!doctype html><html><head><title>Hello</title></head><body>Hello</body></html>",
                "text/html",
                "site",
            )

    def test_http_error_and_empty_body_are_aggregated(self):
        pages = (
            sync_specs.Page("one", "unused", "One"),
            sync_specs.Page("two", "unused", "Two"),
        )
        self.handler.routes.update(
            {
                "/raw/one": (404, "text/plain", b"missing"),
                "/site/one": (200, "text/html", b""),
                "/raw/two": (200, "text/plain", b" \n"),
                "/site/two": (503, "text/html", b"down"),
            }
        )
        successes, failures = self.run_sync(pages)
        self.assertFalse(successes)
        self.assertEqual([item["topic"] for item in failures], ["one", "two"])
        self.assertTrue(all(len(item["attempt_errors"]) == 2 for item in failures))
        self.assertFalse(list(self.task_dir.glob("*.md")))
        self.assertFalse(list(self.task_dir.glob("*.html")))
        self.assertFalse(list(self.task_dir.glob(".sync-*")))

    def test_raw_success_records_actual_source_and_digest(self):
        page = sync_specs.Page("good", "unused", "Good")
        body = b"# Official markdown\n"
        self.handler.routes["/raw/good"] = (200, "text/plain; charset=utf-8", body)
        successes, failures = self.run_sync([page], "780d720")
        self.assertFalse(failures)
        result = successes[0]
        self.assertEqual(result["source_url"], f"{self.base}/raw/good")
        self.assertEqual(result["official_commit"], "780d720")
        self.assertEqual(result["sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual((self.task_dir / "good.md").read_bytes(), body)

    def test_incomplete_main_record_is_not_success(self):
        task = Path(self.temporary.name) / "main-task"
        failure = {
            "topic": "package",
            "title": "package.yml",
            "status": "offline-unavailable",
            "attempt_errors": [
                {"source_kind": "raw", "url": "https://example.invalid/raw", "error": "offline"},
                {"source_kind": "site", "url": "https://example.invalid/site", "error": "offline"},
            ],
        }
        with mock.patch.object(sync_specs, "create_task_dir", return_value=task), mock.patch.object(
            sync_specs, "sync_pages", return_value=([], [failure])
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = sync_specs.main(["--lzcos-version", "1.6.1", "--cli-version", "2.0.0"])
        self.assertEqual(code, 2)
        record = json.loads((task / "calibration.json").read_text("utf-8"))
        self.assertEqual(record["result"], "incomplete-offline")
        self.assertIn("未把本地快照", record["offline_declaration"])

    def test_required_new_topics_are_available(self):
        required = {
            "passwordless-login",
            "inject-dev-cookbook",
            "compose-override",
            "vt",
            "entries",
            "aipod-package-spec",
            "aipod-llms-full",
        }
        self.assertTrue(required.issubset(sync_specs.PAGE_BY_TOPIC))

    def test_aipod_profile_always_adds_both_exclusive_sources(self):
        selected = sync_specs.select_pages(False, ["route"], "lazycat-aipod-developer")
        topics = {page.topic for page in selected}
        self.assertEqual(
            {"aipod-package-spec", "aipod-llms-full"},
            topics & {"aipod-package-spec", "aipod-llms-full"},
        )
        self.assertEqual(len(topics), len(selected))

    def test_versions_and_timeout_must_be_explicit(self):
        with self.assertRaises(Exception):
            sync_specs.validate_version("latest")
        self.assertEqual(sync_specs.validate_version("v1.6.1"), "1.6.1")
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            sync_specs.main(["--lzcos-version", "1.6.1", "--cli-version", "2.0.0", "--timeout", "0"])


if __name__ == "__main__":
    unittest.main()
