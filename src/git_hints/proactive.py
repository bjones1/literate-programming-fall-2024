# `proactive.py` -- Hints triggered by repository state
# =====================================================
#
# Running `git-hints` with no subcommand inspects the repository containing
# the current directory and shows the hints whose conditions hold. Each hint
# has a check function below which returns the hint or `None`; a check raises
# `InspectionError` when a command it depends on fails unexpectedly, which
# suppresses only that hint. Every check except `not-a-repo` assumes that the
# current directory is inside a working tree.
#
# Before recommending a workflow command, a check consults `Repo.operations`
# and `Repo.unmerged_paths`: a paused merge, rebase, cherry-pick, or revert
# makes some commands fail or interfere, so the hints suggesting them are
# suppressed while `operation-in-progress` and `merge-conflicts` explain how to
# finish. See Operation-in-progress protection in the specification.
#
# Imports
# -------
#
# ### Standard library
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal

# ### Local
from .git import GitLaunchError, InspectionError, Repo, split_nul
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

# Output text
# -----------
#
# Without `--all`, show at most this many hints.
HINT_LIMIT = 3

NOT_IN_WORK_TREE = (
    "Not inside a working tree (bare repository or .git directory); "
    "run git-hints from the project directory."
)

FETCH_FAILED = "Fetch failed; showing results as of last fetch."

FETCH_TIMEOUT_SECONDS = 10


# Return "1 commit", "2 commits", and so on.
def plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


# Inspection context
# ------------------
@dataclass(frozen=True)
class Context:
    repo: Repo
    # True when `--fetch` just updated the remote-tracking branches, so hints
    # based on them can omit their "as of last fetch" qualifier.
    fetched: bool


# Outside a repository
# --------------------
#
# This is the only hint shown outside a working tree, and the only one that
# doesn't take a `Context`.
def not_a_repo() -> Hint:
    return Hint(
        id="not-a-repo",
        priority=Priority.INFORMATIONAL,
        text=(
            "Would you like to clone a "
            "[repository](https://git-scm.com/docs/git-clone "
            '"Clone a repository into a new directory")? '
            "To start a new project instead, "
            "[initialize](https://git-scm.com/docs/git-init "
            '"Create an empty Git repository") one.'
        ),
        stage=(
            "You are not inside a Git repository; you need to either clone or "
            "initialize a repository before you can begin tracking files."
        ),
        commands=(
            Command(
                "`git clone <repository-url>`",
                "Git creates a local copy of the specified repository.",
            ),
            Command(
                "`git init`",
                "Git creates an empty repository in the current directory.",
            ),
        ),
    )


# Conflicts and paused operations
# -------------------------------
#
# `merge-conflicts` is both proactive and reactive, so `reactive.py` uses this
# check too.
def merge_conflicts(ctx: Context) -> Hint | None:
    repo = ctx.repo
    if not repo.unmerged_paths:
        return None
    paths = [repo.display_path(path) for path in repo.unmerged_paths]
    return Hint(
        id="merge-conflicts",
        priority=Priority.ERROR_BLOCKED,
        text=(
            "Unresolved [merge conflicts]"
            "(https://git-scm.com/docs/git-merge#_how_conflicts_are_presented "
            '"Conflicts occur when Git cannot automatically combine changes") '
            f"remain in these files: {summarize(paths)}. "
            "Resolve them before continuing."
        ),
        stage=(
            "Your working directory and index contain unresolved conflicts "
            "that must be resolved and staged before the active operation can "
            "continue."
        ),
        commands=(
            Command(
                "`git status`",
                "Git names the active operation and lists the conflicted files "
                'under "Unmerged paths".',
            ),
            Command(
                "After resolving each file: "
                + code(git_with_paths(["add"], paths[:5], separator=True)),
                "The resolved files have no unmerged index entries.",
            ),
            Command(
                "`git status` again, then follow its instructions to finish "
                "the active operation",
                "Git can continue the operation.",
            ),
        ),
    )


# The documentation page's one-line summary for each operation that
# `operation-in-progress` explains.
OPERATION_SUMMARIES = {
    "merge": "Join two or more development histories together",
    "rebase": "Reapply commits on top of another base tip",
    "cherry-pick": "Apply the changes introduced by some existing commits",
    "revert": "Revert some existing commits",
}


