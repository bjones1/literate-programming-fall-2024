# `test_changes.py` -- Tests for hints about working-tree and index changes
# =========================================================================
#
# Each test follows the test case of the same name in the specification.
import shlex
from pathlib import Path

import pytest
from git_test_tools import (
    all_blocks,
    append,
    collapse,
    commands,
    commit_file,
    config_user,
    git,
    hint_ids,
    make_repo,
    make_temps,
    run_hints,
    write,
)


# A repository on `main` containing committed files with the given names.
def committed_repo(repo: Path, names: list[str]) -> None:
    make_repo(
        repo,
        [
            ["git", "init", "-b", "main"],
            *[write(repo / name, f"{name} initial\n") for name in names],
            ["git", "add", *names],
            ["git", "commit", "-m", "Add initial files."],
        ],
    )


FOUR_FILES = ["one.txt", "two.txt", "three.txt", "four.txt"]


# `unstaged-changes`
# ------------------
def test_unstaged_changes(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    make_repo(
        repo,
        [
            ["git", "init", "-b", "main"],
            write(repo / "foo.txt", "xxx"),
            ["git", "add", "foo.txt"],
            ["git", "commit", "-m", "Add foo."],
            append(repo / "foo.txt", "y"),
        ],
    )
    assert "unstaged-changes" in hint_ids(repo)
    git(repo, "add", "foo.txt")
    assert "unstaged-changes" not in hint_ids(repo)


# `staged-and-unstaged-changes` and `staged-changes`
# --------------------------------------------------
def test_staged_and_unstaged_changes(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    commit_file(repo, "foo.txt", "xxx", "Add foo.")

    # Staged only.
    make_repo(repo, [append(repo / "foo.txt", "y"), ["git", "add", "foo.txt"]])
    ids = hint_ids(repo)
    assert "staged-and-unstaged-changes" not in ids
    assert "staged-changes" in ids
    _, found = all_blocks(repo)
    staged = found["staged-changes"]
    assert "git diff --cached" in commands(staged)
    assert 'git commit -m "message"' in commands(staged)
    assert "https://git-scm.com/docs/git-diff" in staged
    assert "https://git-scm.com/docs/git-commit" in staged

    # Unstaged only.
    git(repo, "commit", "-m", "Append y.")
    append(repo / "foo.txt", "z")()
    ids = hint_ids(repo)
    assert "staged-and-unstaged-changes" not in ids
    assert "staged-changes" not in ids

    # Staged plus unstaged.
    git(repo, "add", "foo.txt")
    append(repo / "foo.txt", "w")()
    ids = hint_ids(repo)
    assert "staged-and-unstaged-changes" in ids
    assert "staged-changes" in ids
    _, found = all_blocks(repo)
    both = found["staged-and-unstaged-changes"]
    assert "git commit [1] records staged changes only" in both
    assert "git diff --cached" in commands(both)
    staged = found["staged-changes"]
    assert "git diff --cached" in commands(staged)
    assert 'git commit -m "message"' in commands(staged)
    assert both != staged
    for block in (both, staged):
        assert "https://git-scm.com/docs/git-diff" in block
        assert "https://git-scm.com/docs/git-commit" in block


def test_staged_and_unstaged_conflict_suppression(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    make_repo(
        repo,
        [
            write(repo / "conflict.txt", "base"),
            write(repo / "other.txt", "base"),
            ["git", "add", "conflict.txt", "other.txt"],
            ["git", "commit", "-m", "Add files."],
            ["git", "switch", "-c", "topic"],
            write(repo / "conflict.txt", "topic change"),
            ["git", "commit", "-am", "Topic change."],
            ["git", "switch", "main"],
            write(repo / "conflict.txt", "main change"),
            ["git", "commit", "-am", "Main change."],
        ],
    )
    assert git(repo, "merge", "topic", check=False).returncode != 0
    try:
        unmerged = git(repo, "diff", "--name-only", "--diff-filter=U")
        assert unmerged.stdout.splitlines() == ["conflict.txt"]
        assert (
            git(repo, "diff", "--cached", "--quiet", check=False).returncode
            == 1
        )
        assert git(repo, "diff", "--quiet", check=False).returncode == 1
        ids = hint_ids(repo)
        assert "staged-and-unstaged-changes" not in ids
        assert "unstaged-changes" not in ids
    finally:
        git(repo, "merge", "--abort")


def test_staged_changes(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    assert "staged-changes" not in hint_ids(repo)
    make_repo(repo, [write(repo / "foo.txt", "xxx"), ["git", "add", "foo.txt"]])
    assert "staged-changes" in hint_ids(repo)
    _, found = all_blocks(repo)
    staged = found["staged-changes"]
    assert "git diff --cached" in commands(staged)
    assert 'git commit -m "message"' in commands(staged)
    assert "https://git-scm.com/docs/git-diff" in staged
    assert "https://git-scm.com/docs/git-commit" in staged
    git(repo, "commit", "-m", "Add foo.")
    assert "staged-changes" not in hint_ids(repo)


# `untracked-files`
# -----------------
#
# Return the paths that a block's `git add` commands stage.
def staged_paths(block: str) -> list[str]:
    paths = []
    for command in commands(block):
        words = shlex.split(command)
        if words[:2] == ["git", "add"] and words[2:] != [".gitignore"]:
            paths += [word for word in words[2:] if word != "--"]
    return paths


def untracked_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    make_repo(repo, [["git", "init", "-b", "main"]])
    commit_file(repo, "foo.txt", "xxx", "Add foo.")
    return repo


def test_untracked_files(tmp_path_factory: pytest.TempPathFactory) -> None:
    repo = untracked_repo(tmp_path_factory)

    write(repo / "notes.txt", "Hello world")()
    assert "?? notes.txt" in git(repo, "status", "--porcelain=v1").stdout
    assert "untracked-files" in hint_ids(repo)
    _, found = all_blocks(repo)
    block = found["untracked-files"]
    assert "git add notes.txt" in commands(block)
    assert "https://git-scm.com/docs/git-add" in block
    assert "https://git-scm.com/docs/gitignore" in block

    git(repo, "add", "notes.txt")
    assert "A  notes.txt" in git(repo, "status", "--porcelain=v1").stdout
    assert "untracked-files" not in hint_ids(repo)

    make_repo(
        repo,
        [
            write(repo / ".env", "TEST_VARIABLE=example"),
            write(repo / "__pycache__" / "example.pyc", "bytecode"),
        ],
    )
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    assert "?? .env" in status.stdout
    assert "?? __pycache__/example.pyc" in status.stdout
    assert "untracked-files" in hint_ids(repo)
    _, found = all_blocks(repo)
    block = found["untracked-files"]
    assert staged_paths(block) == []
    assert "Add the line .env to .gitignore" in commands(block)
    assert "Add the line __pycache__/ to .gitignore" in commands(block)
    assert "https://git-scm.com/docs/gitignore" in block

    make_repo(
        repo,
        [
            write(repo / ".gitignore", ".env\n__pycache__/\n*.pyc\n"),
            ["git", "add", ".gitignore"],
        ],
    )
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    assert ".env" not in status.stdout.replace(".gitignore", "")
    assert "__pycache__" not in status.stdout
    assert "untracked-files" not in hint_ids(repo)


def test_untracked_spaces_and_unicode(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    repo = untracked_repo(tmp_path_factory)
    make_repo(
        repo,
        [
            write(repo / "my notes.txt", "notes"),
            write(repo / "café.txt", "café"),
        ],
    )
    assert "untracked-files" in hint_ids(repo)
    _, found = all_blocks(repo)
    assert sorted(staged_paths(found["untracked-files"])) == [
        "café.txt",
        "my notes.txt",
    ]
    # The suggested commands work when run.
    for command in commands(found["untracked-files"]):
        words = shlex.split(command)
        if words[:2] == ["git", "add"]:
            git(repo, *words[1:])
    assert "untracked-files" not in hint_ids(repo)


def test_untracked_nested_ignore_candidates(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    repo = untracked_repo(tmp_path_factory)
    make_repo(
        repo,
        [
            write(repo / "src" / "app.py", "print()"),
            write(repo / "src" / ".env", "SECRET=1"),
            write(repo / "src" / "__pycache__" / "example.pyc", "bytecode"),
        ],
    )
    _, found = all_blocks(repo)
    block = found["untracked-files"]
    assert staged_paths(block) == ["src/app.py"]
    assert "src/.env" in block
    assert "src/__pycache__/example.pyc" in block
    patterns = [
        command.removeprefix("Add the line ").removesuffix(" to .gitignore")
        for command in commands(block)
        if command.startswith("Add the line ")
    ]
    assert sorted(patterns) == [".env", "__pycache__/"]
    # The suggested patterns ignore both candidates.
    write(repo / ".gitignore", "".join(f"{p}\n" for p in patterns))()
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    assert sorted(status.stdout.splitlines()) == [
        "?? .gitignore",
        "?? src/app.py",
    ]


def test_untracked_limits(tmp_path_factory: pytest.TempPathFactory) -> None:
    repo = untracked_repo(tmp_path_factory)
    ordinary = [f"file{n}.txt" for n in range(6)]
    candidates = [
        ".env",
        "src/.env",
        "__pycache__/a.pyc",
        "pkg/__pycache__/b.pyc",
        "node_modules/x.js",
        "build/out.o",
        "dist/app.zip",
        "loose.pyc",
    ]
    make_repo(repo, [write(repo / path, "x") for path in ordinary + candidates])
    _, found = all_blocks(repo)
    block = found["untracked-files"]
    staged = staged_paths(block)
    assert len(staged) == 5
    assert set(staged) <= set(ordinary)
    text = block.splitlines()[2]
    listed_candidates = [path for path in candidates if path in text]
    assert 1 <= len(listed_candidates) <= 5
    assert "and 3 more" in text
    assert "and 1 more" in text


def test_untracked_ignores_status_configuration(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    repo = untracked_repo(tmp_path_factory)
    git(repo, "config", "--local", "status.showUntrackedFiles", "no")
    write(repo / "notes.txt", "Hello world")()
    assert "untracked-files" in hint_ids(repo)


# `many-changed-files`
# --------------------
def test_many_changed_files(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    committed_repo(repo, FOUR_FILES)
    assert "many-changed-files" not in hint_ids(repo)

    make_repo(
        repo,
        [
            append(repo / "one.txt", "changed\n"),
            append(repo / "two.txt", "changed\n"),
            write(repo / "untracked.txt", "new\n"),
        ],
    )
    status = git(repo, "status", "--porcelain=v1").stdout.splitlines()
    assert sorted(status) == [" M one.txt", " M two.txt", "?? untracked.txt"]
    # C = 2, T = 4: exactly half.
    assert "many-changed-files" not in hint_ids(repo)

    make_repo(
        repo, [["git", "add", "one.txt"], append(repo / "one.txt", "again\n")]
    )
    assert "MM one.txt" in git(repo, "status", "--porcelain=v1").stdout
    assert "many-changed-files" not in hint_ids(repo)

    append(repo / "three.txt", "changed\n")()
    assert "many-changed-files" in hint_ids(repo)
    _, found = all_blocks(repo)
    block = found["many-changed-files"]
    assert "Priority: workflow" in block
    assert "Git stage: " in block
    assert 'git commit -m "Describe your changes"' in commands(block)
    assert "Result: " in block
    assert "https://git-scm.com/docs/git-commit" in block

    git(repo, "add", "one.txt", "two.txt", "three.txt")
    git(repo, "commit", "-m", "Save tracked changes.")
    assert "many-changed-files" not in hint_ids(repo)


def test_many_changed_files_deletions(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    committed_repo(repo, FOUR_FILES)
    (repo / "one.txt").unlink()
    (repo / "two.txt").unlink()
    assert "many-changed-files" not in hint_ids(repo)
    (repo / "three.txt").unlink()
    assert "many-changed-files" in hint_ids(repo)


def test_many_changed_files_without_commits(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    make_repo(
        repo,
        [
            ["git", "init", "-b", "main"],
            write(repo / "foo.txt", "xxx"),
            ["git", "add", "foo.txt"],
        ],
    )
    result = run_hints(repo, "--all", "--ids-only")
    assert result.returncode == 0, result.stderr
    assert "no-commits" in result.stdout.splitlines()
    assert "many-changed-files" not in result.stdout.splitlines()


def test_many_changed_files_small_repository(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    committed_repo(repo, ["README.md"])
    append(repo / "README.md", "changed\n")()
    assert "many-changed-files" not in hint_ids(repo)


def test_many_changed_files_rename(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    committed_repo(repo, FOUR_FILES)
    git(repo, "mv", "one.txt", "renamed.txt")
    append(repo / "two.txt", "changed\n")()
    assert "many-changed-files" not in hint_ids(repo)
    append(repo / "three.txt", "changed\n")()
    assert "many-changed-files" in hint_ids(repo)


def test_many_changed_files_staged_then_restored(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    committed_repo(repo, FOUR_FILES)
    changed = ["one.txt", "two.txt", "three.txt"]
    make_repo(
        repo,
        [
            *[append(repo / name, "changed\n") for name in changed],
            ["git", "add", *changed],
            ["git", "restore", "--source=HEAD", "--worktree", "--", *changed],
        ],
    )
    cached = git(repo, "diff", "--cached", "--name-only").stdout.splitlines()
    assert sorted(cached) == sorted(changed)
    assert git(repo, "diff", "HEAD", "--name-only").stdout == ""
    assert "many-changed-files" in hint_ids(repo)


def test_many_changed_files_conflict_suppression(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    committed_repo(repo, FOUR_FILES)
    make_repo(
        repo,
        [
            ["git", "switch", "-c", "topic"],
            *[
                append(repo / name, "topic\n")
                for name in ["one.txt", "two.txt", "three.txt"]
            ],
            ["git", "commit", "-am", "Topic changes."],
            ["git", "switch", "main"],
            append(repo / "one.txt", "main\n"),
            ["git", "commit", "-am", "Main change."],
        ],
    )
    assert git(repo, "merge", "topic", check=False).returncode != 0
    try:
        unmerged = git(repo, "diff", "--name-only", "--diff-filter=U").stdout
        assert unmerged.splitlines() == ["one.txt"]
        changed = git(repo, "diff", "HEAD", "--name-only").stdout.splitlines()
        assert 2 * len(changed) > 4
        assert "many-changed-files" not in hint_ids(repo)
    finally:
        git(repo, "merge", "--abort")


# `tracked-but-ignored`
# ---------------------
def test_tracked_but_ignored(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    make_repo(
        repo,
        [
            write(repo / "foo.txt", "xxx"),
            write(repo / "debug.log", "log"),
            write(repo / "my notes.log", "notes"),
            ["git", "add", "foo.txt", "debug.log", "my notes.log"],
            ["git", "commit", "-m", "Add files."],
        ],
    )
    assert not (repo / ".gitignore").exists()
    assert git(repo, "ls-files", "-ci", "--exclude-standard").stdout == ""
    assert "tracked-but-ignored" not in hint_ids(repo)

    write(repo / ".gitignore", "*.log\n")()
    ignored = git(repo, "ls-files", "-ci", "--exclude-standard").stdout
    assert ignored.splitlines() == ["debug.log", "my notes.log"]

    _, found = all_blocks(repo)
    block = collapse(found["tracked-but-ignored"])
    assert "debug.log" in block
    assert 'git rm --cached debug.log "my notes.log"' in block
    assert "foo.txt" not in block
    for phrase in (
        "git rm --cached",
        "git add .gitignore",
        "git diff --cached",
        "git commit",
        "earlier commits",
        "https://git-scm.com/docs/git-rm",
        "https://git-scm.com/docs/gitignore",
    ):
        assert phrase in block
    assert "tracked-but-ignored" in hint_ids(repo)

    git(repo, "rm", "--cached", "debug.log", "my notes.log")
    assert (repo / "debug.log").exists() and (repo / "my notes.log").exists()
    assert "tracked-but-ignored" not in hint_ids(repo)
    git(repo, "add", ".gitignore")
    staged = git(repo, "diff", "--cached", "--name-status").stdout.splitlines()
    assert sorted(staged) == [
        "A\t.gitignore",
        "D\tdebug.log",
        "D\tmy notes.log",
    ]
    git(repo, "commit", "-m", "Stop tracking log files.")
    committed = git(repo, "show", "--name-status", "--format=", "HEAD").stdout
    assert sorted(committed.splitlines()) == sorted(staged)
    assert (repo / "debug.log").exists() and (repo / "my notes.log").exists()
    assert "tracked-but-ignored" not in hint_ids(repo)

    # Negation re-includes a file, so it isn't ignored.
    make_repo(
        repo,
        [
            write(repo / ".gitignore", "*.log\n!debug.log\n"),
            ["git", "add", "debug.log"],
        ],
    )
    assert "tracked-but-ignored" not in hint_ids(repo)

    # Many files.
    names = [f"build/{letter}.txt" for letter in "abcdefg"]
    make_repo(
        repo,
        [
            write(repo / ".gitignore", "build/\n"),
            *[write(repo / name, name) for name in names],
            ["git", "add", "-f", "build"],
        ],
    )
    _, found = all_blocks(repo)
    block = found["tracked-but-ignored"]
    for name in names[:5]:
        assert name in block
    for name in names[5:]:
        assert name not in block
    assert "and 2 more" in block

    git(repo, "rm", "-r", "--cached", "build")
    assert "tracked-but-ignored" not in hint_ids(repo)


# `changes-on-default-branch`
# ---------------------------
def test_changes_on_default_branch(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    upstream, work, unborn = make_temps(tmp_path_factory, 3)
    config_user("user1", "user1@example.com")
    make_repo(upstream, [["git", "init", "-b", "main"]])
    commit_file(upstream, "foo.txt", "xxx", "Add foo.")
    make_repo(work, [["git", "clone", str(upstream), "local"]])
    local = work / "local"

    assert (
        git(local, "symbolic-ref", "--quiet", "--short", "HEAD").stdout.strip()
        == "main"
    )
    origin_head = git(
        local, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"
    )
    assert origin_head.stdout.strip() == "origin/main"
    assert git(local, "diff", "--quiet", check=False).returncode == 0
    assert (
        git(local, "diff", "--cached", "--quiet", check=False).returncode == 0
    )
    assert "changes-on-default-branch" not in hint_ids(local)

    write(local / "foo.txt", "xxxy")()
    assert git(local, "diff", "--quiet", check=False).returncode == 1
    _, found = all_blocks(local)
    block = found["changes-on-default-branch"]
    assert "Priority: workflow" in block
    assert "git switch -c" in block
    assert "https://git-scm.com/docs/git-switch" in block
    assert "changes-on-default-branch" in hint_ids(local)

    git(local, "add", "foo.txt")
    assert git(local, "diff", "--quiet", check=False).returncode == 0
    assert (
        git(local, "diff", "--cached", "--quiet", check=False).returncode == 1
    )
    assert "changes-on-default-branch" in hint_ids(local)

    make_repo(
        local,
        [
            ["git", "commit", "-m", "Append y."],
            write(local / "notes.txt", "Hello world"),
        ],
    )
    ids = hint_ids(local)
    assert "changes-on-default-branch" not in ids
    assert "untracked-files" in ids

    make_repo(
        local,
        [["git", "switch", "-c", "feature"], write(local / "foo.txt", "xxxyz")],
    )
    assert git(local, "diff", "--quiet", check=False).returncode == 1
    assert "changes-on-default-branch" not in hint_ids(local)

    make_repo(
        unborn,
        [
            ["git", "init", "-b", "main"],
            ["git", "remote", "add", "origin", str(upstream)],
            ["git", "fetch", "origin"],
            ["git", "remote", "set-head", "origin", "main"],
            write(unborn / "foo.txt", "xxx"),
            ["git", "add", "foo.txt"],
        ],
    )
    origin_head = git(
        unborn, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"
    )
    assert origin_head.stdout.strip() == "origin/main"
    assert (
        git(
            unborn, "rev-parse", "--verify", "--quiet", "HEAD", check=False
        ).returncode
        == 1
    )
    assert (
        git(unborn, "diff", "--cached", "--quiet", check=False).returncode == 1
    )
    ids = hint_ids(unborn)
    assert "no-commits" in ids
    assert "changes-on-default-branch" not in ids

    make_repo(
        local,
        [
            ["git", "commit", "-am", "Change foo on feature."],
            ["git", "switch", "main"],
            ["git", "merge", "--no-commit", "--no-ff", "feature"],
        ],
    )
    try:
        merge_head = git(
            local,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "MERGE_HEAD",
        ).stdout.strip()
        assert Path(merge_head).exists()
        assert git(local, "diff", "--name-only", "--diff-filter=U").stdout == ""
        assert (
            git(local, "diff", "--cached", "--quiet", check=False).returncode
            == 1
        )
        assert (
            git(
                local, "symbolic-ref", "--quiet", "--short", "HEAD"
            ).stdout.strip()
            == "main"
        )
        assert "changes-on-default-branch" not in hint_ids(local)
    finally:
        git(local, "merge", "--abort")
