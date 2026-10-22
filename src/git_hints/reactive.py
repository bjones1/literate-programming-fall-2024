# `reactive.py` -- Explain a failed Git command
# =============================================
#
# `git-hints explain -- git <command>` runs the command once, with standard
# input and (normally) standard output connected to the terminal, so prompts,
# editors, and Git's own output behave as usual. Standard error is captured,
# shown after Git exits, and matched against the English diagnostics that
# reactive hints recognize; an unrecognized diagnostic produces no hint rather
# than a guess.
#
# Most reactive hints also inspect the repository after the command runs. When
# the command's global options point Git at another repository (`-C`,
# `--git-dir`, `--work-tree`, or `--bare`), inspecting the current directory
# would describe the wrong repository, so only hints which need nothing beyond
# the exit code and standard error are evaluated.
#
# Imports
# -------
#
# ### Standard library
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

# ### Local
from .git import GitLaunchError, InspectionError, Repo, decode
from .hint import (
    Command,
    Hint,
    Priority,
    Safety,
    code,
    git_with_paths,
    render_block,
    shell_quote,
    sort_hints,
    summarize,
)
from .proactive import Context, merge_conflicts

# Parsing the Git command
# -----------------------
#
# Git's global options which take a value as the following argument (rather
# than after `=`).
GLOBAL_OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--config-env",
    "--attr-source",
}
# Global options which select a repository other than the current directory's.
REDIRECTING_OPTIONS = {"-C", "--git-dir", "--work-tree", "--bare"}


@dataclass(frozen=True)
class GitCommand:
    # The complete argument list, starting with `git`.
    argv: Sequence[str]
    # The subcommand, such as `push`, or `None` when there is none.
    subcommand: str | None
    # The arguments following the subcommand.
    arguments: Sequence[str]
    # True when global options redirect Git to another repository.
    redirected: bool

    # The command as the user could type it again.
    @property
    def text(self) -> str:
        return " ".join(shell_quote(word) for word in self.argv)


def parse_command(argv: Sequence[str]) -> GitCommand:
    redirected = False
    index = 1
    while index < len(argv) and argv[index].startswith("-"):
        option = argv[index]
        if option.split("=", 1)[0] in REDIRECTING_OPTIONS:
            redirected = True
        if option in GLOBAL_OPTIONS_WITH_VALUE:
            index += 1
        index += 1
    if index >= len(argv):
        return GitCommand(argv, None, [], redirected)
    return GitCommand(argv, argv[index], argv[index + 1 :], redirected)


# Return a subcommand's positional arguments.
def positional_arguments(
    arguments: Sequence[str],
    # Options which take a value as the following argument.
    options_with_value: set[str],
) -> list[str]:
    positionals: list[str] = []
    words = iter(arguments)
    for word in words:
        if word == "--":
            positionals += words
            break
        if word.startswith("-") and word != "-":
            if word in options_with_value:
                next(words, None)
            continue
        positionals.append(word)
    return positionals


# True when a `git pull` replays local commits instead of merging; the last of
# conflicting options wins, as in Git.
def pull_rebases(arguments: Sequence[str]) -> bool:
    rebase = False
    for word in arguments:
        if word == "--":
            break
        if word in ("-r", "--rebase"):
            rebase = True
        elif word.startswith("--rebase="):
            rebase = word.split("=", 1)[1] not in ("false", "no", "off", "0")
        elif word == "--no-rebase":
            rebase = False
    return rebase


# Diagnostics
# -----------
#
# Match fragments rather than complete lines, which vary between Git versions.
#
# Tracked changes blocking a merge or checkout. Git lists the affected paths on
# the following lines, each indented by a tab. An untracked-file obstruction
# says "untracked working tree files" instead, so it doesn't match.
OVERWRITTEN = re.compile(
    r"local changes.*would be overwritten by", re.IGNORECASE
)

# One rejected ref per line, such as ` ! [rejected]  main -> main (fetch
# first)`. A hook rejection reads `[remote rejected]`, so it doesn't match.
REJECTED = re.compile(
    r"^\s*!\s+\[rejected\]\s+(?P<source>\S+)\s+->\s+(?P<destination>\S+)\s+"
    r"\((?P<reason>fetch first|non-fast-forward)\)",
    re.MULTILINE,
)

