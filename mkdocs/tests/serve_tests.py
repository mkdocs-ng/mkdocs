#!/usr/bin/env python

import contextlib
import signal
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from mkdocs.commands import serve
from mkdocs.tests.base import tempdir


class ServeTests(unittest.TestCase):
    @tempdir()
    def test_sigterm_cleans_temporary_site_dir(self, temp_dir):
        site_dir = Path(temp_dir, "site")
        site_dir.mkdir()

        config = SimpleNamespace(
            config_file_path=None,
            _inherited_config_files=(),
            dev_addr=("127.0.0.1", 8000),
            docs_dir=str(Path(temp_dir, "docs")),
            plugins=mock.Mock(),
            site_url=None,
            theme=SimpleNamespace(dirs=[]),
            watch=[],
        )
        config.plugins.on_serve.side_effect = lambda server, **kwargs: server

        signal_handlers = {signal.SIGTERM: signal.SIG_DFL}

        def signal_side_effect(signum, handler):
            previous_handler = signal_handlers[signum]
            signal_handlers[signum] = handler
            return previous_handler

        def serve_side_effect(**kwargs):
            signal_handlers[signal.SIGTERM](signal.SIGTERM, None)

        server = mock.Mock()
        server.serve.side_effect = serve_side_effect

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.tempfile.mkdtemp", return_value=site_dir
                )
            )
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            mock_signal = stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.signal.signal",
                    side_effect=signal_side_effect,
                )
            )

            serve.serve()

        self.assertFalse(site_dir.exists())
        server.shutdown.assert_called_once_with()
        config.plugins.on_shutdown.assert_called_once_with()
        self.assertEqual(signal_handlers[signal.SIGTERM], signal.SIG_DFL)
        mock_signal.assert_has_calls(
            [
                mock.call(signal.SIGTERM, mock.ANY),
                mock.call(signal.SIGTERM, signal.SIG_DFL),
            ]
        )

    @tempdir()
    def test_watches_inherited_config_files(self, temp_dir):
        config = SimpleNamespace(
            config_file_path=str(Path(temp_dir, "mkdocs.yml")),
            _inherited_config_files=[
                str(Path(temp_dir, "config", "base.yml")),
                str(Path(temp_dir, "config", "plugins.yml")),
            ],
            dev_addr=("127.0.0.1", 8000),
            docs_dir=str(Path(temp_dir, "docs")),
            plugins=mock.Mock(),
            site_url=None,
            theme=SimpleNamespace(dirs=[]),
            watch=[],
        )
        config.plugins.on_serve.side_effect = lambda server, **kwargs: server
        server = mock.Mock()

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            serve.serve()

        self.assertEqual(
            server.watch.call_args_list,
            [
                mock.call(config.docs_dir),
                mock.call(config.config_file_path),
                mock.call(config._inherited_config_files[0]),
                mock.call(config._inherited_config_files[1]),
            ],
        )

    @staticmethod
    def make_config(temp_dir, **kwargs):
        config = SimpleNamespace(
            config_file_path=None,
            _inherited_config_files=(),
            dev_addr=("127.0.0.1", 8000),
            docs_dir=str(Path(temp_dir, "docs")),
            plugins=mock.Mock(),
            site_url=None,
            theme=SimpleNamespace(dirs=[]),
            watch=[],
        )
        config.plugins.on_serve.side_effect = lambda server, **kwargs: server
        for key, value in kwargs.items():
            setattr(config, key, value)
        return config

    @tempdir()
    def test_rebuild_loads_fresh_config(self, temp_dir):
        config = self.make_config(temp_dir)
        fresh_config = self.make_config(temp_dir)
        server = mock.Mock()
        server.bind.return_value = 8000

        with contextlib.ExitStack() as stack:
            mock_load_config = stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.load_config",
                    side_effect=[config, fresh_config],
                )
            )
            mock_build = stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            mock_server_cls = stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            # A file change makes the server call the builder without a config.
            server.serve.side_effect = lambda **kwargs: (
                mock_server_cls.call_args.kwargs["builder"]()
            )
            serve.serve(build_type="dirty")

        self.assertEqual(mock_load_config.call_count, 2)
        serve_url = "http://127.0.0.1:8000/"
        self.assertEqual(fresh_config.site_url, serve_url)
        self.assertEqual(
            mock_build.call_args_list,
            [
                mock.call(config, serve_url=serve_url, dirty=True),
                mock.call(fresh_config, serve_url=serve_url, dirty=True),
            ],
        )
        config.plugins.on_startup.assert_called_once_with(command="serve", dirty=True)

    @tempdir()
    def test_rebuilds_share_a_render_cache(self, temp_dir):
        from mkdocs.structure import render_cache

        config = self.make_config(temp_dir)
        server = mock.Mock()
        seen = []

        def fake_build(*args, **kwargs):
            seen.append(render_cache.active)

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.load_config",
                    side_effect=[config, self.make_config(temp_dir)],
                )
            )
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.build", side_effect=fake_build)
            )
            mock_server_cls = stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            server.serve.side_effect = lambda **kwargs: (
                mock_server_cls.call_args.kwargs["builder"]()
            )
            serve.serve()

        self.assertEqual(len(seen), 2)
        self.assertIsInstance(seen[0], render_cache.RenderCache)
        self.assertIs(seen[0], seen[1])
        self.assertIsNone(render_cache.active)

    @tempdir()
    def test_clean_build_type_uses_no_caches(self, temp_dir):
        from mkdocs.structure import render_cache
        from mkdocs.utils import output

        config = self.make_config(temp_dir)
        server = mock.Mock()
        seen = []

        def fake_build(*args, **kwargs):
            seen.append((render_cache.active, output.active))

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.load_config",
                    side_effect=[config, self.make_config(temp_dir)],
                )
            )
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.build", side_effect=fake_build)
            )
            mock_server_cls = stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            server.serve.side_effect = lambda **kwargs: (
                mock_server_cls.call_args.kwargs["builder"]()
            )
            serve.serve(build_type="clean")

        self.assertEqual(seen, [(None, None), (None, None)])

    @tempdir()
    def test_error_handler_serves_built_error_pages(self, temp_dir):
        site_dir = Path(temp_dir, "site")
        site_dir.mkdir()
        config = self.make_config(temp_dir)
        server = mock.Mock()
        responses = {}

        def serve_side_effect(**kwargs):
            Path(site_dir, "404.html").write_bytes(b"<h1>Not here</h1>")
            for code in (404, 500, 403):
                responses[code] = server.error_handler(code)

        server.serve.side_effect = serve_side_effect

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.tempfile.mkdtemp", return_value=site_dir
                )
            )
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            serve.serve(build_type="clean")

        # A built 404 page is used; missing pages and other codes fall back to the default.
        self.assertEqual(responses, {404: b"<h1>Not here</h1>", 500: None, 403: None})
        config.plugins.on_startup.assert_called_once_with(command="build", dirty=False)
        self.assertFalse(site_dir.exists())

    @tempdir()
    def test_watches_theme_and_extra_paths(self, temp_dir):
        theme_dirs = [str(Path(temp_dir, "theme1")), str(Path(temp_dir, "theme2"))]
        config = self.make_config(
            temp_dir, theme=SimpleNamespace(dirs=theme_dirs), watch=["from_config"]
        )
        server = mock.Mock()

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            serve.serve(watch_theme=True, watch=["from_cli"])

        self.assertEqual(
            server.watch.call_args_list,
            [
                mock.call(config.docs_dir),
                mock.call(theme_dirs[0]),
                mock.call(theme_dirs[1]),
                mock.call("from_config"),
                mock.call("from_cli"),
            ],
        )

    @tempdir()
    def test_no_livereload_watches_nothing(self, temp_dir):
        config = self.make_config(temp_dir, watch=["from_config"])
        server = mock.Mock()

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            serve.serve(livereload=False, open_in_browser=True)

        server.watch.assert_not_called()
        config.plugins.on_serve.assert_not_called()
        server.serve.assert_called_once_with(open_in_browser=True)

    @tempdir()
    def test_sigterm_during_initial_build(self, temp_dir):
        site_dir = Path(temp_dir, "site")
        site_dir.mkdir()
        config = self.make_config(temp_dir)
        server = mock.Mock()

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.tempfile.mkdtemp", return_value=site_dir
                )
            )
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.build", side_effect=serve._ShutdownRequested
                )
            )
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            log_cm = stack.enter_context(self.assertLogs("mkdocs.commands.serve"))
            serve.serve()

        self.assertEqual(
            log_cm.output,
            [
                "INFO:mkdocs.commands.serve:Building documentation...",
                "INFO:mkdocs.commands.serve:Shutting down...",
            ],
        )
        server.serve.assert_not_called()
        config.plugins.on_shutdown.assert_called_once_with()
        self.assertFalse(site_dir.exists())

    def _serve_with_port(self, temp_dir, dev_addr, bound_port):
        config = self.make_config(temp_dir, dev_addr=dev_addr)
        server = mock.Mock()
        server.bind.return_value = bound_port

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            mock_build = stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            serve.serve()
        return config, server, mock_build

    @tempdir()
    def test_default_port_falls_back_to_next_ports(self, temp_dir):
        config, server, mock_build = self._serve_with_port(
            temp_dir, ("127.0.0.1", 8000), 8001
        )
        server.bind.assert_called_once_with(try_next_ports=serve._PORT_FALLBACKS)
        # The site is built for the port it is actually served on.
        self.assertEqual(config.site_url, "http://127.0.0.1:8001/")
        mock_build.assert_called_once_with(
            config, serve_url="http://127.0.0.1:8001/", dirty=False
        )

    @tempdir()
    def test_custom_port_does_not_fall_back(self, temp_dir):
        config, server, _ = self._serve_with_port(temp_dir, ("127.0.0.1", 9000), 9000)
        server.bind.assert_called_once_with(try_next_ports=0)
        self.assertEqual(config.site_url, "http://127.0.0.1:9000/")

    def _serve_logs(self, temp_dir, host, site_url):
        config = self.make_config(temp_dir, dev_addr=(host, 8000), site_url=site_url)
        server = mock.Mock()
        server.bind.return_value = 8000

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch("mkdocs.commands.serve.load_config", return_value=config)
            )
            stack.enter_context(mock.patch("mkdocs.commands.serve.build"))
            stack.enter_context(
                mock.patch(
                    "mkdocs.commands.serve.LiveReloadServer", return_value=server
                )
            )
            log_cm = stack.enter_context(self.assertLogs("mkdocs.commands.serve"))
            serve.serve()
        return [line for line in log_cm.output if "site_url" in line]

    @tempdir()
    def test_public_address_notes_site_url_is_replaced(self, temp_dir):
        lines = self._serve_logs(temp_dir, "0.0.0.0", "https://example.com/foo/")
        self.assertEqual(len(lines), 1)
        self.assertIn("http://0.0.0.0:8000/foo/", lines[0])
        self.assertIn("(https://example.com/foo/)", lines[0])
        self.assertIn("mkdocs build", lines[0])

    @tempdir()
    def test_no_site_url_note_on_loopback_or_without_site_url(self, temp_dir):
        for host, site_url in [
            ("127.0.0.1", "https://example.com/"),
            ("localhost", "https://example.com/"),
            ("::1", "https://example.com/"),
            ("0.0.0.0", None),
        ]:
            with self.subTest(host=host, site_url=site_url):
                self.assertEqual(self._serve_logs(temp_dir, host, site_url), [])


if __name__ == "__main__":
    unittest.main()
