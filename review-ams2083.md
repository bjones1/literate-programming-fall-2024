Review of spec section 1 (ams2083)
==================================

This section (spec.md lines 1-15 and 40-234) covers the overview, CLI commands,
Future Work, Hint structure with Repository context, and the introduction to
Implementation. It sets the rules every other hint must follow, so gaps here
show up as inconsistencies everywhere else. The core ideas are sound: priority
classes, permanent IDs, an `ID:` block format, `--all`/`--ids-only` for tests,
and "as of last fetch" labels. Several rules are incomplete, though. Plain
`git-hints` has no general rule for a merge, rebase, or bisect in progress. It
does not handle a bare repository or `--fetch` failures. The `explain` output
format is undefined. Sorting by ID within a priority class can hide the most
important hint behind the three-hint limit. The safety prefix rule is attached
to one priority class, but hints in other classes use it. All five TODOs in the
section can be resolved with the wording proposed below. All experiments used
Git 2.56.0.windows.2 in an isolated environment that matches `git_setup()`, and
Typer 0.27.3 from the project's `.venv`.

### Correctness and detection

1. **Plain `git-hints` has no rule for an unresolved merge conflict. It
   proposes a commit that Git refuses.**
   * Location: Hint structure item 6.1 (line 192). It lists "unresolved merge
     conflicts" as an error/blocked condition. The only conflict hint,
     `merge-conflicts` (line 1049), is reactive.
   * Scenario: the user runs `git merge topic` without `explain`, gets a
     conflict, and then runs `git-hints`. No error/blocked hint appears.
     `staged-changes` (line 599) triggers because `git diff --cached --quiet`
     exits 1, and it suggests `git commit -m "message"`.
   * Verified: in a repository with a conflicting `git merge topic` (exit 1),
     `git diff --cached --quiet` exited 1, `git diff --quiet` exited 1, and
     `git commit -m x` printed "Committing is not possible because you have
     unmerged files" and exited 128. `git branch --show-current` still printed
     `main`.
   * Fix: add a general rule to Hint structure: "While an operation is in
     progress (unmerged index entries, or `MERGE_HEAD`, `rebase-merge`,
     `rebase-apply`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, or `BISECT_START`
     found with `git rev-parse --git-path`), suppress every workflow hint
     whose command would fail or interfere, and show a proactive error/blocked
     hint for the operation." The simplest way to do that is to make
     `merge-conflicts` both proactive and reactive. Today `unstaged-changes`,
     `staged-and-unstaged-changes`, and `detached-head` each reimplement part
     of this check.

2. **A bare repository, or a directory inside `.git`, gets neither the context
   line nor `not-a-repo`.**
   * Location: Repository context (line 140, "inside a Git working tree") and
     the `not-a-repo` condition (line 324, exit 128 only).
   * Verified: inside `.git` and inside a bare repository,
     `git rev-parse --is-inside-work-tree` printed `false` and exited 0, and
     `git branch --show-current` printed `main` and exited 0. Outside any
     repository, both exited 128 ("not a git repository").
   * Why it matters: no rule covers `false` with exit 0. An implementation
     might print nothing, crash, or run working-tree commands such as
     `git diff`, which fail in a bare repository.
   * Fix: add "If `git rev-parse --is-inside-work-tree` prints `false`, print
     `Not inside a working tree (bare repository or .git directory); run
     git-hints from the project directory.`, show no hints, and exit 0." You
     could also give it its own ID, such as `not-a-work-tree`.

