# `test_remote.py` -- Tests for hints about upstream branches and fetching
# ========================================================================
#
# Each test follows the test case of the same name in the specification.
from pathlib import Path

import pytest
from git_test_tools import (
    all_blocks,
    append,
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

FETCH_FAILED = "Fetch failed; showing results as of last fetch."


def branch_ab(repo: Path) -> str:
    status = git(repo, "status", "--porcelain=v2", "--branch").stdout
    return next(
        line for line in status.splitlines() if line.startswith("# branch.ab ")
    )


def branch_upstream(repo: Path) -> str:
    status = git(repo, "status", "--porcelain=v2", "--branch").stdout
    return next(
        line
        for line in status.splitlines()
        if line.startswith("# branch.upstream ")
    )


# `push-ahead`
# ------------
def test_push_ahead(tmp_path_factory: pytest.TempPathFactory) -> None:
    remote, local, other = make_temps(tmp_path_factory, 3)
    config_user("user1", "user1@example.com")
    make_repo(remote, [["git", "init", "--bare", "-b", "main"]])
    make_repo(local, [["git", "clone", str(remote), str(local)]])
    make_repo(
        local,
        [
            write(local / "foo.txt", "xxx"),
            ["git", "add", "foo.txt"],
            ["git", "commit", "-m", "Add foo."],
            ["git", "push", "-u", "origin", "main"],
        ],
    )
    assert "push-ahead" not in hint_ids(local)

    make_repo(
        local,
        [
            append(local / "foo.txt", "y"),
            ["git", "commit", "-am", "Change foo."],
        ],
    )
    log = git(local, "log", "--format=%H", "origin/main..HEAD").stdout
    assert len(log.splitlines()) == 1
    ids = hint_ids(local)
    assert "push-ahead" in ids
    assert "behind" not in ids and "diverged" not in ids
    _, found = all_blocks(local)
    block = found["push-ahead"]
    assert "As of last fetch: " in block
    assert "git push origin HEAD:main" in commands(block)

    make_repo(other, [["git", "clone", str(remote), str(other)]])
    commit_file(other, "other.txt", "other", "Add other.")
    git(other, "push")
    git(local, "fetch")
    assert branch_ab(local) == "# branch.ab +1 -1"
    ids = hint_ids(local)
    assert "push-ahead" not in ids
    assert "diverged" in ids

    # Different local and upstream branch names.
    make_repo(
        local,
        [
            ["git", "switch", "-c", "dev", "--track", "origin/main"],
            write(local / "dev.txt", "xxx"),
            ["git", "add", "dev.txt"],
            ["git", "commit", "-m", "Add dev."],
        ],
    )
    assert branch_upstream(local) == "# branch.upstream origin/main"
    assert branch_ab(local) == "# branch.ab +1 -0"
    assert "push-ahead" in hint_ids(local)
    _, found = all_blocks(local)
    assert "git push origin HEAD:main" in commands(found["push-ahead"])

    # A local upstream can't be pushed to.
    make_repo(
        local,
        [
            ["git", "switch", "main"],
            ["git", "switch", "-c", "local-test"],
            ["git", "branch", "--set-upstream-to=main", "local-test"],
            write(local / "local.txt", "xxx"),
            ["git", "add", "local.txt"],
            ["git", "commit", "-m", "Add local."],
        ],
    )
    assert branch_upstream(local) == "# branch.upstream main"
    assert branch_ab(local) == "# branch.ab +1 -0"
    assert "push-ahead" not in hint_ids(local)


# `behind`
# --------
#
# Steps 1–5 of the `behind` test case: `repo1` has a commit that `repo2`, its
# clone, hasn't fetched.
def behind_setup(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    repo1, repo2 = make_temps(tmp_path_factory, 2)
    make_repo(repo1, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    commit_file(repo1, "foo.txt", "xxx", "Add foo.")
    make_repo(repo2, [["git", "clone", str(repo1), str(repo2)]])
    make_repo(
        repo1,
        [
            append(repo1 / "foo.txt", "y"),
            ["git", "commit", "-am", "Change foo."],
        ],
    )
    return repo1, repo2


def test_behind(tmp_path_factory: pytest.TempPathFactory) -> None:
    repo1, repo2 = behind_setup(tmp_path_factory)
    assert branch_ab(repo2) == "# branch.ab +0 -0"
    assert "behind" not in hint_ids(repo2)

    git(repo2, "fetch")
    assert branch_ab(repo2) == "# branch.ab +0 -1"
    ids = hint_ids(repo2)
    assert "behind" in ids
    assert "diverged" not in ids and "push-ahead" not in ids
    _, found = all_blocks(repo2)
    block = found["behind"]
    assert "As of last fetch: " in block
    assert "git pull" in commands(block)
    assert "https://git-scm.com/docs/git-pull" in block

    make_repo(
        repo1,
        [
            append(repo1 / "foo.txt", "z"),
            ["git", "commit", "-am", "Change foo again."],
        ],
    )
    git(repo2, "fetch")
    assert branch_ab(repo2) == "# branch.ab +0 -2"
    assert "behind" in hint_ids(repo2)

    git(repo2, "pull")
    assert branch_ab(repo2) == "# branch.ab +0 -0"
    assert "behind" not in hint_ids(repo2)

    make_repo(
        repo1,
        [
            append(repo1 / "foo.txt", "w"),
            ["git", "commit", "-am", "Change foo once more."],
        ],
    )
    assert "behind" not in hint_ids(repo2)
    assert "behind" in hint_ids(repo2, "--fetch")
    # A successful fetch removes the qualifier.
    result = run_hints(repo2, "--all", "--fetch")
    assert result.returncode == 0, result.stderr
    assert "As of last fetch" not in result.stdout
    assert FETCH_FAILED not in result.stdout


# `diverged`
# ----------
def test_diverged(tmp_path_factory: pytest.TempPathFactory) -> None:
    _, repo2 = behind_setup(tmp_path_factory)
    commit_file(repo2, "bar.txt", "zzz", "Add bar.")
    assert branch_ab(repo2) == "# branch.ab +1 -0"
    ids = hint_ids(repo2)
    assert "push-ahead" in ids
    assert "diverged" not in ids

    git(repo2, "fetch")
    assert branch_ab(repo2) == "# branch.ab +1 -1"
    ids = hint_ids(repo2)
    assert "diverged" in ids
    assert "behind" not in ids and "push-ahead" not in ids
    _, found = all_blocks(repo2)
    block = found["diverged"]
    assert "As of last fetch: " in block
    assert (
        "git pull --no-rebase, resolve any conflicts, then git push"
        in commands(block)
    )
    assert any(
        command.startswith("Caution: git pull --rebase")
        for command in commands(block)
    )
    assert "https://git-scm.com/docs/git-pull" in block
    assert "https://git-scm.com/docs/git-push" in block


# `no-upstream-branch`
# --------------------
def test_no_upstream_branch(tmp_path_factory: pytest.TempPathFactory) -> None:
    first, second = make_temps(tmp_path_factory, 2)
    make_repo(first, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    commit_file(first, "foo.txt", "xxx", "Add foo.")
    git(first, "switch", "-c", "feature-test")
    make_repo(second, [["git", "init", "--bare", "-b", "main"]])
    git(first, "remote", "add", "origin", str(second))
    upstream = [
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    ]
    assert git(first, *upstream, check=False).returncode != 0

    assert "no-upstream-branch" in hint_ids(first)
    _, found = all_blocks(first)
    assert "git push -u origin feature-test" in commands(
        found["no-upstream-branch"]
    )

    git(first, "push", "-u", "origin", "feature-test")
    assert git(first, *upstream).stdout.strip() == "origin/feature-test"
    assert "no-upstream-branch" not in hint_ids(first)


# `--fetch`
# ---------
def test_fetch_failure(tmp_path_factory: pytest.TempPathFactory) -> None:
    repo1, repo2 = behind_setup(tmp_path_factory)
    git(repo2, "fetch")
    git(repo2, "remote", "set-url", "origin", str(repo1.parent / "missing"))
    result = run_hints(repo2, "--all", "--fetch")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[:2] == ["Branch: main", FETCH_FAILED]
    block = result.stdout.split("ID: behind", 1)[1]
    assert "As of last fetch: " in block
    # `--ids-only` prints only IDs.
    result = run_hints(repo2, "--all", "--ids-only", "--fetch")
    assert result.returncode == 0
    assert "behind" in result.stdout.splitlines()
    assert FETCH_FAILED not in result.stdout


def test_fetch_without_remote(tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo,) = make_temps(tmp_path_factory, 1)
    make_repo(repo, [["git", "init", "-b", "main"]])
    config_user("user1", "user1@example.com")
    commit_file(repo, "foo.txt", "xxx", "Add foo.")
    result = run_hints(repo, "--all", "--fetch")
    assert result.returncode == 0, result.stderr
    assert FETCH_FAILED not in result.stdout
    assert result.stdout.splitlines()[0] == "Branch: main"
