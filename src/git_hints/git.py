# `git.py` -- Run Git and inspect a repository
# ============================================
#
# Every Git process this tool starts goes through this module. Inspection
# commands pass their arguments as a list with `shell=False` and `check=False`;
# each caller interprets the exit code according to that command's documented
# meaning, since many expected outcomes (such as `git diff --quiet` reporting
# changes) use a nonzero code. An exit code that the documentation doesn't
# predict raises `InspectionError`, which suppresses the hints depending on
# that command and makes `git-hints` report the failure and exit nonzero.
#
# The `Repo` class memoizes each command's result, since several hints share
# the same facts (for example, whether unmerged paths exist) and every Git
# process costs tens of milliseconds, particularly on Windows. For the same
# reason, callers may evaluate hints in parallel threads; `Repo.run` lets a
# thread wait for a command another thread already started instead of running
# it twice.
#
# Imports
# -------
#
# ### Standard library
import os
import posixpath
import subprocess
import threading
from collections.abc import Collection, Sequence
from concurrent.futures import Future
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Literal

# Running Git
# -----------


# The outcome of one Git command.
@dataclass(frozen=True)
class GitResult:
    # The arguments passed to Git, excluding the leading `git`.
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


# Git could not be started, so no Git exit code or repository condition is
# available.
class GitLaunchError(Exception):
    pass


# An inspection command produced an exit code its documentation doesn't
# predict, or output showing that the repository is damaged or unreadable.
class InspectionError(Exception):
    def __init__(
        self,
        # The command which exposed the problem.
        result: GitResult,
        # What the problem means; by default, Git's error message.
        message: str | None = None,
    ) -> None:
        command = " ".join(["git", *result.args])
        detail = message or result.stderr.strip() or "no error message"
        super().__init__(
            f"`{command}` exited with code {result.returncode}: {detail}"
        )
        self.result = result


# Git writes paths as raw bytes; decode them as UTF-8 regardless of the
# locale, replacing undecodable bytes rather than failing.
def decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


# The environment for inspection commands.
#
# * `GIT_OPTIONAL_LOCKS=0` keeps `git status` from refreshing and rewriting
#   the index, so inspection never contends for `index.lock` with a Git
#   command the user is running.
# * `LC_ALL=C` keeps the few diagnostics that inspection matches (such as
#   "not a git repository") in English.
def inspection_env() -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"
    return env


# Run an inspection command. Standard input is closed, so no command can wait
# for input.
def run_git(
    # The arguments to pass to Git, excluding the leading `git`.
    args: Sequence[str],
    # The directory to run in; `None` uses the current directory.
    cwd: Path | None = None,
) -> GitResult:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=inspection_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            shell=False,
            check=False,
        )
    except OSError as error:
        raise GitLaunchError(f"Could not launch Git: {error}") from error
    return GitResult(
        tuple(args),
        completed.returncode,
        decode(completed.stdout),
        decode(completed.stderr),
    )


# Split NUL-delimited output (from a `-z` option) into records.
def split_nul(output: str) -> list[str]:
    return [record for record in output.split("\0") if record]


# Repository facts
# ----------------
#
# The upstream state reported by `git status --porcelain=v2 --branch`.
@dataclass(frozen=True)
class BranchStatus:
    # The upstream's short name, such as `origin/main`, or `None` when no
    # upstream is configured.
    upstream: str | None
    # Commit counts relative to the upstream as of the last fetch; both are
    # `None` when Git omits the `# branch.ab` line, which happens when there
    # is no upstream or the upstream ref doesn't exist.
    ahead: int | None
    behind: int | None