# `git pull` refusing to integrate diverged branches.
PULL_DIVERGED = (
    "Need to specify how to reconcile divergent branches",
    "Not possible to fast-forward",
)


# Return the paths whose tracked changes blocked the command, an empty list
# when the diagnostic names none reliably, or `None` when the diagnostic
# doesn't report tracked changes being overwritten.
def overwritten_paths(stderr: str) -> list[str] | None:
    lines = stderr.splitlines()
    for index, line in enumerate(lines):
        if OVERWRITTEN.search(line):
            paths = []
            for following in lines[index + 1 :]:
                if not following.startswith("\t"):
                    break
                paths.append(following[1:])
            return paths
    return None


# Reactive hints
# --------------
@dataclass(frozen=True)
class Failure:
    command: GitCommand
    returncode: int
    stderr: str
    # The repository the command ran in, or `None` when inspecting it doesn't
    # apply: the command was redirected or ran outside a working tree.
    repo: Repo | None

    def display_path(self, path: str) -> str:
        return self.repo.display_path(path) if self.repo else path


def reactive_merge_conflicts(failure: Failure) -> Hint | None:
    if failure.repo is None:
        return None
    return merge_conflicts(Context(failure.repo, fetched=False))


def pull_blocked_local_changes(failure: Failure) -> Hint | None:
    if failure.command.subcommand != "pull":
        return None
    paths = overwritten_paths(failure.stderr)
    if paths is None:
        return None
    # Git refuses to pull at all while conflicts remain; `merge-conflicts`
    # covers that.
    if failure.repo is not None and failure.repo.unmerged_paths:
        return None
    paths = [failure.display_path(path) for path in paths]
    text = (
        "The attempted [git pull]"
        "(https://git-scm.com/docs/git-pull#_description "
        '"Fetch and integrate changes into the current branch") was blocked '
        "because incoming changes would overwrite uncommitted tracked "
        "changes. Preserve your local work before retrying."
    )
    if paths:
        text += f" Affected files: {summarize(paths)}."
    text += (
        " Default stashing excludes untracked files. See "
        "[git stash](https://git-scm.com/docs/git-stash#_description "
        '"Temporarily save working-directory and index changes").'
    )
    add = (
        git_with_paths(["add"], paths[:5], separator=True)
        if paths
        else "git add -- <files>"
    )
    return Hint(
        id="pull-blocked-local-changes",
        priority=Priority.ERROR_BLOCKED,
        text=text,
        stage=(
            "Your working directory or staging area contains uncommitted "
            "tracked changes that incoming commits would overwrite."
        ),
        commands=(
            Command(
                "`git status`, `git diff`, and `git diff --cached`",
                "Git shows the uncommitted changes and the files they affect.",
            ),
            Command(
                f"To commit: {code(add)}, then "
                '`git commit -m "Save local changes"`',
                "The selected changes are saved in a local commit.",
            ),
            Command(
                'To stash: `git stash push -m "Save work before pull"`, then '
                "`git stash list`",
                "Tracked changes are saved and removed from the working "
                "directory and index; the list shows the saved entry.",
            ),
            Command(
                "After preserving the changes, retry: "
                + code(failure.command.text),
                "The pull proceeds. If you stashed, run `git stash apply` "
                "afterward, resolve any conflicts, and keep the stash until "
                "the restoration is verified.",
            ),
        ),
    )


# Push options which take a value as the following argument.
PUSH_OPTIONS_WITH_VALUE = {
    "-o",
    "--push-option",
    "--receive-pack",
    "--exec",
    "--repo",
}


# Return the remote a push went to: its explicit repository argument, or the
# configured push destination.
def push_remote(repo: Repo, command: GitCommand, branch: str | None) -> str:
    positionals = positional_arguments(
        command.arguments, PUSH_OPTIONS_WITH_VALUE
    )
    if positionals:
        return positionals[0]
    for argument in command.arguments:
        if argument.startswith("--repo="):
            return argument.removeprefix("--repo=")
    keys = ["remote.pushDefault"]
    if branch is not None:
        keys = [f"branch.{branch}.pushRemote", *keys, f"branch.{branch}.remote"]
    for key in keys:
        value = repo.config(key)
        if value:
            return value
    return "origin"


