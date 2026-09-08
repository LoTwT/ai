"""Run with: python3 -m unittest discover -s tests -v

These are documentation-contract and extracted-snippet regressions, not an LLM
or GitHub end-to-end evaluator. Git writes use disposable repos and a synthetic
HOME; no host Git config, credentials, hooks, or remote services are consumed.
For a historical snapshot: python3 tests/test_git_workflow_skills.py --source-root PATH
"""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
GIT = shutil.which("git")


def document(relative):
    return (SOURCE / "skills/git-workflow" / relative).read_text(encoding="utf8")


class GitWorkflowRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="git-workflow-regression-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.identity = {
            "GIT_AUTHOR_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        }
        # Deliberately not os.environ.copy(): tests must not use host policy.
        self.env = {
            "PATH": os.defpath,
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / "xdg"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            **self.identity,
        }

    def git(self, cwd, *args, env=None, check=True, data=None):
        if GIT is None:
            self.fail("Git is required for the isolated behavior regressions")
        return subprocess.run(
            [GIT, *args], cwd=cwd, env=self.env if env is None else env,
            input=data, capture_output=True, check=check,
        )

    def repo(self, name):
        repo = self.root / name
        repo.mkdir()
        self.git(repo, "init", "-b", "main")
        return repo

    def stage(self, repo, name="file.txt"):
        (repo / name).write_text("fixture\n", encoding="utf8")
        self.git(repo, "--literal-pathspecs", "add", "--", name)

    def test_environment_example_preserves_global_hook(self):
        text = document("git-commit/references/safe-execution.md")
        block = text.split("env = {", 1)[1].split("\n}", 1)[0]
        for key in self.identity:
            self.assertIn(key, block)
        # Interpret only the documented env-copy operation; this is pseudocode,
        # not a claim that the complete skill has been executed.
        execution_env = self.env.copy() if "...current_environment" in block else {}
        execution_env.update(self.identity)
        hooks = self.root / "hooks"
        hooks.mkdir()
        hook = hooks / "pre-commit"
        hook.write_text("#!/bin/sh\necho FIXTURE_REQUIRED_HOOK >&2\nexit 73\n")
        hook.chmod(0o755)
        (self.home / ".gitconfig").write_text(f"[core]\n\thooksPath = {hooks}\n")
        repo = self.repo("hook-test")
        self.stage(repo)
        preflight = self.git(repo, "config", "--get", "core.hooksPath")
        self.assertEqual(preflight.stdout.rstrip(b"\n"), os.fsencode(hooks))
        result = self.git(
            repo, "-C", str(repo), "-c", "core.fsmonitor=false",
            "commit", "--cleanup=verbatim", "--file", "-",
            env=execution_env, check=False, data=b"fixture: hook rejection\n",
        )
        self.assertIn(b"FIXTURE_REQUIRED_HOOK", result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(self.git(repo, "rev-parse", "--verify", "HEAD", check=False).returncode, 0)

    def test_extracted_shell_root_transport_preserves_bytes(self):
        text = document("git-commit/references/safe-execution.md")
        snippet = text.split("```bash\n", 1)[1].split("author_name=", 1)[0]
        self.assertIn("<exact frozen repository root>", snippet)
        for suffix in ("ordinary", "trailing\n", "trailing\n\n", "quote'$(printf INJECTED)`printf OTHER`", "dot."):
            with self.subTest(path=repr(suffix)):
                repo = self.repo(suffix)
                script = snippet.replace("<exact frozen repository root>", str(repo))
                script += "printf '%s' \"$repository_root\"\n"
                result = subprocess.run(
                    ["/bin/bash", "--noprofile", "--norc", "-c", script], cwd=self.root, env=self.env,
                    capture_output=True, check=True,
                )
                self.assertEqual(result.stdout, os.fsencode(repo))

    def test_literal_pathspec_positive_and_ablation_controls(self):
        text = document("git-commit/references/exact-staging.md")
        self.assertIn('"--literal-pathspecs", "add", "--"', text)
        for literal in (True, False):
            with self.subTest(literal=literal):
                repo = self.repo("literal-" + str(literal))
                (repo / "a*.txt").write_text("selected\n")
                (repo / "abc.txt").write_text("unrelated\n")
                args = ["--literal-pathspecs"] if literal else []
                self.git(repo, *args, "add", "--", "a*.txt")
                staged = self.git(repo, "diff", "--cached", "--name-only", "-z").stdout.split(b"\0")[:-1]
                expected = [b"a*.txt"] if literal else [b"a*.txt", b"abc.txt"]
                self.assertEqual(staged, expected)

    def test_cleanup_contract_excludes_nontracking_destinations(self):
        text = document("git-cleanup/SKILL.md")
        self.assertIn("### Prune Safety Gate", text)
        self.assertIn("Require every positive destination", text)
        self.assertIn("refs/remotes/<configured-remote>/", text)
        self.assertIn("`refs/heads/`, `refs/tags/`, another remote's namespace", text)
        self.assertIn("no overlap with `keep`, `confirm-required`", text)
        self.assertIn("If the set cannot be established completely, retain it", text)
        self.assertIn("`fetch.pruneTags` or `remote.<name>.pruneTags`", text)
        self.assertIn("re-read the configuration, candidate refs/OIDs", text)
        self.assertNotIn("only when that remote's refspec maps no tags", text)

    def test_git_prune_counterexample_without_tag_mapping(self):
        # Real Git mechanism fixture, not a reimplementation of the skill gate.
        remote = self.root / "origin.git"
        remote.mkdir()
        self.git(remote, "init", "--bare", "-b", "main")
        seed = self.repo("seed")
        self.stage(seed)
        self.git(seed, "commit", "-m", "fixture: base")
        self.git(seed, "remote", "add", "origin", str(remote))
        self.git(seed, "push", "origin", "main:refs/heads/main")
        for namespace in ("refs/remotes/origin/", "refs/heads/"):
            with self.subTest(namespace=namespace):
                repo = self.root / ("normal" if "remotes" in namespace else "unsafe")
                self.git(self.root, "clone", str(remote), str(repo))
                self.git(repo, "switch", "-c", "local-only")
                self.stage(repo, "unpublished.txt")
                self.git(repo, "commit", "-m", "fixture: unpublished")
                self.git(repo, "switch", "main")
                self.git(repo, "config", "remote.origin.fetch", "+refs/heads/*:" + namespace + "*")
                dry = self.git(repo, "remote", "prune", "--dry-run", "origin")
                self.git(repo, "remote", "prune", "origin")
                survived = self.git(repo, "show-ref", "--verify", "refs/heads/local-only", check=False).returncode == 0
                self.assertEqual(survived, namespace != "refs/heads/")
                if not survived:
                    self.assertIn(b"refs/heads/local-only", dry.stdout)

    def test_setup_explicit_configured_update_contract(self):
        text = document("git-workflow-setup/SKILL.md")
        self.assertIn("plus only those `configured` sections the current request explicitly selects for an update", text)
        self.assertIn("A generic initialize/sync request never selects", text)
        self.assertIn("Keep every unselected or unconfirmed `configured` section byte-for-byte unchanged", text)
        self.assertIn("Changed replacement bytes require a new confirmation", text)
        self.assertNotIn("Never touch a `configured` section", text)
        self.assertIn("A fixed section with drift is not also `configured`", text)
        guide = document("git-workflow-setup/references/config-guide.md")
        self.assertIn("Keep configured sections byte-for-byte unchanged", guide)

    def test_family_relative_markdown_links_resolve(self):
        family = SOURCE / "skills/git-workflow"
        count = 0
        for path in family.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf8")):
                if target.startswith(("http:", "https:", "#")):
                    continue
                count += 1
                self.assertTrue((path.parent / target.split("#", 1)[0]).resolve().is_file(), (path, target))
        self.assertGreater(count, 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=SOURCE)
    args, rest = parser.parse_known_args()
    SOURCE = args.source_root.resolve()
    unittest.main(argv=[__file__, *rest])
