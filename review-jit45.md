Review of spec section 2 (jit45)
================================

This section (spec.md lines 235-426) specifies four proactive hints:
`unstaged-changes`, `push-ahead`, `not-a-repo`, and
`staged-and-unstaged-changes`, plus a conflict suppression test. The two
working-tree hints have sound detection logic: I confirmed every `git diff
--quiet` / `git diff --cached --quiet` exit code their tests rely on. The
conflict suppression test does not work as written, though, because Git refuses
the merge before any conflict exists. The three staged/unstaged hints also all
fire together. `push-ahead` and `not-a-repo` need more work. One parses a
human-oriented status format and suggests a command that the test contradicts.
The other treats every exit code 128 as "not a repository" and ignores bare
repositories. All experiments used Git 2.56.0.windows.2 in an isolated
environment matching `git_setup()`.

### Correctness

1. **The conflict suppression test never creates a conflict: `git merge topic`
   refuses to start because `other.txt` has staged changes.**
   * Location: Keep unstaged changes out of this commit?, Conflict suppression
     test, steps 6-7 (spec.md lines 416-421).
   * Git requires the index to match HEAD before a merge. Step 6 stages a change
     to `other.txt`, so step 7 fails without touching `conflict.txt`, and
     `--diff-filter=U` lists nothing. The step 7 precondition fails, and an
     implementation that skips preconditions would "pass" without testing
     suppression at all. The step 9 cleanup also fails in the corrected order.
   * Verified: running steps 1-7 exactly as written printed `error: Your local
     changes to the following files would be overwritten by merge: other.txt` /
     `Merge with strategy ort failed.`, with exit 2. `git diff --name-only
     --diff-filter=U` printed nothing.
   * Verified: with the merge run first, `git merge topic` exited 1 and
     `--diff-filter=U` listed `conflict.txt`. The conflict alone already made
     `git diff --cached --quiet` and `git diff --quiet` both exit 1, and
     `git diff --cached` printed `* Unmerged path conflict.txt`. This is exactly
     why suppression is needed. After `other.txt` was also modified,
     `git merge --abort` failed with `error: Entry 'other.txt' not uptodate.
     Cannot merge.` and exit 128.
   * Fix: Move step 6 after step 7: "Run `git merge topic` and verify that it
     exits 1 and `git diff --name-only --diff-filter=U` lists `conflict.txt`.
     Then append `staged change` to `other.txt`, run `git add other.txt`, and
     append `unstaged change`." Replace step 9 with "No cleanup is needed; the
     temporary directory is discarded." Alternatively, drop `other.txt`, since
     the conflict alone makes both commands exit 1.

2. **`staged-and-unstaged-changes`, `staged-changes`, and `unstaged-changes`
   always fire together, filling the three-hint limit with overlapping and
   partly contradictory advice.**
   * Location: Stage files Conditions (line 251) and Keep unstaged changes
     Conditions (line 356); compare Review staged changes (line 599).
   * Whenever `staged-and-unstaged-changes` applies, both of its exit codes are
     1, so `staged-changes` (cached = 1) and `unstaged-changes` (worktree = 1)
     also apply. All three are workflow hints, so they sort by ID and take all
     three normal-output slots. That hides `untracked-files` and anything else
     sorted after them. `unstaged-changes` says "stage files" while
     `staged-and-unstaged-changes` says "keep unstaged changes out".
     `staged-and-unstaged-changes` and `staged-changes` show the same command
     (`git diff --cached`, then `git commit -m "message"`). The Git stage text
     of `staged-changes` (line 589) already says unstaged edits will not be
     included.
   * Verified: the test's step 7 state gave `git diff --cached --quiet` exit 1
     and `git diff --quiet` exit 1, which meets all three conditions.
   * Fix: Follow the `diverged` precedent (line 507). Add "When this hint
     applies, do not show `staged-changes` or `unstaged-changes`, because this
     hint replaces them." Give the hint both choices: `git add <file>` to
     include the unstaged edits, or `git commit` to leave them out. In test
     step 7.4, assert that `staged-changes` and `unstaged-changes` are absent.

