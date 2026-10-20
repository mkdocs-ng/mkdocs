#!/usr/bin/env python

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

import mkdocs
from mkdocs import __main__ as cli
from mkdocs.tests.base import tempdir
from mkdocs.utils import dist_conflict

UPSTREAM_METADATA = "Metadata-Version: 2.1\nName: mkdocs\nVersion: 1.6.1\n"
NG_METADATA = "Metadata-Version: 2.4\nName: mkdocs-ng\nVersion: 2.0.0\n"


class _Base(unittest.TestCase):
    def setUp(self):
        # The check only runs once per process; reset that for every test.
        dist_conflict.warn_if_upstream_installed.cache_clear()
        self.addCleanup(dist_conflict.warn_if_upstream_installed.cache_clear)

    def use_site_packages(self, site):
        """Make `site` the only place distributions are looked up and `mkdocs` lives."""
        for patcher in (
            mock.patch.object(sys, "path", [site]),
            mock.patch.object(
                mkdocs, "__file__", os.path.join(site, "mkdocs", "__init__.py")
            ),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)


class FindConflictingDistributionTests(_Base):
    @tempdir(
        files={
            "mkdocs/__init__.py": "",
            "mkdocs_ng-2.0.0.dist-info/METADATA": NG_METADATA,
        }
    )
    def test_only_mkdocs_ng_installed(self, site):
        self.use_site_packages(site)
        self.assertIsNone(dist_conflict.find_conflicting_distribution())

    @tempdir(
        files={
            "mkdocs/__init__.py": "",
            "mkdocs_ng-2.0.0.dist-info/METADATA": NG_METADATA,
            "mkdocs-1.6.1.dist-info/METADATA": UPSTREAM_METADATA,
            "mkdocs-1.6.1.dist-info/INSTALLER": "pip\n",
        }
    )
    def test_upstream_installed_in_same_location(self, site):
        self.use_site_packages(site)
        dist = dist_conflict.find_conflicting_distribution()
        self.assertIsNotNone(dist)
        self.assertEqual(dist.version, "1.6.1")

    @tempdir(
        files={
            "ng/mkdocs/__init__.py": "",
            "ng/mkdocs_ng-2.0.0.dist-info/METADATA": NG_METADATA,
            "other/mkdocs/__init__.py": "",
            "other/mkdocs-1.6.1.dist-info/METADATA": UPSTREAM_METADATA,
        }
    )
    def test_upstream_installed_elsewhere(self, td):
        # E.g. MkDocs NG in a virtualenv and upstream MkDocs in user site-packages:
        # nothing gets overwritten, so this isn't a conflict.
        ng = os.path.join(td, "ng")
        other = os.path.join(td, "other")
        with (
            mock.patch.object(sys, "path", [ng, other]),
            mock.patch.object(
                mkdocs, "__file__", os.path.join(ng, "mkdocs", "__init__.py")
            ),
        ):
            self.assertIsNone(dist_conflict.find_conflicting_distribution())

    def test_ignores_distribution_with_other_name(self):
        dist = mock.Mock()
        dist.metadata = {"Name": "mkdocs-ng"}
        with mock.patch.object(
            dist_conflict.metadata, "distribution", return_value=dist
        ):
            self.assertIsNone(dist_conflict.find_conflicting_distribution())


