#!/usr/bin/env python

import datetime
import unittest
from unittest import mock

import mkdocs
from mkdocs.utils import cache


class DownloadUrlTests(unittest.TestCase):
    @mock.patch("urllib.request.urlopen")
    def test_download_url(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b"data"

        self.assertEqual(cache.download_url("https://example.com/file.yml"), b"data")

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.com/file.yml")
        self.assertEqual(
            request.get_header("User-agent"), f"mkdocs/{mkdocs.__version__}"
        )


class DownloadAndCacheUrlTests(unittest.TestCase):
    @mock.patch("mkdocs_get_deps.cache.download_and_cache_url", return_value=b"cached")
    def test_delegates_to_mkdocs_get_deps(self, mock_download_and_cache):
        download = mock.Mock()
        duration = datetime.timedelta(hours=1)
        result = cache.download_and_cache_url(
            "https://example.com/file.yml", duration, download=download, comment=b"// "
        )
        self.assertEqual(result, b"cached")
        mock_download_and_cache.assert_called_once_with(
            url="https://example.com/file.yml",
            cache_duration=duration,
            download=download,
            comment=b"// ",
        )

    @mock.patch("mkdocs_get_deps.cache.download_and_cache_url")
    def test_defaults(self, mock_download_and_cache):
        cache.download_and_cache_url(
            "https://example.com/file.yml", datetime.timedelta(days=1)
        )
        kwargs = mock_download_and_cache.call_args.kwargs
        self.assertIs(kwargs["download"], cache.download_url)
        self.assertEqual(kwargs["comment"], b"# ")


if __name__ == "__main__":
    unittest.main()
