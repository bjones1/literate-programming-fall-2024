Review of spec section 3 (ewj55)
================================

Section 3 (spec.md lines 427-633) specifies four full-format proactive hints
(`behind`, `diverged`, `no-upstream-branch`, `staged-changes`) and two items
still in the old one-paragraph format (5, gitignore; 10, commit identity). The
`behind` hint is solid: every Git claim in its conditions and test case held
up when I ran it. The main problems are missing suppression during an
in-progress merge or rebase. In those states `staged-changes` and `diverged`
recommend commands that Git refuses to run. `no-upstream-branch` also has false
positives. The two old-format items need to be rewritten, not just
reformatted. All experiments used Git 2.56.0.windows.2 with the isolation
`git_setup()` describes. "Verified" lines report what I observed.

### Correctness and detection

1. **`staged-changes` appears during an unresolved merge conflict or a stopped
   rebase and tells the user to run `git commit`, which fails.**
   * Location: Review staged changes before committing?, Conditions, line 599.
   * Scenario: a learner's `git pull --no-rebase` stops with a conflict.
     `git diff --cached --quiet` exits 1 because the index holds unmerged
     entries. So the hint appears and recommends `git commit -m "message"`.
     Unlike `unstaged-changes` and `staged-and-unstaged-changes`, this hint
     has no `--diff-filter=U` suppression. During a stopped rebase, HEAD is
     detached and the right next step is `git rebase --continue`, not a new
     commit.
   * Verified: in a diverged clone, `git pull --no-rebase` exited 1. Then
     `git diff --cached --quiet` exited 1, and `git commit -m message` exited
     128 with "Committing is not possible because you have unmerged files."
     After a conflicted `git pull --rebase`, I resolved the file and ran
     `git add`. Then `git diff --cached --quiet` exited 1 and
     `git symbolic-ref -q HEAD` exited 1.
   * Fix: add the same first sentence the sibling hints use: "Do not display
     this hint while the index contains unresolved merge entries; check with
     `git diff --name-only --diff-filter=U`." Also suppress it while a rebase
     is in progress. Use the `rebase-merge`/`rebase-apply` path checks that
     `detached-head` already defines (line 835).

2. **`diverged` keeps appearing during an in-progress merge and recommends
   `git pull --no-rebase` again, which Git refuses.**
   * Location: Branch has diverged from upstream, Conditions, line 504.
   * Scenario: the hint's own command produces a conflicted merge.
     `# branch.ab` still reads `+1 -1` until the merge commit exists. So the
     hint stays and repeats the pull, both while conflicts are unresolved and
     after the user resolves and stages them. The `--diff-filter=U` check
     would not catch the second case.
   * Verified: during the conflict, `git status --porcelain=v2 --branch`
     showed `# branch.ab +1 -1`. A second `git pull --no-rebase` exited 128
     with "Pulling is not possible because you have unmerged files". After
     `git add foo.txt`, status still showed `+1 -1`, and the pull exited 128
     with "You have not concluded your merge (MERGE_HEAD exists)".
   * Fix: add "Do not display this hint while a merge is in progress
     (`git rev-parse -q --verify MERGE_HEAD` exits 0) or while the index has
     unresolved entries." Apply the same rule to `behind`. During a rebase,
     the porcelain output has no `# branch.ab` line (verified:
     `# branch.head (detached)` with no upstream lines), so no rebase check is
     needed.

