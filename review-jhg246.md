Review of spec section 5 (jhg246)
==================================

This section covers the `detached-head` hint, the `no-commits` hint and item 15,
"Committing to protected/main branch?" (spec.md lines 803-1025). The first two
hints are careful and complete. I ran every step of both test cases with Git
2.56.0 in an isolated environment that matches `git_setup()`. Every stated
precondition and exit code holds, including the bisect and `rebase --exec`
steps. The main problems are elsewhere. Item 15 is not yet a hint, and its
command and advice are wrong as written. The unborn-branch state interacts badly
with `no-upstream-branch`. `detached-head` misses the one case where a detached
HEAD can lose work.

### Correctness and detection

1. **Item 15's branch-listing command and its "switch to another branch" advice
   are wrong as written.**

   * Location: item 15, "Committing to protected/main branch?", spec.md
     1019-1024.
   * The single quotes in `--format='%(refname:short)'` are shell quoting. The
     spec requires `shell=False` (Language and libraries, item 6), so the quotes
     reach Git literally and every name is printed wrapped in quotes.
   * The listing includes the current branch itself. It also includes `origin`,
     which is the short name of `refs/remotes/origin/HEAD`, and `origin/main`.
     So after any plain clone, "other branches exist" is true, and the hint
     tells the user to switch to a branch that cannot be switched to.
   * Switching to an existing branch is also the wrong remedy for uncommitted
     work on `main`. Depending on the files, it either carries the changes onto
     an unrelated branch or fails. `git switch -c <new-branch>` always works and
     carries the changes along.
   * Verified: in a fresh clone, `git for-each-ref "--format='%(refname:short)'"
     refs/heads refs/remotes` printed `'main'`, `'origin'` and `'origin/main'`,
     quotes included. `git switch origin/main` exited 128 with `fatal: a branch
     is expected, got remote branch 'origin/main'`. With a modified `foo.txt`,
     `git switch -c feature` exited 0, and `git status` then showed
     `## feature` and ` M foo.txt`.
   * Fix: drop the `for-each-ref` step and the "switch to an existing branch"
     branch of the advice. Always suggest `git switch -c <new-branch>`.

