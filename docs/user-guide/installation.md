# MkDocs Installation

A detailed guide.

---

## Requirements

MkDocs requires a recent version of [Python] and the Python package
manager, [pip], to be installed on your system.

You can check if you already have these installed from the command line:

```console
$ python --version
Python 3.12.0
$ pip --version
pip 24.2 from /usr/local/lib/python3.12/site-packages/pip (python 3.12)
```

If you already have those packages installed, you may skip down to [Installing
MkDocs](#installing-mkdocs).

### Installing Python

Install [Python] using your package manager of choice, or by downloading an
installer appropriate for your system from [python.org] and running it.

> NOTE:
> If you are installing Python on Windows, be sure to check the box to have
> Python added to your PATH if the installer offers such an option (it's
> normally off by default).
>
> ![Add Python to PATH](../img/win-py-install.png)

### Installing pip

If you're using a recent version of Python, the Python package manager, [pip],
is most likely installed by default. However, you may need to upgrade pip to the
lasted version:

```bash
pip install --upgrade pip
```

If you need to install pip for the first time, download [get-pip.py].
Then run the following command to install it:

```bash
python get-pip.py
```

## Installing MkDocs

Install the `mkdocs-ng` package using pip:

```bash
pip install mkdocs-ng
```

You should now have the `mkdocs` command installed on your system. Run `mkdocs
--version` to check that everything worked okay.

```console
$ mkdocs --version
mkdocs, version 1.7.0 from /usr/local/lib/python3.12/site-packages/mkdocs (Python 3.12)
```

> NOTE:
> If you would like manpages installed for MkDocs, the [click-man] tool can
> generate and install them for you. Simply run the following two commands:
>
> ```bash
> pip install click-man
> click-man --target path/to/man/pages mkdocs
> ```
>
> See the [click-man documentation] for an explanation of why manpages are
> not automatically generated and installed by pip.
<!-- -->
> NOTE:
> If you are using Windows, some of the above commands may not work
> out-of-the-box.
>
> A quick solution may be to preface every Python command with `python -m`
> like this:
>
> ```bash
> python -m pip install mkdocs-ng
> python -m mkdocs
> ```
>
> For a more permanent solution, you may need to edit your `PATH` environment
> variable to include the `Scripts` directory of your Python installation.
> Recent versions of Python include a script to do this for you. Navigate to
> your Python installation directory (for example `C:\Python312\`), open the
> `Tools`, then `Scripts` folder, and run the `win_add2path.py` file by double
> clicking on it. Alternatively, you can download the [script][a2p] and run it
> (`python win_add2path.py`).

## Installing plugins and themes

Almost every third-party plugin and theme, including Material for MkDocs,
depends on the `mkdocs` package. MkDocs NG provides the same `mkdocs` module
and command, but it is published as `mkdocs-ng`, so installers don't know that
it already satisfies that dependency. They install the upstream `mkdocs`
package as well:

```console
$ pip install mkdocs-ng mkdocs-material
$ pip list | grep mkdocs
mkdocs                     1.6.1
mkdocs-get-deps            0.2.2
mkdocs-material            9.7.7
mkdocs-material-extensions 1.3.1
mkdocs-ng                  1.8.0
```

Both packages install the same `mkdocs/` files, so whichever is installed last
wins, and `pip uninstall mkdocs` deletes the `mkdocs` command and most of MkDocs
NG along with it. Run `mkdocs --version` to see which one you are using: a 1.6.x
version means the upstream files have replaced MkDocs NG's. When MkDocs NG's
files are in place but the upstream package is still installed, MkDocs NG (2.0.0
and newer) prints a warning with the commands to repair the environment. The
warning is shown before the build starts, so it doesn't fail `strict` builds.

To keep the upstream package out, use one of the following approaches.

### With uv (recommended)

[uv] can drop the `mkdocs` dependency from all plugins and themes. In a uv
project, add an override with an environment marker that never matches to your
`pyproject.toml`:

```toml
[project]
name = "my-docs"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "mkdocs-ng",
    "mkdocs-material",
]

[tool.uv]
# Plugins and themes depend on "mkdocs"; mkdocs-ng already provides it.
override-dependencies = ["mkdocs; sys_platform == 'never'"]
```

Then install and build as usual with `uv sync` and `uv run mkdocs build`. The
override also applies to plugins you add later with `uv add`.

With uv 0.9.8 or newer, `exclude-dependencies = ["mkdocs"]` in the `[tool.uv]`
table does the same. Older versions of uv ignore that setting (with a warning)
and install the upstream package, while `override-dependencies` works in all
recent versions.

If you install from a requirements file, or with `uvx` or `uv tool`, put the
same line in an overrides file and pass it with `--overrides`:

```bash
echo "mkdocs; sys_platform == 'never'" > overrides.txt
```

```bash
uv pip install -r requirements.txt --overrides overrides.txt
```

```bash
uvx --from mkdocs-ng --with mkdocs-material --overrides overrides.txt mkdocs build
```

```bash
uv tool install mkdocs-ng --with mkdocs-material --overrides overrides.txt
```

### With pip

pip can't skip a dependency of another package. Install everything as usual,
then remove the upstream package and reinstall MkDocs NG:

```bash
pip install mkdocs-ng mkdocs-material
pip uninstall -y mkdocs
pip install --force-reinstall --no-deps mkdocs-ng
```

`pip uninstall -y mkdocs` also deletes the files that both packages share,
which is why MkDocs NG has to be reinstalled afterwards. This approach has some
limitations:

*   Run the last two commands again after every `pip install` that adds or
    upgrades a plugin or theme. pip notices that their `mkdocs` dependency is
    missing and installs the upstream package again.
*   `pip check` reports a missing dependency for each plugin and theme, such as
    `mkdocs-material 9.7.7 requires mkdocs, which is not installed.` This is
    expected.
*   Don't skip the uninstall step. Reinstalling MkDocs NG on its own restores its
    files, but leaves the upstream package registered, so a later
    `pip uninstall mkdocs` breaks MkDocs NG again.

In CI, run the same commands after installing your requirements. If your
requirements file pins `mkdocs-ng`, use the same version in the last command:

```bash
pip install -r requirements.txt
pip uninstall -y mkdocs
pip install --force-reinstall --no-deps "mkdocs-ng==1.8.0"
```

### Switching from upstream MkDocs

If upstream MkDocs is already installed, with or without plugins, install MkDocs
NG, then remove the upstream package and reinstall MkDocs NG:

```bash
pip install -U mkdocs-ng
pip uninstall -y mkdocs
pip install --force-reinstall --no-deps mkdocs-ng
```

`mkdocs --version` should now report MkDocs NG's version. Your configuration,
plugins and themes keep working unchanged. The limitations of the [pip
approach](#with-pip) apply from then on, or switch to [uv](#with-uv-recommended)
and replace `mkdocs` with `mkdocs-ng` in your dependencies.

[uv]: https://docs.astral.sh/uv/
[Python]: https://www.python.org/
[python.org]: https://www.python.org/downloads/
[pip]: https://pip.readthedocs.io/en/stable/installing/
[get-pip.py]: https://bootstrap.pypa.io/get-pip.py
[click-man]: https://github.com/click-contrib/click-man
[click-man documentation]: https://github.com/click-contrib/click-man#automatic-man-page-installation-with-setuptools-and-pip
[a2p]: https://github.com/python/cpython/blob/master/Tools/scripts/win_add2path.py
