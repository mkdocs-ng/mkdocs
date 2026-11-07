"""
Make `import mkdocs` load MkDocs NG.

MkDocs NG provides the `mkdocs` package, but almost every plugin and theme
depends on the upstream `mkdocs` distribution, which installs a package of the
same name. To keep the two from overwriting each other's files, MkDocs NG
installs its package to `site-packages/mkdocs_ng/mkdocs/` instead of
`site-packages/mkdocs/`, and runs `install()` at interpreter startup: from
`mkdocs_ng.start` on Python 3.15+ (PEP 829), and from the import line in
`mkdocs_ng.pth` on older versions. From then on `import mkdocs` finds MkDocs
NG first, whether or not the upstream package is installed too.

This module is imported by every Python process in the environment, so it must
stay small and must not import MkDocs itself.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _find_root() -> str | None:
    """Return the directory that contains MkDocs NG's `mkdocs` package."""
    # Installed from a wheel: site-packages/mkdocs_ng/mkdocs/
    if os.path.isfile(os.path.join(_HERE, "mkdocs", "__init__.py")):
        return _HERE
    # Source checkout or editable install: <repo>/mkdocs/ next to <repo>/mkdocs_ng/
    parent = os.path.dirname(_HERE)
    if os.path.isfile(os.path.join(parent, "pyproject.toml")) and os.path.isfile(
        os.path.join(parent, "mkdocs", "__init__.py")
    ):
        return parent
    return None


def _path_finder():
    # The standard path-based finder is already on sys.meta_path. Looking it up
    # there avoids importing importlib.machinery (and warnings) at startup.
    for finder in sys.meta_path:
        if getattr(finder, "__name__", None) == "PathFinder":
            return finder
    from importlib.machinery import PathFinder

    return PathFinder


class MkDocsFinder:
    """
    A meta path finder that loads the top-level `mkdocs` package from `root`.

    Submodules are then found through the package's `__path__` as usual, so
    they're never mixed with files from another `mkdocs` package.

    It also makes mike build with MkDocs NG, see `_MikeLoader`.
    """

    def __init__(self, root: str) -> None:
        self.root = root

    def find_spec(self, fullname, path=None, target=None):
        if fullname == MIKE_MODULE:
            spec = _path_finder().find_spec(fullname, path)
            if spec is not None and spec.loader is not None:
                spec.loader = _MikeLoader(spec.loader)
            return spec
        if fullname != "mkdocs":
            return None
        return _path_finder().find_spec(fullname, [self.root])

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.root!r})"


MIKE_MODULE = "mike.mkdocs_utils"


class _MikeLoader:
    """
    Load `mike.mkdocs_utils`, then point it at MkDocs NG.

    mike runs `properdocs build` instead of `mkdocs build` whenever ProperDocs
    is installed, which plugins such as mkdocs-redirects do. The build then
    doesn't use MkDocs NG, and fails on its settings such as `languages`.
    """

    def __init__(self, loader) -> None:
        self.loader = loader

    def __getattr__(self, name):
        return getattr(self.loader, name)

    def create_module(self, spec):
        return self.loader.create_module(spec)

    def exec_module(self, module) -> None:
        self.loader.exec_module(module)
        if not hasattr(module, "_program_name"):
            return  # A mike version that works differently: leave it alone.
        module._program_name = "mkdocs"
        # Also shown in the messages of mike's commits.
        from importlib import metadata

        try:
            module._version = metadata.version("mkdocs-ng")
            module._brand = "MkDocs NG"
        except metadata.PackageNotFoundError:
            pass


def install() -> bool:
    """Put MkDocs NG's finder first on `sys.meta_path`. Returns True if it's active."""
    if any(type(f).__name__ == "MkDocsFinder" for f in sys.meta_path):
        return True
    root = _find_root()
    if root is None:
        return False
    sys.meta_path.insert(0, MkDocsFinder(root))
    return True


def main():
    """Entry point of the `mkdocs` command; works even if `.pth` files are skipped."""
    install()
    from mkdocs.__main__ import cli

    return cli()
