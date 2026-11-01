"""
# MkDocs Integration tests.

This is a simple integration test that builds the MkDocs
documentation against all of the builtin themes.

From the root of the MkDocs git repo, use:

    python -m mkdocs.tests.integration --help


TODOs
    - Build with different configuration options.
    - Build documentation other than just MkDocs as it is relatively simple.
"""

import logging
import os
import re
import subprocess
import tempfile

import click
import yaml

import mkdocs

log = logging.getLogger("mkdocs")

DIR = os.path.dirname(__file__)
MKDOCS_CONFIG = os.path.abspath(os.path.join(DIR, "../../mkdocs.yml"))
MKDOCS_THEMES = ["mkdocs", "readthedocs"]
TEST_PROJECTS = os.path.abspath(os.path.join(DIR, "integration"))
VERSION_ORIGIN_RE = re.compile(r"from (.+) \(Python")

# The documentation site uses the Sumi theme. To build it with a built-in theme,
# leave out the `sumi` plugin, and let pages that use one of Sumi's page
# templates (the home page is a Sumi landing page) fall back to `main.html`.
SUMI_TEMPLATES_HOOK = """
SUMI_TEMPLATES = {"landing.html", "blog.html", "blog-post.html", "releases.html", "print.html"}


def on_page_markdown(markdown, page, **kwargs):
    if page.meta.get("template") in SUMI_TEMPLATES:
        del page.meta["template"]
"""


def builtin_theme_config(theme: str, directory: str) -> str:
    """Write a copy of the docs configuration that uses a built-in theme."""
    with open(MKDOCS_CONFIG, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    root = os.path.dirname(MKDOCS_CONFIG)

    hook = os.path.join(directory, "sumi_templates.py")
    with open(hook, "w", encoding="utf-8") as f:
        f.write(SUMI_TEMPLATES_HOOK)

    config["theme"] = {"name": theme}
    config["docs_dir"] = os.path.join(root, config.get("docs_dir", "docs"))
    config["hooks"] = [os.path.join(root, h) for h in config.get("hooks", [])] + [hook]
    config["plugins"] = [
        p
        for p in config.get("plugins", [])
        if p != "sumi" and not (isinstance(p, dict) and "sumi" in p)
    ]
    config.pop("watch", None)

    path = os.path.join(directory, f"mkdocs-{theme}.yml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
    return path


def check_mkdocs_command() -> None:
    """
    Verify that the `mkdocs` command runs the same code as these tests.

    The builds below shell out to the `mkdocs` console script. Documentation
    tooling also depends on an upstream distribution that ships a package of
    the same name, and whichever lands last in site-packages wins for console
    scripts - so without this check the tests could silently exercise a
    different MkDocs than the one being developed.
    """
    assert mkdocs.__file__ is not None
    expected = os.path.realpath(os.path.dirname(mkdocs.__file__))

    output = subprocess.check_output(["mkdocs", "--version"], text=True)
    match = VERSION_ORIGIN_RE.search(output)
    if match is None:
        raise click.ClickException(
            f"Could not tell which MkDocs the 'mkdocs' command runs: {output.strip()!r}"
        )

    actual = os.path.realpath(match[1])
    if actual != expected:
        raise click.ClickException(
            f"The 'mkdocs' command runs {actual}, but these tests are for "
            f"{expected}. Run them through 'hatch run integration:test', which "
            f"puts the project first on sys.path."
        )


@click.command()
@click.option(
    "--output",
    help="The output directory to use when building themes",
    type=click.Path(file_okay=False, writable=True),
)
def main(output=None):
    if output is None:
        directory = tempfile.TemporaryDirectory(prefix="mkdocs_integration-")
        output = directory.name

    log.propagate = False
    stream = logging.StreamHandler()
    formatter = logging.Formatter("\033[1m\033[1;32m *** %(message)s *** \033[0m")
    stream.setFormatter(formatter)
    log.addHandler(stream)
    log.setLevel(logging.DEBUG)

    check_mkdocs_command()

    base_cmd = ["mkdocs", "build", "-q", "-s", "--site-dir"]

    log.debug("Building installed themes.")
    configs = tempfile.TemporaryDirectory(prefix="mkdocs_integration_config-")
    for theme in sorted(MKDOCS_THEMES):
        log.debug(f"Building theme: {theme}")
        project_dir = os.path.dirname(MKDOCS_CONFIG)
        out = os.path.join(output, theme)
        config_file = builtin_theme_config(theme, configs.name)
        command = [*base_cmd, out, "--config-file", config_file]
        subprocess.check_call(command, cwd=project_dir)

    log.debug("Building test projects.")
    for project in os.listdir(TEST_PROJECTS):
        project_dir = os.path.join(TEST_PROJECTS, project)
        if not os.path.isdir(project_dir):
            continue
        log.debug(f"Building test project: {project}")
        out = os.path.join(output, project)
        command = [*base_cmd, out]
        subprocess.check_call(command, cwd=project_dir)

    log.debug(f"Theme and integration builds are in {output}")


if __name__ == "__main__":
    main()
