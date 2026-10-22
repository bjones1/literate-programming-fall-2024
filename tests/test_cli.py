# `test_cli.py` -- Tests for the command line, output format, and rendering
# =========================================================================
#
# These cover requirements from CLI commands and Hint structure in the
# specification.
import os
import shlex

import pytest
from git_test_tools import (
    commit_file,
    config_user,
    git,
    make_repo,
    make_temps,
    output_ids,
    run_hints,
    write,
)

from git_hints.hint import (
    Command,
    Hint,
    Priority,
    Safety,
    code,
    render_block,
    shell_quote,
    sort_hints,
    summarize,
    to_terminal,
)

LINK = '[docs](https://git-scm.com/docs/git "Git documentation")'


def make_hint(hint_id: str, priority: Priority = Priority.WORKFLOW) -> Hint:
    return Hint(
        id=hint_id,
        priority=priority,
        text=f"See the {LINK}.",
        stage="You are working in the local repository.",
        commands=(Command("`git status`", "Git shows the status."),),
    )


# Rendering
# ---------
def test_render_example() -> None:
    references: list[tuple[str, str, str]] = []
    text = to_terminal(
        "Do you want to [stage](https://git-scm.com/docs/git-add "
        '"Choose changed files for the staging area") files?',
        references,
    )
    lines = [text] + [
        f"[{n}] {label}: {title} {url}"
        for n, (label, title, url) in enumerate(references, 1)
    ]
    assert lines == [
        "Do you want to stage [1] files?",
        (
            "[1] stage: Choose changed files for the staging area "
            "https://git-scm.com/docs/git-add"
        ),
    ]


def test_code_spans() -> None:
    assert to_terminal("Run `git status` now.") == "Run git status now."
    for text in ["a`b", "`a", "a`", "``", " a ", "plain"]:
        assert to_terminal(code(text)) == text
    # A link inside a code span is code, not a link.
    assert to_terminal(code(LINK)) == LINK


def test_link_rules() -> None:
    with pytest.raises(ValueError):
        to_terminal(LINK)  # Links aren't allowed outside hint text.
    long_title = "x" * 161
    with pytest.raises(ValueError):
        to_terminal(f'[a](https://git-scm.com "{long_title}")', [])
    assert to_terminal(f'[a](https://git-scm.com "{"x" * 160}")', []) == "a [1]"


def test_hint_validation() -> None:
    with pytest.raises(ValueError):
        make_hint("Not-Kebab")
    with pytest.raises(ValueError):
        make_hint("trailing-")
    with pytest.raises(ValueError):
        Hint(
            "no-link",
            Priority.WORKFLOW,
            "No link.",
            "Stage.",
            (Command("a", "b"),),
        )
    with pytest.raises(ValueError):
        Hint("no-command", Priority.WORKFLOW, LINK, "Stage.", ())


def test_render_block() -> None:
    hint = Hint(
        id="example",
        priority=Priority.WORKFLOW,
        text=f"Read the {LINK}.",
        stage="You are working in the `local` repository.",
        commands=(
            Command("`git status`", "Git shows the status."),
            Command(
                "`git pull --rebase`", "Commits are replayed.", Safety.CAUTION
            ),
            Command("`git reset --hard`", "Back up first.", Safety.WARNING),
        ),
        as_of_last_fetch=True,
    )
    assert hint.safety is Safety.WARNING
    assert render_block(hint) == [
        "ID: example",
        "Priority: workflow",
        "As of last fetch: Read the docs [1].",
        "[1] docs: Git documentation https://git-scm.com/docs/git",
        "Git stage: You are working in the local repository.",
        "Command: git status",
        "Result: Git shows the status.",
        "Command: Caution: git pull --rebase",
        "Result: Commits are replayed.",
        "Command: Warning: git reset --hard",
        "Result: Back up first.",
    ]


def test_sort_hints() -> None:
    hints = [
        make_hint("zeta", Priority.INFORMATIONAL),
        make_hint("untracked-files"),
        make_hint("alpha"),
        make_hint("behind"),
        make_hint("detached-head", Priority.DATA_LOSS_RISK),
        make_hint("merge-conflicts", Priority.ERROR_BLOCKED),
        make_hint("diverged"),
        make_hint("no-commits", Priority.INFORMATIONAL),
    ]
    assert [hint.id for hint in sort_hints(hints)] == [
        "merge-conflicts",
        "detached-head",
        "diverged",
        "behind",
        "untracked-files",
        "alpha",
        "no-commits",
        "zeta",
    ]


def test_summarize() -> None:
    assert to_terminal(summarize(["a"])) == "a"
    assert to_terminal(summarize(["a", "b"])) == "a and b"
    assert to_terminal(summarize(["a", "b", "c"])) == "a, b, and c"
    assert (
        to_terminal(summarize(list("abcdefg"))) == "a, b, c, d, e, and 2 more"
    )


def test_shell_quote() -> None:
    words = ["notes.txt", "src/app.py", "my notes.txt", "café.txt", "it's"]
    for word in words:
        assert shlex.split(shell_quote(word)) == [word]
    assert shell_quote("notes.txt") == "notes.txt"
    assert shell_quote("my notes.txt") == '"my notes.txt"'
    if os.name != "nt":
        assert shlex.split(shell_quote('a"$b')) == ['a"$b']


