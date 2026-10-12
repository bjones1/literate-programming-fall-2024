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
   fixture, and pytest fails any test that calls a fixture directly.**

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
   also assumes newer pull behavior.**

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
   restriction, because some Git failures report only on stdout.**

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
