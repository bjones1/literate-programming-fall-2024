Project 2 submission
====================

Team members are Aknur Seidazym, Madina Amangeldi, Zhassulan Kainazarov, and
Aiym Takimbayeva. The specification consists of the file [spec.md](spec.md); our
team's section is "Development strategy".

Draft submission
----------------

### Contributions

* Aknur Seidazym: wrote the "Implementation Strategy" section of `spec.md`,
  reviewed it with an LLM over three rounds, and recorded that history in
  [llm-review.md](llm-review.md).
* Madina Amangeldi: verified the build, linters, and all tests on macOS with
  Python 3.10 and 3.14, fixed places where "Implementation Strategy"
  contradicted the rest of the specification (live stderr streaming and
  `os.fsdecode()` decoding) through review rounds 4–7, and assembled this
  `submission.md`.
* Zhassulan Kainazarov: wrote the introduction and ground rules of the
  "Development strategy" section and its "Documentation anchors and CodeChat
  markup" and "New proactive hints" subsections, extended "Implementation
  Strategy" with the module map, the output details, and the
  `GIT_OPTIONAL_LOCKS=0` requirement with its test case, restored the
  specification's original markup, and assembled this `submission.md`.
* Aiym Takimbayeva: wrote the "Specification gaps" subsection of `spec.md` with
  help from Claude Opus 5.5, reviewed it with GitHub Copilot over two rounds,
  and verified the build on Windows.

### Compiler test

The following statements summarize LLM output on each team member's computer,
based on the prompt "Verify that you can compile and run the project in the
current git repo."

#### Aknur Seidazym

OpenAI GPT-6.1-Sol (default effort), macOS, Python 3.14.6: the LLM built and
installed the `git-hints` wheel in a temporary virtual environment, ran
`git-hints --help`, `git-hints`, and `git-hints explain -- git status --short`
successfully, reported that Ruff and ty passed, and ran the test suite with all
58 tests passing. The full output is in
[build-verification.md](build-verification.md).

#### Madina Amangeldi

Claude Opus 5.5 (`claude-opus-5-5`, in Claude Code), macOS 15.3.1, Git 2.39.5:

* `uv sync` built the project and installed its dependencies into `.venv`.
* `uv run git-hints --help` printed the help text, with usage examples and the
  `explain` command.
* `uv run git-hints` printed `Branch: git-tool` and `No hints.`, and exited 0.
* `uv run git-hints explain -- git status --short` printed `Git exited with
  code 0.` and `No error detected.`, and exited 0.
* `uv run ruff check .`, `uv run ruff format --check .`, and `uv run ty check`
  all passed.
* `uv run pytest` passed all 58 tests on Python 3.14.6. Because the
  specification requires Python 3.10 or later, the LLM also ran the suite in a
  separate environment on Python 3.10.12, where all 58 tests passed.
* The working tree was unchanged afterward.

#### Zhassulan Kainazarov

Claude Fable 5.1 (`claude-fable-5-1`, in Claude Code), Arch Linux, Python
3.14.8, uv 0.12.0, Git 2.56.0:

* `uv sync --frozen` installed the project and its dependencies into `.venv`
  without changing `uv.lock`.
* `uv run git-hints --help` printed the help text with the `explain` command.
* `uv run git-hints` printed `Branch: git-tool` followed by the hints for the
  uncommitted edits present at the time, and exited 0.
* `uv run git-hints explain -- git status --short` printed Git's output, then
  `Git exited with code 0.` and `No error detected.`, and exited 0.
* `uv run ruff check .`, `uv run ruff format --check .`, and `uv run ty check`
  all passed.
* `uv run pytest -n auto` passed all 58 tests.
* The working tree was unchanged afterward.

#### Aiym Takimbayeva

GitHub Copilot in VS Code (Agent mode, automatically routed to `gpt-6-luna`),
Windows, Python 3.12.6:

* The LLM built a wheel and installed it in a temporary environment.
* `compileall` completed successfully.
* `git-hints --help`, `git-hints`, and `git-hints explain -- git status
  --short` ran successfully.
* All 58 tests passed.
* The LLM removed the temporary environment afterward and left the working tree
  unchanged.

### Spec review rounds