3. **`--fetch` does not say what happens when the fetch fails, times out, or
   has no remote.**
   * Location: CLI commands item 1.5 (line 78).
   * Verified: `git fetch` with no remotes exited 0 and printed nothing. With
     only a remote named `other` and no upstream, it also exited 0 silently.
     With an `origin` that points at a missing path, it exited 128, both
     attached and detached. `git fetch -h` lists `--[no-]auto-maintenance`. A
     fetch normally runs `git maintenance --auto` afterward, which could use
     up the 10-second budget.
   * Why it matters: the Language and libraries section (line 1391) says
     plain `git-hints` exits nonzero only on unexpected inspection failures. A
     network failure is expected, so the spec should say so. It also doesn't
     say whether the "as of last fetch" label is dropped after a successful
     fetch, or what `--ids-only --fetch` prints when the fetch fails.
   * Fix: replace item 1.5 with:

     > `--fetch`: before inspecting, run `git fetch --quiet
     > --no-auto-maintenance` with `GIT_TERMINAL_PROMPT=0`, standard input set
     > to `subprocess.DEVNULL`, output captured, and a 10-second timeout. Git
     > fetches the current branch's upstream remote, or `origin`. Skip the
     > fetch outside a working tree. If it exits 0, omit the "as of last fetch"
     > labels. If it exits nonzero or times out, print `Fetch failed; showing
     > results as of last fetch.` after the context line (omit it with
     > `--ids-only`), keep the labels, and continue; this is not an inspection
     > failure. Without this option, never fetch, and label `push-ahead`,
     > `behind`, and `diverged` "as of last fetch".

     Check that `--no-auto-maintenance` exists in Git 2.32, the minimum
     version. I confirmed it only on 2.56.

4. **Sorting by ID within a priority class, combined with the three-hint
   limit, hides `detached-head` and `no-commits` exactly when they matter
   most.**
   * Location: Hint structure item 6 (lines 208-209); CLI commands item 1.
   * Scenario: on a detached HEAD with a file that is both staged and
     modified, plus one untracked file, four workflow hints trigger:
     `staged-and-unstaged-changes`, `staged-changes`, `unstaged-changes`, and
     `untracked-files`. The informational `detached-head` comes fifth, so
     default output never shows it. A new commit there can be lost when the
     user switches away. An empty repository with similar changes hides
     `no-commits` the same way.
   * Verified: after `git switch --detach` with that setup, the conditions
     from the hints gave `git diff --cached --quiet` exit 1, `git diff
     --quiet` exit 1, `git status --porcelain=v1` lines `MM a` and `?? new`,
     and `git symbolic-ref --quiet --short HEAD` exit 1. Those are the
     triggering results for all five hints. I could not run `git-hints`
     itself, so the hidden fifth hint follows from the spec's rules rather
     than from observed output.
   * The class definitions add to the confusion. "Data-loss risk" (line 195)
     keys on "an action", but it does not say whether that is the suggested
     command or the user's likely next step. As a result,
     `rebase-after-repeated-integration-failures` (line 1253) ranks above
     every workflow hint because its suggestion is risky. Meanwhile
     `detached-head`, a state that does risk losing commits, is
     informational.
   * Fix: (a) classify a hint by the state it reports, and use the safety
     prefix (finding 5) for the risk of the command it suggests. (b) Replace
     "order them by their permanent hint ID" with an explicit ranked list of
     IDs in Hint structure, and use IDs, sorted by code point, only as a
     tiebreak for hints missing from the list. (c) Consider making
     `detached-head` data-loss risk when HEAD has commits that no branch
     contains, which `git for-each-ref --contains HEAD refs/heads` reports as
     empty output.

5. **The safety prefix rule applies only to the data-loss class, but other
   hints use the prefixes. The `safety:` field that every hint declares is
   never defined.**
   * Location: Hint structure item 6.2 (lines 198-202).
   * Conflicts: `diverged` (line 497) is workflow / `safety: safe` but
     suggests `Caution: git pull --rebase`. `pull-blocked-local-changes`
     (line 1102) uses `Warning:` and is error/blocked / `safety: safe`. Every
     hint ends with `safety: safe|caution`, a field this section never
     defines. Item 6.2 also exempts only "read-only actions", which taken
     literally requires a prefix on `git add` and `git commit`.
   * Fix: make it a separate numbered item:

     > Safety prefixes apply to every suggested command, whatever the hint's
     > class. Prefix a command with `Caution:` when it rewrites commits or
     > moves a branch away from them while they stay recoverable through the
     > reflog (`git pull --rebase`, `git commit --amend`). Prefix it with
     > `Warning:` when it can permanently lose uncommitted, staged, or
     > untracked work, a stash, or commits on a remote (`git reset --hard`,
     > `git clean -f`, `git stash drop`, `git push --force`). Name what could
     > be lost and tell the user to back it up first. Other commands need no
     > prefix. A hint's `safety` field is the strongest prefix it uses:
     > `safe`, `caution`, or `warning`.

     After this change, `diverged` becomes `safety: caution`.