3. **`no-upstream-branch` triggers when an upstream is configured but its
   remote branch is gone, and on an unborn branch. Its exit-code check cannot
   tell these cases from real errors.**
   * Location: Configure an upstream branch?, Conditions, lines 547-554.
   * Scenario A: a feature branch's pull request is merged and the remote
     branch is deleted. `git fetch --prune` removes `origin/feature`. The hint
     then says "no upstream branch configured" and tells the user to
     `git push -u origin feature`, which recreates the deleted branch.
   * Scenario B: right after cloning an empty repository, or after
     `git init` plus `git remote add origin`, the hint recommends
     `git push -u origin main`. That push fails because the branch has no
     commits.
   * Verified: after deleting and pruning `origin/feature-test`,
     `git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}"` exited
     128, while `git config --get branch.feature-test.merge` still printed
     `refs/heads/feature-test` and `git status -sb` showed `[gone]`. After
     cloning an empty bare repo, the same rev-parse exited 128. On an unborn
     `main` with `origin` added, it exited 128 ("no such branch: 'main'"), and
     `git push -u origin main` exited 1 with "src refspec main does not match
     any". Outside a repository and with no upstream at all, rev-parse also
     exits 128. The spec gives no way to separate these.
   * Fix: detect from the `git status --porcelain=v2 --branch` output that
     `behind` and `diverged` already parse. "No upstream" means there is no
     `# branch.upstream` line. A `# branch.upstream` line with no
     `# branch.ab` line means the upstream is gone or not yet fetched; do not
     show this hint then. Also require `git rev-parse -q --verify HEAD` to
     exit 0, which leaves unborn branches to `no-commits`.

4. **The `diverged` command text says a plain `git pull` works when `pull.ff`
   is configured. With `pull.ff=only`, the common setting, it still fails.**
   * Location: Branch has diverged from upstream, Command, lines 499-500.
   * Verified: on a branch at `+1 -1`, plain `git pull` exited 128 with
     "Need to specify how to reconcile divergent branches." With
     `git config pull.ff only` it exited 128 with "Not possible to
     fast-forward, aborting". With `pull.ff true` it merged and exited 0.
     Git's own advice lists `pull.ff only` as one of the three choices, so
     learners are likely to have that setting.
   * The spec allows Git 2.32 (line 1397). I believe the "must specify how
     to reconcile" default arrived after 2.32, and older versions merged with
     a warning. I could not test 2.32.
   * Fix: "A plain `git pull` fails on diverged branches unless `pull.rebase`
     is set, or `pull.ff` is set to something other than `only`; the explicit
     `--no-rebase` or `--rebase` always works."

5. **The commit-identity conditions report a false positive when identity
   comes from environment variables. The description also misstates what
   happens when identity is missing.**
   * Location: item 10, lines 620-626.
   * Verified: with no `user.*` configured, `git config --get user.name`
     exited 1, but `git commit` with `GIT_AUTHOR_NAME`, `GIT_COMMITTER_NAME`
     and `EMAIL` set recorded `Env <env@example.com>` cleanly. With nothing
     configured and no environment variables, `git commit` succeeded (exit
     0). It recorded an auto-detected identity built from the Windows account
     and domain and printed "Your name and email address were configured
     automatically". With `user.name` set to an empty string,
     `git config --get` exited 0 with an empty line and `git commit` exited
     128 ("empty ident name ... not allowed"). With `user.useConfigOnly=true`
     and no email, `git commit` exited 128.
   * Why it matters: when nothing is configured, the main harm is commits
     published under a guessed identity, not a blocked commit. That decides
     the priority class and the wording. `git var GIT_AUTHOR_IDENT` is no
     substitute check, because it returns the guessed identity with exit 0
     (verified).
   * Fix: treat a value as missing only when the config value is missing or
     empty and the matching environment variables are not set. For the name,
     those are `GIT_AUTHOR_NAME` and `GIT_COMMITTER_NAME`. For the email, they
     are `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL`, or `EMAIL`. Hint text:
     "Git may guess your identity from your computer account and record it in
     every commit."