def operation_in_progress(ctx: Context) -> Hint | None:
    repo = ctx.repo
    operation = repo.operations.paused
    if operation is None:
        return None
    text = (
        f"A [{code(operation)}](https://git-scm.com/docs/git-{operation} "
        f'"{OPERATION_SUMMARIES[operation]}") is in progress. Git paused it '
        "and is waiting for you to finish or cancel it."
    )
    continue_command = code(f"git {operation} --continue")
    abort_command = code(f"git {operation} --abort")
    # Name only the detected operation, so the hint can't be mistaken for
    # advice about another one.
    continue_result = (
        "Git resumes replaying commits and updates the branch once the rebase "
        "completes."
        if operation == "rebase"
        else f"Git resumes the {operation} and records a new commit."
    ) + (
        " If another conflict occurs, Git pauses again and this hint remains. "
        "Once the entire operation completes, `git status` no longer reports "
        "an operation in progress."
    )
    abort_result = (
        f"Git cancels the {operation} and returns to the state before it "
        "began, discarding the conflict resolutions you have made so far. Git "
        "may be unable to restore uncommitted changes that existed before the "
        f"{operation} started, so back up any edited files first."
    )
    commands: list[Command] = []
    if repo.unmerged_paths:
        paths = [repo.display_path(path) for path in repo.unmerged_paths]
        text += (
            f" Some files have conflicts: {summarize(paths)}. Open each "
            "conflicted file, choose the final content, then "
            "[stage](https://git-scm.com/docs/git-add "
            '"Marks a resolved file so Git knows the conflict is fixed") it. '
            "When no conflicts remain, run the continue command. To cancel "
            "instead, run the abort command."
        )
        commands += [
            Command("`git status`", "Git lists the unmerged files."),
            Command(
                "`git add <file>` for each resolved file",
                "Git records that the file's conflict is resolved.",
            ),
        ]
    else:
        text += (
            " No conflicts remain. Run the continue command to finish, or the "
            "abort command to cancel."
        )
    commands += [
        Command(continue_command, continue_result),
        Command(abort_command, abort_result, Safety.WARNING),
    ]
    return Hint(
        id="operation-in-progress",
        priority=Priority.ERROR_BLOCKED,
        text=text,
        stage=(
            "You are working in the local repository: Git has paused an "
            "operation that combines commits, and any conflicted files stay "
            "in your working directory and staging area until you resolve "
            "them."
        ),
        commands=commands,
    )


# The specification asks that a healthy bisect be explained rather than
# treated as an error; this hint does that.
def bisect_in_progress(ctx: Context) -> Hint | None:
    if not ctx.repo.operations.bisect:
        return None
    return Hint(
        id="bisect-in-progress",
        priority=Priority.INFORMATIONAL,
        text=(
            "A [bisect](https://git-scm.com/docs/git-bisect "
            '"Use binary search to find the commit that introduced a bug") '
            "is in progress. Git checks out commits for you to test, so HEAD "
            "stays detached until the bisect ends."
        ),
        stage=(
            "You are working in the local repository at a commit Git chose "
            "for testing, rather than on a branch."
        ),
        commands=(
            Command(
                "`git bisect good` or `git bisect bad`, after testing this "
                "commit",
                "Git checks out the next commit to test, or names the first "
                "bad commit.",
            ),
            Command(
                "`git bisect reset`",
                "Git ends the bisect and returns to the branch where it "
                "started.",
            ),
        ),
    )


# HEAD
# ----
def detached_head(ctx: Context) -> Hint | None:
    repo = ctx.repo
    # Step 1: an attached HEAD, including an unborn branch, isn't detached.
    if repo.current_branch is not None:
        return None
    # Step 2: report a HEAD that doesn't name a commit separately.
    head = repo.check(
        "rev-parse", "--verify", "--quiet", "HEAD^{commit}", ok=(0, 1)
    )
    if head.returncode != 0:
        raise InspectionError(head, "HEAD is detached but names no commit.")
    # Step 3: a detached HEAD is normal in a submodule.
    superproject = repo.check("rev-parse", "--show-superproject-working-tree")
    if superproject.stdout.strip():
        return None
    # Step 4: rebases and bisects detach HEAD as part of their work.
    operations = repo.operations
    if operations.rebase_dir_exists or operations.bisect:
        return None
    # Step 5: find the local branches that contain HEAD. Pass the format as a
    # single argument with no quote characters.
    branches = repo.check(
        "for-each-ref",
        "--contains",
        "HEAD",
        "--format=%(refname:short)",
        "refs/heads",
    ).stdout.splitlines()
    text = (
        "You are in [detached HEAD]"
        "(https://git-scm.com/docs/git-checkout#_detached_head "
        '"HEAD points at a commit instead of a branch; new commits belong to '
        'no branch"). Create a branch if you want to keep working here and '
        "give your commits a branch name."
    )
    if not branches:
        text += (
            " Your commits made here are not on any branch; create a branch "
            "before switching away or they will be hard to find."
        )
    commands = [
        Command(
            "`git switch -c <name>`, replacing `<name>` with an unused branch "
            "name",
            "Git creates a branch at the current commit and switches to it, "
            "so any subsequent commits belong to that branch. This also gives "
            "commits already made at the current detached HEAD a branch name.",
        )
    ]
    # Switching away from commits on no branch would leave them behind.
    if branches:
        branch = branches[0]
        commands.append(
            Command(
                "To return to a branch without keeping anything: "
                + code(f"git switch {shell_quote(branch)}"),
                f"HEAD is attached to {code(branch)} again, and `git status` "
                f"reports {code('On branch ' + branch)}.",
            )
        )
    return Hint(
        id="detached-head",
        priority=(
            Priority.INFORMATIONAL if branches else Priority.DATA_LOSS_RISK
        ),
        text=text,
        stage=(
            "You are working in the local repository at a specific commit "
            "instead of on a named local branch."
        ),
        commands=commands,
    )


