#!/usr/bin/env python

import io
import logging
import os
import unittest
import warnings
from unittest import mock

import click
from click.testing import CliRunner

from mkdocs import __main__ as cli
from mkdocs import utils
from mkdocs.tests.base import tempdir


class CLITests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_unset_default_source_values_restores_default_values(self):
        kwargs = {"build_type": "False", "strict": False, "use_directory_urls": False}
        ctx = mock.Mock()
        ctx.get_parameter_source.return_value = cli.click.core.ParameterSource.DEFAULT

        with mock.patch("mkdocs.__main__.click.get_current_context", return_value=ctx):
            cli.unset_default_source_values(
                kwargs, "build_type", "strict", "use_directory_urls"
            )

        self.assertIsNone(kwargs["build_type"])
        self.assertIsNone(kwargs["strict"])
        self.assertIsNone(kwargs["use_directory_urls"])

    def test_unset_default_source_values_preserves_commandline_values(self):
        kwargs = {"strict": False, "use_directory_urls": False}
        ctx = mock.Mock()
        ctx.get_parameter_source.return_value = (
            cli.click.core.ParameterSource.COMMANDLINE
        )

        with mock.patch("mkdocs.__main__.click.get_current_context", return_value=ctx):
            cli.unset_default_source_values(kwargs, "strict", "use_directory_urls")

        self.assertFalse(kwargs["strict"])
        self.assertFalse(kwargs["use_directory_urls"])

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_default(self, mock_serve):
        result = self.runner.invoke(cli.cli, ["serve"], catch_exceptions=False)

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_config_file(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--config-file", "mkdocs.yml"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_serve.call_count, 1)
        args, kwargs = mock_serve.call_args
        self.assertTrue("config_file" in kwargs)
        self.assertIsInstance(kwargs["config_file"], io.BufferedReader)
        self.assertEqual(kwargs["config_file"].name, "mkdocs.yml")

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_dev_addr(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--dev-addr", "0.0.0.0:80"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr="0.0.0.0:80",
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_strict(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--strict"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=True,
            theme=None,
            use_directory_urls=None,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_theme(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--theme", "readthedocs"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=None,
            theme="readthedocs",
            use_directory_urls=None,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_use_directory_urls(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--use-directory-urls"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=True,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_no_directory_urls(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--no-directory-urls"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=False,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_livereload(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--livereload"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_no_livereload(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--no-livereload"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=False,
            build_type=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_dirtyreload(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--dirty"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type="dirty",
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            watch_theme=False,
            watch=[],
        )

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_serve_watch_theme(self, mock_serve):
        result = self.runner.invoke(
            cli.cli, ["serve", "--watch-theme"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(
            dev_addr=None,
            open_in_browser=False,
            livereload=True,
            build_type=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            watch_theme=True,
            watch=[],
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_defaults(self, mock_build, mock_load_config):
        result = self.runner.invoke(cli.cli, ["build"], catch_exceptions=False)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        args, kwargs = mock_build.call_args
        self.assertTrue("dirty" in kwargs)
        self.assertFalse(kwargs["dirty"])
        mock_load_config.assert_called_once_with(
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            site_dir=None,
        )
        for log_name in "mkdocs", "mkdocs.structure.pages", "mkdocs.plugins.foo":
            self.assertEqual(
                logging.getLogger(log_name).getEffectiveLevel(), logging.INFO
            )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_clean(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--clean"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        args, kwargs = mock_build.call_args
        self.assertTrue("dirty" in kwargs)
        self.assertFalse(kwargs["dirty"])

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_dirty(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--dirty"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        args, kwargs = mock_build.call_args
        self.assertTrue("dirty" in kwargs)
        self.assertTrue(kwargs["dirty"])

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_config_file(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--config-file", "mkdocs.yml"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        self.assertEqual(mock_load_config.call_count, 1)
        args, kwargs = mock_load_config.call_args
        self.assertTrue("config_file" in kwargs)
        self.assertIsInstance(kwargs["config_file"], io.BufferedReader)
        self.assertEqual(kwargs["config_file"].name, "mkdocs.yml")

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_strict(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--strict"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            config_file=None,
            strict=True,
            theme=None,
            use_directory_urls=None,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_theme(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--theme", "readthedocs"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            config_file=None,
            strict=None,
            theme="readthedocs",
            use_directory_urls=None,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_use_directory_urls(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--use-directory-urls"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=True,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_no_directory_urls(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--no-directory-urls"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=False,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_site_dir(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--site-dir", "custom"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            site_dir="custom",
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_verbose(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--verbose"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        for log_name in "mkdocs", "mkdocs.structure.pages", "mkdocs.plugins.foo":
            self.assertEqual(
                logging.getLogger(log_name).getEffectiveLevel(), logging.DEBUG
            )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    def test_build_quiet(self, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["build", "--quiet"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_build.call_count, 1)
        # Warnings are still emitted (so `strict` can count them), just not printed.
        for log_name in "mkdocs", "mkdocs.structure.pages", "mkdocs.plugins.foo":
            self.assertLessEqual(
                logging.getLogger(log_name).getEffectiveLevel(), logging.WARNING
            )
        stream = [
            h
            for h in logging.getLogger("mkdocs").handlers
            if h.name == "MkDocsStreamHandler"
        ][-1]
        self.assertEqual(stream.level, logging.ERROR)

    def test_build_quiet_strict_aborts_on_warnings(self):
        with self.runner.isolated_filesystem():
            os.mkdir("docs")
            with open("docs/index.md", "w") as f:
                f.write("# Home\n\n[missing](missing.md)\n")
            with open("mkdocs.yml", "w") as f:
                f.write("site_name: Test\n")

            result = self.runner.invoke(cli.cli, ["build", "--quiet", "--strict"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Aborted with 1 warnings in strict mode!", result.output)
        self.assertNotIn("missing.md", result.output)

    @mock.patch("mkdocs.commands.new.new", autospec=True)
    def test_new(self, mock_new):
        result = self.runner.invoke(cli.cli, ["new", "project"], catch_exceptions=False)

        self.assertEqual(result.exit_code, 0)
        mock_new.assert_called_once_with("project")

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_defaults(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(cli.cli, ["gh-deploy"], catch_exceptions=False)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        g_args, g_kwargs = mock_gh_deploy.call_args
        self.assertTrue("message" in g_kwargs)
        self.assertEqual(g_kwargs["message"], None)
        self.assertTrue("force" in g_kwargs)
        self.assertEqual(g_kwargs["force"], False)
        self.assertTrue("ignore_version" in g_kwargs)
        self.assertEqual(g_kwargs["ignore_version"], False)
        self.assertEqual(mock_build.call_count, 1)
        b_args, b_kwargs = mock_build.call_args
        self.assertTrue("dirty" in b_kwargs)
        self.assertFalse(b_kwargs["dirty"])
        mock_load_config.assert_called_once_with(
            remote_branch=None,
            remote_name=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_clean(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--clean"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        args, kwargs = mock_build.call_args
        self.assertTrue("dirty" in kwargs)
        self.assertFalse(kwargs["dirty"])

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_dirty(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--dirty"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        args, kwargs = mock_build.call_args
        self.assertTrue("dirty" in kwargs)
        self.assertTrue(kwargs["dirty"])

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_config_file(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli,
            ["gh-deploy", "--config-file", "mkdocs.yml"],
            catch_exceptions=False,
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        self.assertEqual(mock_load_config.call_count, 1)
        args, kwargs = mock_load_config.call_args
        self.assertTrue("config_file" in kwargs)
        self.assertIsInstance(kwargs["config_file"], io.BufferedReader)
        self.assertEqual(kwargs["config_file"].name, "mkdocs.yml")

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_message(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli,
            ["gh-deploy", "--message", "A commit message"],
            catch_exceptions=False,
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        g_args, g_kwargs = mock_gh_deploy.call_args
        self.assertTrue("message" in g_kwargs)
        self.assertEqual(g_kwargs["message"], "A commit message")
        self.assertEqual(mock_build.call_count, 1)
        self.assertEqual(mock_load_config.call_count, 1)

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_remote_branch(
        self, mock_gh_deploy, mock_build, mock_load_config
    ):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--remote-branch", "foo"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            remote_branch="foo",
            remote_name=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_remote_name(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--remote-name", "foo"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            remote_branch=None,
            remote_name="foo",
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_force(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--force"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        g_args, g_kwargs = mock_gh_deploy.call_args
        self.assertTrue("force" in g_kwargs)
        self.assertEqual(g_kwargs["force"], True)
        self.assertEqual(mock_build.call_count, 1)
        self.assertEqual(mock_load_config.call_count, 1)

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_ignore_version(
        self, mock_gh_deploy, mock_build, mock_load_config
    ):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--ignore-version"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        g_args, g_kwargs = mock_gh_deploy.call_args
        self.assertTrue("ignore_version" in g_kwargs)
        self.assertEqual(g_kwargs["ignore_version"], True)
        self.assertEqual(mock_build.call_count, 1)
        self.assertEqual(mock_load_config.call_count, 1)

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_strict(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--strict"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            remote_branch=None,
            remote_name=None,
            config_file=None,
            strict=True,
            theme=None,
            use_directory_urls=None,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_theme(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--theme", "readthedocs"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            remote_branch=None,
            remote_name=None,
            config_file=None,
            strict=None,
            theme="readthedocs",
            use_directory_urls=None,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_use_directory_urls(
        self, mock_gh_deploy, mock_build, mock_load_config
    ):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--use-directory-urls"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            remote_branch=None,
            remote_name=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=True,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_no_directory_urls(
        self, mock_gh_deploy, mock_build, mock_load_config
    ):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--no-directory-urls"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            remote_branch=None,
            remote_name=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=False,
            site_dir=None,
        )

    @mock.patch("mkdocs.config.load_config", autospec=True)
    @mock.patch("mkdocs.commands.build.build", autospec=True)
    @mock.patch("mkdocs.commands.gh_deploy.gh_deploy", autospec=True)
    def test_gh_deploy_site_dir(self, mock_gh_deploy, mock_build, mock_load_config):
        result = self.runner.invoke(
            cli.cli, ["gh-deploy", "--site-dir", "custom"], catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_gh_deploy.call_count, 1)
        self.assertEqual(mock_build.call_count, 1)
        mock_load_config.assert_called_once_with(
            remote_branch=None,
            remote_name=None,
            config_file=None,
            strict=None,
            theme=None,
            use_directory_urls=None,
            site_dir="custom",
        )

    def test_unset_default_source_values_without_click_context(self):
        kwargs = {"strict": False, "use_directory_urls": False}
        cli.unset_default_source_values(kwargs, "strict", "use_directory_urls")
        self.assertEqual(kwargs, {"strict": False, "use_directory_urls": False})

    def _restore_mkdocs_log_handlers(self):
        # `get-deps` attaches a warning counter to the "mkdocs" logger.
        logger = logging.getLogger("mkdocs")
        handlers = logger.handlers[:]
        self.addCleanup(setattr, logger, "handlers", handlers)

    @tempdir(files={"mkdocs.yml": "site_name: Test\nplugins: [redirects]\n"})
    def test_get_deps(self, tdir):
        self._restore_mkdocs_log_handlers()
        config_path = os.path.join(tdir, "mkdocs.yml")
        with (
            mock.patch("mkdocs_get_deps.get_projects_file") as mock_get_projects_file,
            mock.patch(
                "mkdocs_get_deps.get_deps",
                return_value=["mkdocs-ng", "mkdocs-redirects"],
            ) as mock_get_deps,
        ):
            result = self.runner.invoke(
                cli.cli,
                ["get-deps", "-f", config_path, "-p", "projects.yaml"],
                catch_exceptions=False,
            )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "mkdocs-ng\nmkdocs-redirects\n")
        mock_get_projects_file.assert_called_once_with("projects.yaml")
        (call,) = mock_get_deps.call_args_list
        self.assertEqual(call.kwargs["config_file"].name, config_path)
        self.assertIs(
            call.kwargs["projects_file"],
            mock_get_projects_file.return_value.__enter__.return_value,
        )

    @tempdir(files={"mkdocs.yml": "site_name: Test\nplugins: [foo]\n"})
    def test_get_deps_with_warnings_exits_with_error(self, tdir):
        self._restore_mkdocs_log_handlers()

        def get_deps(config_file, projects_file):
            logging.getLogger("mkdocs.get_deps").warning(
                "Plugin 'foo' was not found in the projects file"
            )
            return ["mkdocs-ng"]

        with (
            mock.patch("mkdocs_get_deps.get_projects_file"),
            mock.patch("mkdocs_get_deps.get_deps", side_effect=get_deps),
        ):
            result = self.runner.invoke(
                cli.cli, ["get-deps", "-f", os.path.join(tdir, "mkdocs.yml")]
            )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("mkdocs-ng\n", result.output)
        self.assertIn("Plugin 'foo' was not found in the projects file", result.output)


class ColorFormatterTests(unittest.TestCase):
    def make_record(self, level, msg):
        return logging.LogRecord("mkdocs", level, __file__, 1, msg, None, None)

    def test_format_without_terminal_width(self):
        formatter = cli.ColorFormatter()
        with mock.patch.object(cli.ColorFormatter.text_wrapper, "width", 0):
            self.assertEqual(
                formatter.format(
                    self.make_record(logging.INFO, "Building documentation...")
                ),
                "INFO    -  Building documentation...",
            )
            self.assertEqual(
                formatter.format(self.make_record(logging.WARNING, "Careful")),
                click.style("WARNING -  ", fg="yellow") + "Careful",
            )

    def test_format_wraps_to_terminal_width(self):
        formatter = cli.ColorFormatter()
        record = self.make_record(
            logging.ERROR, "one two three four five six seven\nsecond line"
        )
        with mock.patch.object(cli.ColorFormatter.text_wrapper, "width", 30):
            output = formatter.format(record)

        # Continuation lines are indented to line up with the text after the prefix.
        self.assertEqual(
            output,
            click.style("ERROR   -  ", fg="red")
            + "one two three four\n"
            + "           five six seven\n"
            + "           second line",
        )


class ShowWarningTests(unittest.TestCase):
    def test_falls_back_to_the_warning_location(self):
        with (
            mock.patch("traceback.extract_stack", side_effect=RuntimeError("no stack")),
            self.assertLogs("mkdocs.__main__", level="INFO") as cm,
        ):
            cli._showwarning("old thing", DeprecationWarning, "plugin.py", 12)

        self.assertEqual(
            cm.output,
            [
                'INFO:mkdocs.__main__:DeprecationWarning: old thing\n  File "plugin.py", line 12'
            ],
        )

    def test_shows_the_calling_location(self):
        def deprecated_api():
            cli._showwarning("old thing", DeprecationWarning, __file__, 1)

        with self.assertLogs("mkdocs.__main__", level="INFO") as cm:
            deprecated_api()

        [message] = cm.output
        self.assertTrue(
            message.startswith("INFO:mkdocs.__main__:DeprecationWarning: old thing\n")
        )
        self.assertIn(f'File "{__file__}", line', message)
        self.assertIn("deprecated_api()", message)

    def test_adds_the_warning_location_if_not_in_the_stack(self):
        with self.assertLogs("mkdocs.__main__", level="INFO") as cm:
            cli._showwarning("bad syntax", SyntaxWarning, "elsewhere.py", 7)

        [message] = cm.output
        self.assertTrue(
            message.startswith("INFO:mkdocs.__main__:SyntaxWarning: bad syntax\n")
        )
        self.assertIn('File "elsewhere.py", line 7', message)


class EnableWarningsTests(unittest.TestCase):
    def test_enable_warnings(self):
        from mkdocs.commands import build

        self.addCleanup(setattr, build.log, "filters", build.log.filters[:])
        with warnings.catch_warnings(), mock.patch.object(cli.sys, "warnoptions", []):
            cli._enable_warnings()
            self.assertIs(warnings.showwarning, cli._showwarning)
            self.assertIsInstance(build.log.filters[-1], utils.DuplicateFilter)

    def test_enable_warnings_keeps_user_configuration(self):
        from mkdocs.commands import build

        self.addCleanup(setattr, build.log, "filters", build.log.filters[:])
        filters = build.log.filters[:]
        with (
            warnings.catch_warnings(),
            mock.patch.object(cli.sys, "warnoptions", ["error::DeprecationWarning"]),
        ):
            showwarning = warnings.showwarning
            cli._enable_warnings()
            self.assertIs(warnings.showwarning, showwarning)
            self.assertEqual(build.log.filters, filters)
