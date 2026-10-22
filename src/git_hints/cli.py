# `cli.py` -- The `git-hints` command line
# ========================================
#
# Global options (`--all`, `--ids-only`, `--fetch`) belong to the top-level
# command and therefore precede `explain`, as in
# `git-hints --ids-only explain -- git push`. With no subcommand, `git-hints`
# shows proactive hints; `explain` runs a Git command and shows reactive hints.
#
# Imports
# -------
#
# ### Standard library
import io
import sys
from dataclasses import dataclass
from typing import Annotated

# ### Third-party
import typer

# ### Local
from . import proactive, reactive

# Exit code for invalid command-line usage, matching Typer's own.
USAGE_ERROR = 2

app = typer.Typer(add_completion=False)


@dataclass(frozen=True)
class GlobalOptions:
    show_all: bool
    ids_only: bool
    fetch: bool


@app.callback(invoke_without_command=True)
def git_hints(
    ctx: typer.Context,
    show_all: Annotated[
        bool,
        typer.Option(
            "--all", help="Show every triggered hint instead of at most three."
        ),
    ] = False,
    ids_only: Annotated[
        bool,
        typer.Option(
            "--ids-only",
            help="Print only the IDs of the hints shown, one per line.",
        ),
    ] = False,
    fetch: Annotated[
        bool,
        typer.Option(
            "--fetch",
            help="Fetch from the upstream remote (or origin) before "
            "inspecting, so ahead/behind hints are current.",
        ),
    ] = False,
) -> None:
    """Show where you are in Git and what to do next.

    With no command, inspect the current repository and show up to three
    hints, most important first.

    Examples: git-hints, git-hints --all, git-hints --fetch
    """
    ctx.obj = GlobalOptions(show_all, ids_only, fetch)
    if ctx.invoked_subcommand is None:
        raise typer.Exit(proactive.show_hints(show_all, ids_only, fetch))


# Accept Git's options as plain arguments, so Git receives every flag intact.
@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def explain(
    ctx: typer.Context,
    command: Annotated[
        list[str] | None,
        typer.Argument(
            help="The Git command to run, starting with git. Put -- before "
            "it so that its options aren't read as options of git-hints."
        ),
    ] = None,
) -> None:
    """Run a Git command, then explain why it failed.

    Git's output appears as usual, followed by its exit code and hints for
    recognized failures. git-hints exits with Git's exit code.

    Example: git-hints explain -- git pull
    """
    options: GlobalOptions = ctx.obj
    argv = [*(command or []), *ctx.args]
    if options.fetch:
        typer.echo("git-hints: --fetch cannot be used with explain.", err=True)
        raise typer.Exit(USAGE_ERROR)
    if not argv or argv[0] != "git":
        typer.echo(
            "git-hints: explain needs a Git command that begins with git, "
            "for example: git-hints explain -- git pull",
            err=True,
        )
        raise typer.Exit(USAGE_ERROR)
    raise typer.Exit(reactive.explain(argv, options.ids_only))


def main() -> None:
    # Git writes paths as UTF-8; do the same rather than failing on a path the
    # locale's code page can't represent.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="replace")
    # On Windows, Click would otherwise expand wildcards, `~`, and environment
    # variables meant for Git.
    app(prog_name="git-hints", windows_expand_args=False)
