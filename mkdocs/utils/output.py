"""
Keep the site directory of `mkdocs serve` between rebuilds.

A normal build empties `site_dir` and writes every file again. During
`mkdocs serve`, a rebuild usually produces the same bytes for nearly every
page, so writing them all again is wasted time. Instead, the site directory is
kept between rebuilds:

- `utils.write_file` skips a file whose content is the same as at its last
  write, as long as the file on disk wasn't changed since.
- At the end of a build, the files that `utils.write_file` or a `File` copy
  produced in an earlier build but not in this one are removed, so that a
  deleted or renamed page doesn't stay around.

Files that plugins write some other way are left alone. The build date that
themes show is the time the server started, so that it doesn't change every
page on each rebuild.
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

log = logging.getLogger(__name__)


def _digest(content: bytes) -> bytes:
    return hashlib.blake2b(content, digest_size=16).digest()


def _state(path: str) -> tuple[int, int] | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_size, st.st_mtime_ns)


class SiteOutput:
    def __init__(self) -> None:
        # Path -> digest of the content we wrote and the file's (size, mtime) after it.
        self._written: dict[str, tuple[bytes, tuple[int, int] | None]] = {}
        # Paths we produced in the previous build, and in this one.
        self._previous: set[str] = set()
        self._current: set[str] = set()
        self._site_dir: str | None = None
        # How deep in nested builds we are: a plugin may run a build of its own.
        self._depth = 0
        # The build date that pages show: when the server started.
        self.build_datetime: datetime | None = None

    @property
    def building(self) -> bool:
        """Whether the outermost build is running, and not a nested one."""
        return self._depth == 1

    def start_build(self, site_dir: str) -> bool:
        """
        Start a build. Returns False for a nested build, which should behave as
        usual (clean the site directory, write every file).
        """
        self._depth += 1
        if self._depth > 1:
            return False
        self._site_dir = os.path.abspath(site_dir)
        # Also keep what a build that failed halfway produced.
        self._previous |= self._current
        self._current = set()
        return True

    def end_build(self, *, success: bool) -> None:
        self._depth -= 1
        if self._depth == 0 and success:
            self._remove_stale()

    def _in_site_dir(self, path: str) -> bool:
        return self._site_dir is not None and path.startswith(self._site_dir + os.sep)

    def write(self, content: bytes, output_path: str, write) -> None:
        """Call `write()` unless `output_path` already holds `content` from our last write."""
        path = os.path.abspath(output_path)
        if not self._in_site_dir(path):
            write()
            return
        self._current.add(path)
        digest = _digest(content)
        entry = self._written.get(path)
        if entry is not None and entry[0] == digest and entry[1] == _state(path):
            return
        write()
        self._written[path] = (digest, _state(path))

    def keep(self, output_path: str, digest: bytes) -> bool:
        """
        Whether `output_path` already holds the content with this digest from
        our last write. If so, it counts as written by this build.
        """
        path = os.path.abspath(output_path)
        entry = self._written.get(path)
        if (
            entry is None
            or entry[0] != digest
            or not self._in_site_dir(path)
            or entry[1] != _state(path)
        ):
            return False
        self._current.add(path)
        return True

    def digest(self, output_path: str) -> bytes | None:
        """The digest of what our last write put in `output_path`."""
        entry = self._written.get(os.path.abspath(output_path))
        return None if entry is None else entry[0]

    def copied(self, output_path: str) -> None:
        path = os.path.abspath(output_path)
        if not self._in_site_dir(path):
            return
        self._current.add(path)
        self._written.pop(path, None)

    def _remove_stale(self) -> None:
        """Remove what an earlier build produced and this one didn't."""
        stale = self._previous - self._current
        dirs: set[str] = set()
        for path in stale:
            self._written.pop(path, None)
            try:
                os.unlink(path)
            except FileNotFoundError:
                continue
            except OSError as e:  # pragma: no cover
                log.debug(f"Could not remove stale file '{path}': {e}")
                continue
            dirs.add(os.path.dirname(path))
        # Remove the directories that this left empty, deepest first.
        assert self._site_dir is not None
        root = self._site_dir + os.sep
        for d in sorted(dirs, key=len, reverse=True):
            while d.startswith(root):
                try:
                    os.rmdir(d)
                except OSError:
                    break
                d = os.path.dirname(d)
        self._previous = self._current
        self._current = set()


# Set by `mkdocs serve` for the duration of the server.
active: SiteOutput | None = None
