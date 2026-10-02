import unittest
from unittest import mock

from ghp_import import GhpError  # type: ignore

from mkdocs import __version__
from mkdocs.commands import gh_deploy
from mkdocs.exceptions import Abort
from mkdocs.tests.base import load_config, tempdir


class TestGitHubDeploy(unittest.TestCase):
    @mock.patch("subprocess.Popen")
    def test_is_cwd_git_repo(self, mock_popeno):
        mock_popeno().wait.return_value = 0

        self.assertTrue(gh_deploy._is_cwd_git_repo())

    @mock.patch("subprocess.Popen")
    def test_is_cwd_not_git_repo(self, mock_popeno):
        mock_popeno().wait.return_value = 1

        self.assertFalse(gh_deploy._is_cwd_git_repo())

    @mock.patch("subprocess.Popen")
    def test_get_current_sha(self, mock_popeno):
        mock_popeno().communicate.return_value = (b"6d98394\n", b"")

        self.assertEqual(gh_deploy._get_current_sha("."), "6d98394")

    @mock.patch("subprocess.Popen")
    def test_get_remote_url_ssh(self, mock_popeno):
        mock_popeno().communicate.return_value = (
            b"git@github.com:mkdocs/mkdocs.git\n",
            b"",
        )

        expected = ("git@", "mkdocs/mkdocs.git")
        self.assertEqual(expected, gh_deploy._get_remote_url("origin"))

    @mock.patch("subprocess.Popen")
    def test_get_remote_url_http(self, mock_popeno):
        mock_popeno().communicate.return_value = (
            b"https://github.com/mkdocs-ng/mkdocs.git\n",
            b"",
        )

        expected = ("https://", "mkdocs-ng/mkdocs.git")
        self.assertEqual(expected, gh_deploy._get_remote_url("origin"))

    @mock.patch("subprocess.Popen")
    def test_get_remote_url_enterprise(self, mock_popeno):
        mock_popeno().communicate.return_value = (
            b"https://notgh.com/mkdocs/mkdocs.git\n",
            b"",
        )

        expected = (None, None)
        self.assertEqual(expected, gh_deploy._get_remote_url("origin"))

    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=True)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="shashas")
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_remote_url",
        mock.Mock(return_value=(None, None)),
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version", mock.Mock())
    @mock.patch("ghp_import.ghp_import", mock.Mock())
    def test_deploy(self):
        config = load_config(
            remote_branch="test",
        )
        gh_deploy.gh_deploy(config)

    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=True)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="shashas")
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_remote_url",
        mock.Mock(return_value=(None, None)),
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version", mock.Mock())
    @mock.patch("ghp_import.ghp_import", mock.Mock())
    @mock.patch("os.path.isfile", mock.Mock(return_value=False))
    def test_deploy_no_cname(self):
        config = load_config(
            remote_branch="test",
        )
        gh_deploy.gh_deploy(config)

    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=True)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="shashas")
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_remote_url",
        mock.Mock(return_value=("git@", "mkdocs/mkdocs.git")),
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version", mock.Mock())
    @mock.patch("ghp_import.ghp_import", mock.Mock())
    def test_deploy_hostname(self):
        config = load_config(
            remote_branch="test",
        )
        gh_deploy.gh_deploy(config)

    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=True)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="shashas")
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_remote_url",
        mock.Mock(return_value=(None, None)),
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version")
    @mock.patch("ghp_import.ghp_import", mock.Mock())
    def test_deploy_ignore_version_default(self, check_version):
        config = load_config(
            remote_branch="test",
        )
        gh_deploy.gh_deploy(config)
        check_version.assert_called_once()

    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=True)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="shashas")
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_remote_url",
        mock.Mock(return_value=(None, None)),
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version")
    @mock.patch("ghp_import.ghp_import", mock.Mock())
    def test_deploy_ignore_version(self, check_version):
        config = load_config(
            remote_branch="test",
        )
        gh_deploy.gh_deploy(config, ignore_version=True)
        check_version.assert_not_called()

    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=True)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="shashas")
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version", mock.Mock())
    @mock.patch(
        "ghp_import.ghp_import", mock.Mock(side_effect=GhpError("TestError123"))
    )
    def test_deploy_error(self):
        config = load_config(
            remote_branch="test",
        )

        with self.assertLogs("mkdocs", level="ERROR") as cm:
            with self.assertRaises(Abort):
                gh_deploy.gh_deploy(config)
        self.assertEqual(
            cm.output,
            [
                (
                    "ERROR:mkdocs.commands.gh_deploy:Failed to deploy to GitHub with error: \n"
                    "TestError123"
                )
            ],
        )

    @mock.patch("subprocess.Popen", side_effect=FileNotFoundError)
    def test_is_cwd_git_repo_without_git(self, mock_popen):
        with self.assertLogs("mkdocs", level="ERROR") as cm:
            with self.assertRaisesRegex(Abort, "Deployment Aborted!"):
                gh_deploy._is_cwd_git_repo()
        self.assertEqual(
            cm.output,
            [
                (
                    "ERROR:mkdocs.commands.gh_deploy:"
                    "Could not find git - is it installed and on your path?"
                )
            ],
        )

    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=False)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="")
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version", mock.Mock())
    @mock.patch(
        "ghp_import.ghp_import",
        mock.Mock(side_effect=GhpError("not a git repository")),
    )
    def test_deploy_outside_git_repo(self):
        config = load_config(remote_branch="test")

        with self.assertLogs("mkdocs", level="ERROR") as cm:
            with self.assertRaises(Abort):
                gh_deploy.gh_deploy(config)
        self.assertEqual(
            cm.output,
            [
                (
                    "ERROR:mkdocs.commands.gh_deploy:"
                    "Cannot deploy - this directory does not appear to be a git repository"
                ),
                (
                    "ERROR:mkdocs.commands.gh_deploy:"
                    "Failed to deploy to GitHub with error: \nnot a git repository"
                ),
            ],
        )

    @tempdir(files={"CNAME": "docs.example.com\n"})
    @mock.patch(
        "mkdocs.commands.gh_deploy._is_cwd_git_repo", mock.Mock(return_value=True)
    )
    @mock.patch(
        "mkdocs.commands.gh_deploy._get_current_sha", mock.Mock(return_value="shashas")
    )
    @mock.patch("mkdocs.commands.gh_deploy._check_version", mock.Mock())
    @mock.patch("mkdocs.commands.gh_deploy._get_remote_url")
    @mock.patch("ghp_import.ghp_import")
    def test_deploy_with_cname(self, site_dir, mock_ghp_import, mock_get_remote_url):
        config = load_config(site_dir=site_dir)

        with self.assertLogs("mkdocs", level="INFO") as cm:
            gh_deploy.gh_deploy(config, message="Docs for {sha} ({version})")

        mock_ghp_import.assert_called_once_with(
            site_dir,
            mesg=f"Docs for shashas ({__version__})",
            remote="origin",
            branch="gh-pages",
            push=True,
            force=False,
            use_shell=False,
            no_history=False,
            nojekyll=True,
        )
        # With a CNAME file, the URL is not derived from the git remote.
        mock_get_remote_url.assert_not_called()
        self.assertEqual(
            cm.output[1:],
            [
                (
                    "INFO:mkdocs.commands.gh_deploy:Based on your CNAME file, your "
                    "documentation should be available shortly at: http://docs.example.com"
                ),
                (
                    "INFO:mkdocs.commands.gh_deploy:NOTE: Your DNS records must be "
                    "configured appropriately for your CNAME URL to work."
                ),
            ],
        )


