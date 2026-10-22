# `test_state.py` -- Tests for hints about the repository's state
# ===============================================================
#
# Each test follows the test case of the same name in the specification;
# tests without one cover requirements stated elsewhere in it.
import subprocess
from pathlib import Path

import pytest
from git_test_tools import (
    all_blocks,
    collapse,
    commit_file,
    config_user,
    git,
    hint_ids,
    make_repo,
    make_temps,
    run_hints,
    write,
)

NOT_IN_WORK_TREE = (
    "Not inside a working tree (bare repository or .git directory); "
    "run git-hints from the project directory."
)


def git_paths(repo: Path, *names: str) -> list[Path]:
    args = ["rev-parse", "--path-format=absolute"]
    for name in names:
        args += ["--git-path", name]
    return [Path(line) for line in git(repo, *args).stdout.splitlines()]


def current_branch(repo: Path) -> subprocess.CompletedProcess[str]:
    return git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)


# Location
# --------
def test_not_a_repo(tmp_path_factory: pytest.TempPathFactory) -> None:
    (directory,) = make_temps(tmp_path_factory, 1)
    result = git(directory, "rev-parse", "--is-inside-work-tree", check=False)
    assert result.returncode == 128
    assert hint_ids(directory) == ["not-a-repo"]
    lines, found = all_blocks(directory)
    block = found["not-a-repo"]
    assert "Command: git clone <repository-url>" in block
    assert "https://git-scm.com/docs/git-clone" in block
    assert lines[0] == "ID: not-a-repo"
    git(directory, "init", "-b", "main")
    assert "not-a-repo" not in hint_ids(directory)


def test_not_inside_work_tree(tmp_path_factory: pytest.TempPathFactory) -> None:
    bare, repo = make_temps(tmp_path_factory, 2)
    make_repo(bare, [["git", "init", "--bare", "-b", "main"]])
    make_repo(repo, [["git", "init", "-b", "main"]])
    for directory in (bare, repo / ".git"):
        result = run_hints(directory, "--all")
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [NOT_IN_WORK_TREE]
        result = run_hints(directory, "--all", "--ids-only")
        assert result.returncode == 0
        assert result.stdout == ""


# `detached-head`
# ---------------
def test_detached_head(tmp_path_factory: pytest.TempPathFactory) -> None:
    local, remote = make_temps(tmp_path_factory, 2)
    config_user("user1", "user1@example.com")
    make_repo(remote, [["git", "init", "--bare", "-b", "main"]])
    make_repo(
        local,
        [
            ["git", "init", "-b", "main"],
            ["git", "remote", "add", "origin", str(remote)],
            write(local / "foo.txt", "xxx"),
            ["git", "add", "foo.txt"],
            ["git", "commit", "-m", "Add foo."],
            write(local / "foo.txt", "xxxy"),
            ["git", "commit", "-am", "Append y."],
            write(local / "foo.txt", "xxxyz"),
            ["git", "commit", "-am", "Append z."],
        ],
    )
    branch = current_branch(local)
    assert (branch.returncode, branch.stdout.strip()) == (0, "main")
    result = run_hints(local, "--all")
    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "Branch: main"
    ids = hint_ids(local)
    assert "detached-head" not in ids
    assert "no-upstream-branch" in ids

    git(local, "switch", "--detach", "HEAD")
    assert current_branch(local).returncode == 1
    assert (
        git(
            local, "rev-parse", "--verify", "--quiet", "HEAD^{commit}"
        ).returncode
        == 0
    )
    operation_paths = git_paths(
        local, "rebase-merge", "rebase-apply", "BISECT_START"
    )
    assert not any(path.exists() for path in operation_paths)

    lines, found = all_blocks(local)
    block = found["detached-head"]
    assert "Priority: informational" in block
    assert "git switch -c" in block
    assert "git switch main" in block
    assert "https://git-scm.com/docs/git-checkout#_detached_head" in block
    assert lines[0] == "Branch: detached HEAD"
    ids = hint_ids(local)
    assert "detached-head" in ids
    assert "no-upstream-branch" not in ids
    assert "no-commits" not in ids

    # Commit while detached.
    make_repo(
        local,
        [
            write(local / "foo.txt", "xxxyzw"),
            ["git", "commit", "-am", "Append w."],
        ],
    )
    containing = git(
        local,
        "for-each-ref",
        "--contains",
        "HEAD",
        "--format=%(refname:short)",
        "refs/heads",
    )
    assert containing.stdout == ""
    _, found = all_blocks(local)
    block = found["detached-head"]
    assert "Priority: data-loss risk" in block
    assert "git switch -c" in block
    assert "git switch main" not in block
    git(local, "switch", "-c", "saved-work")
    assert current_branch(local).stdout.strip() == "saved-work"
    assert "detached-head" not in hint_ids(local)

    # Bisect.
    git(local, "bisect", "start", "HEAD", "HEAD~2")
    try:
        assert current_branch(local).returncode == 1
        assert git_paths(local, "BISECT_START")[0].exists()
        result = run_hints(local, "--all")
        assert result.returncode == 0
        assert result.stdout.splitlines()[0] == "Branch: detached HEAD"
        ids = hint_ids(local)
        assert "detached-head" not in ids
        assert "no-upstream-branch" not in ids
        assert "bisect-in-progress" in ids
        # Operation-state paths must resolve correctly from a subdirectory.
        (local / "sub").mkdir()
        assert "detached-head" not in hint_ids(local / "sub")
    finally:
        git(local, "bisect", "reset")
    assert current_branch(local).stdout.strip() == "saved-work"
    assert not git_paths(local, "BISECT_START")[0].exists()

    # A stopped rebase.
    missing = "refs/heads/git-hints-test-missing"
    assert (
        git(
            local, "show-ref", "--verify", "--quiet", missing, check=False
        ).returncode
        != 0
    )
    rebase = subprocess.run(
        [
            "git",
            "rebase",
            "--exec",
            f"git rev-parse --verify {missing}",
            "HEAD~1",
        ],
        cwd=local,
        shell=False,
        check=False,
        capture_output=True,
    )
    try:
        assert rebase.returncode != 0
        assert current_branch(local).returncode == 1
        assert git_paths(local, "rebase-merge")[0].exists()
        result = run_hints(local, "--all")
        assert result.returncode == 0
        assert result.stdout.splitlines()[0] == "Branch: detached HEAD"
        ids = hint_ids(local)
        assert "detached-head" not in ids
        assert "no-upstream-branch" not in ids
    finally:
        git(local, "rebase", "--abort")
    assert current_branch(local).stdout.strip() == "saved-work"
    assert not any(
        path.exists()
        for path in git_paths(local, "rebase-merge", "rebase-apply")
    )
    git(local, "switch", "--detach", "HEAD")
    assert "detached-head" in hint_ids(local)
    git(local, "switch", "saved-work")