# Map a branch on a remote to its remote-tracking branch using the remote's
# fetch refspecs, such as `+refs/heads/*:refs/remotes/origin/*`. Return `None`
# when no refspec maps it.
def tracking_branch(repo: Repo, remote: str, destination: str) -> str | None:
    if remote not in repo.remotes:
        return None
    ref = (
        destination
        if destination.startswith("refs/")
        else f"refs/heads/{destination}"
    )
    for refspec in repo.config_all(f"remote.{remote}.fetch"):
        refspec = refspec.removeprefix("+")
        if refspec.startswith("^") or ":" not in refspec:
            continue
        source, target = refspec.split(":", 1)
        if "*" in source:
            prefix, suffix = source.split("*", 1)
            if (
                ref.startswith(prefix)
                and ref.endswith(suffix)
                and len(ref) >= len(prefix) + len(suffix)
            ):
                match = ref[len(prefix) : len(ref) - len(suffix)]
                return target.replace("*", match, 1).removeprefix(
                    "refs/remotes/"
                )
        elif source == ref:
            return target.removeprefix("refs/remotes/")
    return None


def push_rejected_non_fast_forward(failure: Failure) -> Hint | None:
    if failure.command.subcommand != "push":
        return None
    rejections = list(REJECTED.finditer(failure.stderr))
    if not rejections:
        return None
    repo = failure.repo
    branch = repo.current_branch if repo else None
    refs = [f"{r['source']} -> {r['destination']}" for r in rejections]
    text = (
        "Git rejected the "
        "[push](https://git-scm.com/docs/git-push#_note_about_fast_forwards "
        '"A non-fast-forward push would replace remote history") because the '
        "remote branch contains history missing from the branch being pushed. "
        f"Integrate that history before retrying. Rejected: {summarize(refs)}."
    )
    status = Command(
        "`git status`",
        "Git shows the current branch and the state of the working directory "
        "and staging area.",
    )
    # Find the rejection of the current branch, which the commands below can
    # integrate.
    current = None
    if repo is not None:
        sources = {"HEAD"}
        if branch is not None:
            sources |= {branch, f"refs/heads/{branch}"}
        current = next((r for r in rejections if r["source"] in sources), None)
    if current is None or repo is None:
        if repo is None:
            text += " Run the commands below in the repository you pushed from."
        else:
            rejected = rejections[0]["source"]
            text += (
                f" The rejected branch {code(rejected)} is not your current "
                f"branch{f' ({code(branch)})' if branch else ''}; switch to it "
                "before integrating its remote history."
            )
        commands = [status]
    else:
        remote = push_remote(repo, failure.command, branch)
        tracking = tracking_branch(repo, remote, current["destination"])
        if tracking is None:
            text += (
                " Replace the placeholders below with the remote and branch "
                "you pushed to."
            )
        fetch = (
            f"git fetch {shell_quote(remote)}"
            if tracking
            else "git fetch <remote>"
        )
        merge = (
            f"git merge {shell_quote(tracking)}"
            if tracking
            else "git merge <remote>/<branch>"
        )
        commands = [
            status,
            Command(
                code(fetch),
                "Git downloads the remote's new commits and updates the "
                "remote-tracking branch.",
            ),
            Command(
                code(merge)
                + ", resolving any conflicts, then retry "
                + code(failure.command.text),
                "The local branch incorporates the rejected destination's "
                "history, and the push can succeed if no other errors remain.",
            ),
        ]
    return Hint(
        id="push-rejected-non-fast-forward",
        priority=Priority.ERROR_BLOCKED,
        text=text,
        stage=(
            "The local and remote repositories have different branch "
            "histories that must be integrated before a normal push can "
            "succeed."
        ),
        commands=commands,
    )


