#!/usr/bin/env python

import contextlib
import email
import io
import os
import socket
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from mkdocs.exceptions import Abort
from mkdocs.livereload import LiveReloadServer, _try_relativize_path
from mkdocs.tests.base import change_dir, tempdir


class FakeRequest:
    def __init__(self, content):
        self.in_file = io.BytesIO(content.encode())
        self.out_file = io.BytesIO()
        self.out_file.close = lambda: None

    def makefile(self, *args, **kwargs):
        return self.in_file

    def sendall(self, data):
        self.out_file.write(data)


@contextlib.contextmanager
def testing_server(root, builder=lambda: None, mount_path="/"):
    """Create the server and start most of its parts, but don't listen on a socket."""
    with mock.patch("socket.socket"):
        server = LiveReloadServer(
            builder,
            host="localhost",
            port=0,
            root=root,
            mount_path=mount_path,
            polling_interval=0.2,
        )
        server.server_name = "localhost"
        server.server_port = 0
        server.setup_environ()
    server.observer.start()
    thread = threading.Thread(target=server._build_loop, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join()


def do_request(server, content):
    request = FakeRequest(content + " HTTP/1.1")
    server.RequestHandlerClass(request, ("127.0.0.1", 0), server)
    response = request.out_file.getvalue()

    headers, _, content = response.partition(b"\r\n\r\n")
    status, _, headers = headers.partition(b"\r\n")
    status = status.split(None, 1)[1].decode()

    headers = email.message_from_bytes(headers)
    headers["_status"] = status
    return headers, content.decode()


SCRIPT_REGEX = r"<script>[\S\s]+?livereload\([0-9]+, [0-9]+\);\s*</script>"


class BuildTests(unittest.TestCase):
    @tempdir({"test.css": "div { color: red; }"})
    def test_serves_normal_file(self, site_dir):
        with testing_server(site_dir) as server:
            headers, output = do_request(server, "GET /test.css")
            self.assertEqual(output, "div { color: red; }")
            self.assertEqual(headers["_status"], "200 OK")
            self.assertEqual(headers.get("content-length"), str(len(output)))

    @tempdir({"docs/foo.docs": "docs1", "mkdocs.yml": "yml1"})
    @tempdir({"foo.site": "original"})
    def test_basic_rebuild(self, site_dir, origin_dir):
        docs_dir = Path(origin_dir, "docs")

        started_building = threading.Event()

        def rebuild():
            started_building.set()
            Path(site_dir, "foo.site").write_text(
                Path(docs_dir, "foo.docs").read_text()
                + Path(origin_dir, "mkdocs.yml").read_text()
            )

        with testing_server(site_dir, rebuild) as server:
            server.watch(docs_dir, rebuild)
            server.watch(Path(origin_dir, "mkdocs.yml"), rebuild)
            time.sleep(0.01)

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "original")

            Path(docs_dir, "foo.docs").write_text("docs2")
            self.assertTrue(started_building.wait(timeout=10))
            started_building.clear()

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "docs2yml1")

            Path(origin_dir, "mkdocs.yml").write_text("yml2")
            self.assertTrue(started_building.wait(timeout=10))
            started_building.clear()

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "docs2yml2")

    @tempdir({"foo.docs": "a"})
    @tempdir({"foo.site": "original"})
    def test_rebuild_after_delete(self, site_dir, docs_dir):
        started_building = threading.Event()

        def rebuild():
            started_building.set()
            Path(site_dir, "foo.site").unlink()

        with testing_server(site_dir, rebuild) as server:
            server.watch(docs_dir, rebuild)
            time.sleep(0.01)

            Path(docs_dir, "foo.docs").write_text("b")
            self.assertTrue(started_building.wait(timeout=10))

            with self.assertLogs("mkdocs.livereload"):
                _, output = do_request(server, "GET /foo.site")

            self.assertIn("404", output)

    @tempdir({"aaa": "something"})
    def test_rebuild_after_rename(self, site_dir):
        started_building = threading.Event()

        with testing_server(site_dir, started_building.set) as server:
            server.watch(site_dir)
            time.sleep(0.01)

            Path(site_dir, "aaa").rename(Path(site_dir, "bbb"))
            self.assertTrue(started_building.wait(timeout=10))

    @tempdir()
    def test_rebuild_on_edit(self, site_dir):
        started_building = threading.Event()

        with open(Path(site_dir, "test"), "wb") as f:
            time.sleep(0.01)

            with testing_server(site_dir, started_building.set) as server:
                server.watch(site_dir)
                time.sleep(0.01)

                f.write(b"hi\n")
                f.flush()

                self.assertTrue(started_building.wait(timeout=10))

    @tempdir()
    def test_unwatch(self, site_dir):
        started_building = threading.Event()

        with testing_server(site_dir, started_building.set) as server:
            with self.assertRaises(KeyError):
                server.unwatch(site_dir)

            server.watch(site_dir)
            server.watch(site_dir)
            server.unwatch(site_dir)
            time.sleep(0.01)

            Path(site_dir, "foo").write_text("foo")
            self.assertTrue(started_building.wait(timeout=10))
            started_building.clear()

            server.unwatch(site_dir)
            Path(site_dir, "foo").write_text("bar")
            self.assertFalse(started_building.wait(timeout=0.5))

            with self.assertRaises(KeyError):
                server.unwatch(site_dir)

    @tempdir({"foo.docs": "docs1"})
    @tempdir({"foo.extra": "extra1"})
    @tempdir({"foo.site": "original"})
    def test_multiple_dirs_can_cause_rebuild(self, site_dir, extra_dir, docs_dir):
        started_building = threading.Barrier(2)

        def rebuild():
            started_building.wait(timeout=10)
            content1 = Path(docs_dir, "foo.docs").read_text()
            content2 = Path(extra_dir, "foo.extra").read_text()
            Path(site_dir, "foo.site").write_text(content1 + content2)

        with testing_server(site_dir, rebuild) as server:
            server.watch(docs_dir)
            server.watch(extra_dir)
            time.sleep(0.01)

            Path(docs_dir, "foo.docs").write_text("docs2")
            started_building.wait(timeout=10)

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "docs2extra1")

            Path(extra_dir, "foo.extra").write_text("extra2")
            started_building.wait(timeout=10)

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "docs2extra2")

    @tempdir({"foo.docs": "docs1"})
    @tempdir({"foo.extra": "extra1"})
    @tempdir({"foo.site": "original"})
    def test_multiple_dirs_changes_rebuild_only_once(
        self, site_dir, extra_dir, docs_dir
    ):
        started_building = threading.Event()

        def rebuild():
            self.assertFalse(started_building.is_set())
            started_building.set()
            content1 = Path(docs_dir, "foo.docs").read_text()
            content2 = Path(extra_dir, "foo.extra").read_text()
            Path(site_dir, "foo.site").write_text(content1 + content2)

        with testing_server(site_dir, rebuild) as server:
            server.watch(docs_dir)
            server.watch(extra_dir)
            time.sleep(0.01)

            _, output = do_request(server, "GET /foo.site")
            Path(docs_dir, "foo.docs").write_text("docs2")
            Path(extra_dir, "foo.extra").write_text("extra2")
            self.assertTrue(started_building.wait(timeout=10))

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "docs2extra2")

    @tempdir({"foo.docs": "a"})
    @tempdir({"foo.site": "original"})
    def test_change_is_detected_while_building(self, site_dir, docs_dir):
        before_finished_building = threading.Barrier(2)
        can_finish_building = threading.Event()

        def rebuild():
            content = Path(docs_dir, "foo.docs").read_text()
            Path(site_dir, "foo.site").write_text(content * 5)
            before_finished_building.wait(timeout=10)
            self.assertTrue(can_finish_building.wait(timeout=10))

        with testing_server(site_dir, rebuild) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            Path(docs_dir, "foo.docs").write_text("b")
            before_finished_building.wait(timeout=10)
            Path(docs_dir, "foo.docs").write_text("c")
            can_finish_building.set()

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "bbbbb")

            before_finished_building.wait(timeout=10)

            _, output = do_request(server, "GET /foo.site")
            self.assertEqual(output, "ccccc")

    @tempdir({"foo.docs": "a"})
    @tempdir({"foo.site": "original"})
    def test_recovers_from_build_error(self, site_dir, docs_dir):
        started_building = threading.Event()
        build_count = 0

        def rebuild():
            started_building.set()
            nonlocal build_count
            build_count += 1
            if build_count == 1:
                raise ValueError("oh no")
            else:
                content = Path(docs_dir, "foo.docs").read_text()
                Path(site_dir, "foo.site").write_text(content * 5)

        with testing_server(site_dir, rebuild) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            err = io.StringIO()
            with (
                contextlib.redirect_stderr(err),
                self.assertLogs("mkdocs.livereload") as cm,
            ):
                Path(docs_dir, "foo.docs").write_text("b")
                started_building.wait(timeout=10)

                Path(docs_dir, "foo.docs").write_text("c")

                _, output = do_request(server, "GET /foo.site")

            self.assertIn("ValueError: oh no", err.getvalue())
            self.assertRegex(
                "\n".join(cm.output),
                r".*Detected file changes\n"
                r".*An error happened during the rebuild.*\n"
                r".*Detected file changes\n",
            )
            self.assertEqual(output, "ccccc")

    @tempdir(
        {
            "normal.html": "<html><body>hello</body></html>",
            "no_body.html": "<p>hi",
            "empty.html": "",
            "multi_body.html": "<body>foo</body><body>bar</body>",
        }
    )
    def test_serves_modified_html(self, site_dir):
        with testing_server(site_dir) as server:
            server.watch(site_dir)

            headers, output = do_request(server, "GET /normal.html")
            self.assertRegex(
                output, rf"^<html><body>hello{SCRIPT_REGEX}</body></html>$"
            )
            self.assertEqual(headers.get("content-type"), "text/html")
            self.assertEqual(headers.get("content-length"), str(len(output)))

            _, output = do_request(server, "GET /no_body.html")
            self.assertRegex(output, rf"^<p>hi{SCRIPT_REGEX}$")

            headers, output = do_request(server, "GET /empty.html")
            self.assertRegex(output, rf"^{SCRIPT_REGEX}$")
            self.assertEqual(headers.get("content-length"), str(len(output)))

            _, output = do_request(server, "GET /multi_body.html")
            self.assertRegex(
                output, rf"^<body>foo</body><body>bar{SCRIPT_REGEX}</body>$"
            )

    @tempdir({"index.html": "<body>aaa</body>", "foo/index.html": "<body>bbb</body>"})
    def test_serves_directory_index(self, site_dir):
        with testing_server(site_dir) as server:
            headers, output = do_request(server, "GET /")
            self.assertRegex(output, r"^<body>aaa</body>$")
            self.assertEqual(headers["_status"], "200 OK")
            self.assertEqual(headers.get("content-type"), "text/html")
            self.assertEqual(headers.get("content-length"), str(len(output)))

            for path in "/foo/", "/foo/index.html":
                _, output = do_request(server, f"GET {path}")
                self.assertRegex(output, r"^<body>bbb</body>$")

            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /foo/index.html/")
            self.assertEqual(headers["_status"], "404 Not Found")

    @tempdir(
        {
            "foo/bar/index.html": "<body>aaa</body>",
            "foo/測試/index.html": "<body>bbb</body>",
        }
    )
    def test_redirects_to_directory(self, site_dir):
        with testing_server(site_dir, mount_path="/sub") as server:
            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /sub/foo/bar")
            self.assertEqual(headers["_status"], "302 Found")
            self.assertEqual(headers.get("location"), "/sub/foo/bar/")

            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /sub/foo/測試")
            self.assertEqual(headers["_status"], "302 Found")
            self.assertEqual(headers.get("location"), "/sub/foo/%E6%B8%AC%E8%A9%A6/")

            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /sub/foo/%E6%B8%AC%E8%A9%A6")
            self.assertEqual(headers["_status"], "302 Found")
            self.assertEqual(headers.get("location"), "/sub/foo/%E6%B8%AC%E8%A9%A6/")

    @tempdir({"я.html": "<body>aaa</body>", "测试2/index.html": "<body>bbb</body>"})
    def test_serves_with_unicode_characters(self, site_dir):
        with testing_server(site_dir) as server:
            _, output = do_request(server, "GET /я.html")
            self.assertRegex(output, r"^<body>aaa</body>$")
            _, output = do_request(server, "GET /%D1%8F.html")
            self.assertRegex(output, r"^<body>aaa</body>$")

            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /%D1.html")
            self.assertEqual(headers["_status"], "404 Not Found")

            _, output = do_request(server, "GET /测试2/")
            self.assertRegex(output, r"^<body>bbb</body>$")
            _, output = do_request(server, "GET /%E6%B5%8B%E8%AF%952/index.html")
            self.assertRegex(output, r"^<body>bbb</body>$")

    @tempdir()
    def test_serves_polling_instantly(self, site_dir):
        with testing_server(site_dir) as server:
            _, output = do_request(server, "GET /livereload/0/0")
            self.assertTrue(output.isdigit())

    @tempdir()
    def test_serves_polling_with_mount_path(self, site_dir):
        with testing_server(site_dir, mount_path="/test/f*o") as server:
            _, output = do_request(server, "GET /livereload/0/0")
            self.assertTrue(output.isdigit())

    @tempdir()
    @tempdir()
    def test_serves_polling_after_event(self, site_dir, docs_dir):
        with testing_server(site_dir) as server:
            initial_epoch = server._visible_epoch

            server.watch(docs_dir)
            time.sleep(0.01)

            Path(docs_dir, "foo.docs").write_text("b")

            _, output = do_request(server, f"GET /livereload/{initial_epoch}/0")

            self.assertNotEqual(server._visible_epoch, initial_epoch)
            self.assertEqual(output, str(server._visible_epoch))

    @tempdir()
    def test_serves_polling_with_timeout(self, site_dir):
        with testing_server(site_dir) as server:
            server.poll_response_timeout = 0.2
            initial_epoch = server._visible_epoch

            start_time = time.monotonic()
            _, output = do_request(server, f"GET /livereload/{initial_epoch}/0")
            self.assertGreaterEqual(time.monotonic(), start_time + 0.2)
            self.assertEqual(output, str(initial_epoch))

    @tempdir()
    def test_error_handler(self, site_dir):
        with testing_server(site_dir) as server:
            server.error_handler = lambda code: b"[%d]" % code
            with self.assertLogs("mkdocs.livereload") as cm:
                headers, output = do_request(server, "GET /missing")

            self.assertEqual(headers["_status"], "404 Not Found")
            self.assertEqual(output, "[404]")
            self.assertRegex(
                "\n".join(cm.output),
                r'^WARNING:mkdocs.livereload:.*"GET /missing HTTP/1.1" code 404',
            )

    @tempdir()
    def test_bad_error_handler(self, site_dir):
        with testing_server(site_dir) as server:
            server.error_handler = lambda code: 0 / 0
            with self.assertLogs("mkdocs.livereload") as cm:
                headers, output = do_request(server, "GET /missing")

            self.assertEqual(headers["_status"], "404 Not Found")
            self.assertIn("404", output)
            self.assertRegex(
                "\n".join(cm.output),
                r"Failed to render an error message[\s\S]+/missing.+code 404",
            )

    @tempdir(
        {
            "test.html": "<!DOCTYPE html>\nhi",
            "test.xml": '<?xml version="1.0" encoding="UTF-8"?>\n<foo></foo>',
            "test.css": "div { color: red; }",
            "test.js": "use strict;",
            "test.json": '{"a": "b"}',
        }
    )
    def test_mime_types(self, site_dir):
        with testing_server(site_dir) as server:
            headers, _ = do_request(server, "GET /test.html")
            self.assertEqual(headers.get("content-type"), "text/html")

            headers, _ = do_request(server, "GET /test.xml")
            self.assertIn(headers.get("content-type"), ["text/xml", "application/xml"])

            headers, _ = do_request(server, "GET /test.css")
            self.assertEqual(headers.get("content-type"), "text/css")

            headers, _ = do_request(server, "GET /test.js")
            self.assertEqual(headers.get("content-type"), "application/javascript")

            headers, _ = do_request(server, "GET /test.json")
            self.assertEqual(headers.get("content-type"), "application/json")

    @tempdir({"index.html": "<body>aaa</body>", "sub/sub.html": "<body>bbb</body>"})
    def test_serves_from_mount_path(self, site_dir):
        with testing_server(site_dir, mount_path="/sub") as server:
            headers, output = do_request(server, "GET /sub/")
            self.assertRegex(output, r"^<body>aaa</body>$")
            self.assertEqual(headers.get("content-type"), "text/html")

            _, output = do_request(server, "GET /sub/sub/sub.html")
            self.assertRegex(output, r"^<body>bbb</body>$")

            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /sub/sub.html")
            self.assertEqual(headers["_status"], "404 Not Found")

    @tempdir()
    def test_redirects_to_mount_path(self, site_dir):
        with testing_server(site_dir, mount_path="/mount/path") as server:
            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /")
            self.assertEqual(headers["_status"], "302 Found")
            self.assertEqual(headers.get("location"), "/mount/path/")

    @tempdir()
    def test_redirects_to_unicode_mount_path(self, site_dir):
        with testing_server(site_dir, mount_path="/mount/測試") as server:
            with self.assertLogs("mkdocs.livereload"):
                headers, _ = do_request(server, "GET /")
            self.assertEqual(headers["_status"], "302 Found")
            self.assertEqual(headers.get("location"), "/mount/%E6%B8%AC%E8%A9%A6/")

    @tempdir({"mkdocs.yml": "original", "mkdocs2.yml": "original"}, prefix="tmp_dir")
    @tempdir(prefix="origin_dir")
    @tempdir({"subdir/foo.md": "original"}, prefix="dest_docs_dir")
    def test_watches_direct_symlinks(self, dest_docs_dir, origin_dir, tmp_dir):
        try:
            Path(origin_dir, "docs").symlink_to(dest_docs_dir, target_is_directory=True)
            Path(origin_dir, "mkdocs.yml").symlink_to(Path(tmp_dir, "mkdocs.yml"))
        except NotImplementedError:  # PyPy on Windows
            self.skipTest("Creating symlinks not supported")

        started_building = threading.Event()

        def wait_for_build():
            result = started_building.wait(timeout=10)
            started_building.clear()
            with self.assertLogs("mkdocs.livereload"):
                do_request(server, "GET /")
            return result

        with testing_server(tmp_dir, started_building.set) as server:
            server.watch(Path(origin_dir, "docs"))
            server.watch(Path(origin_dir, "mkdocs.yml"))
            time.sleep(0.01)

            Path(origin_dir, "unrelated.md").write_text("foo")
            self.assertFalse(started_building.wait(timeout=0.5))

            Path(tmp_dir, "mkdocs.yml").write_text("edited")
            self.assertTrue(wait_for_build())

            Path(dest_docs_dir, "subdir", "foo.md").write_text("edited")
            self.assertTrue(wait_for_build())

    @tempdir(
        ["file_dest_1.md", "file_dest_2.md", "file_dest_unused.md"], prefix="tmp_dir"
    )
    @tempdir(["file_under.md"], prefix="dir_to_link_to")
    @tempdir()
    def test_watches_through_symlinks(self, docs_dir, dir_to_link_to, tmp_dir):
        try:
            Path(docs_dir, "link1.md").symlink_to(Path(tmp_dir, "file_dest_1.md"))
            Path(docs_dir, "linked_dir").symlink_to(
                dir_to_link_to, target_is_directory=True
            )

            Path(dir_to_link_to, "sublink.md").symlink_to(
                Path(tmp_dir, "file_dest_2.md")
            )
        except NotImplementedError:  # PyPy on Windows
            self.skipTest("Creating symlinks not supported")

        started_building = threading.Event()

        def wait_for_build():
            result = started_building.wait(timeout=10)
            started_building.clear()
            with self.assertLogs("mkdocs.livereload"):
                do_request(server, "GET /")
            return result

        with testing_server(docs_dir, started_building.set) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            Path(tmp_dir, "file_dest_1.md").write_text("edited")
            self.assertTrue(wait_for_build())

            Path(dir_to_link_to, "file_under.md").write_text("edited")
            self.assertTrue(wait_for_build())

            Path(tmp_dir, "file_dest_2.md").write_text("edited")
            self.assertTrue(wait_for_build())

            Path(docs_dir, "link1.md").unlink()
            self.assertTrue(wait_for_build())

            Path(tmp_dir, "file_dest_unused.md").write_text("edited")
            self.assertFalse(started_building.wait(timeout=0.5))

    @tempdir(prefix="site_dir")
    @tempdir(["docs/unused.md", "README.md"], prefix="origin_dir")
    def test_watches_through_relative_symlinks(self, origin_dir, site_dir):
        docs_dir = Path(origin_dir, "docs")
        with change_dir(docs_dir):
            try:
                Path(docs_dir, "README.md").symlink_to(Path("..", "README.md"))
            except NotImplementedError:  # PyPy on Windows
                self.skipTest("Creating symlinks not supported")

        started_building = threading.Event()

        with testing_server(docs_dir, started_building.set) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            Path(origin_dir, "README.md").write_text("edited")
            self.assertTrue(started_building.wait(timeout=10))

    @tempdir({"foo.md": "original"})
    def test_ignores_dotfile_changes(self, docs_dir):
        """Hidden files (starting with '.') should not trigger rebuild."""
        started_building = threading.Event()
        with testing_server(docs_dir, started_building.set) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            # Vim swap file
            Path(docs_dir, ".foo.md.swp").write_text("swap")
            self.assertFalse(started_building.wait(timeout=0.5))

            # Generic dotfile
            Path(docs_dir, ".hidden").write_text("hidden")
            self.assertFalse(started_building.wait(timeout=0.5))

    @tempdir({"foo.md": "original"})
    def test_ignores_tilde_backup_files(self, docs_dir):
        """Editor backup files (ending with '~') should not trigger rebuild."""
        started_building = threading.Event()
        with testing_server(docs_dir, started_building.set) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            # Backup file created by editors
            Path(docs_dir, "foo.md~").write_text("backup")
            self.assertFalse(started_building.wait(timeout=0.5))

    @tempdir({"foo.md": "original"})
    def test_ignores_emacs_autosave_files(self, docs_dir):
        """Emacs auto-save files (#*#) should not trigger rebuild."""
        started_building = threading.Event()
        with testing_server(docs_dir, started_building.set) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            # Emacs auto-save pattern
            Path(docs_dir, "#foo.md#").write_text("autosave")
            self.assertFalse(started_building.wait(timeout=0.5))

    @tempdir()
    def test_watch_with_broken_symlinks(self, docs_dir):
        Path(docs_dir, "subdir").mkdir()

        try:
            if sys.platform != "win32":
                Path(docs_dir, "subdir", "circular").symlink_to(Path(docs_dir))

            Path(docs_dir, "broken_1").symlink_to(Path(docs_dir, "oh no"))
            Path(docs_dir, "broken_2").symlink_to(
                Path(docs_dir, "oh no"), target_is_directory=True
            )
            Path(docs_dir, "broken_3").symlink_to(Path(docs_dir, "broken_2"))
        except NotImplementedError:  # PyPy on Windows
            self.skipTest("Creating symlinks not supported")

        started_building = threading.Event()
        with testing_server(docs_dir, started_building.set) as server:
            server.watch(docs_dir)
            time.sleep(0.01)

            Path(docs_dir, "subdir", "test").write_text("test")
            self.assertTrue(started_building.wait(timeout=10))