def no_commits(ctx: Context) -> Hint | None:
    repo = ctx.repo
    # Step 1.
    if repo.head_commit is not None:
        return None
    # Step 2: confirm an unborn local branch; anything else is a damaged or
    # unreadable repository rather than an empty branch.
    symbolic = repo.check("symbolic-ref", "--quiet", "HEAD", ok=(0, 1))
    branch_ref = symbolic.stdout.strip()
    if symbolic.returncode != 0 or not branch_ref.startswith("refs/heads/"):
        raise InspectionError(
            symbolic, "HEAD names neither a commit nor an unborn branch."
        )
    exists = repo.check(
        "show-ref", "--verify", "--quiet", branch_ref, ok=(0, 1)
    )
    if exists.returncode == 0:
        raise InspectionError(
            exists, f"{branch_ref} exists, but HEAD does not resolve to it."
        )
    text = (
        "Your current branch has no commits yet. Prepare the files you want "
        "to save, then create your first "
        "[commit](https://git-scm.com/docs/git-commit "
        '"Record staged changes as a new commit"). Select files to save using '
        "[git add](https://git-scm.com/docs/git-add "
        '"Add selected file contents to the staging area").'
    )
    # Step 3: offer a commit only once something is staged.
    if repo.has_staged_changes:
        commands = [
            Command(
                '`git commit -m "Initial commit"`',
                "Git creates the first commit on the current branch from the "
                "staged changes. This requires a configured commit identity.",
            )
        ]
    else:
        commands = [
            Command(
                "`git status`",
                "Git lists the files in your working directory.",
            ),
            Command(
                "`git add <files to stage>`",
                "`git status` lists the selected files under "
                '"Changes to be committed".',
            ),
        ]
    return Hint(
        id="no-commits",
        priority=Priority.INFORMATIONAL,
        text=text,
        stage=(
            "You are preparing the first saved snapshot on the current local "
            "branch; edits in the working directory must enter the staging "
            "area before a normal commit includes them, and other branches "
            "may already have history."
        ),
        commands=commands,
    )


# Upstream
# --------
#
# These hints read `# branch.ab +<ahead> -<behind>` from `git status
# --porcelain=v2 --branch`. The counts compare against the remote-tracking
# branch as of the last fetch, so they're qualified unless `--fetch`
# succeeded.
def diverged(ctx: Context) -> Hint | None:
    repo = ctx.repo
    status = repo.branch_status
    if not status.ahead or not status.behind:
        return None
    # `git pull` refuses to start while another operation is paused.
    if repo.operations.combining or repo.unmerged_paths:
        return None
    return Hint(
        id="diverged",
        priority=Priority.WORKFLOW,
        text=(
            "Your branch has diverged from its upstream "
            f"{code(status.upstream or '')}: it has "
            f"{plural(status.ahead, 'commit')} the upstream lacks, and the "
            f"upstream has {plural(status.behind, 'commit')} your branch "
            "lacks. Do you want to integrate the remote commits with "
            "[git pull](https://git-scm.com/docs/git-pull "
            '"Fetches and integrates remote commits; --rebase replays yours on '
            'top of them.") and then share yours with '
            "[git push](https://git-scm.com/docs/git-push "
            '"Uploads local commits to the remote branch.")? A plain '
            "`git pull` fails on diverged branches unless `pull.rebase` or "
            "`pull.ff` is configured."
        ),
        stage=(
            "You are working in the local repo, which has commits that the "
            "remote lacks while the remote has commits that your local repo "
            "lacks."
        ),
        commands=(
            Command(
                "`git pull --no-rebase`, resolve any conflicts, then "
                "`git push`",
                "`git status` reports that your branch is up to date with its "
                "upstream.",
            ),
            Command(
                "`git pull --rebase`, if you prefer a linear history",
                "Git replays your local commits on top of the remote ones, "
                "which changes them; they remain recoverable through the "
                "reflog.",
                Safety.CAUTION,
            ),
        ),
        as_of_last_fetch=not ctx.fetched,
    )


