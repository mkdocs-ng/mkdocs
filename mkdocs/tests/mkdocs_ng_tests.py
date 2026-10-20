#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

import mkdocs_ng
from mkdocs.tests.base import tempdir

REPO_ROOT = Path(__file__).resolve().parents[2]
PTH_FILE = REPO_ROOT / "mkdocs_ng.pth"


class FindRootTests(unittest.TestCase):
    @tempdir(files=["mkdocs_ng/__init__.py", "mkdocs_ng/mkdocs/__init__.py"])
    def test_wheel_layout(self, site):
        with mock.patch.object(mkdocs_ng, "_HERE", os.path.join(site, "mkdocs_ng")):
            self.assertEqual(mkdocs_ng._find_root(), os.path.join(site, "mkdocs_ng"))

    @tempdir(files=["pyproject.toml", "mkdocs_ng/__init__.py", "mkdocs/__init__.py"])
    def test_source_checkout(self, repo):
        with mock.patch.object(mkdocs_ng, "_HERE", os.path.join(repo, "mkdocs_ng")):
            self.assertEqual(mkdocs_ng._find_root(), repo)

    @tempdir(files=["mkdocs_ng/__init__.py", "mkdocs/__init__.py"])
    def test_never_falls_back_to_upstream(self, site):
        # site-packages/mkdocs/ belongs to upstream MkDocs: don't pick it up
        # just because MkDocs NG's own package is missing.
        with mock.patch.object(mkdocs_ng, "_HERE", os.path.join(site, "mkdocs_ng")):
            self.assertIsNone(mkdocs_ng._find_root())


class FinderTests(unittest.TestCase):
    @tempdir(files=["mkdocs/__init__.py", "mkdocs/sub.py"])
    def test_find_spec(self, root):
        finder = mkdocs_ng.MkDocsFinder(root)
        spec = finder.find_spec("mkdocs")
        self.assertEqual(spec.origin, os.path.join(root, "mkdocs", "__init__.py"))
        self.assertEqual(
            list(spec.submodule_search_locations), [os.path.join(root, "mkdocs")]
        )

    @tempdir(files=["mkdocs/__init__.py", "mkdocs/sub.py"])
    def test_only_handles_top_level_package(self, root):
        # Submodules are found through the package's __path__.
        finder = mkdocs_ng.MkDocsFinder(root)
        self.assertIsNone(finder.find_spec("mkdocs.sub"))
        self.assertIsNone(finder.find_spec("mkdocs_material"))
        self.assertIsNone(finder.find_spec("os"))

    @tempdir(files=["mkdocs/__init__.py"])
    def test_install(self, root):
        meta_path = [object()]
        with (
            mock.patch.object(sys, "meta_path", meta_path),
            mock.patch.object(mkdocs_ng, "_find_root", return_value=root),
        ):
            self.assertTrue(mkdocs_ng.install())
            self.assertTrue(mkdocs_ng.install())
        self.assertEqual(len(meta_path), 2)
        self.assertIsInstance(meta_path[0], mkdocs_ng.MkDocsFinder)
        self.assertEqual(meta_path[0].root, root)

    def test_install_without_package(self):
        meta_path = [object()]
        with (
            mock.patch.object(sys, "meta_path", meta_path),
            mock.patch.object(mkdocs_ng, "_find_root", return_value=None),
        ):
            self.assertFalse(mkdocs_ng.install())
        self.assertEqual(len(meta_path), 1)


@unittest.skipUnless(PTH_FILE.is_file(), "needs a source checkout")
class SitePackagesTests(unittest.TestCase):
    """Run a fresh interpreter on a fake site-packages that has both packages."""

    FILES = {
        # Upstream MkDocs, installed because a plugin depends on it.
        "mkdocs/__init__.py": "NAME = 'upstream'\n",
        "mkdocs/__main__.py": "def cli():\n    return 'upstream cli'\n",
        "mkdocs/only_in_upstream.py": "",
        # MkDocs NG, relocated by the wheel.
        "mkdocs_ng/mkdocs/__init__.py": "NAME = 'ng'\n",
        "mkdocs_ng/mkdocs/__main__.py": "def cli():\n    return 'ng cli'\n",
        "mkdocs_ng/mkdocs/plugins.py": "",
    }

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="mkdocs_test-")
        self.addCleanup(tmp.cleanup)
        self.site = Path(tmp.name)
        for name, content in self.FILES.items():
            path = self.site / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        shutil.copy(mkdocs_ng.__file__, self.site / "mkdocs_ng" / "__init__.py")
        shutil.copy(PTH_FILE, self.site / "mkdocs_ng.pth")

    def run_python(self, code):
        # -S: don't load the real site-packages. -I: ignore PYTHONPATH and cwd.
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-c", textwrap.dedent(code)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.split()

    def test_pth_file_makes_mkdocs_ng_win(self):
        out = self.run_python(
            f"""
            import site
            site.addsitedir({str(self.site)!r})
            import mkdocs, mkdocs.plugins
            print(mkdocs.NAME, mkdocs.plugins.__file__)
            try:
                import mkdocs.only_in_upstream
            except ImportError:
                print('no-mixing')
            """
        )
        self.assertEqual(
            out,
            [
                "ng",
                str(self.site / "mkdocs_ng" / "mkdocs" / "plugins.py"),
                "no-mixing",
            ],
        )

    def test_upstream_launcher_runs_mkdocs_ng(self):
        # If upstream's `mkdocs` script was installed last, it runs
        # `from mkdocs.__main__ import cli`.
        out = self.run_python(
            f"""
            import site
            site.addsitedir({str(self.site)!r})
            from mkdocs.__main__ import cli
            print(cli().replace(' ', '-'))
            """
        )
        self.assertEqual(out, ["ng-cli"])

    def test_entry_point_without_pth_file(self):
        # MkDocs NG's own `mkdocs` script works even if .pth files aren't processed.
        out = self.run_python(
            f"""
            import sys
            sys.path.append({str(self.site)!r})
            import mkdocs_ng
            print(mkdocs_ng.main().replace(' ', '-'))
            """
        )
        self.assertEqual(out, ["ng-cli"])

    def test_without_upstream(self):
        shutil.rmtree(self.site / "mkdocs")
        out = self.run_python(
            f"""
            import site
            site.addsitedir({str(self.site)!r})
            import mkdocs
            print(mkdocs.NAME)
            """
        )
        self.assertEqual(out, ["ng"])


if __name__ == "__main__":
    unittest.main()