3. **`push-ahead` parses `git status -sb`, whose branch header is not a stable
   format, and its condition also matches diverged branches.**
   * Location: Push, Conditions (spec.md lines 288-292).
   * The `git-status` documentation reserves stability guarantees for
     `--porcelain`. User configuration changes the short header. `behind`,
     `diverged`, and the `diverged` test (lines 446, 505, 517) all use
     `git status --porcelain=v2 --branch`, so this hint is the odd one out.
     "Ahead of its upstream by one or more commits" is also true when the
     branch is behind as well. That relies on `diverged` suppressing it instead
     of being stated here. "Local repository was changed and looks different
     from remote repository" is vague.
   * Verified: with `-c status.aheadBehind=false`, `git status -sb` printed
     `## main...origin/main [different]`, which has no count, while porcelain
     v2 still printed `# branch.ab +1 -0`. On a diverged branch, `-sb` printed
     `[ahead 1, behind 1]`. I could not check translated output, because no
     Git locales are installed here.
   * Verified: after cloning an empty bare repository and committing, porcelain
     v2 printed `# branch.upstream origin/main` with no `branch.ab` line, and
     `git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}"` exited
     128. So `push-ahead` is absent, and `no-upstream-branch` (which suggests
     `git push -u origin main`) correctly covers this common beginner state.
   * Fix: "Run `git status --porcelain=v2 --branch` and read `# branch.ab
     +<ahead> -<behind>`. The hint applies when `<ahead>` is above 0 and
     `<behind>` is 0. If the line is absent (no upstream, upstream gone, or
     detached HEAD), do not show this hint; `no-upstream-branch` handles a
     missing upstream." Delete the vague first sentence.

4. **`push-ahead`'s command contradicts its test, and its expected result
   describes a format learners will not see.**
   * Location: Push, Command (lines 282-284), and test step 9 (line 307).
   * The Command field gives `git push <remote> <local>:<remote-branch>`, but
     the test expects the hint to suggest `git push`. The expected result
     quotes the `<flag> <summary> <from> -> <to> (<reason>)` table from the
     git-push manual. A successful push prints no `(<reason>)`, and "most
     likely in tabular format" is not a checkable result. Plain `git push`
     also fails in two states that trigger this hint: the upstream has a
     different name (for example, after `git switch -c dev --track
     origin/main`), or the upstream is a local branch (remote `.`).
   * Verified: a successful `git push` printed `To <path>` and
     `   28d26d6..b0267a6  main -> main`. With `dev` tracking `origin/main`,
     the status header was `## dev...origin/main [ahead 1]`, and `git push`
     exited 128 with `fatal: The upstream branch of your current branch does
     not match the name of your current branch`. With `feature` tracking local
     `main`, porcelain v2 showed `# branch.upstream main` and `# branch.ab +1
     -0`, and `git push` failed the same way (suggesting `git push .
     HEAD:main`).
   * Fix: "Command: `git push`; afterward, `git status` reports `Your branch is
     up to date with '<upstream>'`. If the upstream branch's name differs from
     the current branch's name, show `git push <remote> HEAD:<upstream-branch>`
     instead." Also say whether to suppress the hint when the upstream remote
     is `.`.

5. **`not-a-repo` treats every exit code 128 as "outside a repository," and it
   ignores exit code 0 with output `false`.**
   * Location: Clone a Repository, Conditions (spec.md lines 322-326).
   * Git uses exit code 128 for every fatal error, so "avoid suggesting cloning
     for other unexpected Git errors" cannot be done from the exit code alone. A
     learner whose repository fails Git's ownership check (common on shared or
     external drives on Windows) is told to clone, as is one with a broken
     `.git` file. In a bare repository or inside `.git`, the command exits 0
     and prints `false`. The spec does not cover that case, so every other
     hint's `git diff` then fails, and the tool reports an inspection failure.
   * Verified: an empty directory printed `fatal: not a git repository (or any
     of the parent directories): .git`, with exit 128. A `.git` file containing
     `gitdir: /nonexistent/path` printed `fatal: gitfile does not point to a
     valid repository`, with exit 128. A repository failing the ownership check
     (simulated with Git's `GIT_TEST_ASSUME_DIFFERENT_OWNER=1`) printed
     `fatal: detected dubious ownership in repository`, with exit 128. In a
     bare repository and inside `.git`, the command printed `false` with exit
     0, and `git diff --quiet` exited 128 with `fatal: this operation must be
     run in a work tree`.
   * Fix: "Trigger the hint only when the command exits 128 and its standard
     error contains `not a git repository`. Run inspection commands with
     `LC_ALL=C` so this text is not translated. Report any other failure,
     including Git's standard error, as an inspection error. If the command
     exits 0 and prints `false`, report that the directory has no working tree
     (a bare repository or a `.git` directory) and run no other hints."

6. **The spec does not say whether other hints, or the context line, run
   outside a repository, and the `not-a-repo` test would then also see
   `commit-identity`.**
   * Location: Clone a Repository, Conditions and test step 3 (lines 322-336);
     Repository context (line 140); commit-identity item (line 620).
   * `git config --get user.name` works outside a repository, and the test
     never calls `config_user()`. An implementation that runs all checks would
     therefore show `commit-identity` beside `not-a-repo`. "Verify that
     `git-hints` exits normally" is weaker than the Language and libraries
     rule (line 1391) that inspection exits 0.
   * Fix: Add to Conditions "When this hint applies, show no other hint and no
     `Branch:` context line." In test step 3, require exit code 0, require that
     `git-hints --all --ids-only` prints exactly `not-a-repo`, and require that
     the `--all` output has no `Branch:` line.

### Test cases

7. **Presence and absence checks use `--all` and hint titles instead of
   `--all --ids-only` and IDs, and two titles match no hint text.**
   * Location: Stage files steps 7 and 9 (lines 268-272); Push steps 6 and 9
     (lines 303-308); Clone steps 3-4 (lines 334-338); Keep unstaged changes
     steps 5.3, 6.3, and 7.4 (lines 379-397).
   * The Testing section (line 1450) says to check presence or absence with
     `git-hints --all --ids-only` and to compare whole lines. `--all` is for
     checking content. "Expected hint: **Push?**" and "**Clone a repo?**" match
     neither hint text ("Do you want to push?", "Would you like to clone
     repo?"), and Clone step 3 says "identified by its permanent ID" without
     naming `not-a-repo`.
   * Fix: Use `git-hints --all --ids-only` for every "appears/absent" check,
     name the IDs, and keep `--all` only for the content checks (command, link,
     "as of last fetch" label).

8. **Several tests skip the positive or negative case that would catch the
   likeliest bugs.**
   * Location: Push test (lines 294-308); Keep unstaged changes test, step 6
     (lines 385-390) and step 7.5 (lines 399-404).
   * The Push test never pushes the new commit to confirm the hint disappears,
     which would also check the expected result. Step 6 of the Keep test is the
     ideal state to assert that `unstaged-changes` is present, but it doesn't.
     Steps 5.4 and 7.5 re-test the content of `staged-changes`, which its own
     test already covers. Step 7.5 expects `https://git-scm.com/docs/git-diff`
     in the `staged-and-unstaged-changes` hint, but that link appears only in
     the heading (line 340), not in the hint text (lines 342-344).
   * Fix: Add Push step 10: "Run `git push`, verify `# branch.ab +0 -0`, and
     verify that `push-ahead` is absent." In Keep step 6, assert that
     `unstaged-changes` appears. Move the `git diff` link from the heading into
     the hint text. Delete the `staged-changes` content checks in 5.4 and 7.5.