6. **The `behind` preview command fails in PowerShell, the default shell on
   Windows.**
   * Location: Branch is behind upstream, Command, lines 440-441.
   * Verified: in PowerShell 7,
     `git diff --name-only HEAD...@{upstream}` exited with "fatal: ambiguous
     argument 'dQBwAHMAdAByAGUAYQBtAA=='" because PowerShell rewrote the
     argument. An unquoted `@{upstream}` in
     `git rev-parse ... @{upstream}` was a PowerShell parse error ("Missing
     '=' operator after key in hash literal"). Quoting `'@{upstream}'`
     worked, and so did the same command in Git Bash.
   * Fix: substitute the real upstream name from `# branch.upstream`, for
     example `git diff --name-only HEAD...origin/main`. This works in every
     shell and teaches the remote-tracking branch name.

### Test cases

7. **Most of the section's tests ignore the Testing section's rule on
   `--all` and `--all --ids-only`.**
   * Location: `behind` steps 6, 9, 10, 11 (lines 467-482). `diverged` step
     3 (line 518). `no-upstream-branch` step 9 (line 578). `staged-changes`
     steps 4, 6, 7 (lines 611-618).
   * Why it matters: the Testing section (lines 1447-1452) requires
     `--all --ids-only` for presence and absence checks. A bare `--ids-only`
     keeps the three-hint limit, so a presence check such as `behind` step 9
     can fail once other hints trigger first. `--all` without `--ids-only`
     makes absence checks scan prose, where another hint may mention the ID.
   * Fix: use `git-hints --all --ids-only` with whole-line comparison for
     every presence or absence check. Keep `--all` only for checks of
     wording, commands and links.

8. **The `diverged` test checks for a command the hint does not recommend
   and never checks the state after integration.**
   * Location: Branch has diverged from upstream, Test case step 5, lines
     522-525.
   * The Command field recommends `git pull --no-rebase` and says plain
     `git pull` fails, but step 5 checks that the hint "suggests `git pull`
     or `git pull --rebase`". A substring check for `git pull` passes no
     matter which form appears.
   * No negative step shows the hint disappearing after integration. A push
     step cannot be added as written, because `repo1` is non-bare with `main`
     checked out.
   * Verified: after `git pull --no-rebase` in `repo2`, status showed
     `# branch.ab +2 -0`. `git push` to `repo1` exited 1 with
     "[remote rejected] main -> main (branch is currently checked out)".
   * Fix: in step 5, check for `git pull --no-rebase` and for `Caution:`
     before `git pull --rebase`. Add step 6: "Run `git pull --no-rebase` and
     verify `# branch.ab +2 -0`. Then run `git-hints --all --ids-only` and
     verify that `diverged` is absent and `push-ahead` is present." If a push
     check is wanted, use a bare remote and two clones, as the `push-ahead`
     test does.

9. **The `no-upstream-branch` test case is not nested under its bullet and
   has no negative cases for the conditions it specifies.**
   * Location: Configure an upstream branch?, Test case, lines 556-579.
   * The numbered list starts in column 0, so Markdown ends the bullet list
     and the steps render as a top-level list detached from the hint. Step 5
     says only that the command "fails". It should require exit code 128
     and the message "no upstream configured for branch 'feature-test'"
     (verified).
   * The conditions name three exclusions: detached HEAD, no `origin`, and a
     valid upstream. Only the last is tested. With finding 3, the gone
     upstream and unborn cases need tests too.
   * Fix: indent the steps two spaces under `* Test case:`. Add these steps:
     before `git remote add`, verify the hint is absent (no `origin`). After
     step 9, run `git push origin --delete feature-test` and
     `git fetch --prune`, then verify the hint is still absent.

10. **No test covers `staged-changes` during a conflict.**
    * Location: `staged-and-unstaged-changes` Conflict suppression test step
      8, line 422; `staged-changes` test, lines 606-618.
    * Fix: after finding 1 is applied, add `staged-changes` to the IDs that
      step 8 checks are absent. That test already stages a change to
      `other.txt` during the conflict.

### Structure and consistency

11. **Item 5 (gitignore) largely duplicates `untracked-files`. Its one
    distinct idea, already tracked files that should be ignored, needs a
    full hint of its own.**
    * Location: item 5, lines 527-530; compare `untracked-files` Conditions,
      lines 656-663.
    * `untracked-files` already flags untracked `.env`, `__pycache__/`,
      `*.pyc` and build output and suggests `.gitignore` patterns. The new
      case is a file that is already tracked or staged. Adding it to
      `.gitignore` has no effect, which confuses learners.
    * Verified: I committed `__pycache__/foo.cpython-312.pyc` and then added
      `__pycache__/` to `.gitignore`. `git status --porcelain=v1` then showed
      only `?? .gitignore`, while `git ls-files -ci --exclude-standard`
      listed the `.pyc`. `git rm --cached __pycache__` exited 128 with "not
      removing '__pycache__' recursively without -r". `git rm -r --cached`
      staged `D  __pycache__/foo.cpython-312.pyc` and left the file on disk.
      After that commit, a second clone's `git pull` deleted its own copy of
      `__pycache__`.
    * Fix: replace the item with a full hint, for example
      `tracked-ignored-files`, priority workflow. Condition:
      `git ls-files -ci --exclude-standard -z` returns at least one path.
      Command: `git rm -r --cached <path>`, then commit. Expected result:
      `git status` lists the path as deleted under "Changes to be committed"
      and the file remains on disk. The hint must explain three things:
      collaborators' copies are deleted when they pull; the file stays in
      history, so a committed secret must be rotated; and
      `git restore --staged <file>` is the way to unstage a newly added file
      that was never committed. Add a Git stage sentence (staging area and
      local repository), a link to the `git rm` and gitignore documentation,
      and a test. Move it next to `untracked-files`.

12. **Item 10 (commit identity) must become a full hint with the ID
    `commit-identity`, which other parts of the spec already use.**
    * Location: item 10, lines 620-632. The ID is referenced at line 70
      (`--dismiss` example), line 212 (example ID) and line 935
      (`no-commits`).
    * Missing fields:
      * hint text with a titled link, for example to
        `https://git-scm.com/docs/git-config` or the Git book's
        "First-Time Git Setup";
      * a Git stage sentence: "This configures your local Git installation;
        every commit you record in the local repository is labeled with this
        identity.";
      * an expected result: `git config --get user.name` prints the name;
      * a priority class: workflow, given finding 5;
      * a test case.
    * Scope: the spec does not say whether the hint appears outside a
      repository. Verified: `git config --get user.name` runs there (exit 1
      when unset). Showing only inside a working tree keeps it consistent
      with `--dismiss`, which stores dismissals in the Git directory.
    * Empty local override: "should be corrected locally" gives no command.
      Suggest `git config --show-scope --show-origin --get user.name`. That
      printed `local  file:.git/config  ...`, which shows where the empty
      value lives. Then suggest `git config --local --unset user.name`.
    * Suggested test steps: initialize a repository without calling
      `config_user` and verify `commit-identity` is present. Set only the
      name and verify it is still present. Call `config_user` and verify it
      is absent. Set `git config --local user.name ""` and verify it is
      present. Unset the local value and verify it is absent.

13. **`pull-before` and Test Cases 14 and 15 duplicate `behind`, with a
    different priority and a forbidden fetch.**
    * Location: Pull before committing, lines 1309-1347; Test Case 14, line
      1462; Test Case 15, line 1485; empty placeholder "Pull remote
      changes?", line 1295.
    * `pull-before` triggers in exactly the `behind` state but is classed
      error/blocked, so both hints would show. Its condition runs
      `git fetch`, which contradicts `--fetch` (lines 78-82) and line 1369.
      Test Case 15 ("Requirement Proactive 4") is the `behind` scenario with
      two commits, which `behind` step 9 already covers.
    * Fix: coordinate with sbe80 and raf322 to delete `pull-before`, the
      placeholder and Test Cases 14 and 15, or to merge any distinct idea
      into `behind`.

14. **`staged-changes` duplicates `staged-and-unstaged-changes` and
    `no-commits`, and its Git stage sentence describes unstaged edits that
    may not exist.**
    * Location: Git stage, lines 589-591; staged-and-unstaged test steps 7.4
      and 7.5, lines 395-404; `no-commits` test step 7, lines 993-997.
    * With staged plus unstaged changes, both hints appear and both
      recommend `git diff --cached` and `git commit -m "message"`. On an
      unborn branch with staged files, `no-commits` and `staged-changes` both
      recommend a commit.
    * Fix: make `staged-and-unstaged-changes` replace `staged-changes`, as
      `diverged` replaces `behind`, and update steps 7.4 and 7.5 to match.
      Alternatively, state that the overlap is intended. Change the Git stage
      text to one sentence: "Your staged changes are in the staging area and
      will be included in the next commit."

15. **`diverged` says it replaces `push-ahead`, but the `push-ahead`
    conditions say nothing about this, and their check matches a diverged
    branch.**
    * Location: diverged Conditions, line 507; push-ahead Conditions, lines
      288-292.
    * Verified: on a diverged branch, `git status -sb` printed
      `## main...origin/main [ahead 1, behind 1]`, which satisfies "ahead of
      its upstream by one or more commits".
    * Fix: add to `push-ahead`: "and not behind it (otherwise `diverged`
      applies)". Better still, have both hints read `# branch.ab` from the
      same porcelain v2 output.

