Review of spec section 7 (sbe80)
================================

Section 7 (spec.md lines 1293 to 1509) covers the empty "Pull remote changes?"
placeholder, the `pull-before` hint, Language and libraries (including the
`subprocess` rules for plain `git-hints` and `git-hints explain`), the Testing
helpers and `git_setup()` isolation, and Test Cases 14 and 15. The Language and
Testing material is in good shape: I implemented `git_setup()` exactly as
specified in Python 3.14 on this machine (Windows, Git 2.56.0.windows.2) and the
isolation works. The hint material is not. `pull-before` repeats the `behind`
hint, contradicts the `--fetch` rule, and suggests a command that fails. Test
Cases 14 and 15 repeat existing tests and cite requirement numbers that no
longer exist. My main recommendation is to delete the placeholder,
`pull-before`, and Test Cases 14 and 15, and to tighten the Testing and
`explain` rules as described below.

All experiments ran in a scratch directory with the isolated environment from
the assignment (`HOME`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_NOSYSTEM=1`,
`GIT_CEILING_DIRECTORIES`, `GIT_TERMINAL_PROMPT=0`, `GIT_EDITOR=true`,
`LC_ALL=C`). Local bare repositories served as remotes.

### Correctness of `pull-before`

1. **`pull-before` detects the same state as the existing `behind` hint, so both
   hints would appear together. It also fires on diverged branches, where the
   spec says `behind`-style hints must be replaced. (Resolved)** 

   * Location: Pull before committing, Conditions (line 1320). Compare `behind`
     Conditions (lines 445 to 452) and `diverged` Conditions (lines 507 and
     508).
   * `behind` already covers "the upstream has commits that HEAD lacks". It
     handles ahead/behind correctly by reading `# branch.ab`, uses the "as of
     last fetch" label, and its test covers both 1 and 2 commits behind (steps 7
     to 9). `git rev-list --count HEAD..@{u}` counts only the behind side, so
     `pull-before` also fires when the branch has diverged. The `diverged` hint
     is supposed to suppress `behind` and `push-ahead` in that state, but
     nothing suppresses `pull-before`, so its advice to run `git pull` would
     contradict the `diverged` hint.
   * Verified: after a fetch in the Test Case 14 setup, `git rev-list --count
     HEAD..@{u}` printed `1` and `git status --porcelain=v2 --branch` printed `#
     branch.ab +0 -1`. After one more local commit, status printed `# branch.ab
     +1 -1` and `rev-list` still printed `1`. A plain `git pull` in that
     diverged state failed with `fatal: Need to specify how to reconcile
     divergent branches.` and exit code 128.
   * Fix: delete `pull-before` and the empty "Pull remote changes?" heading
     (lines 1295 to 1347). If raf322 wants anything from them preserved, add it
     to `behind`. Nothing here is missing from `behind`.
2. **`pull-before` runs `git fetch` on every invocation, which the spec forbids
   unless `--fetch` is given.(Technically resolved because this is just being
   removed)** 

   * Location: Pull before committing, Conditions (line 1321). This conflicts
     with CLI commands item 1.5 (lines 78 to 82) and with Language and
     libraries, which says "Do not fetch unless `--fetch` is supplied" (lines
     1369 and 1370).
   * Consequences:
     * Plain `git-hints` would need the network, could hang without a timeout,
       and would update the remote-tracking refs as a side effect. That makes
       the "as of last fetch" labels on `behind`, `diverged`, and `push-ahead`
       inaccurate.
     * The `behind` test, step 11 (lines 479 to 482), would fail. Its first
       `git-hints --ids-only` run would fetch the new commit, so `behind` could
       appear before `--fetch` is ever used.
     * On this machine, the system configuration sets
       `credential.helper=manager`, so an HTTPS fetch could start Git Credential
       Manager. `GIT_TERMINAL_PROMPT=0` only disables Git's own terminal prompt.
       I did not run a network fetch to confirm whether GCM shows a window.
     * The spec does not say how a failed fetch interacts with the exit-code
       rule at lines 1391 to 1393.
   * Fix: delete the hint (see finding 1). If it is kept, remove the `git fetch`
     and rely on `--fetch`.
3. **The suggested command `git pull <name of branch>` fails, because `git pull`
   treats its first argument as a remote, not a branch (Technically resolved).**

   * Location: Pull before committing, Command (line 1316).
   * Verified: in the Test Case 14 `temp1` repository, `git pull main` printed
     `fatal: 'main' does not appear to be a git repository` and `fatal: Could
     not read from remote repository.`, then exited with code 1.
   * Fix: use `git pull`, as `behind` does, or `git pull <remote> <branch>`.
     Also state the expected result, which is that `git status` reports the
     branch is up to date.
