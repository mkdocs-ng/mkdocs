# Python API

MkDocs can be used as a Python library in addition to a command-line tool.
This is useful for CI scripts, build system integrations (for example Hatch or
`uv` plugins), or any other programmatic use such as generating multiple sites
or building documentation from an application.

## Building a site

The [`mkdocs.build()`][mkdocs.build] function is the programmatic equivalent
of the `mkdocs build` command:

```python
import mkdocs

config = mkdocs.build(config_file="mkdocs.yml")
print(f"Built site to {config.site_dir}")
```

The loaded configuration is returned, so you can inspect or reuse it (for
example `config.site_dir` or `config.site_url`).

### Overriding configuration in code

Any configuration option can be overridden directly from Python, without
editing the config file — or even without a config file at all. Options passed
as keyword arguments behave like the corresponding command line options:

```python
import mkdocs

config = mkdocs.build(
    config_file="mkdocs.yml",
    site_name="My project",
    site_url="https://example.com",
    use_directory_urls=False,
    strict=True,
)
```

When `config_file` is omitted, `mkdocs.yml` in the current directory is used.
If you want to define the whole configuration in code, pass the values as
keyword arguments and point `config_file` at a minimal (or empty) file.

### Building without a config file

A config file is always loaded, but you can build with only programmatic
options by providing an empty config file:

```python
import pathlib
import tempfile

import mkdocs

with tempfile.TemporaryDirectory() as tmp:
    config_file = pathlib.Path(tmp) / "mkdocs.yml"
    config_file.write_text("site_name: Generated docs\n", encoding="utf-8")

    config = mkdocs.build(
        config_file=config_file,
        site_dir=pathlib.Path(tmp) / "site",
        nav=[{"Home": "index.md"}],
    )
```

## Running the development server

The [`mkdocs.serve()`][mkdocs.serve] function is the programmatic equivalent
of the `mkdocs serve` command. It blocks until the server is shut down
(Ctrl+C or SIGTERM):

```python
import mkdocs

mkdocs.serve(
    config_file="mkdocs.yml",
    dev_addr="127.0.0.1:8000",
    livereload=True,
    watch=["../shared-assets"],
)
```

## Behavior notes

*   Errors and warnings are reported through the standard Python `logging`
    module using the `mkdocs` logger, exactly as with the command line tool.
    In `strict` mode, warnings abort the build.
*   Plugin startup and shutdown events are fired automatically around the
    build, so plugin behavior matches `mkdocs build` / `mkdocs serve`.
*   For anything not covered here, the `mkdocs build` and `mkdocs serve`
    command line options map directly to the keyword arguments of
    `mkdocs.build()` and `mkdocs.serve()`. See the API reference for the
    complete signatures.