# The operations Git can leave paused or in progress. See Operation-in-progress
# protection in the specification.
@dataclass(frozen=True)
class Operations:
    merge: bool
    # A rebase: the `rebase-merge` directory, or a `rebase-apply` directory
    # which isn't a `git am` session.
    rebase: bool
    # A `git am` session, which also uses `rebase-apply`. This tool doesn't
    # explain it, but must not give advice that would interfere with it.
    am: bool
    cherry_pick: bool
    revert: bool
    bisect: bool

    # The operation `operation-in-progress` explains. A rebase that stops on a
    # conflict may also record `CHERRY_PICK_HEAD`, so check it first.
    @property
    def paused(self) -> str | None:
        if self.rebase:
            return "rebase"
        if self.merge:
            return "merge"
        if self.cherry_pick:
            return "cherry-pick"
        if self.revert:
            return "revert"
        return None

    # True when `rebase-merge` or `rebase-apply` exists, for any reason.
    @property
    def rebase_dir_exists(self) -> bool:
        return self.rebase or self.am

    # True for any operation that combines commits.
    @property
    def combining(self) -> bool:
        return self.paused is not None or self.am


# Where `git rev-parse --is-inside-work-tree` places the current directory.
WorkTree = Literal["inside", "outside", "not-a-repo"]


