#!/usr/bin/env python

import unittest

import markdown
import markdown.treeprocessors

from mkdocs.utils import rendering


class _CaptureHeadingText(markdown.treeprocessors.Treeprocessor):
    text = None

    def run(self, root):
        self.text = rendering.get_heading_text(root.find("h1"), self.md)


def heading_text(source, extensions=()):
    md = markdown.Markdown(extensions=list(extensions))
    capture = _CaptureHeadingText(md)
    # Run after the inline patterns and the other tree processors.
    md.treeprocessors.register(capture, "capture_heading_text", priority=-100)
    md.convert(source)
    return capture.text


class GetHeadingTextTests(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(heading_text("# Hello world"), "Hello world")

    def test_image_alt_text_keeps_surrounding_text(self):
        # The image is replaced by its alt text, which is carried over to the
        # tail of the preceding element.
        self.assertEqual(heading_text("# *Hello* ![world](world.png)!"), "Hello world!")

    def test_image_without_alt_text_is_dropped(self):
        self.assertEqual(heading_text("# Logo ![](logo.png) *here*"), "Logo here")

    def test_footnote_reference_is_dropped(self):
        self.assertEqual(
            heading_text("# Title[^1] *here*\n\n[^1]: The note.", ["footnotes"]),
            "Title here",
        )


class StripTagsTests(unittest.TestCase):
    def test_strip_tags(self):
        self.assertEqual(
            rendering._strip_tags("<b>Bold</b>  and <!-- <i>hidden</i> -->\n text"),
            "Bold and text",
        )


if __name__ == "__main__":
    unittest.main()
