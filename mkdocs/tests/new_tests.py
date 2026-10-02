#!/usr/bin/env python

import os
import unittest

from mkdocs.commands import new
from mkdocs.tests.base import change_dir, tempdir


class NewTests(unittest.TestCase):
    @tempdir()
    def test_new(self, temp_dir):
        with change_dir(temp_dir):
            new.new("myproject")

            expected_paths = [
                os.path.join(temp_dir, "myproject"),
                os.path.join(temp_dir, "myproject", "mkdocs.yml"),
                os.path.join(temp_dir, "myproject", "docs"),
                os.path.join(temp_dir, "myproject", "docs", "index.md"),
            ]

            for expected_path in expected_paths:
                self.assertTrue(os.path.exists(expected_path))

    @tempdir(files={"myproject/mkdocs.yml": "site_name: Existing\n"})
    def test_new_existing_project(self, temp_dir):
        with change_dir(temp_dir):
            with self.assertLogs("mkdocs.commands.new") as cm:
                new.new("myproject")

        self.assertEqual(
            cm.output, ["INFO:mkdocs.commands.new:Project already exists."]
        )
        with open(
            os.path.join(temp_dir, "myproject", "mkdocs.yml"), encoding="utf-8"
        ) as f:
            self.assertEqual(f.read(), "site_name: Existing\n")
        self.assertFalse(os.path.exists(os.path.join(temp_dir, "myproject", "docs")))

    @tempdir(files={"myproject/docs/index.md": "# My own index\n"})
    def test_new_keeps_existing_index(self, temp_dir):
        with change_dir(temp_dir):
            new.new("myproject")

        self.assertTrue(
            os.path.isfile(os.path.join(temp_dir, "myproject", "mkdocs.yml"))
        )
        with open(
            os.path.join(temp_dir, "myproject", "docs", "index.md"), encoding="utf-8"
        ) as f:
            self.assertEqual(f.read(), "# My own index\n")
