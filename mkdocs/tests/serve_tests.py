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


if __name__ == "__main__":
    unittest.main()