All rounds reviewed only the "Implementation Strategy" section with the same
prompt, shown under [Last LLM review](#last-llm-review). Rounds 1–3 used OpenAI
Codex (GPT-6.1-Sol); rounds 4–7 used Claude Opus 5.5. Before round 4, two
contradictions with the rest of the specification were fixed by hand: `explain`
now prints captured standard error after Git exits instead of streaming it, and
Git output is decoded as UTF-8 with replacement instead of with
`os.fsdecode()`.

| Round | Findings | Main changes made                                                                                                                                                                                                        |
| ----- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1     | 3        | Clarified lossless filename decoding and invalid UTF-8 handling; added `GIT_OPTIONAL_LOCKS=0` for read-only inspection; specified stdin, stdout, and stderr handling for `explain`.                                     |
| 2     | 1        | Specified real-time stderr streaming while retaining output for hint matching; added an interactive prompt test.                                                                                                        |
| 3     | 0        | No further changes.                                                                                                                                                                                                      |
| 4     | 15       | Named the exact command for untracked files; redirection options are detected only before the Git subcommand; added the exit-code exceptions; limited `GIT_OPTIONAL_LOCKS=0` to inspection; listed the permitted writes. |
| 5     | 11       | Reactive hints appear only on a nonzero exit, with `No error detected.` on success; made the redirection-option list open, as in the specification.                                                                     |
| 6     | 10       | Required `-z` for parsed path lists; listed `FETCH_HEAD` as a fetch write; stated that only `explain` updates the failure counter; added the `explain` output lines and the `--ids-only` behavior.                       |
| 7     | 11       | No changes: every finding asks the section to repeat requirements already defined elsewhere in the specification, which would overspecify the strategy.                                                                 |

### Last LLM review

Prompting Claude Opus 5.5 (`claude-opus-5-5`, in Claude Code) with the
following prompt produced the output below (nested lists merged into
sentences); strikethrough indicates LLM output
that we deemed incorrect or irrelevant. Findings 1–3 and 6–11 restate
requirements that other sections of `spec.md` already define, so repeating them
in the strategy would overspecify it. Finding 4 conflicts with the required
UTF-8 decoding. Finding 5 is already covered: the specification states that
diagnostic-based recognition supports English Git messages only. The review
history from rounds 1–3 is in [llm-review.md](llm-review.md).

```text
Review ONLY the "Implementation Strategy" section of spec.md. Check for technical inaccuracies, contradictions with existing requirements, missing implementation decisions, and ambiguous or untestable statements. Do not review other sections. Do not modify any files. Report only relevant, actionable findings in a numbered list, followed by the total number of findings. Avoid stylistic suggestions and unnecessary expansion.
```

I reviewed only the Implementation Strategy section of spec.md (lines
2194–2289) and checked it against the rest of the spec (CLI commands, Hint
structure, Implementation, Language and libraries, Testing). No files were
modified.

1. ~~**Upstream detection (Repository Inspection):** The strategy treats `git
   status --porcelain=v2 --branch` as the source of upstream status. Its `#
   branch.upstream` line gives a name like `origin/main`, but it cannot tell a
   remote upstream from a local branch with the same name. The `push-ahead`
   hint must not appear for a local upstream, and it needs the remote name and
   branch name separately for `git push <remote> HEAD:<upstream-branch>`. State
   the extra lookup to use, such as `branch.<name>.remote` or `git rev-parse
   --symbolic-full-name @{upstream}`.~~

2. ~~**Operation-state detection is incomplete (Repository Inspection):** "`git
   rev-parse` for operation-state paths" leaves out several required pieces:
   use `--git-path` for `rebase-merge` and `rebase-apply` and check that the
   directory exists; ignore `rebase-apply` when it contains `applying` (that is
   `git am`); detect in the fixed order rebase, merge, cherry-pick, revert;
   check `BISECT_START`; check for unmerged entries with `git diff --name-only
   --diff-filter=U -z`; and for the `rev-parse --verify` checks, map exit codes
   0/1/other to in progress / not in progress / error. Without these, the
   suppression rules cannot be implemented as specified.~~

3. ~~**Unexpected failures are not designed (Git Command Execution):**
   "Distinguish expected Git exit codes from unexpected failures" does not say
   how. The strategy needs to decide how expected exit codes are declared for
   each command, how a missing `git` binary (`FileNotFoundError`) is handled,
   how a failure is reported and which dependent hints are suppressed, and
   which nonzero exit code plain `git-hints` and `explain` return on an
   inspection or launch failure.~~

4. ~~**Re-emitting stderr can change Git's output (Reactive Error Handling):**
   Git's stderr is decoded with `errors="replace"` and then printed again. Any
   bytes that are not valid UTF-8 (such as some filenames) are permanently
   replaced, so the user does not see Git's original error. Decide whether to
   capture raw bytes, write them unchanged to `sys.stderr.buffer`, and decode a
   separate copy only for matching.~~

5. ~~**Locale breaks stderr matching (Reactive Error Handling):** Reactive hints
   and the failure counter match English text such as "Need to specify how to
   reconcile divergent branches", "(fetch first)" and "Not possible to
   fast-forward". Only the tests set `LC_ALL=C`. The strategy needs a decision
   for real users with a non-English locale: either force a C or English locale
   for `explain` (which changes what the user sees) or document that matching
   works in English only.~~

6. ~~**No subcommand parsing (Reactive Error Handling):** Choosing reactive
   hints and qualifying failures depends on knowing the subcommand (`push` or
   `pull`). The strategy mentions "global options before the Git subcommand"
   but does not say how to parse them. Some take a separate value (`-C <path>`,
   `-c <k=v>`, `--git-dir <path>`, `--work-tree <path>`, `--namespace <name>`)
   and some use `=` (`--git-dir=...`). It also does not say how `pull --rebase`
   and `pull --ff-only` are recognised.~~

7. ~~**Required `explain` CLI behaviour is missing:** The strategy does not
   mention these requirements from the CLI commands section: reject arguments
   that do not start with exactly `git` (run nothing and exit 2); reject
   `--fetch` with `explain` without running Git; use `allow_extra_args=True`
   and `ignore_unknown_options=True`; use `app(windows_expand_args=False)` at
   the entry point; include a usage example in each docstring.~~

8. ~~**Reactive hint order is not defined (Hint Detection and Prioritization /
   Reactive Error Handling):** Sorting is described only for proactive hints.
   The spec requires the immediate push or pull failure hint to come before
   `rebase-after-repeated-integration-failures`, and requires `merge-conflicts`
   to be possible after a failed command. The strategy should say whether
   reactive hints use the same class-then-precedence sort or an explicit rule.
   It should also note that `detached-head` gets its priority class when
   evaluated (`data-loss risk` or `informational`, via `git for-each-ref
   --contains HEAD refs/heads`), not a fixed class.~~

9. ~~**Suppression vs. the three-hint limit is ambiguous (Hint Detection and
   Prioritization):** "Before displaying hints, the engine will apply
   operation-in-progress suppression" does not say whether suppression happens
   before or after sorting and truncation. The order must be: suppress, then
   sort, then apply the limit, then compute `<n>` for the "more hint(s)
   available" notice. Otherwise both the shown hints and `<n>` can be
   wrong.~~

10. ~~**Output Rendering leaves out required items:** It does not mention the
    `Branch: <name>` / `Branch: detached HEAD` context line; the
    not-inside-a-working-tree message; `No hints.`; the exact `<n> more hint(s)
    available; run "git-hints --all" to see them.` notice and where it goes;
    `Fetch failed; showing results as of last fetch.`; the "As of last fetch"
    prefix; converting Markdown links into `[n]` references (`[n] label: title
    URL`) and removing code-span backticks; the exact block line order (`ID:`,
    `Priority:`, text, `Git stage:`, `Command:`, `Result:`).~~

11. ~~**Untestable statements:** "Hint IDs will remain stable" cannot be tested
    as written. Replace it with checkable rules: IDs are unique across
    proactive and reactive definitions and match `[a-z][a-z0-9]*(-[a-z0-9]+)*`.
    "Tests will verify … remote behavior" does not say which behaviours, for
    example `--fetch` success, failure or timeout, and the "as of last fetch"
    labelling.~~

Total findings: 11

### Specification gaps review rounds

Aiym Takimbayeva reviewed only the "Specification gaps" subsection with GitHub
Copilot in VS Code (Agent mode, automatic model selection), using the prompt
shown below.

| Round | Findings | Main changes made |
| ----- | -------- | ----------------- |
| 1     | 1        | `git commit` fails without these settings only when Git finds no identity elsewhere, such as in environment variables. |
| 2     | 3        | A bisect is in progress exactly when `BISECT_LOG` exists; the other two findings were rejected, as explained below. |

### Last LLM review of Specification gaps

Prompting GitHub Copilot in VS Code (Agent mode, automatically routed to
`mai-code-1.1-flash`) with the following prompt produced the output below;
strikethrough indicates LLM output that I deemed incorrect or irrelevant.
Finding 1 asks this subsection to repeat detection rules that the Conditions of
`commit-identity` already define, which would overspecify it. Finding 2 does not
apply: conflicts are detected from repository state, never by matching Git's
messages, so neither the Git version nor the output stream matters. Finding 3
was applied.

```text
Review ONLY the "Specification gaps" subsection of spec.md. Check for technical inaccuracies, contradictions with existing requirements, missing implementation decisions, and ambiguous or untestable statements. Do not review other sections. Do not modify any files. Report only relevant, actionable findings in a numbered list, followed by the total number of findings. Avoid stylistic suggestions and unnecessary expansion.
```

1. ~~The `commit-identity` fix is still under-specified: it says the hint should
   use priority class `workflow` and that the test should follow
   `test_commit_identity`, but it does not define the exact detection precedence
   (local config vs global config vs environment variables vs empty values), so
   different implementations can legitimately disagree on whether the hint
   should fire.~~

2. ~~The merge-conflict statement is not a stable contract across Git versions:
   it asserts that Git prints conflict text only on standard output, then says
   the reactive explanation will "say so," but it never specifies the exact
   matching rule for `explain` when Git versions differ or when some commands
   emit conflict markers to stderr. That leaves the behavior ambiguous and not
   reliably testable.~~

3. The bisect fix changes detection from `BISECT_START` to `BISECT_LOG` without
   deciding the compatibility behavior for older Git or partially stale bisect
   state. The subsection says "we switch to `BISECT_LOG`," but it does not
   define what to do when `BISECT_LOG` is missing, when only the older file
   exists, or when the files disagree, so the implementation decision is
   incomplete.

Total findings: 3
