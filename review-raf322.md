Review of spec section 4 (raf322)
=================================

This section covers two proactive hints, `untracked-files` (spec.md lines
636-711) and `many-changed-files` (lines 713-801), and one reactive hint,
`rebase-after-repeated-integration-failures` (lines 1233-1291). The two
proactive hints are close to implementable. They use real Git commands that
behave mostly as described, but each has a parsing or edge-case gap, and their
tests miss the cases that matter. The reactive hint is not yet implementable.
It never says where the failure count is kept between `git-hints` processes,
it counts failures that a rebase cannot fix, and its reset rules are
ambiguous. Its test case also fails at step 9 as written. All experiments used
Git 2.56.0.windows.2 in an isolated environment (scratch `HOME`,
`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CEILING_DIRECTORIES`,
`LC_ALL=C`) with local bare remotes.

### Correctness: `rebase-after-repeated-integration-failures`

1. **The spec never says where the failure count is stored, so it cannot be
   implemented as written.**
   - Location: Conditions, line 1256.
   - Each `git-hints explain` call is a separate process, so the count must be
     kept on disk. The spec gives no file, no format, no key, and no rule for
     unreadable state. Two implementers would build incompatible versions.
     They could keep it in memory, which never triggers, or in a home
     directory file shared by every repository.
   - Verified: `git rev-parse --git-path git-hints/integration-failures.json`
     printed `.git/git-hints/integration-failures.json` in a normal clone. In
     a linked worktree it printed `.git/worktrees/wt/git-hints/...`, so the
     path is per worktree.
   - Fix: add a paragraph, matching the `--dismiss` storage at line 60:
     "Store the count in `git-hints/integration-failures.json` at the path
     returned by `git rev-parse --git-path`. Key it by the full branch ref
     (`git symbolic-ref --quiet HEAD`), and store the count and the `HEAD`
     commit ID. Do not count when the command runs outside a working tree or
     with a detached HEAD. If the file is missing or unreadable, treat the
     count as 0. Write it atomically (write a temporary file, then rename
     it)." Also state what happens when the user passes `git -C <dir>` or
     `--git-dir`. The simplest rule is to skip counting in that case.