6. **The output format of `git-hints explain` is undefined, and tests cannot
   request IDs from it.**
   * Location: CLI commands item 4 (lines 93-111); Hint structure items 7-8;
     the Repository context section.
   * Missing rules: whether `explain` prints the context line, whether the
     three-hint limit applies, where Git's standard error and the exit code
     appear relative to `ID:` blocks, what text the exit code line uses, and
     how `--all`/`--ids-only` are passed. Under item 7, captured standard
     error printed after the hints becomes part of the last hint block. The
     reactive test cases (lines 1076, 1155, 1222, 1277) check that a hint ID
     "appears", but no ID-only output exists for them.
   * Verified with a Typer app built as item 4 specifies (callback with
     `--all`/`--ids-only`, `explain` with `allow_extra_args` and
     `ignore_unknown_options`):
     * `git-hints --all explain -- git push` set `--all` in the callback and
       passed `['git', 'push']`.
     * `git-hints explain --all -- git push` passed `['--all', 'git', 'push']`
       to `explain`, which the "must start with `git`" rule rejects.
     * `git-hints explain git pull --rebase` without `--` also worked.
     * `git-hints explain -- git log -- foo` kept the inner `--`.
   * Fix: add to item 4:

     > Options go before `explain` (`git-hints --ids-only explain -- git
     > push`); `--fetch` is rejected with `explain`. Run Git, re-emit its
     > captured standard error to standard error, then print `Git exited with
     > code <n>.` and every triggered reactive hint on standard output, in the
     > item 7 format, with no context line and no three-hint limit. With
     > `--ids-only`, standard output holds only IDs. A nonzero exit code is an
     > error. On exit code 0 print `No error detected.` If the argument list
     > does not start with `git`, print an error to standard error, run
     > nothing, and exit 2.

     This also fixes line 99, "instead generating an appropriate hint", which
     can be read two opposite ways.
   * Related: `rebase-after-repeated-integration-failures` (line 1256) must
     count failures across runs, but the CLI section defines persistent state
     only for the future-work `dismissals.json`. Add "Store persistent state
     in the directory given by `git rev-parse --git-path git-hints`." Use
     `--git-path`, not the Git directory, so that linked worktrees behave
     consistently.

### Output format

7. **The plain-text link rendering example breaks sentences, and no Markdown
   subset or parser is specified.**
   * Location: Hint structure item 5 (lines 177-187).
   * Scenario: applying the example "Git status — Shows the working tree ...
     Documentation: https://..." inline to the `unstaged-changes` text gives
     "Do you want to stage — Also called the index; select which changed files
     to store in a commit. Documentation: https://git-scm.com/docs/git-add
     files?". The spec also never says whether backticks around code spans
     are kept. Language and libraries names no Markdown library, and later
     hints use constructs that a simple regex mishandles: a code span inside
     a link label, and links with no title (lines 1250-1251).
   * Fix: "Hints use only plain text, code spans, and inline links of the
     form `[label](url "title")`. The title is required and contains no `"`.
     In plain-text output, print the label inline followed by `[n]`, strip
     backticks, and after the hint text print one line per link: `[n] label:
     title url`." Example:

     ```
     Do you want to stage [1] files?
     [1] stage: Also called the index; select which changed files to store in
         a commit. https://git-scm.com/docs/git-add
     ```

8. **The overall output layout is unspecified, which leaves TODO item 8
   open.**
   * Location: CLI commands item 1 (line 47); Repository context; Hint
     structure items 7-8 (lines 216-225).
   * Missing rules: whether the context line or the additional-hints notice
     comes first, the notice wording, the output when no hint triggers, where
     the "as of last fetch" label goes, and where the hint text, Git stage,
     command, result, and priority go inside a block. Tests at lines 866 and
     986 already require `Branch: ...` to be the first line, so the notice
     must come second. Later tests also refer to hint titles such as
     **Push?** and **Clone a repo?** (lines 306, 334), but titles are not a
     defined field.
   * Fix: resolve TODO item 8 with a normative template such as:

     ```
     Branch: main
     2 more hints available; run `git-hints --all` to see them.
     ID: behind
     Priority: workflow
     As of last fetch: Do you want to pull [1] the newest remote commits ...
     [1] pull: Fetches commits from the remote ...
         https://git-scm.com/docs/git-pull
     Git stage: You are working in the local repo, which is missing ...
     Command: git pull
     Result: git status reports that your branch is up to date.
     ```

     Specify the notice exactly as `<n> more hint(s) available; run
     "git-hints --all" to see them.`. With zero hints, print `No hints.`
     after the context line. Decide whether hint titles exist. If they don't,
     change tests 306 and 334 to identify hints by ID.

