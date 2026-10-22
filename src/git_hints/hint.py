# `hint.py` -- The hint model and its terminal rendering
# ======================================================
#
# A hint is data: a permanent ID, a priority class, Markdown text which links
# to the official documentation, a sentence naming the Git stage involved, and
# one or more suggested commands with their expected results. This module
# defines that data, orders hints for display, and renders each one as the
# `ID:` block described under Hint structure in the specification.
#
# Imports
# -------
#
# ### Standard library
import os
import re
import shlex
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

# Hint data
# ---------


# A priority class, highest priority first. Classify a hint by the repository
# state or failure it reports, not by the danger of its suggested commands.
class Priority(Enum):
    ERROR_BLOCKED = "error/blocked"
    DATA_LOSS_RISK = "data-loss risk"
    WORKFLOW = "workflow"
    INFORMATIONAL = "informational"


# How much work a suggested command can lose, least risky first.
#
# * `CAUTION`: rewrites commits or moves a branch, but the prior commits
#   generally remain recoverable through the reflog.
# * `WARNING`: can permanently destroy uncommitted, staged, or untracked work,
#   a stash, or remote commits. The command's result must say what might be
#   lost and tell the user to back up first.
class Safety(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"


SAFETY_PREFIX = {
    Safety.SAFE: "",
    Safety.CAUTION: "Caution: ",
    Safety.WARNING: "Warning: ",
}


# A suggested command and its expected result, both in Markdown. Links belong
# in the hint text, not here.
@dataclass(frozen=True)
class Command:
    text: str
    result: str
    safety: Safety = Safety.SAFE


ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)*")


@dataclass(frozen=True)
class Hint:
    # The permanent ID; never reuse one for a different hint.
    id: str
    priority: Priority
    # Markdown containing at least one documentation link.
    text: str
    # One sentence naming the working directory, staging area, local
    # repository, or remote repository involved.
    stage: str
    commands: Sequence[Command]
    # True to qualify a hint computed from remote-tracking branches which may
    # be stale.
    as_of_last_fetch: bool = False

    def __post_init__(self) -> None:
        if not ID_PATTERN.fullmatch(self.id):
            raise ValueError(f"Invalid hint ID {self.id!r}.")
        if not self.commands:
            raise ValueError(f"Hint {self.id} has no command.")
        if not _LINK.search(self.text):
            raise ValueError(f"Hint {self.id} has no documentation link.")

    # The strongest risk among this hint's commands.
    @property
    def safety(self) -> Safety:
        order = list(Safety)
        return max((c.safety for c in self.commands), key=order.index)


# Ordering
# --------
#
# Within a priority class, these IDs come first, in this order, ahead of the
# remaining IDs, which sort by Unicode code point. A new ID that needs special
# precedence must be added here explicitly.
PRECEDENCE = [
    "merge-conflicts",
    "detached-head",
    "no-commits",
    "diverged",
    "behind",
    "push-ahead",
    "staged-and-unstaged-changes",
    "staged-changes",
    "unstaged-changes",
    "untracked-files",
]


def sort_hints(hints: Iterable[Hint]) -> list[Hint]:
    priorities = list(Priority)

    def key(hint: Hint) -> tuple[int, int, str]:
        precedence = (
            PRECEDENCE.index(hint.id)
            if hint.id in PRECEDENCE
            else len(PRECEDENCE)
        )
        return (priorities.index(hint.priority), precedence, hint.id)

    return sorted(hints, key=key)


# Markdown
# --------
#
# Hint source text supports plain text, inline code spans, and inline links of
# the form `[label](url "title")`. Each title must be meaningful, at most 160
# Unicode code points, and contain no double quote; a longer explanation
# belongs in the documentation itself.
MAX_TITLE_LENGTH = 160

_LINK = re.compile(
    r"\[(?P<label>(?:[^\[\]`]|`[^`]*`)+)\]"
    r'\((?P<url>[^\s()]+) "(?P<title>[^"]*)"\)'
)


# Wrap text in a code span. Following CommonMark, the fence is one backtick
# longer than any backtick run inside the text, and padding spaces keep a
# leading or trailing backtick (or space) from merging with the fence.
def code(text: str) -> str:
    longest = max((len(run) for run in re.findall("`+", text)), default=0)
    fence = "`" * (longest + 1)
    needs_pad = (
        text[:1] == "`"
        or text[-1:] == "`"
        or (text[:1] == " " and text[-1:] == " " and text.strip() != "")
    )
    pad = " " if needs_pad else ""
    return f"{fence}{pad}{text}{pad}{fence}"