def behind(ctx: Context) -> Hint | None:
    repo = ctx.repo
    status = repo.branch_status
    if not status.behind or status.ahead != 0:
        return None
    # `git pull` refuses to start while another operation is paused.
    if repo.operations.combining or repo.unmerged_paths:
        return None
    return Hint(
        id="behind",
        priority=Priority.WORKFLOW,
        text=(
            "Do you want to [pull](https://git-scm.com/docs/git-pull "
            '"Fetches commits from the remote and integrates them into your '
            'current branch") the newest remote commits before you start '
            "editing? Your branch does not contain remote commits that were "
            "known at the last fetch."
        ),
        stage=(
            "You are working in the local repo, which is missing commits that "
            "the remote repo already has."
        ),
        commands=(
            Command(
                "`git pull`",
                "`git status` reports that your branch is up to date with its "
                "upstream.",
            ),
            # PowerShell would parse an unquoted `@{upstream}` as a hash
            # table.
            Command(
                'To preview first: `git diff --name-only "HEAD...@{upstream}"`',
                "Git lists the files the pull would bring in.",
            ),
        ),
        as_of_last_fetch=not ctx.fetched,
    )


def push_ahead(ctx: Context) -> Hint | None:
    repo = ctx.repo
    branch = repo.current_branch
    status = repo.branch_status
    if branch is None or not status.ahead or status.behind != 0:
        return None
    # Only an upstream on a configured remote can be pushed to; a local
    # upstream has the remote `.`.
    remote = repo.config(f"branch.{branch}.remote")
    merge = repo.config(f"branch.{branch}.merge")
    if remote is None or merge is None or remote not in repo.remotes:
        return None
    upstream_branch = merge.removeprefix("refs/heads/")
    refspec = shell_quote(f"HEAD:{upstream_branch}")
    push = f"git push {shell_quote(remote)} {refspec}"
    return Hint(
        id="push-ahead",
        priority=Priority.WORKFLOW,
        text=(
            "Do you want to [push](https://git-scm.com/docs/git-push "
            '"Uploads the latest changes of your local repository (repo) to a '
            "remote repository so other collaborators can download your "
            'work.")? Your branch has '
            f"{plural(status.ahead, 'commit')} that "
            f"{code(status.upstream or upstream_branch)} does not contain."
        ),
        stage=(
            "Your local repository has commits that are not contained in its "
            "upstream tracking branch."
        ),
        commands=(
            Command(
                code(push),
                "After a successful push, the remote branch contains the "
                "uploaded commits.",
            ),
        ),
        as_of_last_fetch=not ctx.fetched,
    )


def no_upstream_branch(ctx: Context) -> Hint | None:
    repo = ctx.repo
    branch = repo.current_branch
    # Detached HEAD has no branch to configure, and pushing a branch with no
    # commits fails with `src refspec <branch> does not match any`.
    if branch is None or repo.head_commit is None:
        return None
    upstream = repo.check(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        ok=(0, 128),
    )
    if upstream.returncode == 0 or "origin" not in repo.remotes:
        return None
    return Hint(
        id="no-upstream-branch",
        priority=Priority.WORKFLOW,
        text=(
            "Do you want to configure an [upstream branch]"
            "(https://git-scm.com/docs/git-branch "
            '"A remote branch that your local branch tracks") before pushing?'
        ),
        stage=(
            "Your current local branch has no upstream branch configured, so "
            "Git does not know which remote branch it tracks for future "
            "pushes and pulls."
        ),
        commands=(
            Command(
                code(f"git push -u origin {shell_quote(branch)}"),
                "Git pushes the current branch to `origin` and configures it "
                "as the upstream for future pushes and pulls.",
            ),
        ),
    )