9. **`--ids-only` is defined in three places, and many tests use it without
   `--all`, which makes their "absent" checks vacuous (TODO at line 75).**
   * Location: CLI commands item 1.4 (line 74), Repository context (lines
     146-149), item 7 (line 220), and Testing (line 1450).
   * Conflict: Testing says to use `--all --ids-only` for presence checks.
     These lines use `--ids-only` alone: 467, 476, 478, 480, 481, 518, 765,
     771, 780, 785, 794, and 799. Without `--all`, an ID can be missing
     because the three-hint limit cut it, so a negative assertion can pass
     even when the hint triggered. Today these tests only pass because of
     alphabetical luck. For example, `many-changed-files` sorts first among
     workflow IDs.
   * Fix: replace item 1.4 with the following, delete lines 146-149, and
     point line 220 at it. Ask the owners of those tests to add `--all`.

     > `--ids-only`: print only the IDs of the hints that would be displayed,
     > one per line, in display order. Print nothing else: no context line,
     > no additional-hints notice, no labels, and no fetch messages. Print
     > nothing if no hint triggers. The three-hint limit still applies;
     > combine with `--all` to list every triggered ID. Exit codes are
     > unchanged. Tests use `git-hints --all --ids-only` to check whether an
     > ID is present or absent.

10. **Repository context should be a numbered item (TODO at line 135), and
    its rebase behavior is worth stating explicitly.**
    * Verified: `git branch --show-current` printed an empty line and exited
      0 when HEAD was detached, during `git bisect start HEAD HEAD~2`, and
      during a stopped `git rebase --exec false HEAD~1`. On an unborn `main`,
      it printed `main`. So the spec's `Branch: detached HEAD` rule matches
      Git, including the expectations in the `detached-head` test. During a
      rebase, though, the user sees "detached HEAD" rather than the branch
      being rebased.
    * Fix: remove the `### Repository context` heading and add as Hint
      structure item 1:

      > Repository context: in normal output and with `--all`, when
      > `git rev-parse --is-inside-work-tree` prints `true`, the first output
      > line is `Branch: <name>`, using `git branch --show-current`. If that
      > prints nothing (detached HEAD, including during a rebase or bisect),
      > print `Branch: detached HEAD`. The context line is not a hint, has no
      > ID, and does not count toward the three-hint limit. `--ids-only`
      > omits it. (sbe80; clarified by drj228)

      Optionally, add `(rebasing <branch>)` from
      `git rev-parse --git-path rebase-merge/head-name` later. That would
      require changing the exact-line assertions at lines 889 and 905.

### Structure and consistency

11. **Hint IDs have no format rule, and several later hints lack IDs, have
    duplicate IDs, or have malformed fields.**
    * Location: Hint structure item 7 (line 211).
    * Conflicts:
      * Item 7 gives `commit-identity` as an example, and lines 70 and 935
        refer to it, but item 10 at line 620 defines no ID.
      * These items have no ID, priority, or Git stage: the gitignore item
        (line 527), the protected-branch item (line 1019), and "Push failed?"
        (line 1175).
      * "Pull remote changes?" (line 1295) is an empty template.
      * `pull-before` (line 1318) has the same condition as `behind` but
        classifies it as error/blocked, although being behind blocks nothing.
        It also requires `git fetch`, which `--fetch` forbids by default.
      * Test Cases 14 and 15 identify hints by title rather than ID.
      * Priority classes use inconsistent spelling: `Informational` (line
        320) versus `informational` (line 820).
    * Fix: add "IDs are lowercase ASCII kebab-case
      (`[a-z][a-z0-9]*(-[a-z0-9]+)*`), unique across proactive and reactive
      hints, and never reused. Write priority classes exactly as
      `error/blocked`, `data-loss risk`, `workflow`, or `informational`." Ask
      the owning reviewers to fill in or delete the items listed above.