2. **Every failed pull or push counts, including failures that `git pull
   --rebase` cannot fix or that it would make worse.**
   - Location: Conditions, lines 1256-1258; Git stage, lines 1240-1242.
   - In each scenario below, five failures would produce a rebase suggestion
     that is wrong:
     - a wrong path, a network problem, or an authentication problem;
     - a branch with no upstream;
     - a dirty working tree, where `git pull --rebase` itself refuses to run;
     - an unresolved conflict, including a failed `git pull --rebase`, where
       the hint would recommend the same command that just failed.
   - In these cases the Git stage sentence ("the local branch and its upstream
     branch have diverged ...") is false.
   - Verified:
     - `git push` to a local path that does not exist exited 128 ("does not
       appear to be a git repository").
     - `git push` on a branch with no upstream exited 128 ("has no upstream
       branch").
     - With an unstaged edit, `git pull --rebase` exited 128 ("cannot pull
       with rebase: You have unstaged changes.").
     - During a stopped rebase, `git pull --rebase` exited 128 ("Pulling is
       not possible because you have unmerged files.").
   - Verified that these are the failures a rebase does fix:
     - `git push` exited 1 with `! [rejected] main -> main (fetch first)`
       before a fetch, and with `(non-fast-forward)` after one.
     - Plain `git pull` exited 128 with "fatal: Need to specify how to
       reconcile divergent branches."
     - `git pull --ff-only` exited 128 with "fatal: Not possible to
       fast-forward, aborting."
   - Fix: "Count only a push rejected with `(fetch first)` or
     `(non-fast-forward)`, or a pull that fails because the branches have
     diverged (`Need to specify how to reconcile divergent branches` or `Not
     possible to fast-forward`). Ignore other failures. Do not show the hint
     while a merge or rebase is in progress, or after a failed `git pull
     --rebase`." Match message fragments, not whole lines, as line 1116
     already requires for `pull-blocked-local-changes`.

3. **The reset and threshold rules are ambiguous, and "consecutive" cannot be
   observed.**
   - Location: Conditions, lines 1258-1261.
   - "Any intervening command executed through `git-hints explain` resets the
     count" does not say whether it means a command in any repository or only
     this repository and branch. It also means a learner who runs
     `git-hints explain -- git status` between pushes to investigate loses the
     count. Commands run outside `git-hints explain` are invisible to the
     tool (line 1381 already says so). For example: three failed pushes
     through `explain`, a plain `git pull` that merges, then two more failures
     for a different reason through `explain` would still reach five. "Show
     this hint after five failures" could also mean on the fifth failure or
     on the sixth. The test (step 7) assumes the fifth.
   - Fix: "Show the hint on the fifth counted failure for the same branch.
     Reset the count to 0 when a pull or push through `git-hints explain`
     succeeds, when the hint is shown, or when the stored `HEAD` commit ID
     differs from the current one. Other commands, and failures that are not
     counted, leave the count unchanged." Comparing `HEAD` catches most work
     done outside the tool.

4. **Test step 9 fails: `git pull --rebase` stops with a conflict.**
   - Location: Test case, steps 5 and 9, lines 1273-1289.
   - Step 5 has both clones change `foo.txt`, which holds one line. The
     obvious way to do that (append a line in each clone) conflicts, so step
     9's "Verify that it succeeds ... and no rebase is left in progress" fails
     and leaves the repository mid-rebase.
   - Verified: with `foo.txt` = `xxx`, `local` appended `y` and `other`
     appended `z` and pushed. `git pull --rebase` in `local` exited 1 with
     "CONFLICT (content): Merge conflict in foo.txt", and `git status`
     reported "interactive rebase in progress". When `local` instead added a
     new file `bar.txt`, `git pull --rebase` exited 0 and the following `git
     push` exited 0.
   - Fix (step 5): "In `local`, create and commit `bar.txt`. In `other`,
     append `z` to `foo.txt`, commit it, and run `git push`." Add `git rebase
     --abort` to cleanup.

5. **The test checks only five pushes, so most of the counting rules are
   untested.**
   - Location: Test case, lines 1263-1291.
   - No step checks any of these:
     - a pull failure, the most common way learners hit a divergence;
     - pull and push failures counted together;
     - a reset by a successful command, or by whatever "intervening command"
       means;
     - a failure that should not count (finding 2);
     - two branches counted separately.
   - Fix: add steps such as these.
     - Three failed `explain -- git push` runs, one `explain -- git pull`
       that fails on divergence, then one more failed push. The hint
       appears.
     - Four failures, then a counted reset. The hint does not appear on the
       next failure.
     - Five `explain -- git push` runs on a branch with no upstream (exit
       128). The hint never appears.
     - Four failures on `main`, then `git switch -c other` and one failure.
       The hint does not appear.

### Correctness: `many-changed-files`

6. **`git diff HEAD` misses a staged change that the working tree has undone,
   so C can be too low.**
   - Location: Conditions, line 743.
   - `git diff HEAD` compares the working tree with `HEAD` and ignores the
     index. If a file is staged and then restored on disk, the next commit
     would still change it, but it is not counted.
   - Verified: appended to `three.txt`, ran `git add three.txt`, then restored
     its `HEAD` content on disk. `git status --porcelain` showed `MM
     three.txt`. `git diff HEAD --name-only --no-renames` did not list it, but
     `git diff --cached --name-only` did.
   - Fix: "Let the changed set be the union of `git diff --cached --name-only
     --no-renames -z` and `git diff --name-only --no-renames -z`, restricted
     to paths in the `HEAD` tree."

7. **`git rev-parse --verify HEAD` exits 128 for an unborn branch, the same
   code as "not a repository", so the two cannot be told apart.**
   - Location: Conditions, line 737.
   - Line 752 says unexpected failures must be reported. With this command,
     an implementation must either swallow every 128 or report an error in
     every new repository, which test step 17 forbids.
   - Verified: in a new repository, `git rev-parse --verify HEAD` printed
     "fatal: Needed a single revision" and exited 128. Outside a repository it
     printed "fatal: not a git repository" and also exited 128. `git rev-parse
     --verify --quiet HEAD` in the new repository exited 1 with no output.
   - Fix: use `git rev-parse --verify --quiet HEAD`, where exit 1 means no
     commit and other nonzero codes are errors. This matches `no-commits`,
     line 944.

8. **The hint fires during a merge conflict and suggests a partial commit.**
   - Location: Conditions, lines 733-753.
   - A merge brings in changes to many files, so `many-changed-files` appears
     next to `merge-conflicts`. It advises `git add <files>` for "the changes
     you want to save". That is the wrong advice mid-merge, and Git refuses a
     partial commit during a merge. `unstaged-changes` (line 251) and
     `staged-and-unstaged-changes` (line 356) are already suppressed in this
     state.
   - Verified: in a 4-file repository, merging a branch that changed 3 files
     (one in conflict) exited 1. `git status --porcelain` showed `M
     four.txt`, `M three.txt`, `UU two.txt`, and `git diff HEAD --name-only
     --no-renames` listed all three, so C = 3 and T = 4 and the hint fires.
   - Fix: copy the suppression sentence used by the two hints above: "Do not
     display this hint while `git diff --name-only --diff-filter=U` returns any
     paths." Also consider suppressing it during a rebase, using the
     `rebase-merge` and `rebase-apply` checks from `detached-head`, line 835.

9. **In a small repository, almost any edit triggers "widespread changes".**
   - Location: Conditions, line 750.
   - A learner's first repository often has one or two files. With T = 1,
     every edit is 100%. With T = 2, editing both files triggers the hint.
     That is noise next to `unstaged-changes`, and it uses up one of the
     three display slots.
   - Verified: in a repository with only `README.md` committed, one appended
     line made `git diff HEAD --name-only` list `README.md` and `git ls-tree
     -r --name-only HEAD` list one path, so C = 1 and T = 1.
   - Fix: add a floor, for example "Trigger exactly when T >= 4 and 2*C > T."
     The existing test already uses T = 4. Add a negative step with T = 1.

### Correctness: `untracked-files`

10. **Parsing `git status --porcelain=v1` without `-z` gives wrong file names
    for paths with spaces or non-ASCII characters.**
    - Location: Conditions, lines 656-657.
    - Porcelain v1 quotes and escapes such paths. Code that strips the `?? `
      prefix would suggest `git add "caf\303\251.txt"`, which names no file.
    - Verified: untracked `my notes.txt` and `café.txt` appeared as `??
      "my notes.txt"` and `?? "caf\303\251.txt"`. With `-z` they appeared
      unquoted (`?? café.txt`, `?? my notes.txt`).
    - Verified: with `-c status.showUntrackedFiles=no`, no `??` lines
      appeared at all. Adding `--untracked-files=normal` brought them back.
    - Fix: "Run `git status --porcelain=v1 -z --untracked-files=normal`."
      Alternatively, say explicitly that a user's
      `status.showUntrackedFiles=no` turns off the hint.

11. **The "should be ignored" rule is open-ended, misses nested files, and
    the test expects hint content that the spec never defines.**
    - Location: Conditions, lines 658-661; test step 7.6, line 697.
    - "Generated build outputs" is not a rule an implementation or a test
      can check. The default listing also hides nested candidates: a new
      `src/` directory is reported only as `?? src/`, so `src/__pycache__/`
      and `src/.env` are never seen. Step 7.6 expects the hint to recommend
      `.gitignore` "instead of staging these files", and step 5.4 expects the
      literal `git add notes.txt`. But the Hint and Command fields (lines
      638-652) are fixed text that always offers both choices with a
      placeholder `<filename>`.
    - Verified: with untracked `src/app.py`, `src/.env` and
      `src/__pycache__/app.cpython-312.pyc`, `git status --porcelain=v1`
      printed only `?? src/`. Adding `--untracked-files=all` listed all three
      files.
    - Fix: give a fixed list of ignore candidates (for example `.env`,
      `__pycache__/`, `*.pyc`, `node_modules/`, `build/`, `dist/`, `.venv/`),
      matched against the `--untracked-files=all` listing. Then state the
      dynamic output: "List up to five untracked paths to stage and up to five
      to ignore, as `git add <path>` and suggested `.gitignore` patterns.
      Omit a group that is empty."

12. **This hint overlaps the separate gitignore item.**
    - Location: line 527 (item 5, "Place these files in gitignore?", in
      section 3 but written by raf322) against lines 658-661.
    - Both suggest `.gitignore` for `__pycache__/` and build outputs, so an
      implementer may build two hints for one condition. The item's `git rm
      --cached` advice is about tracked files, a different condition.
    - Fix: fold the untracked half of item 5 into `untracked-files`. Keep or
      remove the `git rm --cached` half as its own hint with an ID.

### Test cases

13. **The `many-changed-files` tests cannot detect the double counting and
    deletion errors they claim to check.**
    - Location: steps 12 and 16, lines 780-796.
    - In step 12, C = 3 whether `one.txt` is counted once or twice (3 or 4 >
      2), so double counting passes. In step 16, "verify that each deleted
      tracked file counts exactly once" cannot be seen through `--ids-only`,
      and 3 deletions out of 4 trigger even if each counts twice.
    - Fix: test at the 50% boundary. In the step 9 state (C = 2, T = 4), run
      `git add one.txt`, then append to `one.txt` again (`MM`), and verify the
      hint is absent. For deletions, delete two of four files and verify the
      hint is absent, then delete a third and verify it appears. Add one step
      each for a staged `git mv` (C counts the source only) and for finding 6.

14. **The tests do not use the helpers and output modes that the Testing
    section requires.**
    - Location: lines 667-711 and 755-801; Testing, lines 1447-1452.
    - Most presence and absence checks in `many-changed-files` (steps 6, 9,
      12, 14, 16, 17) run `git-hints --ids-only` without `--all`. Under the
      three-hint limit, a hint can be missing because it was cut off, so an
      absence check can pass when it should fail. `untracked-files` checks
      presence and absence with `--all` output instead of `--all --ids-only`.
    - Step 1 of `untracked-files` says "create one temporary directory"
      without naming `make_temps(1)`, and neither test uses `make_repo()`.
      `git_setup()` is an autouse fixture, so "Call `git_setup()`" (lines 667,
      757, 1265) should say that the fixture provides it.
    - Steps 8.6-8.7 repeat steps 8.4-8.5 word for word. Step 15 is a
      requirement, not a step.
    - Step 17 does not say how the second repository is created
      (`make_temps(1)`). It also does not check that `no-commits` is present,
      which would show that the repository was really unborn.
    - Fix: use `git-hints --all --ids-only` for every presence or absence
      check, and `--all` only when checking text. Name `make_temps()` and
      `make_repo()`. Delete steps 8.6-8.7 and 15.

### Structure and consistency

15. **The reactive hint is missing required Hint-structure fields, and its
    `Caution:` prefix is inside the code span.**
    - Location: lines 1235-1254.
    - The Hint field is an instruction to the implementer ("Explain that
      ...") rather than hint text, and it has no documentation link. The two
      links in Command have no title, which item 5 (line 177) requires.
      `` `Caution: git pull --rebase` `` puts the prefix inside the command,
      so a learner who copies it pastes `Caution:` into the shell. The
      spec also does not say how this hint is ordered against the push-failed
      item (line 1175) and `pull-blocked-local-changes`, which fire on the
      same failures.
    - Fix: write the actual hint text with a titled link, for example
      ``[git pull --rebase](https://git-scm.com/docs/git-pull "Fetches and
      replays your local commits on top of the upstream branch")``. Write the
      command as ``Caution: `git pull --rebase` ``. State that on a counted
      failure this hint is shown after the push-failed or divergence hint
      (data-loss risk sorts after error/blocked) rather than replacing it.

16. **Broken Markdown nesting in both proactive hints.**
    - Location: lines 643-711 and 737-753.
    - In `untracked-files`, the Git stage, Command, ID, Conditions and Test
      case bullets are indented under the Hint bullet, so they render as
      sub-items of the hint text. In `many-changed-files`, the four
      Conditions paragraphs (lines 737-753) start at column 0. That ends the
      bullet list, so Conditions is split and Test case starts a new list.
    - Fix: dedent lines 643-711 by two spaces. Indent lines 737-753 by two
      spaces.

17. **The `untracked-files` command teaches the machine format and states no
    expected result.**
    - Location: Command, lines 648-652.
    - `git status --porcelain=v1` is meant for scripts. Learners should see
      `git status`, which lists the files under "Untracked files:". The
      Command field says "Run `git status` afterward to verify the changes"
      without saying what the user will see.
    - Fix: "Run `git status`; untracked files appear under 'Untracked
      files:'. After `git add <file>`, the file appears under 'Changes to be
      committed:'. After adding a pattern to `.gitignore`, it no longer
      appears."

### Minor

- Line 755: the title "Commit repo? (... formerly Test Case 12)" is stale.
  Name the test after the hint.
- Lines 790-796: step 16 lacks code formatting for `make_temps(1)`, `git
  init -b main`, `git-hints --ids-only`, and `many-changed-files`.
- Line 704: step 8.3 uses `git status --porcelain`, while the other steps use
  `--porcelain=v1`. Pick one.
- Line 1235: "Five repeated failures to pull or push may be resolved by ..."
  says the failures are resolved. Reword to "After five failed pulls or
  pushes, replaying your local commits on top of the upstream branch may
  resolve the problem."
- Lines 1268 and 1272: `config_user()` sets global configuration (line
  1415), so "call it there" is misleading. The second call also changes
  `local`'s identity.
- Line 1254: "safety: caution" uses a field value that the Hint structure
  section never defines. The other hints use only "safe".
- `untracked-files` and `no-commits` both suggest `git add` in a new
  repository with untracked files. That is acceptable, but say so, or
  suppress one of them.