2. **Item 15 has none of the Hint structure fields, and its trigger is undefined
   and would fire constantly.**

   * Location: spec.md 1019-1024.
   * It has no hint text or link, no Git stage sentence, no expected result, no
     ID, no priority class and no test case. "There are changes" could mean
     unstaged, staged or untracked changes, or commits ahead of upstream.
     "Protected" is a hosting-site setting (GitHub branch protection) that Git
     cannot see locally. As written, the hint fires in every single-branch
     learner repository whenever a file is edited. It also fires on an unborn
     `main`, where committing to `main` is exactly what `no-commits` tells the
     user to do. The hard-coded `main`/`master` also misses repositories whose
     default branch has another name.
   * Fix: rewrite it in the standard format. Here is a suggested outline:
     * Hint: "You have uncommitted changes on `<branch>`, the branch your
       remote treats as its default. Do you want to make them on a new
       [branch](https://git-scm.com/docs/git-switch "Create a new branch at the
       current commit and switch to it") instead?"
     * Git stage: "Your edits are in the working directory or staging area of
       the default branch and have not been committed."
     * Command: `git switch -c <new-branch>`. Expected result: Git creates the
       branch at the current commit and switches to it. The uncommitted changes
       come along, and `git status` reports `On branch <new-branch>`.
     * ID: `changes-on-default-branch`, priority class: workflow.
     * Conditions: `git symbolic-ref --quiet --short HEAD` exits 0, and its
       output equals the branch part of `git symbolic-ref --quiet --short
       refs/remotes/origin/HEAD` (exit 0, for example `origin/main`). If that
       ref is absent, decide explicitly whether to fall back to `main`/`master`
       or skip the hint. Also require `git diff --quiet` or `git diff --cached
       --quiet` to exit 1, and say whether untracked files count. Suppress the
       hint when `no-commits` applies or unresolved merge entries exist.
       Verified: `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`
       printed `origin/main` (exit 0) in a fresh clone.
     * Test case: a positive case (a clone with `foo.txt` modified on `main`)
       and negative cases: a clean `main`, a feature branch with changes, and an
       unborn `main` with a staged file.
     * Also replace the `15.` numbering with a `####` heading.

3. **`no-upstream-branch` fires on an unborn branch and recommends a push that
   fails, and the `no-commits` test cannot catch it.**

   * Location: `no-commits` "Related output" (spec.md 959-963) and Test case
     11. The conflicting rule is in `no-upstream-branch` Conditions, spec.md
     547-554.
   * A learner who runs `git init`, `git remote add origin ...` and then
     `git-hints` meets all three `no-upstream-branch` conditions: a symbolic
     HEAD, no upstream and an existing `origin`. The tool then suggests
     `git push -u origin main`, which fails because there is nothing to push.
   * Verified: in a new repository with `origin` added and no commits,
     `git symbolic-ref --quiet --short HEAD` printed `main` (exit 0). `git
     rev-parse --abbrev-ref --symbolic-full-name "@{upstream}"` exited 128, and
     `git push -u origin main` exited 1 with `error: src refspec main does not
     match any`.
   * Fix: add this to `no-commits` Related output: "`no-upstream-branch` must
     remain absent while the current branch has no commits." Add `git rev-parse
     --verify --quiet HEAD` exits 0 to the `no-upstream-branch` Conditions. In
     Test case 11, add a bare remote as `origin` in step 1, and assert
     `no-upstream-branch` absent in steps 4 and 12 and present in step 10.

4. **`detached-head` does not distinguish a harmless detached HEAD from one
   holding commits that are on no branch, which is the case that loses work.**

   * Location: `detached-head` Hint, Command, priority class and Conditions,
     spec.md 807-842.
   * A learner who commits while detached and then runs `git switch main`
     leaves those commits reachable only through the reflog. As an
     informational hint, `detached-head` sorts last, so in plain `git-hints` it
     is hidden whenever three workflow hints trigger. The hint also gives no
     way back for the common case where the user did not mean to detach (for
     example after `git checkout <tag>`).
   * Verified: after `git switch --detach HEAD~1`, `git for-each-ref --contains
     HEAD --format=%(refname:short) refs/heads` printed `main` and
     `saved-work`. After one commit it printed nothing, and `git switch
     saved-work` then printed `Warning: you are leaving 1 commit behind, not
     connected to any of your branches`.
   * Fix: when that `for-each-ref --contains HEAD refs/heads` call prints
     nothing, raise the priority class to workflow. Add to the hint text: "Your
     commits made here are not on any branch; create a branch before switching
     away or they will be hard to find." Also add a second command: "To return
     to a branch without keeping anything: `git switch <branch>`." Add a test
     step that commits while detached and asserts the raised priority.

5. **The overlap between `no-commits` and `staged-changes` / `untracked-files`
   is not specified, so the user gets duplicate `git add` and `git commit`
   advice.**

   * Location: `no-commits` Command and Related output (spec.md 924-963), and
     Test case 11 steps 5 and 7.
   * In step 7, `staged-changes` (a workflow hint) and `no-commits` (an
     informational hint) both appear, and both tell the user to run
     `git commit -m ...`. In step 5, `untracked-files` also triggers on
     `foo.txt` and suggests `git add`, the same command that `no-commits`
     shows. The spec never says whether this duplication is intended, and the
     test never asserts `untracked-files` either way.
   * Fix: decide on one rule and state it in Related output. One choice:
     "`no-commits` replaces `staged-changes` and `untracked-files` while the
     branch is unborn", in the same way that `diverged` replaces `behind`.
     Another choice is to drop the command from `no-commits` and leave it as
     context only. Then assert the decision in steps 5 and 7.

6. **Neither hint defines the result inside a `.git` directory or a bare
   repository, where `--is-inside-work-tree` prints `false` with exit 0.**

   * Location: `detached-head` Conditions step 1 (spec.md 824-827) and
     `no-commits` Conditions step 1 (spec.md 941-943).
   * `detached-head` says to handle a non-work-tree "through the existing
     `not-a-repo` behavior". But `not-a-repo` (spec.md 322-326) triggers only
     on exit 128, so in these locations no hint, no error and no context line
     is specified.
   * Verified: `git rev-parse --is-inside-work-tree` printed `false` (exit 0)
     both in `local/.git` and in a bare repository. Outside any repository it
     exited 128.
   * Fix: state the rule once, near Repository context: "Exit 0 with `false`
     means inside a Git directory or bare repository: print a short message
     saying git-hints needs a working tree, show no hints, and exit 0." Then
     have both hints refer to that rule instead of repeating step 1.

7. **`detached-head` fires inside submodules, where a detached HEAD is Git's
   normal state.**

   * Location: `detached-head` Conditions, spec.md 822-842.
   * After `git clone --recurse-submodules`, every submodule is detached, and
     the advice to create a branch is usually wrong there.
   * Verified: in a submodule checked out by `git clone --recurse-submodules`,
     `git symbolic-ref --quiet --short HEAD` exited 1. `git rev-parse
     --show-superproject-working-tree` printed the superproject path.
   * Fix: either suppress the hint when `--show-superproject-working-tree` is
     non-empty, or add a sentence saying that submodules are normally detached
     and that this is expected.

### Test cases

8. **The detached-HEAD test never exercises the `rebase-apply` path or a
   subdirectory, even though the Conditions describe both.**

   * Location: Conditions step 4 (spec.md 835-840), and Test case 10 steps 6,
     9 and 12.
   * `git rev-parse --git-path` returns a path relative to the current
     directory, so a bug that resolves it against the repository root passes
     every step of the current test.
   * Verified: run in `local/sub`, `git rev-parse --git-path rebase-merge`
     printed `../.git/rebase-merge`. `git rev-parse --path-format=absolute
     --git-path rebase-merge --git-path rebase-apply --git-path BISECT_START`
     printed all three as absolute paths in one call (exit 0). In a linked
     worktree it correctly printed `.git/worktrees/wt/BISECT_START`.
   * Fix: in Conditions step 4, use that single `--path-format=absolute` call
     (available since Git 2.31; the spec requires 2.32) and delete the "resolve
     relative paths" sentence. Add a step that runs `git-hints --all
     --ids-only` from a subdirectory during the bisect. Optionally, cover
     `rebase-apply` with a conflicting `git rebase --apply`.

9. **Step 12 avoids `make_repo()` because the command must fail, but the
   Testing section never says what `make_repo()` does when a command fails.**

   * Location: Test case 10 step 12 (spec.md 895-903); Testing, `make_repo`
     (spec.md 1406-1414).
   * Fix: in Testing, add "`make_repo` raises if any command exits nonzero",
     which is what step 12 assumes. Otherwise, remove the instruction from step
     12.

   Steps verified, for the record: step 4 (`symbolic-ref` printed `main`, exit
   0; `@{upstream}` exited 128 with no upstream). Step 6 (exit 1 and exit 0;
   none of the three paths existed). Step 9 (`git bisect start HEAD HEAD~2`
   exited 0 and checked out `Append y.`; `symbolic-ref` exited 1;
   `.git/BISECT_START` existed). Step 11 (`saved-work`, and `BISECT_START`
   removed). Step 12 (`git rev-parse --verify` on the missing ref exits 128;
   the rebase stopped with exit 1, even with `GIT_SEQUENCE_EDITOR=false`, so no
   editor runs; `symbolic-ref` exited 1; `.git/rebase-merge` existed).
   Step 14 (`saved-work`; neither path existed). For Test case 11, steps 2, 6,
   9 and 11 all held exactly as stated; `rev-parse --verify --quiet HEAD`
   printed nothing to stdout or stderr. `git switch --orphan fresh` also
   removes `foo.txt` from the working tree, which the step 12 assertions
   tolerate.

### Structure and consistency

10. **The working-tree check is repeated as step 1 of each hint's Conditions
    instead of being stated once for all proactive hints.**

    * Location: spec.md 824-827 and 941-943.
    * Every other proactive hint relies on the same precondition implicitly, so
      the two copies can drift apart, and they already differ in wording.
    * Fix: move it to the `### git-hints` introduction (spec.md 232-233),
      together with the rule from finding 6.

11. **The test case labels use the old numbering ("Test case 10", "Test case
    11"), which the rest of the spec has replaced.**

    * Location: spec.md 848 and 965.
    * Fix: change them to "Test case: Detached HEAD state (written and revised
      by drj228; formerly Test Case 10)". Use the same form for 11.

### Minor

* The "detached HEAD" link title (spec.md 808) describes `git switch`, not the
  linked term. Use `https://git-scm.com/docs/git-checkout#_detached_head` with a
  title such as "HEAD points at a commit instead of a branch; new commits
  belong to no branch".
* "Related output" (spec.md 843, 959) is not a field in Hint structure. Either
  add it there or fold it into Conditions.
* `* Related output:` (spec.md 843, 959) and `* ID:` (spec.md 937) follow a
  nested list with no blank line, which mixes tight and loose list items.
* The "division by zero" sentence (spec.md 963) belongs in
  `many-changed-files`, whose `2*C > T` test cannot divide anyway.
* Item 15 is credited to raf322 but sits inside the jit45/drj228 hints. Credit
  whoever rewrites it.