12. **Text fragment TODO (line 173): replace the bold example with a short
    rule that prefers existing anchors.**
    * Why: git-scm.com already gives options and environment variables
      anchors, and the Testing section uses them (for example,
      `https://git-scm.com/docs/git#Documentation/git.txt-GITCONFIGGLOBAL`).
      Anchors are more stable than text fragments, which break when the page
      wording changes.
    * Fix:

      > Each link to a Git manual page points at the passage the hint
      > summarizes. Use the page's existing anchor if it has one. Otherwise
      > append a [text fragment](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Fragment/Text_fragments)
      > `#:~:text=<start>[,<end>]` that quotes text appearing verbatim on the
      > page, with `-`, `,`, and `&` percent-encoded. For example,
      > `https://git-scm.com/docs/git-push#:~:text=Updates%20one%20or%20more%20branches`.
      > The link must still be useful in a browser that ignores the fragment.

    * I did not check fragment URLs against git-scm.com, because this review
      used no network access.

13. **Future Work holds one unrelated item while the real future-work items
    are scattered through CLI commands (TODO at line 130).**
    * Location: Future Work (lines 123-131). The CLI items `--exclude`,
      `--dismiss`, `def`, `howto`, and `--bug` are each marked "Future work.
      Do not implement."
    * Resolution: the CodeChat item is not part of `howto`. It shows a
      definition and a link for a term, which is what `git-hints def` does.
      Move `def`, `howto`, `--bug`, `--exclude`, and `--dismiss` under Future
      Work, and add the CodeChat item as a sub-item of `def`: "An editor such
      as the CodeChat Editor could call `git-hints def <term>` to show inline
      definitions." `def` takes a `<command>`, but "repo" is a term rather
      than a command, so change its argument to `<term>`. CLI commands then
      lists only what to build.
    * Related: item 6 (line 121) asks for help examples using
      `git-hints def status` and `git-hints howto commit`, which must not be
      implemented. Use `git-hints --all` and
      `git-hints explain -- git pull` instead.
    * Before `--bug` is implemented, require a preview and the user's
      consent. Repository state can include file names and remote URLs with
      embedded tokens, and the bug report would post it to a public tracker.

14. **The required fields are weakened by "actionable" and "about a specific
    task", with no list of exempt hints.**
    * Location: Hint structure items 1 and 3 (lines 151 and 160); the
      overview (line 11) says "each hint" shows a command and a link.
    * Conflict: item 2 requires a one-sentence Git stage, but
      `no-upstream-branch` (line 538) and `untracked-files` (line 643) use two
      or three sentences. `not-a-repo` (line 318) gives a command with no
      expected result.
    * Fix: "Every hint has hint text with at least one documentation link, a
      one-sentence Git stage, at least one command with its expected result,
      an ID, a priority class, and a safety level."

### Minor

* Line 133: `<h2 id="cc-SbouyCXTsP">` is raw HTML in an otherwise setext
  document, and nothing links to the ID. Use `Hint structure` with a `---`
  underline.
* Line 82: add a blank line before `2. git-hints def` so the nested list
  closes cleanly.
* Line 102: say where `windows_expand_args=False` goes. Pass it as
  `app(windows_expand_args=False)` from the wrapper entry point, as
  `pyproject.toml` already does. It applies to the whole CLI. Verified: without
  it, Typer turned a quoted `'*.py'` into the matching file names and `'~'`
  into `C:\Users\bj147`, the real profile directory, even though `HOME` was
  redirected. With it, both arguments passed through unchanged.
* Line 97: `--` is optional in practice (verified above). Say "`--` is
  recommended" or reject a missing `--` explicitly.
* Line 59: with linked worktrees, "inside the repository's Git directory" is
  ambiguous. Use `git rev-parse --git-path git-hints/dismissals.json`.
* Line 177: say what "160 characters" counts (Unicode code points).
* Typos: line 99 "instead generating" should be "instead of generating"; line
  171 "Its similar" should be "It's similar"; line 172 "specifc" should be
  "specific"; line 128 "Purpose of this feature" should be "The purpose of this
  feature".