# Changes
# -------
def staged_and_unstaged_changes(ctx: Context) -> Hint | None:
    repo = ctx.repo
    if repo.unmerged_paths:
        return None
    if not (repo.has_staged_changes and repo.has_unstaged_changes):
        return None
    return Hint(
        id="staged-and-unstaged-changes",
        priority=Priority.WORKFLOW,
        text=(
            "Do you want to keep unstaged changes out of this commit? "
            "[git commit](https://git-scm.com/docs/git-commit "
            '"Records the staged changes in a new commit.") records staged '
            "changes only. Review the staged changes with "
            "[git diff](https://git-scm.com/docs/git-diff "
            '"Shows changes staged for the next commit").'
        ),
        stage=(
            "Some of your edits are in the staging area and will be included "
            "in the next commit; other edits remain in the working directory "
            "and will not be included."
        ),
        commands=(
            Command(
                "`git diff --cached`",
                "The displayed changes are the ones staged for the next "
                "commit.",
            ),
            Command(
                '`git commit -m "message"`, when ready',
                "Git commits the staged changes; the unstaged edits remain in "
                "your working directory.",
            ),
        ),
    )


def staged_changes(ctx: Context) -> Hint | None:
    repo = ctx.repo
    # A rebase commits for you as it continues.
    if repo.unmerged_paths or repo.operations.rebase_dir_exists:
        return None
    if not repo.has_staged_changes:
        return None
    return Hint(
        id="staged-changes",
        priority=Priority.WORKFLOW,
        text=(
            "Would you like to review your [staged changes]"
            "(https://git-scm.com/docs/git-diff "
            '"Show changes staged for the next commit") before committing? '
            "Use [git commit](https://git-scm.com/docs/git-commit "
            '"Record the staged changes in a new commit") when they are ready.'
        ),
        stage=(
            "You have changes in the staging area that will be included in "
            "the next commit, while any unstaged edits remain in the working "
            "directory and will not be included."
        ),
        commands=(
            Command(
                "`git diff --cached`",
                "Git shows the staged changes.",
            ),
            Command(
                '`git commit -m "message"`',
                "Git creates a commit containing those staged changes.",
            ),
        ),
    )


def unstaged_changes(ctx: Context) -> Hint | None:
    repo = ctx.repo
    if repo.unmerged_paths or not repo.has_unstaged_changes:
        return None
    return Hint(
        id="unstaged-changes",
        priority=Priority.WORKFLOW,
        text=(
            "Do you want to [stage](https://git-scm.com/docs/git-add "
            '"Also called the index; select which changed files to store in a '
            'commit") files?'
        ),
        stage=(
            "Your edits are in the working directory; Git won't put them in a "
            "commit until you stage them."
        ),
        commands=(
            Command(
                "`git add <files to stage>`",
                "`git status` lists these files under "
                '"Changes to be committed."',
            ),
        ),
    )


# Directories whose contents are usually generated, and so are ignore
# candidates at any depth.
GENERATED_DIRECTORIES = (
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    ".venv",
)


# Return the `.gitignore` pattern for an untracked path that looks generated
# or secret, or `None` for an ordinary file. Patterns without a leading slash
# match at any depth, so they also cover nested paths.
def ignore_pattern(
    # A path relative to the repository root, using `/` separators.
    path: str,
) -> str | None:
    *directories, name = path.split("/")
    for directory in directories:
        if directory in GENERATED_DIRECTORIES:
            return f"{directory}/"
    if name == ".env":
        return ".env"
    if name.endswith(".pyc"):
        return "*.pyc"
    return None


# Return untracked paths relative to the repository root. `-z` output names
# each file without Git's quoting; a rename or copy record is followed by an
# extra record holding the original path.
def untracked_paths(repo: Repo) -> list[str]:
    # `--untracked-files=all` overrides `status.showUntrackedFiles` and lists
    # individual files rather than untracked directories.
    output = repo.check(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).stdout
    records = iter(split_nul(output))
    paths = []
    for record in records:
        status, path = record[:2], record[3:]
        if status == "??":
            paths.append(path)
        elif "R" in status or "C" in status:
            next(records, None)
    return paths