16. **The `staged-changes` conditions can be read as forbidding the hint on
    an unborn branch, but `no-commits` expects it to appear there.**
    * Location: lines 602-603. "Do not display the hint when the staging
      area is empty. This includes staged files in a repository with no
      commits yet." `no-commits` test step 7 (line 996) and `staged-changes`
      test step 6 both expect the hint to appear.
    * Verified: on an unborn `main`, `git diff --cached --quiet` exited 0
      with an empty index and 1 after `git add foo.txt`.
    * Fix: "Do not display the hint when the staging area is empty. Display
      it on a branch with no commits yet as well; there `git diff --cached`
      compares the index with an empty tree."

17. **The Git stage fields of `no-upstream-branch` and `staged-changes` are
    two sentences long, and the first does not name a stage.**
    * Location: lines 538-540 and 589-591; rule at lines 156-158.
    * Fix for `no-upstream-branch`: "Your commits are in the local
      repository, and this branch is not yet linked to a branch on the
      remote."

### Minor

* `behind` hint text (lines 433-434) says "before you start editing", but the
  hint also appears after edits. Show the count instead: "Your branch is N
  commits behind `origin/main` (as of last fetch)."
* `behind` Conditions (line 447): the `# branch.ab` line is also absent when
  the upstream is configured but gone or not yet fetched (verified). Say so.