# Proactive output
# ----------------
#
# A repository where five hints trigger: `no-upstream-branch`,
# `staged-and-unstaged-changes`, `staged-changes`, `unstaged-changes`, and
# `untracked-files`.
def busy_repo(tmp_path_factory: pytest.TempPathFactory):
    repo, remote = make_temps(tmp_path_factory, 2)
    config_user("user1", "user1@example.com")
    make_repo(remote, [["git", "init", "--bare", "-b", "main"]])
    make_repo(
        repo,
        [
            ["git", "init", "-b", "main"],
            ["git", "remote", "add", "origin", str(remote)],
        ],
    )
    commit_file(repo, "foo.txt", "xxx", "Add foo.")
    make_repo(
        repo,
        [
            write(repo / "foo.txt", "staged"),
            ["git", "add", "foo.txt"],
            write(repo / "foo.txt", "unstaged"),
            write(repo / "notes.txt", "notes"),
        ],
    )
    return repo


def test_hint_limit(tmp_path_factory: pytest.TempPathFactory) -> None:
    repo = busy_repo(tmp_path_factory)
    expected = [
        "staged-and-unstaged-changes",
        "staged-changes",
        "unstaged-changes",
        "untracked-files",
        "no-upstream-branch",
    ]

    result = run_hints(repo)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[:3] == [
        "Branch: main",
        '2 more hint(s) available; run "git-hints --all" to see them.',
        "ID: staged-and-unstaged-changes",
    ]
    assert output_ids(result.stdout) == expected[:3]
    # Every block has the required fields, in order.
    for block in result.stdout.split("ID: ")[1:]:
        fields = [line.split(":")[0] for line in block.splitlines()]
        assert fields[1] == "Priority"
        assert fields.index("Git stage") < fields.index("Command")
        assert fields[-1] == "Result"

    result = run_hints(repo, "--all")
    assert output_ids(result.stdout) == expected
    assert "more hint(s) available" not in result.stdout

    result = run_hints(repo, "--ids-only")
    assert result.stdout.splitlines() == expected[:3]
    result = run_hints(repo, "--ids-only", "--all")
    assert result.stdout.splitlines() == expected


def test_no_hints(tmp_path_factory: pytest.TempPathFactory) -> None:
    upstream, local = make_temps(tmp_path_factory, 2)
    config_user("user1", "user1@example.com")
    make_repo(upstream, [["git", "init", "-b", "main"]])
    commit_file(upstream, "foo.txt", "xxx", "Add foo.")
    make_repo(local, [["git", "clone", str(upstream), str(local)]])
    result = run_hints(local)
    assert (result.returncode, result.stdout) == (
        0,
        "Branch: main\nNo hints.\n",
    )
    result = run_hints(local, "--ids-only")
    assert (result.returncode, result.stdout) == (0, "")


def test_help(tmp_path_factory: pytest.TempPathFactory) -> None:
    (directory,) = make_temps(tmp_path_factory, 1)
    result = run_hints(directory, "--help")
    assert result.returncode == 0
    assert "git-hints --all" in result.stdout
    assert "explain" in result.stdout
    result = run_hints(directory, "explain", "--help")
    assert result.returncode == 0
    assert "git-hints explain -- git pull" in result.stdout


# `explain` command line
# ----------------------
def test_explain_requires_git(tmp_path_factory: pytest.TempPathFactory) -> None:
    (directory,) = make_temps(tmp_path_factory, 1)
    for args in (
        ["explain"],
        ["explain", "--", "echo", "hi"],
        ["explain", "--", "gitk"],
    ):
        result = run_hints(directory, *args)
        assert result.returncode == 2
        assert result.stdout == ""
        assert "begins with git" in result.stderr


def test_explain_rejects_fetch(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (directory,) = make_temps(tmp_path_factory, 1)
    result = run_hints(
        directory, "--fetch", "explain", "--", "git", "init", "new"
    )
    assert result.returncode == 2
    assert "--fetch" in result.stderr
    assert not (directory / "new").exists()


def test_explain_success(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    commit_file(repo, "foo.txt", "xxx", "Add foo.")
    # Git receives its options intact, with or without `--`.
    for args in (
        ["explain", "--", "git", "rev-parse", "--abbrev-ref", "HEAD"],
        ["explain", "git", "rev-parse", "--abbrev-ref", "HEAD"],
    ):
        result = run_hints(repo, *args)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [
            "main",
            "Git exited with code 0.",
            "No error detected.",
        ]
    # Under `--ids-only`, Git's standard output is discarded.
    result = run_hints(
        repo, "--ids-only", "explain", "--", "git", "rev-parse", "HEAD"
    )
    assert (result.returncode, result.stdout) == (0, "")
    # Arguments that Click would otherwise expand on Windows reach Git
    # unchanged: Git's pathspec `*.txt` also matches the nested file, while a
    # wildcard expanded in the current directory would not.
    commit_file(repo, "sub/bar.txt", "bar", "Add bar.")
    result = run_hints(repo, "explain", "--", "git", "ls-files", "--", "*.txt")
    assert result.stdout.splitlines()[:2] == ["foo.txt", "sub/bar.txt"]


def test_explain_failure(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    result = run_hints(
        repo, "explain", "--", "git", "rev-parse", "--verify", "nope"
    )
    assert result.returncode == 128
    assert "fatal: Needed a single revision" in result.stderr
    assert result.stdout.splitlines() == [
        "Git exited with code 128.",
        "No hints.",
    ]
    result = run_hints(
        repo,
        "--ids-only",
        "explain",
        "--",
        "git",
        "rev-parse",
        "--verify",
        "nope",
    )
    assert (result.returncode, result.stdout) == (128, "")
    assert "fatal: Needed a single revision" in result.stderr
    # Outside a repository, Git's exit code still passes through.
    git(repo, "status")
    (outside,) = make_temps(tmp_path_factory, 1)
    result = run_hints(outside, "explain", "--", "git", "status")
    assert result.returncode == 128
