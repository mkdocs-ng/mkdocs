#!/usr/bin/env python

import unittest
from pathlib import Path
from unittest import mock

import mkdocs
from mkdocs.tests.base import tempdir


class BuildTests(unittest.TestCase):
    @tempdir(
        files={
            "project/mkdocs.yml": "site_name: My Docs\n",
            "project/docs/index.md": "# Hello\n",
        }
    )
    def test_build(self, td):
        project = Path(td, "project")
        config = mkdocs.build(
            config_file=project / "mkdocs.yml", site_dir=project / "site"
        )

        self.assertTrue((project / "site" / "index.html").is_file())
        self.assertEqual(config.site_name, "My Docs")
        self.assertEqual(config.site_dir, str(project / "site"))

    @tempdir(
        files={
            "project/mkdocs.yml": "site_name: My Docs\n",
            "project/docs/index.md": "# Hello\n",
        }
    )
    def test_build_overrides_config_from_kwargs(self, td):
        project = Path(td, "project")
        config = mkdocs.build(
            config_file=project / "mkdocs.yml",
            site_dir=project / "site",
            site_name="Overridden",
        )

        self.assertTrue((project / "site" / "index.html").is_file())
        self.assertEqual(config.site_name, "Overridden")

    @tempdir(
        files={
            "project/mkdocs.yml": "site_name: My Docs\n",
            "project/docs/index.md": "# Hello\n",
        }
    )
    def test_build_accepts_file_object(self, td):
        project = Path(td, "project")
        with open(project / "mkdocs.yml", "rb") as f:
            config = mkdocs.build(config_file=f, site_dir=project / "site")

        self.assertTrue((project / "site" / "index.html").is_file())
        self.assertEqual(config.site_name, "My Docs")

    @tempdir(
        files={
            "project/mkdocs.yml": "site_name: My Docs\n",
            "project/docs/index.md": "# Hello\n",
        }
    )
    def test_build_dirty(self, td):
        project = Path(td, "project")
        with self.assertLogs("mkdocs", level="WARNING"):
            config = mkdocs.build(
                config_file=project / "mkdocs.yml",
                site_dir=project / "site",
                dirty=True,
            )

        self.assertTrue((project / "site" / "index.html").is_file())
        self.assertEqual(config.site_name, "My Docs")


class ServeTests(unittest.TestCase):
    @mock.patch("mkdocs.commands.serve.serve")
    def test_serve_forwards_arguments(self, mock_serve):
        mkdocs.serve(
            config_file=Path("mkdocs.yml"),
            dev_addr="127.0.0.1:9000",
            livereload=False,
            build_type="dirty",
            watch_theme=True,
            watch=("a", "b"),
            open_in_browser=True,
            strict=True,
            theme="readthedocs",
            use_directory_urls=False,
            site_name="My Docs",
        )

        mock_serve.assert_called_once_with(
            config_file="mkdocs.yml",
            dev_addr="127.0.0.1:9000",
            livereload=False,
            build_type="dirty",
            watch_theme=True,
            watch=["a", "b"],
            open_in_browser=True,
            strict=True,
            theme="readthedocs",
            use_directory_urls=False,
            site_name="My Docs",
        )

    @mock.patch("mkdocs.commands.serve.serve")
    def test_serve_defaults(self, mock_serve):
        mkdocs.serve()

        mock_serve.assert_called_once_with(
            config_file=None,
            dev_addr=None,
            livereload=True,
            build_type=None,
            watch_theme=False,
            watch=[],
            open_in_browser=False,
            strict=None,
            theme=None,
            use_directory_urls=None,
        )


if __name__ == "__main__":
    unittest.main()