* The `behind` and `diverged` conditions always require the "as of last
  fetch" label, but `--fetch` (line 81) applies it only without that option.
  Pick one rule.
* `no-upstream-branch` Command uses `<branch-name>`, but the test expects
  `feature-test`. State that the hint substitutes the current branch name.
  The hint is silent for repositories whose only remote is not named
  `origin`; say whether that is intended.
* `diverged` expected result: say that `git pull --no-rebase` creates a merge
  commit, which needs a configured identity and may open an editor for the
  message. I did not verify the editor behavior, because `GIT_EDITOR=true`.
* `diverged` is marked `safety: safe` but offers a `Caution:` alternative.
  `rebase-after-repeated-integration-failures` (lines 1253-1254) classifies
  the same `git pull --rebase` as data-loss risk/caution. State that the
  safety field describes the primary command.
* Items 5 and 10 begin with stray ordered-list numbers ("5.", "10.") left
  from the old numbering. They render as one-item lists that start at 5 and
  10.
* Attribution style varies: `(jhg246)` in headings versus `**sbe80**` at line
  581. Use parentheses.
* None of the links uses the text fragments that Hint structure item 4
  requires (the TODO at line 173).
* `no-upstream-branch` step 5 leaves `@{upstream}` unquoted, while step 8
  quotes it. Make them consistent.