def stash_local_changes(failure: Failure) -> Hint | None:
    repo = failure.repo
    if failure.command.subcommand not in ("merge", "switch") or repo is None:
        return None
    paths = overwritten_paths(failure.stderr)
    if paths is None or repo.unmerged_paths:
        return None
    paths = [repo.display_path(path) for path in paths]
    affected = f" Affected files: {summarize(paths)}." if paths else ""
    stash_link = (
        "[stash](https://git-scm.com/docs/git-stash#_description "
        '"Save working-directory and index changes temporarily")'
    )
    status = Command("`git status`", "Git shows the changes.")
    # Git can't stash on a branch with no commits.
    if repo.head_commit is None:
        text = (
            "Git blocked the operation because it would overwrite tracked "
            f"local changes.{affected} This branch has no commits yet, so a "
            f"{stash_link} cannot save them; back up the files first."
        )
        commands = [
            status,
            Command(
                "Copy the affected files to a folder outside this repository, "
                "then verify the copies",
                "The work has a separate backup.",
            ),
        ]
    else:
        text = (
            "Git blocked the operation because it would overwrite tracked "
            f"local changes.{affected} A {stash_link} can preserve those "
            "changes while you retry the operation. Default stashing excludes "
            "untracked files."
        )
        commands = [
            status,
            Command(
                '`git stash push -m "Save work before retrying"`, then '
                "`git stash list`",
                "Git saves the tracked changes and removes them from the "
                "working directory and index; the list shows the saved entry.",
            ),
            Command(
                f"Retry: {code(failure.command.text)}",
                "The blocked operation proceeds.",
            ),
            Command(
                "`git stash apply <stash>`, using the entry from "
                "`git stash list`",
                "Git restores the saved changes. Reapplying may cause "
                "conflicts; resolve them and keep the stash until the "
                "restoration is verified.",
            ),
        ]
    return Hint(
        id="stash-local-changes",
        priority=Priority.ERROR_BLOCKED,
        text=text,
        stage=(
            "The working tree or index contains tracked changes, and a "
            "`git merge` or `git switch` was blocked before it changed the "
            "repository state."
        ),
        commands=commands,
    )


REACTIVE_CHECKS: list[Callable[[Failure], Hint | None]] = [
    reactive_merge_conflicts,
    pull_blocked_local_changes,
    push_rejected_non_fast_forward,
    stash_local_changes,
]


# Repeated integration failures
# -----------------------------
#
# After five qualifying failures to integrate with the upstream branch, suggest
# `git pull --rebase`. Counts are kept per local branch, keyed by its full ref,
# in a JSON file under the Git directory (so that linked worktrees each have
# their own), along with the commit at HEAD: a new commit means the user has
# changed course, so the count starts over.
FAILURE_COUNTS_PATH = "git-hints/integration-failures.json"
FAILURE_THRESHOLD = 5


def rebase_after_repeated_integration_failures() -> Hint:
    return Hint(
        id="rebase-after-repeated-integration-failures",
        priority=Priority.ERROR_BLOCKED,
        text=(
            "After five qualifying failures to integrate with the upstream "
            "branch, replaying your local commits using "
            "[git pull --rebase](https://git-scm.com/docs/git-pull "
            '"Fetch upstream changes and replay local commits on top of '
            'them") may resolve the problem. Rebasing changes local commit '
            "IDs and may cause conflicts. Make sure your local work is "
            "committed or otherwise backed up before attempting it. See the "
            "[git rebase documentation](https://git-scm.com/docs/git-rebase "
            '"Replay commits on another base and resolve rebase conflicts").'
        ),
        stage=(
            "Your local repository contains commits that have not been "
            "incorporated into the upstream branch, while the upstream "
            "contains commits missing from your local branch."
        ),
        commands=(
            Command(
                "`git pull --rebase`",
                "The local branch contains the upstream commits followed by "
                "the replayed local commits and can be pushed if no other "
                "errors remain. If conflicts occur, resolve them and run "
                "`git rebase --continue`, or cancel with `git rebase --abort`.",
                Safety.CAUTION,
            ),
        ),
    )


# True for a push rejected as non-fast-forward, or a merging pull refused
# because the branches diverged.
def is_qualifying_failure(command: GitCommand, stderr: str) -> bool:
    if command.subcommand == "push":
        return "(fetch first)" in stderr or "(non-fast-forward)" in stderr
    if command.subcommand == "pull":
        return not pull_rebases(command.arguments) and any(
            fragment in stderr for fragment in PULL_DIVERGED
        )
    return False