4. **The `rev-list` condition exits with code 128 in common states, and the spec
   does not say how to handle that (Technically resolved).**

   * Location: Pull before committing, Conditions (lines 1320 to 1323).
   * Verified: `git rev-list --count HEAD..@{u}` exited with code 128 in each of
     these states:
     * No upstream: `fatal: no upstream configured for branch 'topic'`.
     * Detached HEAD: `fatal: HEAD does not point to a branch`.
     * A repository with no commits: `fatal: no such branch: 'HEAD..'`.
   * Under Language and libraries (lines 1384 to 1393), an unexpected exit code
     is an inspection failure that makes plain `git-hints` exit nonzero. As
     written, running `git-hints` in a new repository or on a new branch would
     report an error. The first sentence is also a double negative: "Determine
     if there are no commits that have not been pulled yet."
   * Fix: covered by deleting the hint. `behind` avoids this problem by reading
     `# branch.ab`, which is absent when there is no upstream.

### Hint structure

5. **`pull-before` lacks most of the required hint fields, and both of raf322's
   headings are in the wrong part of the spec (Technically resolved).**

   * Location: lines 1295 to 1323.
   * Missing or wrong fields:
     * The hint text has no documentation link and no title (Hint structure
       items 3 and 5).
     * There is no "as of last fetch" label.
     * The priority class is error/blocked, but being behind does not block
       committing or any other workflow. `behind` correctly uses workflow.
     * The Git stage sentence ("You are trying to commit and merge") describes
       an intent that a proactive inspection cannot observe.
     * The ID line is missing a comma after `` `pull-before` ``.
   * "Pull remote changes?" (lines 1295 to 1307) contains only empty field
     labels.
   * Both headings are `###` headings that follow "`git-hints explain -- git
     <command>`" (line 1028), so they read as reactive hints. They are actually
     proactive: the test runs plain `git-hints`. The neighboring hints use
     `####`.
   * Fix: delete both, per finding 1.

### Testing section

6. **The Testing section tells tests to call `git_setup()`, but it is an autouse
   fixture, and pytest fails any test that calls a fixture directly.** (Resolved
   In all sections)

   * Location: Testing, line 1447 ("A typical test calls `git_setup()` (provided
     as an autouse fixture)") and lines 1454 to 1458. Most tests copy this, for
     example line 1327 ("Call `git_setup`") and lines 296, 330, 369, 456, 608,
     1059, 1135, 1208, and 1265.
   * Verified: with pytest 9.1.1, a test that called an autouse fixture named
     `git_setup` failed with `Fixture "git_setup" called directly. Fixtures are
     not meant to be called directly`.
   * The section also never states the fixture's scope or how it applies the
     environment:
     * It must use function scope. `config_user()` writes to the
       `GIT_CONFIG_GLOBAL` file, so a shared file would leak identities between
       tests.
     * It must change `os.environ`, for example with `monkeypatch.setenv` and
       `monkeypatch.delenv`. Otherwise a `git-hints` run in-process through
       Typer's `CliRunner` would not see the isolated environment, which
       violates lines 1454 and 1455.
   * Fix: replace the first sentence at line 1447 with: "`git_setup` is a
     function-scoped autouse pytest fixture. It applies the environment above to
     `os.environ` with `monkeypatch`, so tests never call it, and both Git and
     in-process `git-hints` runs inherit it." Then change "Call `git_setup()`"
     in each test to "The autouse `git_setup` fixture provides the isolated
     environment", or delete that step. Test cases 10 and 11 (lines 850 and 967)
     already use this wording.