def untracked_files(ctx: Context) -> Hint | None:
    repo = ctx.repo
    paths = untracked_paths(repo)
    if not paths:
        return None
    ordinary = [
        repo.display_path(p) for p in paths if ignore_pattern(p) is None
    ]
    candidates = [p for p in paths if ignore_pattern(p) is not None]
    text = (
        "Do you need to [stage](https://git-scm.com/docs/git-add "
        '"Add files to the staging area") or '
        "[ignore](https://git-scm.com/docs/gitignore "
        '"Specify intentionally untracked files that Git should ignore") '
        "untracked files?"
    )
    commands = [
        Command("`git status`", 'Git lists the files under "Untracked files:".')
    ]
    if ordinary:
        text += (
            " Files to stage if they belong in the project: "
            f"{summarize(ordinary)}."
        )
        for path in ordinary[:5]:
            commands.append(
                Command(
                    code(git_with_paths(["add"], [path])),
                    f"`git status` lists {code(path)} under "
                    '"Changes to be committed."',
                )
            )
    if candidates:
        shown = [repo.display_path(p) for p in candidates]
        text += (
            " Files that look generated or secret, which you may want to "
            f"ignore instead: {summarize(shown)}."
        )
        patterns = dict.fromkeys(ignore_pattern(p) or "" for p in candidates)
        for pattern in patterns:
            commands.append(
                Command(
                    f"Add the line {code(pattern)} to `.gitignore`",
                    "Matching files no longer appear under "
                    '"Untracked files:" in `git status`.',
                )
            )
        commands.append(
            Command(
                "`git add .gitignore`",
                "Git stages the ignore rules, so your next commit shares them "
                "with collaborators.",
            )
        )
    return Hint(
        id="untracked-files",
        priority=Priority.WORKFLOW,
        text=text,
        stage=(
            "Your working directory contains untracked files that can be "
            "staged for a future commit if they are ordinary project files, "
            "or excluded using `.gitignore` if they contain secrets or are "
            "generated outputs."
        ),
        commands=commands,
    )


# Trigger when more than half of the files tracked in `HEAD` (T, at least 4)
# have staged or unstaged changes (C): $2C > T$. Disabling rename detection
# counts a renamed file's original path without also counting its
# destination, which isn't in `HEAD`.
def many_changed_files(ctx: Context) -> Hint | None:
    repo = ctx.repo
    operations = repo.operations
    if repo.unmerged_paths or operations.merge or operations.rebase_dir_exists:
        return None
    if repo.head_commit is None:
        return None
    # `--full-tree` lists the whole repository, not just the current
    # directory.
    tracked = set(
        split_nul(
            repo.check(
                "ls-tree", "-r", "--full-tree", "--name-only", "-z", "HEAD"
            ).stdout
        )
    )
    if len(tracked) < 4:
        return None
    changed = set()
    for staged in (["--cached"], []):
        changed |= set(
            split_nul(
                repo.check(
                    "diff", *staged, "--name-only", "--no-renames", "-z"
                ).stdout
            )
        )
    count = len(changed & tracked)
    if 2 * count <= len(tracked):
        return None
    return Hint(
        id="many-changed-files",
        priority=Priority.WORKFLOW,
        text=(
            "More than half of the tracked files in this repository have "
            f"changes ({count} of {len(tracked)}). Would you like to review "
            "the changes and [commit](https://git-scm.com/docs/git-commit "
            '"Records staged changes as a new commit in the local '
            'repository") the work you want to save?'
        ),
        stage=(
            "Changes to tracked files may exist in the working directory, "
            "staging area, or both, but only staged changes will be included "
            "in the next commit in the local repository."
        ),
        commands=(
            Command("`git status`", "Git lists the changed files."),
            Command(
                "`git diff HEAD`",
                "Git shows the changes relative to the last commit.",
            ),
            Command(
                "`git add <files>`",
                "Git stages the changes you want to save.",
            ),
            Command("`git diff --cached`", "Git shows what will be committed."),
            Command(
                '`git commit -m "Describe your changes"`',
                "Git creates a new local commit containing the staged changes; "
                "verify the result with `git status`.",
            ),
        ),
    )


def changes_on_default_branch(ctx: Context) -> Hint | None:
    repo = ctx.repo
    # Step 1.
    branch = repo.current_branch
    if branch is None:
        return None
    # Step 2: without `origin/HEAD`, don't guess `main` or `master`.
    default = repo.check(
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
        ok=(0, 1),
    )
    if default.returncode != 0:
        return None
    if branch != default.stdout.strip().removeprefix("origin/"):
        return None
    # Step 3: on a branch with no commits, `no-commits` applies instead.
    if repo.head_commit is None:
        return None
    # Step 4: `git switch` refuses to run during these operations. Rebases and
    # bisects detach HEAD, so step 1 already excludes them.
    operations = repo.operations
    if (
        repo.unmerged_paths
        or operations.merge
        or operations.cherry_pick
        or operations.revert
    ):
        return None
    # Step 5: untracked files alone don't count; `git switch -c` carries them
    # along anyway.
    if not (repo.has_unstaged_changes or repo.has_staged_changes):
        return None
    return Hint(
        id="changes-on-default-branch",
        priority=Priority.WORKFLOW,
        text=(
            f"You have uncommitted changes on {code(branch)}, the branch your "
            "remote treats as its default. Do you want to make them on a new "
            "[branch](https://git-scm.com/docs/git-switch "
            '"Create a new branch at the current commit and switch to it") '
            "instead?"
        ),
        stage=(
            "Your edits are in the working directory or staging area of the "
            "default branch and have not been committed."
        ),
        commands=(
            Command(
                "`git switch -c <new-branch>`, replacing `<new-branch>` with "
                "an unused branch name",
                "Git creates the branch at the current commit and switches to "
                "it. The uncommitted changes come along, and `git status` "
                "reports `On branch <new-branch>`.",
            ),
        ),
    )