# An unreadable HEAD is reported separately, with a nonzero exit, while other
# hints are still shown.
def test_invalid_detached_head(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    config_user("user1", "user1@example.com")
    make_repo(repo, [["git", "init", "-b", "main"]])
    commit_file(repo, "foo.txt", "xxx", "Add foo.")
    # `commit-identity` doesn't depend on HEAD, so it still triggers.
    git(repo, "config", "--global", "--unset", "user.email")
    (repo / ".git" / "HEAD").write_text("1" * 40 + "\n", encoding="utf-8")
    result = run_hints(repo, "--all", "--ids-only")
    assert result.returncode == 1
    assert "HEAD is detached but names no commit" in result.stderr
    assert "commit-identity" in result.stdout.splitlines()
    assert "detached-head" not in result.stdout.splitlines()


# `no-commits`
# ------------
def test_no_commits(tmp_path_factory: pytest.TempPathFactory) -> None:
    local, remote = make_temps(tmp_path_factory, 2)
    config_user("user1", "user1@example.com")
    make_repo(remote, [["git", "init", "--bare", "-b", "main"]])
    make_repo(
        local,
        [
            ["git", "init", "-b", "main"],
            ["git", "remote", "add", "origin", str(remote)],
        ],
    )
    head = git(local, "rev-parse", "--verify", "--quiet", "HEAD", check=False)
    assert (head.returncode, head.stdout, head.stderr) == (1, "", "")
    assert current_branch(local).stdout.strip() == "main"
    assert (
        git(
            local,
            "show-ref",
            "--verify",
            "--quiet",
            "refs/heads/main",
            check=False,
        ).returncode
        == 1
    )
    assert (
        git(local, "diff", "--cached", "--quiet", check=False).returncode == 0
    )

    lines, found = all_blocks(local)
    assert lines[0] == "Branch: main"
    block = found["no-commits"]
    assert "git status" in block and "git add" in block
    assert "https://git-scm.com/docs/git-add" in block
    assert "git commit" not in block
    ids = hint_ids(local)
    assert "no-commits" in ids
    for absent in (
        "detached-head",
        "many-changed-files",
        "staged-changes",
        "no-upstream-branch",
    ):
        assert absent not in ids

    write(local / "foo.txt", "xxx")()
    lines, found = all_blocks(local)
    assert lines[0] == "Branch: main"
    assert "git commit" not in found["no-commits"]
    ids = hint_ids(local)
    assert "no-commits" in ids and "untracked-files" in ids
    for absent in ("detached-head", "many-changed-files", "staged-changes"):
        assert absent not in ids

    git(local, "add", "foo.txt")
    assert (
        git(local, "diff", "--cached", "--quiet", check=False).returncode == 1
    )
    assert (
        git(
            local, "rev-parse", "--verify", "--quiet", "HEAD", check=False
        ).returncode
        == 1
    )
    _, found = all_blocks(local)
    block = found["no-commits"]
    assert 'git commit -m "Initial commit"' in block
    assert "https://git-scm.com/docs/git-commit" in block
    ids = hint_ids(local)
    assert "no-commits" in ids and "staged-changes" in ids
    assert "detached-head" not in ids and "many-changed-files" not in ids

    git(local, "commit", "-m", "Initial commit")
    assert git(local, "rev-parse", "--verify", "--quiet", "HEAD").stdout.strip()
    assert current_branch(local).stdout.strip() == "main"
    assert (
        git(local, "diff", "--cached", "--quiet", check=False).returncode == 0
    )
    lines, _ = all_blocks(local)
    assert lines[0] == "Branch: main"
    ids = hint_ids(local)
    assert "no-upstream-branch" in ids
    for absent in (
        "no-commits",
        "detached-head",
        "many-changed-files",
        "staged-changes",
    ):
        assert absent not in ids

    git(local, "switch", "--orphan", "fresh")
    try:
        assert current_branch(local).stdout.strip() == "fresh"
        assert (
            git(
                local, "rev-parse", "--verify", "--quiet", "HEAD", check=False
            ).returncode
            == 1
        )
        assert (
            git(
                local,
                "show-ref",
                "--verify",
                "--quiet",
                "refs/heads/fresh",
                check=False,
            ).returncode
            == 1
        )
        assert (
            git(
                local,
                "show-ref",
                "--verify",
                "--quiet",
                "refs/heads/main",
                check=False,
            ).returncode
            == 0
        )
        assert (
            git(local, "diff", "--cached", "--quiet", check=False).returncode
            == 0
        )
        lines, found = all_blocks(local)
        assert lines[0] == "Branch: fresh"
        block = found["no-commits"]
        assert "git status" in block and "git add" in block
        assert "git commit" not in block
        ids = hint_ids(local)
        assert "no-commits" in ids
        for absent in (
            "detached-head",
            "many-changed-files",
            "staged-changes",
            "no-upstream-branch",
        ):
            assert absent not in ids
    finally:
        git(local, "switch", "main")


# `operation-in-progress`
# -----------------------
OPERATIONS = ("merge", "rebase", "cherry-pick", "revert")


# Check the block for one operation: it names the operation, links to its
# documentation, and shows only its continue and abort commands.
def check_operation_block(block: str, operation: str) -> None:
    text = collapse(block)
    assert f"A {operation} [1] is in progress" in text
    assert f"git {operation} --continue" in text
    assert f"Warning: git {operation} --abort" in text
    assert f"https://git-scm.com/docs/git-{operation}" in text
    for other in OPERATIONS:
        if other != operation:
            assert f"git {other} --continue" not in text
            assert f"git {other} --abort" not in text


def test_operation_in_progress(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    commit_file(repo, "foo.txt", "base", "Add foo.")
    assert "operation-in-progress" not in hint_ids(repo)
    make_repo(
        repo,
        [
            ["git", "switch", "-c", "topic"],
            write(repo / "foo.txt", "topic"),
            ["git", "commit", "-am", "Topic change."],
            ["git", "switch", "main"],
            write(repo / "foo.txt", "main"),
            ["git", "commit", "-am", "Main change."],
        ],
    )

    # Merge conflict.
    assert git(repo, "merge", "topic", check=False).returncode != 0
    try:
        assert (
            git(
                repo, "rev-parse", "--verify", "--quiet", "MERGE_HEAD"
            ).returncode
            == 0
        )
        assert git(
            repo, "diff", "--name-only", "--diff-filter=U"
        ).stdout.split() == ["foo.txt"]
        lines, found = all_blocks(repo)
        assert lines[0] == "Branch: main"
        block = found["operation-in-progress"]
        check_operation_block(block, "merge")
        assert "foo.txt" in block
        assert "git add" in block
        assert "operation-in-progress" in hint_ids(repo)

        # Resolved but not yet continued.
        make_repo(
            repo,
            [write(repo / "foo.txt", "resolved"), ["git", "add", "foo.txt"]],
        )
        assert "operation-in-progress" in hint_ids(repo)
        _, found = all_blocks(repo)
        block = collapse(found["operation-in-progress"])
        assert "No conflicts remain" in block
        assert "git merge --continue" in block
        assert "foo.txt" not in block

        git(repo, "merge", "--continue")
    finally:
        if (
            git(
                repo,
                "rev-parse",
                "--verify",
                "--quiet",
                "MERGE_HEAD",
                check=False,
            ).returncode
            == 0
        ):
            git(repo, "merge", "--abort")
    assert (
        git(
            repo, "rev-parse", "--verify", "--quiet", "MERGE_HEAD", check=False
        ).returncode
        == 1
    )
    assert "operation-in-progress" not in hint_ids(repo)

    # Abort.
    make_repo(
        repo,
        [
            ["git", "switch", "-c", "topic2"],
            write(repo / "foo.txt", "topic2"),
            ["git", "commit", "-am", "Topic change 2."],
            ["git", "switch", "main"],
            write(repo / "foo.txt", "main2"),
            ["git", "commit", "-am", "Main change 2."],
        ],
    )
    assert git(repo, "merge", "topic2", check=False).returncode != 0
    try:
        assert "operation-in-progress" in hint_ids(repo)
    finally:
        git(repo, "merge", "--abort")
    assert "operation-in-progress" not in hint_ids(repo)

    # Rebase.
    git(repo, "switch", "topic2")
    assert git(repo, "rebase", "main", check=False).returncode != 0
    try:
        assert git_paths(repo, "rebase-merge")[0].is_dir()
        lines, found = all_blocks(repo)
        check_operation_block(found["operation-in-progress"], "rebase")
        assert "cherry-pick" not in found["operation-in-progress"]
        assert lines[0] == "Branch: detached HEAD"
        assert "detached-head" not in hint_ids(repo)
        make_repo(
            repo,
            [write(repo / "foo.txt", "resolved2"), ["git", "add", "foo.txt"]],
        )
        git(repo, "rebase", "--continue")
        assert "operation-in-progress" not in hint_ids(repo)
    finally:
        if git_paths(repo, "rebase-merge")[0].exists():
            git(repo, "rebase", "--abort")

    # Cherry-pick.
    make_repo(
        repo,
        [
            ["git", "switch", "main"],
            ["git", "switch", "-c", "pick-src"],
            write(repo / "foo.txt", "pick"),
            ["git", "commit", "-am", "Pick change."],
            ["git", "switch", "main"],
            write(repo / "foo.txt", "main3"),
            ["git", "commit", "-am", "Main change 3."],
        ],
    )
    assert git(repo, "cherry-pick", "pick-src", check=False).returncode != 0
    try:
        assert (
            git(
                repo, "rev-parse", "--verify", "--quiet", "CHERRY_PICK_HEAD"
            ).returncode
            == 0
        )
        _, found = all_blocks(repo)
        check_operation_block(found["operation-in-progress"], "cherry-pick")
    finally:
        git(repo, "cherry-pick", "--abort")
    assert "operation-in-progress" not in hint_ids(repo)

    # Revert.
    make_repo(
        repo,
        [
            write(repo / "foo.txt", "main4"),
            ["git", "commit", "-am", "Main change 4."],
        ],
    )
    assert git(repo, "revert", "HEAD~1", check=False).returncode != 0
    try:
        assert (
            git(
                repo, "rev-parse", "--verify", "--quiet", "REVERT_HEAD"
            ).returncode
            == 0
        )
        _, found = all_blocks(repo)
        check_operation_block(found["operation-in-progress"], "revert")
    finally:
        git(repo, "revert", "--abort")
    assert "operation-in-progress" not in hint_ids(repo)


# `commit-identity`
# -----------------
def test_commit_identity(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    _, found = all_blocks(repo)
    block = found["commit-identity"]
    assert 'git config --global user.name "Your Name"' in block
    assert 'git config --global user.email "you@example.com"' in block
    assert "https://git-scm.com/docs/git-config" in block

    # Fixing only the name leaves the email missing.
    git(repo, "config", "--global", "user.name", "user1")
    _, found = all_blocks(repo)
    block = found["commit-identity"]
    assert "user.name" not in block.split("Command:", 1)[1]
    assert 'git config --global user.email "you@example.com"' in block

    git(repo, "config", "--global", "user.email", "user1@example.com")
    assert "commit-identity" not in hint_ids(repo)

    # An empty local value overrides the global one and is fixed locally.
    git(repo, "config", "--local", "user.email", "")
    _, found = all_blocks(repo)
    assert (
        'git config --local user.email "you@example.com"'
        in found["commit-identity"]
    )