7. **`git_setup()` isolation works as specified on Windows with Git 2.56.
   However, the `subprocess` rules do not set an output encoding, so Python 3.14
   on Windows corrupts any non-ASCII path or message that Git prints.**
   (Resolved)

   * Location: Language and libraries, item 6 (lines 1384 to 1389), and Testing,
     `git_setup()` (line 1445).
   * Verified isolation, using a Python script that builds the environment
     exactly as lines 1418 to 1445 describe:
     * Starting from a parent environment containing `GIT_DIR`,
       `GIT_AUTHOR_NAME`, and `GIT_CONFIG_COUNT`/`KEY_0`/`VALUE_0`, the only
       configuration shown by `git config --list --show-scope` was `global
       init.defaultbranch=main`.
     * `config_user` wrote to the scratch `GIT_CONFIG_GLOBAL` file, and commits
       were authored by `user1 <user1@foo.com>`.
     * With `GIT_CEILING_DIRECTORIES` set to a stand-in base temp directory
       inside an enclosing repository, `git rev-parse --is-inside-work-tree`
       exited 128. It also exited 128 with a forward-slash path and with the 8.3
       short form of the path. Without the ceiling, the enclosing repository was
       found.
     * A `HOME/.config/git/ignore` file was honored, which confirms the claim at
       lines 1425 and 1426.
     * `GIT_EDITOR=true` made `git commit` without `-m` stop immediately with
       `Aborting commit due to empty commit message.`
     * When `GIT_DIR` was not removed, Git operated on the enclosing repository.
     * The system configuration that `GIT_CONFIG_NOSYSTEM=1` skips contains
       `core.autocrlf=true`, `credential.helper=manager`, and `core.editor=code
       --wait`, so the variable is needed.
     * I could not verify `LC_ALL=C`, because this Git for Windows build ships
       no translations and prints English regardless.
   * Verified encoding: in a repository containing `café.txt`, `git ls-tree -r
     --name-only -z HEAD` run with `text=True` returned `'caf\xc3\xa9.txt'`,
     which is mojibake from the cp1252 default. With `encoding="utf-8"` it
     returned `'caf\xe9.txt'`.
   * Without `-z`, `git diff --name-only` printed `"caf\303\251.txt"` with octal
     escapes and quotes, because `core.quotePath` defaults to true.
     `merge-conflicts` (line 1053) and `pull-blocked-local-changes` (line 1119)
     show these paths to the user.
   * Fix: add to item 6: "Decode Git output as UTF-8 (`encoding="utf-8",
     errors="replace"`), not with the locale default. When a path list is
     parsed, use `-z` or `-c core.quotePath=false`." Also state the minimum
     Python version at item 1.
8. **The minimum Git version of 2.32 is correct for `GIT_CONFIG_GLOBAL`, but the
   spec does not note that the tests are what require it. The `diverged` hint
   also assumes newer pull behavior.** (Resolved)

   * Location: Language and libraries, item 8 (line 1397).
   * Checked against the installed release notes (`RelNotes/*.adoc`):
     * `GIT_CONFIG_GLOBAL` was added in 2.32.0.
     * The other commands and variables that the spec uses are older:
       * `GIT_CONFIG_COUNT`: 2.31.
       * `init -b` and `init.defaultBranch`: 2.28.
       * `switch`, `restore`, and `switch --orphan`: 2.23.
       * `branch --show-current`: 2.22.
       * `stash push`: 2.13.
       * `status --porcelain=v2`: 2.11.
       * `GIT_TERMINAL_PROMPT`: 2.3.
     * So 2.32 is enough for the tests. The tool itself needs only 2.23, because
       it suggests `git switch`.
   * The `diverged` hint (lines 499 and 500) says a plain `git pull` fails on
     diverged branches. That is true on 2.56 (finding 1, exit code 128). Git
     2.27 to 2.33.0 only warned and then merged. I believe the failure was added
     by the pull rework noted in 2.33.1 ("`git pull` had various corner cases
     ..."), but the notes do not name the behavior, and I could not run an older
     Git to confirm.
   * Fix: "Git 2.32 or later. The tests require it for `GIT_CONFIG_GLOBAL`. Hint
     wording assumes the Git 2.34 `git pull` behavior on diverged branches."

### `git-hints explain` rules

9. **Leaving stdout connected to the terminal works for today's reactive hints,
   but only because none of them reads Git's stdout. The spec should state that
   restriction, because some Git failures report only on stdout.** (I do not
   agree with this one because it is redundant)

   * Location: Language and libraries, `git-hints explain` (lines 1372 to 1382).
   * Verified streams (Git 2.56):
     * On stderr: the push rejection (`! [rejected] main -> main (fetch
       first)`); the pull blocked by local changes (`error: Your local changes
       ... overwritten by merge:`, exit code 2 with the ort strategy); the
       blocked `git merge` and `git switch` (exit code 1); and the diverged-pull
       `fatal:` message.
     * On stdout only: the `CONFLICT (content): Merge conflict in foo.txt` and
       `Automatic merge failed` lines from `git pull --no-rebase` (exit code 1),
       and `git commit` with nothing to commit (exit code 1, empty stderr).
   * So `merge-conflicts` cannot use Git's message, and correctly runs `git diff
     --name-only --diff-filter=U` after the command (line 1052).
   * Capturing stderr also has costs:
     * Git suppresses progress meters when stderr is not a terminal (see the
       `--progress` option in git-fetch and git-push).
     * Showing stderr only after the command finishes reverses the order of
       Git's output. For example, during `git pull --rebase` the stdout
       `CONFLICT` line appeared before the stderr `error: could not apply` line.
   * Fix: add: "Reactive hint conditions may use only the command line, the exit
     code, captured standard error, and repository state inspected after the
     command; never Git's standard output." Also consider echoing stderr to the
     terminal as it arrives while keeping a copy, instead of displaying it after
     completion. The sentence at lines 1377 and 1378 repeats lines 1374 and
     1375; delete one of them.

### Test cases

10. **Test Cases 14 and 15 repeat existing tests, cite requirement numbers that
    no longer exist, and assert on hint text instead of IDs.**

    * Location: Test Case 14 (line 1462) and Test Case 15 (line 1485).
    * Duplication:
      * Test Case 14 repeats the `pull-before` test (lines 1327 to 1347) word
        for word, except that it omits the `git_setup` step.
      * Test Case 15 sets up the 2-commits-behind state that `behind` step 9
        (lines 474 to 476) already checks.
    * "Requirement Proactive 7" and "Requirement Proactive 4" refer to a
      numbered list that no longer exists, either in this file or in `HEAD`.
    * The expected texts are swapped relative to the hints:
      * Test Case 14 expects "Is my branch up to date before I start editing?",
        which matches neither hint's text but is closest to `behind`.
      * Test Case 15 expects "Pull needed, your branch is behind!", which is
        `pull-before`'s text.
    * Both tests break the Testing rules:
      * They run plain `git-hints`, not `--all` / `--all --ids-only` (lines 1449
        to 1451).
      * They match wording instead of IDs (Hint structure item 7).
      * They have no negative case, such as checking that the hint is absent
        before the fetch or after `git pull`.
      * Test Case 15 step 5 says "`cd` to `local1`". Tests should pass the
        directory to `make_repo()` or the `subprocess` call, not change the
        process directory.
    * Verified: the Test Case 14 steps produce the stated state. `git clone
      <remote> .` worked in the empty `temp2`, and after the fetch `temp1`
      reported `# branch.ab +0 -1`.
    * Fix: delete both test cases and the TODO heading above them (line 1460).
      The `behind` test already covers both states, with positive and negative
      assertions.
11. **The `pull-before` test has broken list nesting and never tests the hint's
    own fetch.**

    * Location: Pull before committing, Test case (lines 1338 to 1346).
    * Step 4 says "In `temp2`, execute:", but steps 5 to 8 are at the top level
      instead of nested under it, so the numbering suggests they run in `temp1`.
    * Step 9 runs `git fetch` by hand, so the test passes whether or not the
      hint fetches.
    * Step 10 expects the text "Is my branch up to date before I start
      editing?", which is not this hint's text (line 1311).
    * Fix: covered by deleting the hint. If it is kept, nest steps 5 to 8,
      assert by ID with `--all --ids-only`, and add an up-to-date negative case.

### Minor

* Line 1415: `config_user()` should say that it writes to the isolated
  `GIT_CONFIG_GLOBAL` file. Because the setting is global, a later
  `config_user("user2", ...)` changes the identity for every repository in the
  test, not just the current one.
* Line 1404: `make_temps()` returns unnamed directories, but tests refer to them
  as `temp1`, `remote`, and so on. Say "assign the returned directories to
  `temp1`, ...".
* Lines 1395 and 1457: write "pytest", not "Pytest" or "PyTest".
* Line 1372: "starts with `git`". Say whether `git.exe` or a full path to Git is
  accepted on Windows.
* Line 330 (outside this section): setting `GIT_CEILING_DIRECTORIES` to the
  temporary directory's parent repeats what `git_setup()` already does, because
  that parent is the pytest base temp directory.

### Whole-document scan and current-spec follow-up

I also scanned the full current `spec.md`, including the sections assigned to
the other reviewers. The following cross-section issues affect the behavior or
testability of section 7, or are concrete document cleanup recommendations.

12. **`--fetch` failure handling belongs to the CLI review.**

    * Location: CLI commands, item 1.5, and the plain `git-hints` subprocess
      rules.
    * This is assigned to ams2083's overview/CLI review, not section 7. Their
      [review](review-ams2083.md) already examines no-remote, nonzero-exit, and
      timeout behavior, proposes output and exit-status rules, and notes
      `--ids-only` and remote freshness labeling. The same concern is also noted
      in [review-ewj55.md](review-ewj55.md) as a freshness-label consistency
      issue.
    * I am leaving the fetch policy to those CLI findings rather than proposing
      a competing rule here. Section 7 should only be updated after the CLI
      owner settles the behavior, particularly where the general subprocess
      exit-code rule applies to an explicitly requested fetch.
13. **The test helper rules leave the working-directory mechanism unclear.**

    * Location: Testing, `make_repo()` and the paragraph beginning "The
      function-scoped autouse" (current lines 1629 to 1637 and 1671 to 1678).
    * The helper says file lambdas run with `temp_dir` as the current directory
      and then restores the previous directory. The tests also say to run
      `git-hints` in a named temporary repository, but do not specify how the
      command receives that working directory. A subprocess launched without
      `cwd=repo_dir` would run from the pytest process's directory instead.
    * Recommendation: specify that Git and `git-hints` subprocesses receive
      `cwd=repo_dir` and the isolated environment. Have file lambdas use paths
      under `temp_dir` rather than changing the process-wide working directory.
      This gives each helper an explicit repository and avoids ambiguity about
      which checkout a test command operates on.
14. **A minimum Python version is given, but it is not the version used to
    validate the specified CLI stack.**

    * Location: Language and libraries, items 1 and 8 (current lines 1688-1689
      and 1740-1743).
    * The earlier version cited Python 3.5 only because `subprocess` is
      available there, but the spec also requires Typer, pytest,
      `encoding`/`errors` subprocess behavior, and modern project tooling. The
      cited Git minimum was tied to a test-only feature, while the Python
      minimum was not tied to any supported dependency versions. That made it
      unclear what environment implementers must support.
    * Recommendation: give the intended supported Python version based on the
      project dependency metadata, or say this item only describes the standard
      library API and that the project metadata controls the actual minimum.
    * Current status: the spec now sets Python 3.10 and Git 2.34 for both
      application and test environments (lines 1688-1689 and 1740-1743).
15. **The specification still contains unresolved editorial TODOs and a
    temporary deletion area.**

    * Location: Hint structure items 4 and 8 (current lines 163 to 175 and 223
      to 225), Future Work (lines 126 to 131), the `--ids-only` note (lines 75
      to 76), and the temporary area beginning at line 1808.
    * The full-document scan found several open TODOs outside section 7, plus
      the `GOING TO DELETE` area that explicitly says its contents are
      temporary. The temporary area still contains the obsolete pull hint and
      Test Cases 14 and 15 described above. Leaving them in the canonical spec
      makes it unclear which requirements implementers and reviewers should
      follow.
    * Recommendation: resolve or remove the TODOs as part of editorial cleanup,
      and delete the marked temporary area when the review is complete. At
      minimum, retain a clear status marker on any unresolved requirement so it
      cannot be mistaken for normative implementation text.
16. **The specification promises text-fragment documentation links but current
    hints use ordinary manual-page links.**

    * Location: Hint structure item 4 (current lines 163 to 175) and the hint
      examples throughout the implementation.
    * The item says links must highlight the cited manual section through text
      fragments, but its embedded TODO proposes rewriting that requirement.
      Existing links such as `https://git-scm.com/docs/git-pull` do not include
      text fragments, and the review/test examples generally assert only the
      manual URL. Thus it is uncertain whether text fragments are required for
      this initial CLI or whether ordinary official documentation links satisfy
      the requirement.
    * Recommendation: make the requirement explicit and testable: either require
      valid text fragments and add them to hint links, or remove the highlight
      requirement and retain official documentation links with descriptive
      titles. This affects the section 7 recommendation to remove the obsolete
      hint's missing-doc-link complaint only if the broader requirement is
      settled consistently.

### Items in section 7 already corrected in the current spec

The current spec has incorporated several recommendations from the original
review. These findings should not be repeated as open defects after the
temporary material is deleted:

* The autouse fixture is now explicitly function-scoped, applies its variables
  to `os.environ`, restores the prior environment, and must not be called
  directly (current lines 1671 to 1673).
* The subprocess output encoding is now specified as UTF-8 with replacement, and
  parsed path lists must use NUL output or disable `core.quotePath` (current
  line 1615).
* The helper descriptions now say that `make_temps()` returns unnamed
  directories and `config_user()` writes to the isolated global config file
  (current lines 1626 to 1628 and 1638 to 1639).
* The test section now gives explicit `--all` and `--all --ids-only` guidance
  (current lines 1675 to 1678).

The original line numbers at the start of this review refer to an earlier
version of `spec.md`; use the current line references in this follow-up when
editing the present copy.

### Current-spec addendum (2026-10-17)

**LLM-reviewed disclaimer:** The suggestions in this addendum were reviewed with
the assistance of an LLM. They are editorial and technical review
recommendations, not a guarantee that every observation is correct; verify
behavior against the project's chosen Python, Git, and pytest versions before
changing requirements.

This pass checked the current `spec.md`. The normative part of section 7 is now
the Language and libraries and Testing material at lines 1686-1806. The
`pull-before` hint, its empty placeholder, and Test Cases 14 and 15 still appear
at lines 1808-1916, but they are inside the explicitly temporary deletion area.
Several earlier findings are already resolved in the current text: Python's
minimum is now stated, Git output encoding and path parsing are specified, the
pytest fixture is function-scoped and autouse, and test invocations specify both
`cwd` and isolated environment. The items below focus on remaining ambiguities
and current cleanup work; earlier findings marked resolved above should not be
reopened.

17. **Remove the temporary pull material and update the review assignment.**

    * Location: the `GOING TO DELETE` block at lines 1808-1916, and review
      assignment 7 near the beginning of `spec.md`.

    * The block still contains a blank hint template, the obsolete `pull-before`
      behavior, a TODO, and two pull tests. Its heading calls the content
      temporary, but the following sentence says it is scheduled for deletion
      "on Sunday" without a date. That is not a durable status, and readers or
      implementers can still mistake these lines for requirements. The review
      assignment continues to list this material as part of section 7.

    * Recommendation: delete the entire marked block when the review material is
      no longer needed. If it must stay temporarily, label it explicitly as
      non-normative with a dated status, and update assignment 7 so it describes
      the section that remains. The earlier correctness findings about
      `pull-before` (duplicate `behind` coverage, implicit fetch, invalid `git
      pull <branch>` syntax, and incomplete edge-case handling) remain reasons
      to remove it rather than promote it into the implementation requirements.

      **Going to do this on Sunday**
18. **Tie the minimum Python and Git versions to the dependency and behavior
    requirements.**

    * Location: Language and libraries, items 1 and 8 (lines 1688 and 1742).

    * Python 3.10 is justified as compatible with "all used libraries," but the
      spec does not identify the dependency versions or the source of truth for
      compatibility. Git 2.34 is stated as a floor without saying whether it
      applies to contributors running the tests as well as to users running the
      CLI. The current floor may be intentional; its scope and rationale are
      what is missing.

    * Recommendation: point implementers to the project's dependency metadata
      and CI matrix as the source of supported Python versions. State directly
      that the Git floor applies to both runtime and test environments, or give
      separate floors if tests require newer Git features. Keep the minimum
      versions synchronized with those project files when they change. Also
      correct the spelling `compatability` to `compatibility`.

    * Current status: Git's scope is now explicit, the Python minimum is stated,
      and the spelling is correct (lines 1688-1689 and 1740-1743). Linking the
      Python floor to dependency metadata remains an optional maintenance idea.

      **Added small clarification to git version. I dont personally agree that versions need super indepth rationale**
19. **Define exactly which executable token `explain` accepts.**

    * Location: CLI command 2 and Language and libraries, item 6 (current lines
      72-78 and 1710-1712).

    * The requirement says the argument list must start with `git` exactly. That
      does not say whether `git.exe` (common on Windows), a full path to Git, or
      another casing is accepted. The implementation note about Windows argument
      expansion makes the platform difference relevant.

    * Recommendation: specify one rule and test it. For example, accept only the
      literal first argument `git` and let `PATH` resolve `git.exe` on Windows;
      otherwise list the additional accepted forms. Keep argument passing as a
      list with `shell=False` as already required.

    * Current status: the spec now says that only the word `git` is accepted
      (lines 1710-1712).

      **Cleared up wording that it accepts only `git`**
20. **Resolve the repository context used for post-command reactive hints.**

    * Location: Language and libraries, item 6, `git-hints explain` (lines
      1710-1723).
    * `explain` may run commands such as `git -C <dir> status`, or commands
      using `--git-dir`/`--work-tree`, while the specification says reactive
      hints can use repository state inspected after the command. It does not
      say whether that inspection targets the command's effective repository or
      the directory where `git-hints` itself was launched. Those can be
      different, so a hint could be selected from unrelated state.
    * Recommendation: say that post-command inspection resolves the same
      repository context as the executed Git command, including `-C` and
      worktree options, and add a test; or explicitly skip repository-state
      hints when the command redirects Git's repository context. Also state what
      happens when the command changes branches or leaves a merge/rebase in
      progress, since those states affect reactive-hint selection.
    * Current status: the spec now skips repository-state hints for commands
      using redirection options such as `-C`, `--git-dir`, and `--work-tree`;
      stderr- and exit-code-based hints may still run (line 1723).
      **Opted to skip hints the change repo context. Fully implementing a fix
      for this will require retooling some of the spec (especially tests) which
      I dont want to do. This would be good future work.**
21. **Define the outcome when inspection fails during `explain`.**

    * Location: Language and libraries, item 6, especially lines 1723-1734.
    * The command's Git exit code is to be returned, while unexpected inspection
      failures must be reported separately. The spec gives a nonzero policy for
      plain `git-hints`, but not for an `explain` run where Git completed and
      the follow-up inspection failed. It also does not define the exit status
      when Git cannot be launched, in which case there is no Git exit code to
      return.
    * Recommendation: preserve the executed Git command's exit code whenever it
      was launched, report a follow-up inspection failure without fabricating a
      hint, and define a nonzero tool exit code for the launch-failure case. If
      the intended policy differs, state it explicitly so a reactive inspection
      error cannot silently change the documented command result.
      **Made some slight clarifications about hint behaviour and unexpected failures. also clarified that Git should return if possible**
22. **Specify how plain inspection failures affect partial results.**

    * Location: Language and libraries, item 6, plain `git-hints` (lines
      1704-1708 and 1725-1734).
    * The spec says to report unexpected failures separately and return nonzero
      if inspection fails, but does not say whether the tool continues
      evaluating other hints, displays hints whose conditions were determined
      successfully, or stops at the first failure. If several inspection
      commands fail, the diagnostic format and selection of a process exit code
      are also unspecified.
    * Recommendation: define whether a run is all-or-nothing or may display
      valid partial results. A practical rule is to continue independent checks,
      suppress only hints whose inputs could not be inspected, report each
      failed check with its command and failure detail (including an exit code
      when one is available), and return nonzero if any unexpected failure
      occurred. Explicitly distinguish expected command-specific nonzero
      statuses from inspection failures, as the current text already intends.
      **My fix in 21 also addresses this I believe**
23. **Avoid changing pytest's process-wide working directory inside file
    lambdas.**

    * Location: `make_repo()` at lines 1753-1759.
    * The earlier helper wording said file lambdas ran after changing the
      process current directory to `temp_dir`, then restored it. Current-
      directory changes are process-wide. Concurrent tests or another thread
      using a relative path can therefore operate in the wrong directory, and
      restoration may be skipped if a lambda raises unless protected by
      `finally`.
    * Recommendation: have lambdas receive `temp_dir` and use explicit paths
      (or provide a file-operation helper rooted there), without calling
      `os.chdir`. If changing the directory is retained, require a `try/finally`
      restoration and prohibit concurrent execution; path-based operations are
      simpler to reason about.
    * Current status: the current spec requires rooted paths and explicitly says
      `make_repo()` does not call `os.chdir` (lines 1753-1759).
      **Changed the lambda to not use relative paths. This is a saftey thing
      and I dont think this will affect the rest of the spec**
24. **Show how `make_temps()` receives pytest's temporary-directory factory.**

    * Location: `make_temps(tmp_path_factory, num)` at lines 1750-1752.
    * The earlier helper was said to use `tmp_path_factory`, but its signature
      only accepted `num`. The spec did not explain whether it was a fixture, a
      module-level helper that received the fixture, or a wrapper around a
      global fixture value. This left a concrete implementation choice
      unresolved.
    * Recommendation: give the helper a signature such as
      `make_temps(tmp_path_factory, num)` and show that tests receive
      `tmp_path_factory` as a pytest fixture, or define `make_temps` itself as a
      fixture that returns a factory function.
    * Current status: the current Testing section specifies that signature and
      says each test must request and pass the pytest fixture (lines 1750-1752).
      **Specified that it is passed as an argument. All tests should now reflect this**
25. **Make test setup command failures fail the test, while retaining explicit
    nonzero assertions for scenarios under test.**

    * Location: `make_repo()` at lines 1753-1759 and the final testing
      paragraphs at lines 1801-1806.
    * `make_repo()` is told to invoke each setup command with
      `subprocess.run(..., shell=False)`, but the setup-failure behavior is
      unstated. If commands such as `git init`, `git commit`, or `git push` fail
      and the helper ignores their exit codes, the test can continue in a state
      different from the one its assertions assume. The general application rule
      `check=False` should not accidentally be read as a direction to ignore
      test-fixture setup failures.
    * Recommendation: require setup commands to check their return codes and
      fail with the command and captured output when setup fails. For the Git
      operation whose failure is the behavior being tested, assert the exact
      expected nonzero status and output explicitly. Also state that helper
      subprocesses inherit the fixture's isolated `os.environ` (or pass that
      environment explicitly).
      **Clarified to abort test if any setup fails**
26. **Make the delayed `explain` stderr behavior an explicit user-facing
    choice.**

    * Location: Language and libraries, item 6, `git-hints explain` (lines
      1710-1715).
    * Standard output remains connected to the terminal, but standard error is
      buffered and printed only after Git exits. This means output can appear
      out of order, and Git progress written to stderr may not display while a
      long command is running because stderr is no longer a terminal. The
      behavior is implementable as written, but it may surprise users running an
      interactive or network command through `explain`.
    * Recommendation: either confirm that delayed stderr and hidden progress are
      intentional, or require stderr to be copied to the terminal as it is
      produced while also retaining a buffer for hint matching. Add a test for
      the chosen behavior, especially if command output visibility is part of
      the CLI's learner-friendly promise.
      **This is minor formatting stuff and I dont really think it is necessary**
27. **Keep reactive-command tests separate from the proactive hint-output
    conventions.**

    * Location: Testing paragraphs at lines 1795-1806 and the temporary tests at
      lines 1808-1916.
    * The `--all` and `--all --ids-only` instructions correctly cover proactive
      hint checks. The temporary Test Cases 14 and 15 still invoke plain
      `git-hints`, assert on prose rather than IDs, and use requirement numbers
      that are not present in the current requirements. If retained as examples,
      their setup and assertion style do not follow the current testing rules;
      they also duplicate the established `behind` coverage.
    * Recommendation: delete them with the temporary block. If either is needed
      later, rewrite it as a test of the surviving hint ID using `--all
      --ids-only`, include an absent-state assertion, and remove the obsolete
      requirement number. For a reactive hint, invoke `git-hints explain -- git
      ...` and assert the command result and reactive hint separately rather
      than applying proactive flags to it.
      **These are being deleted**

The current spec has addressed the earlier working-directory ambiguity for Git
and `git-hints` test subprocesses (lines 1795-1804), and it now explicitly keeps
file lambdas from changing the process working directory (lines 1753-1759).

### Additional LLM suggestions (2026-10-17)

These are LLM suggestions from a separate pass over the current section. They
include technical and test-spec questions as well as small editorial fixes.

28. **Fix two copyediting issues in the current section.**

    * Location: Language and libraries, lines 1725-1730; Testing,
      `make_temps()` at lines 1750-1752.
    * The phrase “suppress hints that depend the failed commands” is missing
      “on.” The `make_temps()` paragraph also runs two sentences together as
      `` `make_temps`.The helper `` and is difficult to scan because the line is
      unusually long.
    * Recommendation: change the phrase to “suppress hints that depend on
      failed commands,” and put the `make_temps()` explanation in a new sentence
      or paragraph with normal spacing and wrapping.

29. **Resolve the `--ids-only` versus Git-stdout behavior in `explain`.**

    * Location: CLI command 2, `--ids-only` (lines 96-100), and Language and
      libraries, `git-hints explain` (lines 1710-1715).
    * The CLI says `--ids-only` standard output contains only reactive hint IDs.
      The language rules leave Git's standard output connected to the terminal.
      Since both streams reach the same stdout, a command such as
      `git-hints --ids-only explain -- git status --short` prints Git output
      alongside the IDs (or alongside the empty result), contradicting the
      output contract.
    * Recommendation: define whether the IDs-only promise applies only to
      `git-hints`-generated output or to the entire process stream. If Git
      stdout remains a pass-through, qualify the CLI rule accordingly; if the
      stream must be machine-readable, specify where Git stdout goes in this
      mode. Add a test that runs a Git command which writes to stdout.
      **Specified that standard output is redirected if --ids-only is used**

30. **Define the `config_user()` helper used throughout the tests.**

    * Location: the Testing helper list (lines 1748-1806) and calls throughout
      the test cases, including lines 1851 and 1876.
    * Many test instructions call `config_user(name, email)`, but `config_user`
      is not described among the test helpers or defined elsewhere in the spec.
      Its behavior matters because tests depend on commits having the intended
      identity, and the isolated configuration is stored in `GIT_CONFIG_GLOBAL`.
    * Recommendation: specify whether the helper writes repository-local or
      global `user.name` and `user.email`, how it invokes Git, which environment
      and working directory it uses, and how it fails if setup does not
      succeed. If it writes global config, state that it updates the isolated
      `GIT_CONFIG_GLOBAL` file.
      **This was an accidental deletion**

31. **Require a fresh or reset global config file for each test.**

    * Location: `git_setup()` and the function-scoped fixture (lines 1760-1794).
    * `config_user()` changes `GIT_CONFIG_GLOBAL`, but the spec only calls it a
      writable temporary file and does not say that the file is newly created
      or reset for each fixture invocation. Function scope restores the
      environment variable; it does not by itself restore the contents of a
      file at a reused path. A prior test's identity could therefore affect a
      later test if the fixture reuses that file.
    * Recommendation: require a distinct temporary config file per test (or
      explicitly rewrite it to the baseline contents before each test), then
      point that test's `GIT_CONFIG_GLOBAL` at it. This makes the stated
      per-test isolation independent of fixture implementation details.
      **Git setup already clarifies this**
### Review follow-up (2026-10-18)

32. **Finish the `explain` launch-failure exit rule (follow-up to finding 21).**

    * Location: Language and libraries, `git-hints explain`, and the shared
      subprocess-failure paragraph.
    * The current text says to always return Git's exit code, then says that if
      Git cannot be launched, report the failure instead of inventing a Git exit
      code. It does not define `git-hints`' own exit status for that launch
      failure, so callers cannot rely on a documented result.
    * Recommendation: specify a nonzero `git-hints` exit status for failure to
      launch Git, keep returning Git's status whenever launch succeeds, and add
      a test for the launch-failure path. This is the remaining part of finding
      21; the current wording clarifies the diagnostic but still leaves the
      tool's exit status open.
      **Git hints already has an exit code for this. Clarified that this also applies to `explain`**

### Final LLM review using the prompt:
My net id is sbe80. Review my section of the spec and add suggestion to the end of my sbe80-review.md file. Do not edit anything already there.

I used GPT-6 Luna with codex on extra high settings.

33. **Make `explain` inspection-error exit behavior consistent.**

    * Location: Language and libraries, the `git-hints explain` and shared
      subprocess-failure rules (current lines 2038-2065).
    * `git-hints explain` is told to always return Git's exit code, and the
      shared rule repeats that any launched Git command's code must be returned.
      The final rule also says `explain` returns nonzero for unexpected
      inspection failures. These instructions conflict when Git exits 0 but a
      post-command reactive-hint inspection fails.
    * Recommendation: state which rule takes precedence and add a test for that
      case. To preserve Git's status whenever Git launches, report the
      inspection failure separately and retain the Git status; if inspection
      failure should instead make `git-hints` nonzero, define how Git's status
      remains available and explicitly qualify the "always return Git's exit
      code" rule.
      **Made a small clarification that git doesnt return its code if unexpected inspection errors occur**

34. **Require unambiguous output when parsing arbitrary Git pathnames.**

    * Location: Language and libraries, the final path-list parsing rule
      (current line 2031).
    * The rule allows either `-z` or `-c core.quotePath=false`. Git documents
      that `core.quotePath=false` only changes whether bytes above 0x80 are
      treated as unusual; control characters, quotes, and backslashes are still
      C-quoted. `-z` instead emits pathnames verbatim with NUL terminators. A
      parser that treats non-`-z` output as plain lines can therefore misread
      valid filenames. See [git-config](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corequotePath)
      and [git-status](https://git-scm.com/docs/git-status).
    * Recommendation: require `-z` whenever code parses arbitrary pathnames.
      If non-`-z` output is allowed, explicitly require decoding Git's quoted
      pathname format and add tests for names containing newlines, quotes, and
      backslashes.