# `-c` lists files in the index, `-i` keeps those matching an ignore rule, and
# `--exclude-standard` applies `.gitignore`, `.git/info/exclude`, and the
# global excludes file. The `:/` pathspec and `--full-name` cover the whole
# repository even from a subdirectory.
def tracked_but_ignored(ctx: Context) -> Hint | None:
    repo = ctx.repo
    # Committing the removal can't succeed until conflicts are resolved.
    if repo.unmerged_paths:
        return None
    output = repo.check(
        "ls-files",
        "-ci",
        "--exclude-standard",
        "-z",
        "--full-name",
        "--",
        ":/",
    ).stdout
    paths = [repo.display_path(path) for path in split_nul(output)]
    if not paths:
        return None
    return Hint(
        id="tracked-but-ignored",
        priority=Priority.WORKFLOW,
        text=(
            "Do you want Git to stop tracking files that match active "
            "[ignore rules](https://git-scm.com/docs/gitignore "
            '"Lists patterns for files Git should not track; it only affects '
            'files that are not already tracked")? These rules may come from '
            "`.gitignore`, `.git/info/exclude`, or a global excludes file. "
            "Ignoring a file does not affect files Git already tracks. "
            f"Tracked files matching these rules: {summarize(paths)}. If you "
            "added any of them deliberately, for example with `git add -f`, "
            "you can keep tracking them. To stop tracking a file but keep it "
            "on your disk, use [`git rm --cached`]"
            "(https://git-scm.com/docs/git-rm "
            '"With --cached, removes a file from the index but leaves it in '
            'your working directory"). Anyone who pulls your commit will have '
            "the file deleted, and it remains in earlier commits, so change "
            "any password or key it contained."
        ),
        stage=(
            "These files are in Git's index and may also have been saved in "
            "previous commits, so Git tracks them even though active ignore "
            "rules match their paths."
        ),
        commands=(
            Command(
                code(git_with_paths(["rm", "--cached"], paths[:5])),
                "`git status` lists each previously committed file as "
                '`deleted:` under "Changes to be committed", and the files '
                "remain in your working directory.",
            ),
            Command(
                "If you added or changed the rule in a project `.gitignore`: "
                "`git add .gitignore`",
                "Git stages the ignore rule.",
            ),
            Command(
                "`git diff --cached`",
                "Git shows the staged removals and rule changes.",
            ),
            Command(
                '`git commit -m "Stop tracking ignored files"`',
                "The selected files no longer appear in "
                "`git ls-files -ci --exclude-standard`. This hint disappears "
                "once no tracked files match an active ignore rule.",
            ),
        ),
    )


# Configuration
# -------------
def commit_identity(ctx: Context) -> Hint | None:
    repo = ctx.repo
    commands = []
    for key, example in (
        ("user.name", "Your Name"),
        ("user.email", "you@example.com"),
    ):
        value = repo.config(key)
        if value is not None and value.strip():
            continue
        # An empty value in this repository's configuration overrides the
        # global one, so correct it locally.
        local = repo.check("config", "--local", "--get", key, ok=(0, 1))
        scope = "--local" if local.returncode == 0 else "--global"
        commands.append(
            Command(
                f'`git config {scope} {key} "{example}"`',
                f"`git config --get {key}` prints the configured value.",
            )
        )
    if not commands:
        return None
    return Hint(
        id="commit-identity",
        priority=Priority.WORKFLOW,
        text=(
            "Do you want to configure your [commit identity]"
            "(https://git-scm.com/docs/git-config"
            "#Documentation/git-config.txt-username "
            '"The name and email address Git records as the author of each '
            'commit")? Git needs both a user name and an email address to '
            "create commits. The `--global` option sets the default for all of "
            "your repositories; `--local` sets an identity for this repository "
            "only, overriding the global one. These settings identify commit "
            "authors; they do not sign you into GitHub."
        ),
        stage=(
            "Your identity is stored in Git's configuration and is recorded in "
            "every commit you create in the local repository."
        ),
        commands=commands,
    )