# Facts about the repository containing a directory, each computed on first
# use. Paths that Git reports relative to the repository root are converted
# for display by `display_path`.
class Repo:
    def __init__(
        self,
        # The directory to inspect; `None` uses the current directory.
        cwd: Path | None = None,
    ) -> None:
        self.cwd = cwd
        self._results: dict[tuple[str, ...], Future[GitResult]] = {}
        self._results_lock = threading.Lock()

    # ### Running commands

    # Run an inspection command, reusing an earlier (or in-progress) result for
    # identical arguments. The thread which first requests a command runs it.
    def run(self, *args: str) -> GitResult:
        with self._results_lock:
            future = self._results.get(args)
            is_runner = future is None
            if future is None:
                future = self._results[args] = Future()
        if is_runner:
            # Hand every exception, even `KeyboardInterrupt`, to the threads
            # waiting on this command; otherwise they would wait forever.
            try:
                future.set_result(run_git(args, self.cwd))
            except BaseException as error:  # noqa: BLE001
                future.set_exception(error)
        return future.result()

    # Run an inspection command, raising `InspectionError` unless its exit
    # code is one of `ok`.
    def check(self, *args: str, ok: Collection[int] = (0,)) -> GitResult:
        result = self.run(*args)
        if result.returncode not in ok:
            raise InspectionError(result)
        return result

    # Run a command which exits 1 to mean "yes" and 0 to mean "no", such as
    # `git diff --quiet`.
    def flag(self, *args: str) -> bool:
        return self.check(*args, ok=(0, 1)).returncode == 1

    # Return the value of a configuration key, or `None` when it's unset (exit
    # code 1).
    def config(self, key: str) -> str | None:
        result = self.check("config", "--get", key, ok=(0, 1))
        return result.stdout.rstrip("\n") if result.returncode == 0 else None

    # Return every value of a multi-valued configuration key.
    def config_all(self, key: str) -> list[str]:
        result = self.check("config", "--get-all", key, ok=(0, 1))
        return result.stdout.splitlines() if result.returncode == 0 else []

    # Return absolute paths for Git-internal files, which may live outside
    # `.git/` in linked worktrees or when the Git directory is elsewhere.
    def git_paths(self, *names: str) -> list[Path]:
        args = ["rev-parse", "--path-format=absolute"]
        for name in names:
            args += ["--git-path", name]
        lines = self.check(*args).stdout.splitlines()
        if len(lines) != len(names):
            raise InspectionError(self.run(*args))
        return [Path(line) for line in lines]

    # Return true when a ref (such as `MERGE_HEAD`) resolves.
    def ref_exists(self, ref: str) -> bool:
        return (
            self.check(
                "rev-parse", "--verify", "--quiet", ref, ok=(0, 1)
            ).returncode
            == 0
        )

    # ### Location

    # Exit code 0 reports `true` or `false`; Git exits 128 outside any
    # repository. Other failures, such as a repository with dubious ownership,
    # also exit 128, so recognize "not a repository" by its message.
    @cached_property
    def work_tree(self) -> WorkTree:
        result = self.run("rev-parse", "--is-inside-work-tree")
        if result.returncode == 0:
            if result.stdout.strip() == "true":
                return "inside"
            if result.stdout.strip() == "false":
                return "outside"
        elif (
            result.returncode == 128
            and "not a git repository" in result.stderr.lower()
        ):
            return "not-a-repo"
        raise InspectionError(result)

    # The current directory relative to the repository root, such as `src/`;
    # empty at the root.
    @cached_property
    def prefix(self) -> str:
        return self.check("rev-parse", "--show-prefix").stdout.strip()

    # Convert a path relative to the repository root, as most Git commands
    # report it, to one relative to the current directory, which is what the
    # user types.
    def display_path(self, root_relative: str) -> str:
        if not self.prefix:
            return root_relative
        return posixpath.relpath(root_relative, self.prefix.rstrip("/"))

    # ### Branches and HEAD

    # The current branch's short name, or `None` when HEAD is detached. An
    # unborn branch (one with no commits) still has a name.
    @cached_property
    def current_branch(self) -> str | None:
        result = self.check(
            "symbolic-ref", "--quiet", "--short", "HEAD", ok=(0, 1)
        )
        return result.stdout.strip() if result.returncode == 0 else None

    # The commit ID at HEAD, or `None` when HEAD doesn't resolve (for example,
    # on a branch with no commits).
    @cached_property
    def head_commit(self) -> str | None:
        result = self.check(
            "rev-parse", "--verify", "--quiet", "HEAD", ok=(0, 1)
        )
        return result.stdout.strip() if result.returncode == 0 else None

    @cached_property
    def branch_status(self) -> BranchStatus:
        # Skip the untracked-file scan, which this doesn't need and which is
        # slow in large repositories.
        result = self.check(
            "status", "--porcelain=v2", "--branch", "--untracked-files=no"
        )
        upstream = ahead = behind = None
        for line in result.stdout.splitlines():
            if line.startswith("# branch.upstream "):
                upstream = line.removeprefix("# branch.upstream ")
            elif line.startswith("# branch.ab "):
                ahead_text, behind_text = line.split()[2:4]
                ahead = int(ahead_text.lstrip("+"))
                behind = int(behind_text.lstrip("-"))
        return BranchStatus(upstream, ahead, behind)

    @cached_property
    def remotes(self) -> list[str]:
        return self.check("remote").stdout.split()

    # ### Changes

    # Paths with unmerged index entries, relative to the repository root.
    @cached_property
    def unmerged_paths(self) -> list[str]:
        output = self.check(
            "diff", "--name-only", "--diff-filter=U", "-z"
        ).stdout
        return list(dict.fromkeys(split_nul(output)))

    # Unstaged edits to tracked files.
    @cached_property
    def has_unstaged_changes(self) -> bool:
        return self.flag("diff", "--quiet")

    # Staged changes, including staged files on a branch with no commits.
    @cached_property
    def has_staged_changes(self) -> bool:
        return self.flag("diff", "--cached", "--quiet")

    # ### Operations

    @cached_property
    def operations(self) -> Operations:
        rebase_merge, rebase_apply, bisect_start = self.git_paths(
            "rebase-merge", "rebase-apply", "BISECT_START"
        )
        am = rebase_apply.is_dir() and (rebase_apply / "applying").exists()
        return Operations(
            merge=self.ref_exists("MERGE_HEAD"),
            rebase=rebase_merge.is_dir() or (rebase_apply.is_dir() and not am),
            am=am,
            cherry_pick=self.ref_exists("CHERRY_PICK_HEAD"),
            revert=self.ref_exists("REVERT_HEAD"),
            bisect=bisect_start.exists(),
        )