# Read the stored counts; a missing or unreadable file means no failures.
def load_counts(path: Path) -> dict[str, dict[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        ref: record
        for ref, record in data.items()
        if isinstance(record, dict)
        and isinstance(record.get("count"), int)
        and isinstance(record.get("head"), str)
    }


# Write the counts atomically, so an interrupted write can't leave a partial
# file.
def save_counts(path: Path, counts: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
    ) as temporary:
        json.dump(counts, temporary, indent=2)
    os.replace(temporary.name, path)


# Record the outcome of a push or pull for the current branch. Return true
# when this failure reaches the threshold, which displays the rebase hint and
# resets the count.
def record_integration_outcome(
    repo: Repo, command: GitCommand, returncode: int, stderr: str
) -> bool:
    if command.subcommand not in ("push", "pull"):
        return False
    # Detached HEAD has no branch to count for.
    symbolic = repo.check("symbolic-ref", "--quiet", "HEAD", ok=(0, 1))
    head = repo.head_commit
    if symbolic.returncode != 0 or head is None:
        return False
    branch_ref = symbolic.stdout.strip()
    path = repo.git_paths(FAILURE_COUNTS_PATH)[0]
    counts = load_counts(path)
    record = counts.get(branch_ref)
    count = record["count"] if record and record["head"] == head else 0
    assert isinstance(count, int)
    show = False
    if returncode == 0:
        if record is None:
            return False
        count = 0
    else:
        if not is_qualifying_failure(command, stderr):
            return False
        upstream = repo.check(
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
            ok=(0, 128),
        )
        # Rebasing isn't the answer while another operation is in progress,
        # and isn't possible without an upstream.
        if (
            upstream.returncode != 0
            or repo.unmerged_paths
            or repo.operations.combining
        ):
            return False
        count += 1
        show = count >= FAILURE_THRESHOLD
        if show:
            count = 0
    counts[branch_ref] = {"count": count, "head": head}
    save_counts(path, counts)
    return show


# Running the command
# -------------------
#
# Copy Git's captured standard error to ours unchanged.
def emit_stderr(data: bytes) -> None:
    sys.stderr.flush()
    buffer = getattr(sys.stderr, "buffer", None)
    if buffer is None:
        sys.stderr.write(decode(data))
    else:
        buffer.write(data)
        buffer.flush()


# Run a Git command, then explain its failure. Return Git's exit code, or 1
# when Git can't be launched or inspection fails unexpectedly.
def explain(
    # The command, starting with `git`.
    argv: Sequence[str],
    # Print only reactive hint IDs, and discard Git's standard output.
    ids_only: bool,
) -> int:
    command = parse_command(argv)
    try:
        completed = subprocess.run(
            list(argv),
            stdout=subprocess.DEVNULL if ids_only else None,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
        )
    except OSError as error:
        print(f"git-hints: Could not launch Git: {error}", file=sys.stderr)
        return 1
    emit_stderr(completed.stderr)
    stderr = decode(completed.stderr)
    returncode = completed.returncode

    errors: list[Exception] = []
    repo: Repo | None = None
    show_rebase = False
    try:
        if not command.redirected and Repo().work_tree == "inside":
            repo = Repo()
            show_rebase = record_integration_outcome(
                repo, command, returncode, stderr
            )
    except (GitLaunchError, InspectionError) as error:
        errors.append(error)

    lines = [] if ids_only else [f"Git exited with code {returncode}."]
    if returncode == 0:
        if not ids_only:
            lines.append("No error detected.")
    else:
        failure = Failure(command, returncode, stderr, repo)
        hints = []
        for check in REACTIVE_CHECKS:
            try:
                hint = check(failure)
            except (GitLaunchError, InspectionError) as error:
                errors.append(error)
                continue
            if hint is not None:
                hints.append(hint)
        if show_rebase:
            hints.append(rebase_after_repeated_integration_failures())
        hints = sort_hints(hints)
        if ids_only:
            lines += [hint.id for hint in hints]
        elif hints:
            lines += [line for hint in hints for line in render_block(hint)]
        else:
            lines.append("No hints.")
    if lines:
        print("\n".join(lines))
    for error in errors:
        print(f"git-hints: {error}", file=sys.stderr)
    return 1 if errors else returncode
