# `test_explain.py` -- Tests for reactive hints from `git-hints explain`
# =====================================================================
#
# Each test follows the test case of the same name in the specification.
# Output-block checks refer to captured standard output, and an absent hint
# means no line equals `ID: <id>`.
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from git_test_tools import (
    append,
    blocks,
    collapse,
    commit_file,
    config_user,
    git,
    hint_ids,
    make_repo,
    make_temps,
    output_ids,
    run_hints,
    write,
)

REBASE_HINT = "rebase-after-repeated-integration-failures"
PUSH_REJECTED = "push-rejected-non-fast-forward"


# Run a Git command through `git-hints explain` in its own process.
def explain(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_hints(repo, "explain", "--", "git", *args)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# `merge-conflicts`
# -----------------
def test_merge_conflicts(tmp_path_factory: pytest.TempPathFactory) -> None:
    repo1, repo2 = make_temps(tmp_path_factory, 2)
    config_user("user1", "user1@example.com")
    make_repo(repo1, [["git", "init", "-b", "main"]])
    commit_file(repo1, "foo.txt", "base", "Add foo.")
    make_repo(repo2, [["git", "clone", str(repo1), str(repo2)]])
    commit_file(repo1, "foo.txt", "remote change", "Remote change.")
    commit_file(repo2, "foo.txt", "local change", "Local change.")
    assert "merge-conflicts" not in hint_ids(repo2)

    result = explain(repo2, "pull", "--no-rebase")
    try:
        assert result.returncode == 1
        unmerged = git(repo2, "diff", "--name-only", "--diff-filter=U").stdout
        assert unmerged.split() == ["foo.txt"]
        block = blocks(result.stdout)["merge-conflicts"]
        assert "Priority: error/blocked" in block
        assert "foo.txt" in block
        assert "git status" in block and "git add" in block
        assert "https://git-scm.com/docs/git-merge" in block

        ids = hint_ids(repo2)
        assert "merge-conflicts" in ids and "operation-in-progress" in ids
        result = explain(
            repo2, "-C", str(repo1), "merge", "nonexistent-test-branch"
        )
        assert result.returncode != 0
        assert "merge-conflicts" not in output_ids(result.stdout)

        make_repo(
            repo2,
            [
                write(repo2 / "foo.txt", "local and remote change"),
                ["git", "add", "foo.txt"],
            ],
        )
        assert "merge-conflicts" not in hint_ids(repo2)
        git(repo2, "merge", "--continue")
    finally:
        if (
            git(
                repo2, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
            ).returncode
            == 0
        ):
            git(repo2, "merge", "--abort")

    result = explain(repo2, "status")
    assert result.returncode == 0
    assert "merge-conflicts" not in output_ids(result.stdout)
    result = explain(repo2, "merge", "nonexistent-test-branch")
    assert result.returncode != 0
    assert "merge-conflicts" not in output_ids(result.stdout)


# `pull-blocked-local-changes`
# ----------------------------
def test_pull_blocked_local_changes(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    remote, local, other = make_temps(tmp_path_factory, 3)
    config_user("user1", "user1@example.com")
    make_repo(remote, [["git", "init", "--bare", "-b", "main"]])
    make_repo(other, [["git", "clone", str(remote), str(other)]])
    commit_file(other, "foo.txt", "base", "Add foo.")
    git(other, "push", "-u", "origin", "main")
    make_repo(local, [["git", "clone", str(remote), str(local)]])

    write(local / "foo.txt", "local change")()
    commit_file(other, "foo.txt", "remote change", "Remote change.")
    git(other, "push")

    result = explain(local, "pull")
    assert result.returncode != 0
    block = blocks(result.stdout)["pull-blocked-local-changes"]
    assert "foo.txt" in block
    assert "Priority: error/blocked" in block
    assert "https://git-scm.com/docs/git-pull" in block
    assert "git commit" in block and "git stash push" in block
    assert "stash-local-changes" not in output_ids(result.stdout)
    assert read(local / "foo.txt") == "local change"
    assert (
        git(local, "diff", "--cached", "--quiet", check=False).returncode == 0
    )
    assert git(local, "stash", "list").stdout == ""
    assert git(local, "diff", "--name-only", "--diff-filter=U").stdout == ""

    git(local, "add", "foo.txt")
    result = explain(local, "pull")
    assert result.returncode != 0
    assert "pull-blocked-local-changes" in output_ids(result.stdout)
    assert "local change" in git(local, "diff", "--cached").stdout
    result = explain(local, "pull", "--rebase")
    assert result.returncode != 0
    assert "pull-blocked-local-changes" not in output_ids(result.stdout)

    git(local, "stash", "push", "-m", "Save work before pull")
    stash = git(local, "rev-parse", "refs/stash").stdout.strip()
    result = explain(local, "pull")
    assert result.returncode == 0, result.stderr
    assert "pull-blocked-local-changes" not in output_ids(result.stdout)
    assert read(local / "foo.txt") == "remote change"

    result = explain(local, "pull", "origin", "nonexistent-test-branch")
    assert result.returncode != 0
    assert "pull-blocked-local-changes" not in output_ids(result.stdout)
    commit_file(other, "new.txt", "remote file", "Add new.")
    git(other, "push")
    write(local / "new.txt", "local file")()
    result = explain(local, "pull")
    assert result.returncode != 0
    assert "pull-blocked-local-changes" not in output_ids(result.stdout)
    assert read(local / "new.txt") == "local file"
    (local / "new.txt").unlink()

    assert git(local, "stash", "apply", check=False).returncode != 0
    assert git(local, "rev-parse", "refs/stash").stdout.strip() == stash
    assert "local change" in git(local, "stash", "show", "-p").stdout
    ids = hint_ids(local)
    assert "merge-conflicts" in ids
    assert "pull-blocked-local-changes" not in ids


# `push-rejected-non-fast-forward`
# --------------------------------
def test_push_rejected_non_fast_forward(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    remote, local, other = make_temps(tmp_path_factory, 3)
    config_user("user1", "user1@example.com")
    make_repo(remote, [["git", "init", "--bare", "-b", "main"]])
    make_repo(local, [["git", "clone", str(remote), str(local)]])
    commit_file(local, "base.txt", "base", "Add base.")
    git(local, "push", "-u", "origin", "main")
    make_repo(other, [["git", "clone", str(remote), str(other)]])

    result = explain(local, "push")
    assert result.returncode == 0
    assert PUSH_REJECTED not in output_ids(result.stdout)

    commit_file(other, "remote.txt", "remote", "Add remote.")
    git(other, "push")
    commit_file(local, "local.txt", "local", "Add local.")

    result = explain(local, "push")
    assert result.returncode == 1
    block = blocks(result.stdout)[PUSH_REJECTED]
    assert "Priority: error/blocked" in block
    assert "https://git-scm.com/docs/git-push" in block
    assert "git fetch origin" in block
    assert "git merge origin/main" in block
    assert "git push --force" not in block

    git(local, "fetch", "origin")
    result = run_hints(local, "--ids-only", "explain", "--", "git", "push")
    assert result.returncode == 1
    assert "(non-fast-forward)" in result.stderr
    assert PUSH_REJECTED in result.stdout.splitlines()

    git(local, "switch", "-c", "side")
    result = explain(local, "push", "origin", "main")
    assert result.returncode == 1
    block = blocks(result.stdout)[PUSH_REJECTED]
    assert "git status" in block
    assert "git merge" not in block
    git(local, "switch", "main")
    git(local, "merge", "origin/main")
    result = explain(local, "push")
    assert result.returncode == 0
    assert PUSH_REJECTED not in output_ids(result.stdout)

    result = explain(local, "push", "nonexistent-test-remote", "main")
    assert result.returncode != 0
    assert PUSH_REJECTED not in output_ids(result.stdout)


# `stash-local-changes`
# ---------------------
def test_stash_local_changes(tmp_path_factory: pytest.TempPathFactory) -> None:
    repo, unborn = make_temps(tmp_path_factory, 2)
    config_user("user1", "user1@example.com")
    make_repo(repo, [["git", "init", "-b", "main"]])
    commit_file(repo, "foo.txt", "base", "Add foo.")
    git(repo, "switch", "-c", "topic")
    commit_file(repo, "foo.txt", "topic change", "Topic change.")
    make_repo(
        repo,
        [["git", "switch", "main"], write(repo / "foo.txt", "local change")],
    )

    result = explain(repo, "merge", "topic")
    assert result.returncode != 0
    block = blocks(result.stdout)["stash-local-changes"]
    assert "Priority: error/blocked" in block
    assert "git stash push" in block and "git stash apply" in block
    assert "https://git-scm.com/docs/git-stash" in block
    assert "pull-blocked-local-changes" not in output_ids(result.stdout)

    result = explain(repo, "switch", "topic")
    assert result.returncode != 0
    assert "stash-local-changes" in output_ids(result.stdout)
    assert read(repo / "foo.txt") == "local change"
    assert (
        git(
            repo, "rev-parse", "--verify", "--quiet", "refs/stash", check=False
        ).returncode
        != 0
    )
    assert git(repo, "diff", "--name-only", "--diff-filter=U").stdout == ""

    git(repo, "stash", "push", "-m", "Save work before retrying")
    stash = git(repo, "rev-parse", "refs/stash").stdout.strip()
    result = explain(repo, "merge", "topic")
    assert result.returncode == 0
    assert "stash-local-changes" not in output_ids(result.stdout)

    result = explain(repo, "switch", "nonexistent-test-branch")
    assert result.returncode != 0
    assert "stash-local-changes" not in output_ids(result.stdout)
    git(repo, "switch", "-c", "extra")
    commit_file(repo, "new.txt", "branch file", "Add new.")
    make_repo(
        repo, [["git", "switch", "main"], write(repo / "new.txt", "local file")]
    )
    result = explain(repo, "switch", "extra")
    assert result.returncode != 0
    assert "stash-local-changes" not in output_ids(result.stdout)
    assert read(repo / "new.txt") == "local file"
    (repo / "new.txt").unlink()

    assert git(repo, "stash", "apply", check=False).returncode != 0
    assert git(repo, "rev-parse", "refs/stash").stdout.strip() == stash
    ids = hint_ids(repo)
    assert "merge-conflicts" in ids
    assert "stash-local-changes" not in ids

    make_repo(unborn, [["git", "init", "-b", "main"]])
    commit_file(unborn, "foo.txt", "main", "Add foo.")
    make_repo(
        unborn,
        [
            ["git", "switch", "--orphan", "empty"],
            write(unborn / "foo.txt", "orphan"),
            ["git", "add", "foo.txt"],
        ],
    )
    result = explain(unborn, "switch", "main")
    assert result.returncode != 0
    block = blocks(result.stdout)["stash-local-changes"]
    assert "outside this repository" in block
    assert "git stash push" not in block


# `rebase-after-repeated-integration-failures`
# --------------------------------------------
#
# Steps 1–4 of the test case: `local` and `other` are clones of `remote` whose
# histories have diverged in different files.
def diverged_clones(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, Path]:
    remote, local, other = make_temps(tmp_path_factory, 3)
    config_user("user1", "user1@example.com")
    make_repo(remote, [["git", "init", "--bare", "-b", "main"]])
    make_repo(local, [["git", "clone", str(remote), str(local)]])
    commit_file(local, "foo.txt", "xxx\n", "Add foo.")
    git(local, "push", "-u", "origin", "main")
    make_repo(other, [["git", "clone", str(remote), str(other)]])
    commit_file(local, "bar.txt", "bar\n", "Add bar.")
    make_repo(
        other,
        [
            append(other / "foo.txt", "z\n"),
            ["git", "commit", "-am", "Append z."],
            ["git", "push"],
        ],
    )
    return remote, local, other


# Attempt a push which must be rejected as non-fast-forward; return the IDs
# shown.
def rejected_push(repo: Path, *args: str) -> list[str]:
    result = explain(repo, "push", *args)
    assert result.returncode != 0
    assert (
        "(fetch first)" in result.stderr
        or "(non-fast-forward)" in result.stderr
    )
    return output_ids(result.stdout)


def rejected_pushes(repo: Path, count: int) -> None:
    for _ in range(count):
        assert REBASE_HINT not in rejected_push(repo)


@pytest.fixture
def rebase_cleanup() -> Iterator[list[Path]]:
    repos: list[Path] = []
    yield repos
    for repo in repos:
        rebase_merge = git(
            repo,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "rebase-merge",
        ).stdout.strip()
        if Path(rebase_merge).exists():
            git(repo, "rebase", "--abort")


def test_rebase_after_repeated_integration_failures(
    tmp_path_factory: pytest.TempPathFactory, rebase_cleanup: list[Path]
) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    rebase_cleanup.append(local)
    rejected_pushes(local, 4)

    result = explain(local, "push")
    assert result.returncode != 0
    assert output_ids(result.stdout) == [PUSH_REJECTED, REBASE_HINT]
    block = collapse(blocks(result.stdout)[REBASE_HINT])
    assert "Priority: error/blocked" in block
    assert "Command: Caution: git pull --rebase" in block
    assert "Result: The local branch contains the upstream commits" in block
    assert "backed up" in block and "conflicts" in block
    assert "https://git-scm.com/docs/git-pull" in block
    assert "https://git-scm.com/docs/git-rebase" in block

    assert REBASE_HINT not in rejected_push(local)

    result = explain(local, "pull", "--rebase")
    assert result.returncode == 0, result.stderr
    log = git(local, "log", "--format=%s").stdout.splitlines()
    assert log == ["Add bar.", "Append z.", "Add foo."]
    rebase_merge = git(
        local,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        "rebase-merge",
    ).stdout.strip()
    assert not Path(rebase_merge).exists()
    result = explain(local, "push")
    assert result.returncode == 0
    assert REBASE_HINT not in output_ids(result.stdout)


def test_counter_mixed_failures(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    rejected_pushes(local, 3)
    result = explain(local, "pull", "--ff-only")
    assert "Not possible to fast-forward" in result.stderr
    assert REBASE_HINT not in output_ids(result.stdout)
    assert REBASE_HINT in rejected_push(local)


def test_counter_reset_by_success(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    rejected_pushes(local, 4)
    head = git(local, "rev-parse", "HEAD").stdout
    result = explain(local, "push", "origin", "HEAD:refs/heads/test-reset-ref")
    assert result.returncode == 0
    assert git(local, "rev-parse", "HEAD").stdout == head
    assert REBASE_HINT not in rejected_push(local)


def test_counter_ineligible_errors(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    git(local, "switch", "-c", "no-upstream")
    for _ in range(5):
        result = explain(local, "push")
        assert result.returncode != 0
        assert "has no upstream branch" in result.stderr
        assert REBASE_HINT not in output_ids(result.stdout)
    git(local, "switch", "main")

    rejected_pushes(local, 3)
    # A network failure doesn't count.
    missing = local.parent / "nonexistent-remote"
    result = explain(local, "push", str(missing), "main")
    assert result.returncode != 0
    assert REBASE_HINT not in output_ids(result.stdout)
    # Nor does a failed `git pull --rebase`.
    append(local / "foo.txt", "dirty\n")()
    result = explain(local, "pull", "--rebase")
    assert result.returncode != 0
    assert REBASE_HINT not in output_ids(result.stdout)
    git(local, "restore", "foo.txt")
    # These two are the fourth and fifth qualifying failures.
    assert REBASE_HINT not in rejected_push(local)
    assert REBASE_HINT in rejected_push(local)


def test_counter_branch_isolation(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    rejected_pushes(local, 4)
    make_repo(
        local,
        [
            ["git", "switch", "-c", "feature", "main"],
            ["git", "branch", "--set-upstream-to=origin/main", "feature"],
        ],
    )
    assert REBASE_HINT not in rejected_push(local, "origin", "HEAD:main")
    git(local, "switch", "main")
    assert REBASE_HINT in rejected_push(local)


def test_counter_unrelated_commands(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    rejected_pushes(local, 4)
    assert explain(local, "status").returncode == 0
    assert REBASE_HINT in rejected_push(local)


def test_counter_changed_head(tmp_path_factory: pytest.TempPathFactory) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    rejected_pushes(local, 4)
    head = git(local, "rev-parse", "HEAD").stdout
    commit_file(local, "baz.txt", "baz\n", "Add baz.")
    assert git(local, "rev-parse", "HEAD").stdout != head
    assert REBASE_HINT not in rejected_push(local)


def test_counter_operation_in_progress(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    _, local, _ = diverged_clones(tmp_path_factory)
    git(local, "fetch", "origin")
    commit_file(local, "foo.txt", "local conflict\n", "Conflicting change.")
    rejected_pushes(local, 4)

    head = git(local, "rev-parse", "HEAD").stdout
    assert git(local, "merge", "origin/main", check=False).returncode != 0
    try:
        unmerged = git(local, "diff", "--name-only", "--diff-filter=U").stdout
        assert unmerged.split() == ["foo.txt"]
        result = explain(local, "push")
        assert result.returncode != 0
        assert "(non-fast-forward)" in result.stderr
        assert REBASE_HINT not in output_ids(result.stdout)
    finally:
        git(local, "merge", "--abort")
    assert git(local, "rev-parse", "HEAD").stdout == head
    assert REBASE_HINT in rejected_push(local)