class _ScriptedCondition:
    """A stand-in for the rebuild condition that replays the results of `wait()`."""

    def __init__(self, waits):
        self._waits = list(waits)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return None

    def wait_for(self, predicate, timeout=None):
        return predicate()

    def wait(self, timeout=None):
        return self._waits.pop(0)

    def notify_all(self):
        pass


def _make_server(root, builder=lambda: None, host="localhost", port=8000):
    """Create the server without binding or listening on a socket."""
    with mock.patch("socket.socket"):
        return LiveReloadServer(builder, host=host, port=port, root=root)


class ServerTests(unittest.TestCase):
    @tempdir()
    def test_address_family(self, site_dir):
        self.assertEqual(
            _make_server(site_dir, host="::1").address_family, socket.AF_INET6
        )
        self.assertEqual(
            _make_server(site_dir, host="127.0.0.1").address_family, socket.AF_INET
        )
        # Host names are not IP addresses; the default (IPv4) family is kept.
        self.assertEqual(
            _make_server(site_dir, host="localhost").address_family, socket.AF_INET
        )

    @tempdir()
    def test_url(self, site_dir):
        with mock.patch("socket.socket"):
            server = LiveReloadServer(
                lambda: None,
                host="127.0.0.1",
                port=8001,
                root=site_dir,
                mount_path="sub",
            )
        self.assertEqual(server.url, "http://127.0.0.1:8001/sub/")
        self.assertEqual(server.mount_path, "/sub/")

    @tempdir()
    def test_watch_rejects_custom_function(self, site_dir):
        server = _make_server(site_dir)
        with self.assertRaisesRegex(
            TypeError, "Plugins can no longer pass a 'func' parameter to watch()"
        ):
            server.watch(site_dir, lambda: None)
        # Passing the server's own builder is still accepted.
        server.watch(site_dir, server.builder)
        server.unwatch(site_dir)

    @tempdir()
    def test_serve_and_open_in_browser(self, site_dir):
        server = _make_server(site_dir)
        server.watch(site_dir)
        with (
            mock.patch.object(server, "server_bind") as server_bind,
            mock.patch.object(server, "server_activate") as server_activate,
            mock.patch.object(server, "observer") as observer,
            mock.patch.object(server, "serve_thread") as serve_thread,
            mock.patch.object(server, "_build_loop") as build_loop,
            mock.patch("webbrowser.open") as open_browser,
            self.assertLogs("mkdocs.livereload") as cm,
        ):
            server.serve(open_in_browser=True)

        server_bind.assert_called_once_with()
        server_activate.assert_called_once_with()
        observer.start.assert_called_once_with()
        serve_thread.start.assert_called_once_with()
        build_loop.assert_called_once_with()
        open_browser.assert_called_once_with("http://localhost:8000/")
        self.assertRegex(
            "\n".join(cm.output),
            r"^INFO:mkdocs.livereload:.*Watching paths for changes: '.+'\n"
            r"INFO:mkdocs.livereload:.*Serving on http://localhost:8000/ "
            r"and opening it in a browser$",
        )

    @tempdir()
    def test_serve_without_watching(self, site_dir):
        server = _make_server(site_dir)
        with (
            mock.patch.object(server, "server_bind"),
            mock.patch.object(server, "server_activate"),
            mock.patch.object(server, "observer") as observer,
            mock.patch.object(server, "serve_thread") as serve_thread,
            mock.patch.object(server, "_build_loop"),
            mock.patch("webbrowser.open") as open_browser,
            self.assertLogs("mkdocs.livereload") as cm,
        ):
            server.serve()

        observer.start.assert_not_called()
        serve_thread.start.assert_called_once_with()
        open_browser.assert_not_called()
        self.assertRegex(
            "\n".join(cm.output),
            r"^INFO:mkdocs.livereload:.*Serving on http://localhost:8000/$",
        )

    @tempdir()
    def test_shutdown_waits_for_running_server(self, site_dir):
        server = _make_server(site_dir)
        with (
            mock.patch("socketserver.BaseServer.shutdown") as base_shutdown,
            mock.patch.object(server, "server_close") as server_close,
            mock.patch.object(server, "observer") as observer,
            mock.patch.object(server, "serve_thread") as serve_thread,
        ):
            serve_thread.is_alive.return_value = True
            server.shutdown(wait=True)

        self.assertTrue(server._shutdown)
        observer.stop.assert_called_once_with()
        base_shutdown.assert_called_once_with()
        server_close.assert_called_once_with()
        serve_thread.join.assert_called_once_with()
        observer.join.assert_called_once_with()

    @tempdir()
    def test_build_loop_waits_for_changes_to_stop(self, site_dir):
        builds = []

        def builder():
            builds.append(server._wanted_epoch)
            server._shutdown = True

        server = _make_server(site_dir, builder)
        # Another change arrives during the first debounce wait, then things settle.
        server._rebuild_cond = _ScriptedCondition(waits=[True, False])
        server._want_rebuild = True
        initial_epoch = server._visible_epoch

        with self.assertLogs("mkdocs.livereload", level="DEBUG") as cm:
            server._build_loop()

        self.assertEqual(len(builds), 1)
        self.assertFalse(server._want_rebuild)
        self.assertEqual(server._visible_epoch, builds[0])
        self.assertGreaterEqual(server._visible_epoch, initial_epoch)
        self.assertRegex(
            "\n".join(cm.output),
            r"^INFO:mkdocs.livereload:.*Detected file changes\n"
            r"DEBUG:mkdocs.livereload:.*Waiting for file changes to stop happening\n"
            r"INFO:mkdocs.livereload:.*Reloading browsers$",
        )

    @tempdir()
    def test_build_loop_reports_abort(self, site_dir):
        def builder():
            server._shutdown = True
            # Raised by a strict build with warnings; it is also a SystemExit.
            raise Abort("Aborted with 1 warnings in strict mode!")

        server = _make_server(site_dir, builder)
        server._rebuild_cond = _ScriptedCondition(waits=[False])
        server._want_rebuild = True
        initial_epoch = server._visible_epoch

        err = io.StringIO()
        with (
            contextlib.redirect_stderr(err),
            self.assertLogs("mkdocs.livereload") as cm,
        ):
            server._build_loop()

        # The message is shown without a traceback and the old site stays visible.
        self.assertEqual(err.getvalue(), "Aborted with 1 warnings in strict mode!\n")
        self.assertEqual(server._visible_epoch, initial_epoch)
        self.assertRegex(
            "\n".join(cm.output),
            r"ERROR:mkdocs.livereload:.*An error happened during the rebuild",
        )

    @tempdir({"index.html": "<body>hi</body>"})
    def test_internal_server_error(self, site_dir):
        with testing_server(site_dir) as server:
            with (
                mock.patch.object(
                    server, "_serve_request", side_effect=ValueError("boom")
                ),
                self.assertLogs("mkdocs.livereload") as cm,
            ):
                headers, output = do_request(server, "GET /index.html")

        self.assertEqual(headers["_status"], "500 Internal Server Error")
        self.assertEqual(output, "500 Internal Server Error")
        log_output = "\n".join(cm.output)
        self.assertIn("ERROR:mkdocs.livereload:", log_output)
        self.assertIn("ValueError: boom", log_output)
        self.assertRegex(log_output, r'"GET /index.html HTTP/1.1" code 500')

    @tempdir({"index.html": "<body>hi</body>"})
    def test_outside_of_mount_path_not_found(self, site_dir):
        with testing_server(site_dir, mount_path="/sub/") as server:
            with self.assertLogs("mkdocs.livereload") as cm:
                headers, output = do_request(server, "GET /index.html")

        self.assertEqual(headers["_status"], "404 Not Found")
        self.assertEqual(output, "404 Not Found")
        self.assertRegex("\n".join(cm.output), r'"GET /index.html HTTP/1.1" code 404')

    @tempdir({"archive.tar.gz": "gzip data", "data.unknownext": "data"})
    def test_more_mime_types(self, site_dir):
        with testing_server(site_dir) as server:
            headers, _ = do_request(server, "GET /archive.tar.gz")
            self.assertEqual(headers.get("content-type"), "application/gzip")

            headers, _ = do_request(server, "GET /data.unknownext")
            self.assertEqual(headers.get("content-type"), "application/octet-stream")

    @tempdir()
    def test_request_line_too_long(self, site_dir):
        with testing_server(site_dir) as server:
            with self.assertLogs("mkdocs.livereload", level="DEBUG") as cm:
                headers, _ = do_request(server, "GET /" + "a" * 70000)

        self.assertTrue(headers["_status"].startswith("414 "), headers["_status"])
        # Errors reported by the HTTP handler itself are logged at DEBUG level.
        self.assertRegex(
            "\n".join(cm.output), r"DEBUG:mkdocs.livereload:.*code 414, message"
        )

    @tempdir()
    def test_try_relativize_path(self, tmp_dir):
        tmp_dir = os.path.realpath(tmp_dir)
        os.mkdir(os.path.join(tmp_dir, "project"))
        with change_dir(os.path.join(tmp_dir, "project")):
            self.assertEqual(
                _try_relativize_path(os.path.join(tmp_dir, "project", "docs")), "docs"
            )
            # Paths outside of the current directory are kept as they are.
            outside = os.path.join(tmp_dir, "elsewhere")
            self.assertEqual(_try_relativize_path(outside), outside)