### Structure and consistency

9. **The `not-a-repo` hint lacks an expected result and links to the wrong
   page.**
   * Location: Clone a Repository, Hint and Command (lines 312-318).
   * Hint structure item 1 requires an expected result. The link goes to the
     Pro Git chapter on maintaining a GitHub project (creating a repository on
     GitHub), not to `git clone`, and its title defines "repo" rather than the
     command. I identified the target from its URL and did not fetch it. The
     Git stage sentence mentions initializing a repository, but the command
     offers only `git clone`. A learner who is simply one directory above their
     project gets no `cd` advice.
   * Fix: "Hint: Do you want to
     [clone](https://git-scm.com/docs/git-clone "Copies an existing repository,
     with its history, into a new directory") a repository? If your project
     already exists, `cd` into its directory first." "Command: `git clone
     <repository-url>`; afterward, Git creates a directory named after the
     repository; `cd` into it. To start a new repository here instead, run
     `git init`."

10. **Heading levels, field layout, and attribution differ among the four
    hints, and the Push test list escapes its bullet.**
    * Location: lines 237, 274, 310, 340, 276-296, 312-318.
    * `### Push` and `### Clone a Repository` are siblings of
      `` ### `git-hints` `` while the other hints are `####`. In Push, Git stage and Command are
      paragraphs inside the Hint bullet, and ID, Conditions, and Test case are
      nested bullets. The numbered steps (indent 2) render as a sibling of
      those bullets, not under "Test case". Clone puts Git stage and Command
      inside the Hint bullet too. Stage files has no author; Push and Clone use
      `(ewj55)`; the last heading uses `**Sbe80**` and embeds a link.
    * Fix: Use `####` headings, write a plain heading such as `#### Keep
      unstaged changes out of the next commit? (sbe80)` and move the link into
      the hint text, make every field a top-level `*` bullet, indent test steps
      4 spaces under `* Test case:`, and add the author of Stage files.

11. **The `staged-and-unstaged-changes` hint text overstates what `git commit`
    does.**
    * Location: Keep unstaged changes, Hint (lines 342-344).
    * "This commit" implies a commit in progress, but the hint is proactive.
      "`git commit` records staged changes only" is false for `git commit -a`
      and `git commit <path>`, which learners often use. They would commit the
      edits that the hint says are excluded.
    * Fix: "Some changes are staged and others are not. A plain `git commit`
      records only the staged changes; `git commit -a` would also include the
      unstaged edits to tracked files."

### Minor

* Line 325: stray `"` after "triggers this hint."; "its outside" should be
  "it's outside".
* Line 279 "Git Stage" and line 320 "Informational" are capitalized unlike the
  other hints.
* Line 277: the push link title is a comma splice, and push sends commits, not
  "changes"; try "Uploads your local commits to the remote branch so
  collaborators can fetch them."
* Line 240: "stage" is not "also called the index" (the staging area is); try
  "Adds file contents to the staging area (the index) for the next commit".
* `safety: safe` (lines 249, 286, 320, 354) is a field that Hint structure
  never defines; define it there or drop it.
* Line 296 and lines 330, 369, 407: tests call `git_setup()` explicitly
  although it is an autouse fixture; lines 369 and 407 say "create one
  temporary directory" where `make_temps(1)` is meant.
* Lines 330-331: setting `GIT_CEILING_DIRECTORIES` again is redundant, because
  `git_setup()` already sets it to pytest's base temporary directory, which is
  the parent of each `make_temps()` directory.
* Line 372: "after initializing the repository" implies an ordering that does
  not matter, since `config_user()` writes global configuration.
* Line 305: for consistency with the `behind` and `diverged` tests, check
  `# branch.ab +1 -0` instead of counting `git log origin/main..HEAD` output.
* Line 323: "using `subprocess`" repeats Language and libraries.
* Line 404-405: add a blank line before `* Conflict suppression test:`.