# Inspection
# ----------
#
# The order here doesn't affect output, which `sort_hints` orders.
CHECKS: list[Callable[[Context], Hint | None]] = [
    merge_conflicts,
    operation_in_progress,
    bisect_in_progress,
    detached_head,
    no_commits,
    diverged,
    behind,
    push_ahead,
    no_upstream_branch,
    staged_and_unstaged_changes,
    staged_changes,
    unstaged_changes,
    untracked_files,
    many_changed_files,
    changes_on_default_branch,
    tracked_but_ignored,
    commit_identity,
]


# Run every check, collecting the triggered hints and the inspection errors
# which suppressed others. Checks run in parallel, since most of their time is
# spent waiting for Git; `Repo` shares each command's result among them. A
# command that fails unexpectedly suppresses every check using it but is
# reported once.
def collect_hints(ctx: Context) -> tuple[list[Hint], list[InspectionError]]:
    def run_check(
        check: Callable[[Context], Hint | None],
    ) -> Hint | InspectionError | None:
        try:
            return check(ctx)
        except InspectionError as error:
            return error

    with ThreadPoolExecutor(max_workers=len(CHECKS)) as executor:
        outcomes = list(executor.map(run_check, CHECKS))
    hints = [outcome for outcome in outcomes if isinstance(outcome, Hint)]
    errors: dict[str, InspectionError] = {}
    for outcome in outcomes:
        if isinstance(outcome, InspectionError):
            errors.setdefault(str(outcome), outcome)
    return hints, list(errors.values())


# Fetching
# --------
FetchOutcome = Literal["fetched", "failed", "skipped"]


# Fetch from the current branch's upstream remote, or from `origin` when there
# is no upstream. A failure, timeout, or missing remote isn't an inspection
# error: inspection continues with the cached remote-tracking branches.
def fetch(repo: Repo) -> FetchOutcome:
    branch = repo.current_branch
    remote = repo.config(f"branch.{branch}.remote") if branch else None
    if remote not in repo.remotes:
        remote = "origin" if "origin" in repo.remotes else None
    if remote is None:
        return "skipped"
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    # Capture output in a file rather than a pipe: a helper process such as
    # `git-remote-https` can outlive a killed `git fetch` and would keep a
    # pipe open, blocking this process.
    with tempfile.TemporaryFile() as output:
        try:
            process = subprocess.Popen(
                ["git", "fetch", "--quiet", "--no-auto-maintenance", remote],
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=output,
                env=env,
                start_new_session=os.name != "nt",
            )
        except OSError as error:
            raise GitLaunchError(f"Could not launch Git: {error}") from error
        try:
            returncode = process.wait(timeout=FETCH_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            kill_process_tree(process)
            return "failed"
    return "fetched" if returncode == 0 else "failed"


def kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            check=False,
        )
    else:
        import signal

        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


# Output
# ------
#
# Show proactive hints for the current directory and return the exit code: 0
# whenever inspection completes, or 1 when an unexpected inspection failure
# occurs or Git can't be launched.
def show_hints(
    # Show every triggered hint instead of at most `HINT_LIMIT`.
    show_all: bool,
    # Print only hint IDs, one per line.
    ids_only: bool,
    # Fetch before inspecting.
    fetch_first: bool,
) -> int:
    repo = Repo()
    lines: list[str] = []
    try:
        work_tree = repo.work_tree
        if work_tree == "outside":
            if not ids_only:
                print(NOT_IN_WORK_TREE)
            return 0
        if work_tree == "not-a-repo":
            hints, errors = [not_a_repo()], []
        else:
            outcome = fetch(repo) if fetch_first else "skipped"
            branch = repo.check("branch", "--show-current").stdout.strip()
            lines.append(f"Branch: {branch or 'detached HEAD'}")
            if outcome == "failed":
                lines.append(FETCH_FAILED)
            hints, errors = collect_hints(Context(repo, outcome == "fetched"))
    except (GitLaunchError, InspectionError) as error:
        print(f"git-hints: {error}", file=sys.stderr)
        return 1

    hints = sort_hints(hints)
    shown = hints if show_all else hints[:HINT_LIMIT]
    if ids_only:
        lines = [hint.id for hint in shown]
    elif not hints:
        lines.append("No hints.")
    else:
        if len(hints) > len(shown):
            lines.append(
                f"{len(hints) - len(shown)} more hint(s) available; run "
                '"git-hints --all" to see them.'
            )
        for hint in shown:
            lines += render_block(hint)
    if lines:
        print("\n".join(lines))
    for error in errors:
        print(f"git-hints: {error}", file=sys.stderr)
    return 1 if errors else 0