# Render Markdown for the terminal: remove code-span fences and replace each
# link with its label followed by a reference number `[n]`.
def to_terminal(
    markdown: str,
    # Receives `(label, title, url)` for each link, in order. `None` forbids
    # links.
    references: list[tuple[str, str, str]] | None = None,
) -> str:
    out: list[str] = []
    index = 0
    while index < len(markdown):
        char = markdown[index]
        if char == "`":
            fence = re.match("`+", markdown[index:])
            assert fence
            width = len(fence.group())
            closing = re.compile(rf"(?<!`)`{{{width}}}(?!`)").search(
                markdown, index + width
            )
            if closing:
                content = markdown[index + width : closing.start()]
                if (
                    len(content) >= 2
                    and content[0] == " "
                    and content[-1] == " "
                    and content.strip()
                ):
                    content = content[1:-1]
                out.append(content)
                index = closing.end()
            else:
                out.append(fence.group())
                index += width
            continue
        if char == "[":
            link = _LINK.match(markdown, index)
            if link:
                if references is None:
                    raise ValueError(f"Link not allowed here: {link.group()}")
                label = to_terminal(link["label"])
                title = link["title"]
                if len(title) > MAX_TITLE_LENGTH or not title.strip():
                    raise ValueError(f"Invalid link title: {title!r}")
                references.append((label, title, link["url"]))
                out.append(f"{label} [{len(references)}]")
                index = link.end()
                continue
        out.append(char)
        index += 1
    return "".join(out)


# Output
# ------


# Render a hint as an output block. Each block starts with a line exactly
# `ID: <id>` and ends immediately before the next `ID:` or at the end of
# output; tests identify hints by that line rather than by wording.
def render_block(hint: Hint) -> list[str]:
    references: list[tuple[str, str, str]] = []
    text = to_terminal(hint.text, references)
    if hint.as_of_last_fetch:
        text = f"As of last fetch: {text}"
    lines = [f"ID: {hint.id}", f"Priority: {hint.priority.value}", text]
    lines += [
        f"[{number}] {label}: {title} {url}"
        for number, (label, title, url) in enumerate(references, 1)
    ]
    lines.append(f"Git stage: {to_terminal(hint.stage)}")
    for command in hint.commands:
        prefix = SAFETY_PREFIX[command.safety]
        lines.append(f"Command: {prefix}{to_terminal(command.text)}")
        lines.append(f"Result: {to_terminal(command.result)}")
    return lines


# Shell quoting
# -------------
#
# Suggested commands must be valid in the user's shell, which on Windows is
# often PowerShell or `cmd` rather than a POSIX shell. Words made of these
# characters need no quoting in any of them:
_SHELL_SAFE = re.compile(r"[A-Za-z0-9_+=:./-]+")
# Double quotes work in POSIX shells, PowerShell, and `cmd` unless the word
# contains a character that one of them still interprets inside double quotes.
_DOUBLE_QUOTE_UNSAFE = set('"$`\\!%')


def shell_quote(word: str) -> str:
    if _SHELL_SAFE.fullmatch(word):
        return word
    if not any(c in _DOUBLE_QUOTE_UNSAFE or ord(c) < 32 for c in word):
        return f'"{word}"'
    # No quoting works everywhere; use the platform's usual shell, which is
    # PowerShell on Windows.
    if os.name == "nt":
        return "'" + word.replace("'", "''") + "'"
    return shlex.quote(word)


# Build a Git command line naming paths. Add `--` when a path could be
# mistaken for an option.
def git_with_paths(
    # The Git arguments preceding the paths, such as `["add"]`.
    args: Sequence[str],
    paths: Sequence[str],
    # True to always separate the paths with `--`.
    separator: bool = False,
) -> str:
    words = ["git", *args]
    if separator or any(path.startswith("-") for path in paths):
        words.append("--")
    words += [shell_quote(path) for path in paths]
    return " ".join(words)


# Format up to `limit` items as code spans, appending "and N more" when items
# are left out.
def summarize(items: Sequence[str], limit: int = 5) -> str:
    shown = [code(item) for item in items[:limit]]
    hidden = len(items) - len(shown)
    if hidden:
        return ", ".join(shown) + f", and {hidden} more"
    if len(shown) <= 2:
        return " and ".join(shown)
    return ", ".join(shown[:-1]) + ", and " + shown[-1]
