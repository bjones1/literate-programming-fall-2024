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

The whole "Development strategy" section was reviewed as one unit with the
prompt shown under [Last LLM review](#last-llm-review). The histories of the
subsections that were reviewed separately before that follow below.

| Round | Findings | Main changes made |
| ----- | -------- | ----------------- |
| 1     | 20       | Inspection may refresh the index's stat cache, so that claim and its test were narrowed; bisect detection stays on `BISECT_START`; the anchor-ID rule now follows Asciidoctor; documentation URLs move to one table with an offline test; `stale-fetch` reads `FETCH_HEAD` and the remote-tracking reflogs; `unpushed-branches` uses one `git log` command; behaviours present only in the code are listed as gaps to adopt. |

### Implementation Strategy review rounds

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
following prompt produced the output below; strikethrough indicates LLM output
that we deemed incorrect or irrelevant. All twenty findings were accepted and
addressed, so nothing is struck through.

```text
Review ONLY the section named "Development strategy" in spec.md, from that heading to the end of the file. Check for technical inaccuracies, contradictions with the rest of spec.md or with the code in src/git_hints/, missing implementation decisions, and ambiguous or untestable statements. Do not review other sections and do not modify any files. Write the findings to docs/specs/review/round-1.md as a numbered list, each with the location, the problem, and why it matters, followed by the total number of findings. Avoid stylistic suggestions.
```

Scope: `spec.md` from the "Development strategy" heading (line 2194) to the end
of the file. Line numbers refer to `spec.md`. Claims about Git were checked
against the Git source at `v2.56.0` and its development branch, and by running
Git 2.56.0.

1. **Location:** Implementation Strategy, Repository Inspection (lines
   2290–2306).
   **Problem:** The section says `GIT_OPTIONAL_LOCKS=0` prevents optional index
   refresh writes and that plain `git-hints` does not modify repository state.
   It then gives a test case built on that claim. In Git only `git status`
   honors the variable: `use_optional_locks()` has a single caller,
   `builtin/commit.c:1655`. Porcelain `git diff`, which the hints run as
   `git diff --quiet`, `git diff --cached --quiet`, and `git diff --name-only
   ... -z`, calls `refresh_index_quietly()` (`builtin/diff.c:237–250`,
   `649–650`). Because `diff.autoRefreshIndex` defaults to true, that call
   takes the index lock and rewrites the index whenever a path differs only in
   its stat data. I reproduced it: after `os.utime()` on a committed file,
   `GIT_OPTIONAL_LOCKS=0 git diff --quiet` changed the bytes of `.git/index`,
   and so did running the installed `git-hints --all --ids-only` from the
   project's `.venv`.
   **Why it matters:** The test case as written fails against the current
   code, and "does not intentionally modify repository state" is false. The
   section makes no decision about the fix, for example running
   `-c diff.autoRefreshIndex=false` or switching to the plumbing commands
   `git diff-files` and `git diff-index`.

2. **Location:** Development strategy introduction (lines 2200–2201) and
   Implementation Strategy, Testing and Validation (lines 2384–2390).
   **Problem:** The introduction says each subsection ends with how its work
   will be implemented and tested in the next phase. Implementation Strategy
   ends instead with a description of the existing 58 tests and defers to the
   other subsections. The index-bytes test case in Repository Inspection is not
   in the suite: no test uses `os.utime`. No step adds it or names the file it
   belongs in.
   **Why it matters:** Work that this subsection requires has no
   implementation step. Together with finding 1, a test that is already known
   to fail has no owner.

3. **Location:** Rules (lines 2243–2246) and Specification gaps (lines
   2524–2583).
   **Problem:** Specification gaps lists only four items, but the code differs
   from the specification in more places:
   * `bisect-in-progress` is a proactive hint registered in `CHECKS`
     (`src/git_hints/proactive.py:238`). It is not defined anywhere in the
     specification.
   * `implementation_notes.md` records further deviations: `not-a-repo` also
     suggests `git init` and links to `git-init`; `behind` and `diverged` are
     suppressed during any paused operation; `tracked-but-ignored` is
     suppressed while conflicts exist; and `explain` prints `No hints.`.
     Output Rendering (line 2366) now states the last of these, although the
     CLI commands section does not.

   The rule says that "the specification is corrected first and the code then
   follows". It does not say whether a divergence is settled by adopting the
   code's behavior into the specification or by removing it from the code.
   **Why it matters:** The new offline link test (check 2, line 2477) requires
   every URL in the code to appear in a hint section of the specification.
   `https://git-scm.com/docs/git-bisect` and `https://git-scm.com/docs/git-init`
   appear in none, so that test fails whatever the anchor work does. The
   `BISECT_LOG` change also alters `bisect-in-progress`, which the plan never
   mentions.

4. **Location:** Specification gaps, "Bisect is detected through a different
   file than Git uses" (lines 2560–2567).
   **Problem:** The section says Git checks `BISECT_LOG` and on that basis
   switches the specification to it. Git itself is inconsistent here. `git
   status` checks `BISECT_LOG` (`wt-status.c:1877–1890`). The bisect command
   checks `BISECT_START`: `bisect_autostart()` prints `You need to start by
   "git bisect start"` when `BISECT_START` is missing or empty, and
   `bisect_reset()` reads `BISECT_START` (`builtin/bisect.c`). Cleanup also
   deletes `BISECT_LOG` before `BISECT_START` (`bisect.c:1212–1222`).
   I reproduced the difference: with only `BISECT_LOG` present, `git status`
   reports "You are currently bisecting", while `git bisect good` answers `You
   need to start by "git bisect start"`.
   **Why it matters:** The decision rests on half of Git's behavior. Under the
   new rule, the state that is newly reported as a bisect, with only
   `BISECT_LOG`, is one in which the bisect commands that `bisect-in-progress`
   suggests do not work. In that same state, `detached-head` is suppressed.

5. **Location:** Specification gaps, Implementation in the next phase, step 2
   (lines 2574–2576).
   **Problem:** The only new test creates `BISECT_START` alone. No case creates
   `BISECT_LOG` alone, which is the positive half of the new rule ("in
   progress exactly when that file exists, whether or not `BISECT_START`
   does"). An implementation that requires both files passes the existing test,
   because `git bisect start` creates both, and it also passes the new one.
   **Why it matters:** The rule as stated is not fully testable with the
   planned tests, so a wrong implementation would go unnoticed.

6. **Location:** Documentation anchors and CodeChat markup, "Choosing and
   deriving anchors", rule 2 (lines 2419–2422).
   **Problem:** The rule says every run of characters other than letters and
   digits becomes `_`. Asciidoctor instead deletes characters other than word
   characters, spaces, hyphens, and periods, and it replaces only spaces,
   hyphens, and periods with `_`. The live site confirms this. On `git-svn`,
   REBASE VS. PULL/MERGE has the ID `_rebase_vs_pullmerge`, where the rule
   gives `_rebase_vs_pull_merge`. On `git`, File/Directory Structure has the
   ID `_filedirectory_structure`.
   **Why it matters:** Offline verification and the maintenance script both
   depend on this rule. Using it, they would reject correct anchors and accept
   anchors that do not exist.

7. **Location:** Documentation anchors and CodeChat markup, Testing (lines
   2473–2481), and "Where the links live" (lines 2463–2469).
   **Problem:** The section never says how the test "reads every documentation
   URL in the hint modules". The code splits URLs across adjacent string
   literals: `"(https://git-scm.com/docs/git-config"` is followed by
   `"#Documentation/git-config.txt-username "` in `proactive.py` at lines
   1032–1033. It also builds `git-{operation}` in an f-string. A scan of the source
   text would read the `git-config` URL without its fragment, so check 3 would
   skip it, and it would need special handling for templates. Extracting URLs
   at run time would require constructing every hint, and most hints need
   repository state for that. On the specification side, `operation-in-progress`
   gives `https://git-scm.com/docs/git-<operation>` as a placeholder. The
   expanded URLs appear only in its test case, so it is undefined whether they
   "appear in a hint section" (check 2). A single fragment on a templated URL
   would also apply to four pages whose section names differ.
   **Why it matters:** Whether the test passes depends on these undecided
   points. The rule that "the code copies it exactly" cannot hold for
   templated links.

8. **Location:** "Choosing and deriving anchors" (lines 2433–2438) and Testing
   (lines 2479–2485).
   **Problem:** The rule "a whole-page link remains only when neither works,
   and the reason is recorded" has no check. The test inspects only URLs that
   have a fragment, so a hint module containing nothing but whole-page links
   passes. Text fragments quote rendered wording, but the planned offline
   verification uses the `.adoc` source, where `linkgit:`, backticks,
   attributes, and includes do not match the rendered text. The section does
   not say how text fragments are verified, either by the test or by the
   maintenance script. It also does not give the path or format of the
   "checked-in list of verified anchors".
   **Why it matters:** The main goal of the subsection, replacing whole-page
   links, can pass the test without a single anchor being added. Text-fragment
   links have no defined way to be verified.

9. **Location:** CodeChat markup and Implementation steps 4–5 (lines
   2489–2519), and the rule "Every change comes with a test" (lines
   2240–2242).
   **Problem:** The markup work has no test. Nothing checks that each
   `cc-...` ID is unique "across the project", that each gather heading lists
   IDs that exist, or that every hint has fragments for both its code and its
   tests. The section also says a fragment covers its doc block plus the next
   block only. The hint functions contain comments of their own, such as the
   `# Step 1:` to `# Step 5:` comments in `detached_head`, and the CodeChat
   Editor treats those as separate doc blocks. A marker placed before such a
   function therefore covers only the code up to its first internal comment,
   and the section does not say how `following` should be set for each
   function. Separately, the rule says tests use the four repository helpers,
   which an offline URL test or markup test has no reason to do.
   **Why it matters:** The markup can be incomplete or broken with every check
   still passing. The step also contradicts the strategy's own rule that every
   change comes with a test.

10. **Location:** New proactive hints, "Keep track of stash entries?" (lines
    2615–2639 and test step 3, lines 2668–2672).
    **Problem:** The placeholder `<n>` stands for both the entry count and a
    stash index.
    * With `<n>` set to `1 stash entry` as specified, the text "This
      repository has `<n>` [stash entries](...)" renders as "1 stash entry
      stash entries".
    * The Command uses `<n>` as an index, but the test expects the literal
      commands `git stash show -p 0`, `git stash apply 0`, and `git stash drop
      0`. The section does not say which index is rendered: always 0, or one
      per listed entry.
    * `<list>` is "up to five lines" inside a sentence, but the section does
      not give the separator. Hint structure, item 4, allows only inline
      Markdown.

    **Why it matters:** No one can produce the output the test expects from
    the definition alone, so implementations will differ.

11. **Location:** "Push your other local branches?", hint text (lines
    2685–2686) and conditions 4.1–4.2 (lines 2720–2727).
    **Problem:** For a branch with no upstream, "commits that exist only in
    this local repository" is checked against all remote-tracking branches
    (`--not --remotes`). For a branch with an upstream, `[ahead <k>]` compares
    the branch only with its own upstream. Those commits may already exist on
    another remote-tracking branch, for example after `git push origin
    feature:main`, yet the hint still says they exist only locally.
    **Why it matters:** The hint makes a false statement about the very
    confusion it is meant to resolve: whether changes are local only or
    already pushed.

12. **Location:** "Push your other local branches?", `<list>` format (lines
    2688–2689) and condition 3 (lines 2712–2719).
    **Problem:** The entry `(ahead of <upstream> by <k> commits)` needs an
    upstream name, but the `for-each-ref` format reads only the remote name and
    the remote ref (`origin` and `refs/heads/feature`). It does not read the
    remote-tracking name (`origin/feature`, which `%(upstream:short)` would
    give). With a custom fetch refspec, the two differ. The section also does
    not specify singular forms for `<k>` and `<n>`, although the
    `stash-entries` hint does.
    **Why it matters:** The specification leaves the exact output text undefined,
    and no test step pins it down.

13. **Location:** "Push your other local branches?", conditions 1–2 (lines
    2706–2711).
    **Problem:** The hint is suppressed during a rebase "because HEAD is
    detached, and the branch being rebased would be listed". The same thing
    happens during a bisect: HEAD is detached, "no branch is excluded", and the
    branch recorded in `BISECT_START` is listed as one of the "other" branches.
    Yet bisect is not in the suppression list, and the hint text says "Besides
    the current branch".
    **Why it matters:** The suppression rule contradicts its own stated reason,
    and the bisect case is untested.

14. **Location:** "Push your other local branches?", condition 4.1 (lines
    2721–2723).
    **Problem:** The condition runs one `git rev-list --count` for each branch
    that has no upstream, with no upper bound. The "and N more" count requires
    evaluating every such branch, even though only five are listed. `git.py`
    itself notes that every Git process costs tens of milliseconds,
    particularly on Windows.
    **Why it matters:** The section is missing a decision on batching or
    limiting these calls. In a repository with many local branches, every plain
    `git-hints` run gets noticeably slower.

15. **Location:** "Fetch to see the newest remote commits?", summary (lines
    2601–2603), conditions 2–3 (lines 2785–2797), and test step 2 (line 2810).
    **Problem:** The summary promises that the hint reports remote-tracking
    branches not updated for more than a day. The conditions instead measure
    the modification time of `FETCH_HEAD`, and that is a different thing:
    * `git clone` and `git push` update remote-tracking branches without
      writing `FETCH_HEAD`. I verified that after a clone and a `push -u`, no
      `FETCH_HEAD` exists. The hint therefore fires right after a fresh clone,
      and test step 2 requires it to.
    * Fetches run in other linked worktrees update the shared remote-tracking
      branches, but their `FETCH_HEAD` files are ignored.
    * A fetch of any remote refreshes `FETCH_HEAD`. After fetching remote A,
      the hint goes silent even though the upstream on remote B is still stale.

    **Why it matters:** The conditions contradict the stated purpose. A new
    user sees "may be out of date" immediately after cloning. The section
    neither accepts these cases explicitly nor chooses a better signal, such
    as the reflogs of `refs/remotes/*`.

16. **Location:** "Fetch to see the newest remote commits?", `<age>` (lines
    2770–2771).
    **Problem:** "The whole number of days" does not say whether to round down
    or to the nearest day. The hint applies from 24 hours on, so at 47 hours
    rounding down prints "1 days ago" and rounding to the nearest day prints
    "2 days ago". The singular form is also unspecified. The test uses an age
    of exactly two days, where both methods agree.
    **Why it matters:** The output is ambiguous, and the planned test does not
    cover the boundary.

17. **Location:** Specification gaps, "`commit-identity` has no priority class
    or test case" (lines 2531–2533).
    **Problem:** The section says that without the settings, "`git commit`
    fails unless Git finds an identity elsewhere, such as in environment
    variables". In fact Git auto-detects an identity: the email from user and
    host, and the name from the passwd entry (`ident.c`). A commit fails only
    if that name is empty, if the email is detected as bogus ("unable to
    auto-detect email address"), or if `user.useConfigOnly` is set. In an
    isolated run, the commit failed only because the name was empty
    ("empty ident name (for <user@host.localdomain>) not allowed"); the email
    had been detected automatically.
    **Why it matters:** The class decision is justified with an inaccurate
    statement of Git's behavior. One of the test case's own states, where the
    name is set and the email is missing, is usually one in which `git commit`
    succeeds.

18. **Location:** Development strategy introduction, area 4 (lines 2226–2230),
    and New proactive hints, introduction (lines 2587–2603).
    **Problem:** The introduction lists three situations: keeping track of
    stashes; knowing whether changes are local only or already pushed; and
    knowing where a branch lives and whether it has an upstream. The subsection
    merges the second and third into one and adds a different third situation,
    getting the newest remote commits before editing, which leads to
    `stale-fetch`. The introduction never mentions that situation.
    **Why it matters:** The two places disagree on the scope of area 4, so it
    is unclear whether `stale-fetch` belongs to the planned work.

19. **Location:** New proactive hints, introduction (lines 2587–2591).
    **Problem:** The subsection says "the sixteen proactive hints cover only in
    part" and then cites `pull-blocked-local-changes` and `stash-local-changes`.
    Both are reactive hints defined under `git-hints explain`, not among the
    sixteen. The count also leaves out `merge-conflicts`, which is proactive as
    well, and `bisect-in-progress`, which is in the code.
    **Why it matters:** This is a factual inaccuracy about the existing hint
    set, and the gap analysis that motivates the new hints rests on it.

20. **Location:** Implementation Strategy, Hint Detection and Prioritization
    (lines 2309–2311).
    **Problem:** The section says every hint is a check function registered in
    `CHECKS` or `REACTIVE_CHECKS`. `rebase-after-repeated-integration-failures`
    is in neither list: `explain` appends it after updating the counter
    (`reactive.py:481–486` and line 690). `not-a-repo` is not in
    `CHECKS` either.
    **Why it matters:** The architecture description does not match the code,
    and that is the description a contributor would follow when adding or
    moving hints.

Total: 20 findings.

### Last LLM review of Implementation Strategy

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