class TestGitHubDeployLogs(unittest.TestCase):
    @mock.patch("subprocess.Popen")
    def test_mkdocs_newer(self, mock_popeno):
        mock_popeno().communicate.return_value = (
            b"Deployed 12345678 with MkDocs version: 0.1.2\n",
            b"",
        )

        with self.assertLogs("mkdocs") as cm:
            gh_deploy._check_version("gh-pages")
        self.assertEqual(
            "\n".join(cm.output),
            f"INFO:mkdocs.commands.gh_deploy:Previous deployment was done with MkDocs "
            f"version 0.1.2; you are deploying with a newer version ({__version__})",
        )

    @mock.patch("subprocess.Popen")
    def test_mkdocs_older(self, mock_popeno):
        mock_popeno().communicate.return_value = (
            b"Deployed 12345678 with MkDocs version: 10.1.2\n",
            b"",
        )

        with self.assertLogs("mkdocs", level="ERROR") as cm:
            with self.assertRaises(Abort):
                gh_deploy._check_version("gh-pages")
        self.assertEqual(
            "\n".join(cm.output),
            f"ERROR:mkdocs.commands.gh_deploy:Deployment terminated: Previous deployment was made with "
            f"MkDocs version 10.1.2; you are attempting to deploy with an older version ({__version__})."
            f" Use --ignore-version to deploy anyway.",
        )

    @mock.patch("subprocess.Popen")
    def test_version_unknown(self, mock_popeno):
        mock_popeno().communicate.return_value = (b"No version specified\n", b"")

        with self.assertLogs("mkdocs") as cm:
            gh_deploy._check_version("gh-pages")
        self.assertEqual(
            "\n".join(cm.output),
            "WARNING:mkdocs.commands.gh_deploy:Version check skipped: No version specified in previous deployment.",
        )
