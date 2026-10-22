# `git_test_tools.py` -- Isolated Git repositories for tests
# ==========================================================
#
# Every Git command a test runs, including those `git-hints` runs, uses the
# isolated environment that the autouse `git_setup` fixture (registered in
# `conftest.py`) places in `os.environ`, so results don't depend on the Git
# configuration of the machine running the tests. Tests set up repositories
# with `make_repo`, which fails the test as soon as a setup command fails; a
# command expected to fail runs through `git` with `check=False` so that the
# test can verify its exit code and output.
#
# Imports
# -------
#
# ### Standard library
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

# ### Third-party
import pytest

# Isolation
# ---------


@pytest.fixture(autouse=True)
def git_setup(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Git sets `GIT_DIR`, `GIT_WORK_TREE`, and `GIT_INDEX_FILE` when Pytest
    # runs from a Git hook, which would make tests act on the outer
    # repository. `GIT_AUTHOR_*`, `GIT_COMMITTER_*`, and `EMAIL` override
    # `user.name` and `user.email`; `GIT_CONFIG_PARAMETERS` and
    # `GIT_CONFIG_COUNT` add configuration that bypasses the files below.
    for name in list(os.environ):
        if name.upper().startswith("GIT_") or name.upper() in (
            "EMAIL",
            "XDG_CONFIG_HOME",
        ):
            monkeypatch.delenv(name)
    # Git reads some files from the home directory even when
    # `GIT_CONFIG_GLOBAL` is set, such as the global ignore file
    # `~/.config/git/ignore`.
    monkeypatch.setenv("HOME", str(tmp_path_factory.mktemp("home")))
    global_config = tmp_path_factory.mktemp("config") / "gitconfig"
    global_config.write_text("[init]\ndefaultBranch = main", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    # Ignore the system configuration, such as Git for Windows'
    # `core.autocrlf=true`.
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    # Never find a repository above a test's temporary directory.
    monkeypatch.setenv(
        "GIT_CEILING_DIRECTORIES", str(tmp_path_factory.getbasetemp())
    )
    # Never wait for a password or an editor.
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setenv("GIT_EDITOR", "true")
    # Keep Git's messages in English.
    monkeypatch.setenv("LC_ALL", "C")


# Set the isolated environment's global identity.
def config_user(username: str, email: str) -> None:
    for key, value in (("user.name", username), ("user.email", email)):
        subprocess.run(["git", "config", "--global", key, value], check=True)


# Directories and repositories
# ----------------------------
#
# Create `num` temporary directories. Name the returned paths in the test.
def make_temps(
    tmp_path_factory: pytest.TempPathFactory, num: int
) -> list[Path]:
    return [tmp_path_factory.mktemp("temp") for _ in range(num)]


# A setup step: a Git argument list, or a zero-argument function that creates,
# modifies, or deletes files using paths rooted at the repository.
SetupCommand = Sequence[str] | Callable[[], object]


# Run setup commands in `temp_dir`, failing the test as soon as one exits
# nonzero. This never changes the process's current directory.
def make_repo(temp_dir: Path, commands: Sequence[SetupCommand]) -> None:
    for command in commands:
        if callable(command):
            command()
            continue
        result = subprocess.run(
            list(command),
            cwd=temp_dir,
            shell=False,
            check=False,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise AssertionError(
                f"Setup command {list(command)} exited with code "
                f"{result.returncode}:\n{result.stdout}{result.stderr}"
            )


# Run one Git command in `cwd`. By default it's a setup command, which must
# succeed; pass `check=False` for a command whose failure is under test.
def git(
    cwd: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        shell=False,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} exited with code {result.returncode}:\n"
            f"{result.stdout}{result.stderr}"
        )
    return result


# Return a file-operation function for `make_repo`. Write `\n` line endings on
# every platform.
def write(path: Path, text: str) -> Callable[[], object]:
    def write_file() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    return write_file


def append(path: Path, text: str) -> Callable[[], object]:
    def append_file() -> None:
        with path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(text)

    return append_file


# Commit a file containing `text`.
def commit_file(repo: Path, name: str, text: str, message: str) -> None:
    make_repo(
        repo,
        [
            write(repo / name, text),
            ["git", "add", name],
            ["git", "commit", "-m", message],
        ],
    )


# Running `git-hints`
# -------------------
#
# Run `git-hints` in its own process, with the repository under test as the
# current directory.
def run_hints(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "git_hints", *args],
        cwd=cwd,
        shell=False,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


# Return the IDs of every triggered proactive hint, requiring a normal exit.
def hint_ids(cwd: Path, *args: str) -> list[str]:
    result = run_hints(cwd, "--all", "--ids-only", *args)
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


# Split normal output into hint blocks keyed by ID. A block runs from its
# `ID:` line to the next `ID:` line or the end of output.
def blocks(stdout: str) -> dict[str, str]:
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in stdout.splitlines():
        if line.startswith("ID: "):
            current = found.setdefault(line.removeprefix("ID: "), [])
        if current is not None:
            current.append(line)
    return {hint_id: "\n".join(lines) for hint_id, lines in found.items()}


# Run `git-hints --all`, requiring a normal exit, and return its hint blocks.
def all_blocks(cwd: Path) -> tuple[list[str], dict[str, str]]:
    result = run_hints(cwd, "--all")
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines(), blocks(result.stdout)


# Return the IDs in output, comparing whole `ID: <id>` lines.
def output_ids(stdout: str) -> list[str]:
    return [
        line.removeprefix("ID: ")
        for line in stdout.splitlines()
        if line.startswith("ID: ")
    ]


# Collapse runs of whitespace, so phrases can be found regardless of wrapping.
def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# Return the commands from a hint block's `Command:` lines.
def commands(block: str) -> list[str]:
    return [
        line.removeprefix("Command: ")
        for line in block.splitlines()
        if line.startswith("Command: ")
    ]