class WarnIfUpstreamInstalledTests(_Base):
    @tempdir(
        files={
            "mkdocs/__init__.py": "",
            "mkdocs_ng-2.0.0.dist-info/METADATA": NG_METADATA,
        }
    )
    def test_no_warning_without_upstream(self, site):
        self.use_site_packages(site)
        with self.assertNoLogs("mkdocs.utils.dist_conflict"):
            self.assertFalse(dist_conflict.warn_if_upstream_installed())

    @tempdir(
        files={
            "mkdocs/__init__.py": "",
            "mkdocs_ng-2.0.0.dist-info/METADATA": NG_METADATA,
            "mkdocs-1.6.1.dist-info/METADATA": UPSTREAM_METADATA,
            "mkdocs-1.6.1.dist-info/INSTALLER": "pip\n",
        }
    )
    def test_warning_with_pip_fix(self, site):
        self.use_site_packages(site)
        with self.assertLogs("mkdocs.utils.dist_conflict", "WARNING") as cm:
            self.assertTrue(dist_conflict.warn_if_upstream_installed())
        [msg] = cm.output
        self.assertIn("'mkdocs' package (version 1.6.1)", msg)
        self.assertIn(
            "pip uninstall -y mkdocs && pip install --force-reinstall --no-deps mkdocs-ng",
            msg,
        )
        self.assertIn(dist_conflict.DOCS_URL, msg)

    @tempdir(
        files={
            "mkdocs/__init__.py": "",
            "mkdocs-1.6.1.dist-info/METADATA": UPSTREAM_METADATA,
            "mkdocs-1.6.1.dist-info/INSTALLER": "uv\n",
        }
    )
    def test_warning_with_uv_fix(self, site):
        self.use_site_packages(site)
        with self.assertLogs("mkdocs.utils.dist_conflict", "WARNING") as cm:
            dist_conflict.warn_if_upstream_installed()
        self.assertIn(
            "uv pip uninstall mkdocs && uv pip install --reinstall --no-deps mkdocs-ng",
            cm.output[0],
        )

    @tempdir(
        files={
            "mkdocs/__init__.py": "",
            "mkdocs-1.6.1.dist-info/METADATA": UPSTREAM_METADATA,
        }
    )
    def test_warning_without_installer_file(self, site):
        self.use_site_packages(site)
        with self.assertLogs("mkdocs.utils.dist_conflict", "WARNING") as cm:
            dist_conflict.warn_if_upstream_installed()
        self.assertIn("pip install --force-reinstall --no-deps mkdocs-ng", cm.output[0])

    @tempdir(
        files={
            "mkdocs/__init__.py": "",
            "mkdocs-1.6.1.dist-info/METADATA": UPSTREAM_METADATA,
        }
    )
    def test_warns_only_once(self, site):
        self.use_site_packages(site)
        with self.assertLogs("mkdocs.utils.dist_conflict", "WARNING") as cm:
            dist_conflict.warn_if_upstream_installed()
            dist_conflict.warn_if_upstream_installed()
        self.assertEqual(len(cm.output), 1)


def _fake_upstream():
    dist = mock.Mock()
    dist.version = "1.6.1"
    dist.read_text.return_value = "pip\n"
    return dist


@mock.patch.object(
    dist_conflict, "find_conflicting_distribution", side_effect=_fake_upstream
)
class EntryPointTests(_Base):
    @tempdir(
        files={
            "project/mkdocs.yml": "site_name: My Docs\nstrict: true\n",
            "project/docs/index.md": "# Hello\n",
        }
    )
    def test_api_build_strict_not_aborted(self, td, _find):
        project = Path(td, "project")
        with self.assertLogs("mkdocs.utils.dist_conflict", "WARNING") as cm:
            mkdocs.build(config_file=project / "mkdocs.yml", site_dir=project / "site")
        self.assertEqual(len(cm.output), 1)
        self.assertTrue((project / "site" / "index.html").is_file())

    @mock.patch("mkdocs.commands.serve.serve", autospec=True)
    def test_api_serve_warns(self, _serve, _find):
        with self.assertLogs("mkdocs.utils.dist_conflict", "WARNING"):
            mkdocs.serve(config_file="mkdocs.yml")
        _serve.assert_called_once()

    @tempdir(
        files={
            "project/mkdocs.yml": "site_name: My Docs\n",
            "project/docs/index.md": "# Hello\n",
        }
    )
    def test_cli_build_strict_warns_once_and_succeeds(self, td, _find):
        project = Path(td, "project")
        with self.assertLogs("mkdocs.utils.dist_conflict", "WARNING") as cm:
            result = CliRunner().invoke(
                cli.cli,
                [
                    "build",
                    "--strict",
                    "-f",
                    str(project / "mkdocs.yml"),
                    "-d",
                    str(project / "site"),
                ],
                catch_exceptions=False,
            )
        self.assertEqual(result.exit_code, 0, result.output)
        # Checked by the CLI group and again by mkdocs.build(), but reported once.
        self.assertEqual(len(cm.output), 1)
        self.assertTrue((project / "site" / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
