`git-hints` specification
=========================

`git-hints` is a Python command-line tool that helps Git learners see where they
are and what to do next. Run with no arguments, it inspects the current
repository's state then displays up to three proactive hints (or every hint with
`--all`), ordered from blocking errors through data-loss risks and workflow
suggestions to informational notes. Run as `git-hints explain -- <git command>`,
it executes the Git command, captures its exit code and standard error, and
offers explanatory hints for failures such as merge conflicts, pulls blocked by
uncommitted changes, and rejected pushes. Each hint has a permanent ID and shows
the terminal command to run and its expected result. It also names the Git stage
the user is working in (working directory, staging area, local repository, or
remote) and links to the official documentation, so users learn Git's mental
model as they work.

Review assignments
------------------

<mark>Each student reviews one of the seven sections below. A "Review section"
note marks where each section begins; the section continues until the next such
note. Sections are roughly equal in length (about 200 lines) and difficulty, and
no student reviews material they wrote or revised.</mark>

1. (ams2083): the overview at the top of this document, CLI commands, Future
   Work, Hint structure, and the introduction to Implementation.
2. (jit45): `unstaged-changes`, `push-ahead`, `not-a-repo`, and
   `staged-and-unstaged-changes`, including its conflict suppression test.
3. (ewj55): `behind`, `diverged`, the gitignore item, `no-upstream-branch`,
   `staged-changes`, and the commit-identity item.
4. (raf322): `untracked-files`, `many-changed-files`, and, among the reactive
   hints, `rebase-after-repeated-integration-failures`.
5. (jhg246): `detached-head`, `no-commits`, and the protected/main branch item.
6. (drj228): the `git-hints explain` introduction, `merge-conflicts`,
   `pull-blocked-local-changes`, the push-failed item, and
   `stash-local-changes`.
7. (sbe80): Pull remote changes, `pull-before`, Language and libraries, Testing,
   and Test Cases 14 and 15.

<mark>Review section 1 (ams2083) begins here; see Review assignments.</mark>

CLI commands
============

1. **`git-hints`**: inspect observable repository state and display up to three
   currently triggered proactive hints in priority order. If more than three
   hints are triggered, state how many additional hints are available. Do not
   perform a network operation unless `--fetch` is supplied. (jit45)

   1. **`--all`**: display every currently triggered proactive hint instead of
      applying the three-hint limit. (jit45)

   2. **`--ids-only`**: print only the IDs of the hints that would otherwise be
      displayed, one per line in display order. Print no branch context,
      explanatory text, additional-hints notice, fetch messages, or other
      labels. Print nothing if no hints trigger. The three-hint limit still
      applies unless `--all` is also present. Use `git-hints --all --ids-only`
      in tests that assert a hint is present or absent. Exit codes are
      unchanged. (sbe80; clarified by drj228)

   3. **`--fetch`**: before inspecting a working tree, run `git fetch --quiet
      --no-auto-maintenance` with `GIT_TERMINAL_PROMPT=0`, standard input
      redirected from `subprocess.DEVNULL`, output captured, and a 10-second
      timeout. Fetch from the remote associated with the current branch's
      upstream, or from `origin` if there is no upstream but `origin` exists. If
      neither exists, skip fetching and treat remote information as cached. Skip
      fetching outside a working tree. A successful fetch permits `push-ahead`,
      `behind`, and `diverged` hints to omit their “as of last fetch” qualifier.
      If fetching fails, times out, or is skipped for lack of an applicable
      remote, continue inspecting using cached information; this is not an
      unexpected inspection failure. After the branch context line, print `Fetch
      failed; showing results as of last fetch.` for a failed or timed-out fetch
      (except under `--ids-only`). Retain “as of last fetch” on affected hints.
      Without `--fetch`, never fetch and label `push-ahead`, `behind`, and
      `diverged` hints “as of last fetch.” (jhg246)
2. **`git-hints explain -- <git command>`**: execute the supplied Git command,
   capture its exit code and standard error, and select reactive hints from the
   resulting error. Return the same exit code as Git. The arguments must begin
   with `git`; otherwise print an error to standard error, run nothing, and
   exit 2.

   * A `--` separator before the Git command is recommended to make argument
     boundaries unambiguous.

   * Global options, where applicable, precede `explain`: for example,
     `git-hints --ids-only explain -- git push`. The `--fetch` option is invalid
     with `explain` and must be rejected without running Git.

   * Emit captured Git standard error to standard error. In normal output, print
     `Git exited with code <n>.` before any reactive hint blocks on standard
     output. When Git exits successfully, print `No error detected.` instead of
     a reactive hint. On a nonzero exit, print all triggered reactive hints
     using the `ID: <id>` block format below; the proactive three-hint limit
     does not apply. No branch context line is printed for `explain`.

   * Under `--ids-only`, standard output contains only triggered reactive hint

IDs, one per line, and no exit-code message. Captured standard error remains on
standard error; the process still returns Git's exit code. With `--all`, the
reactive output remains complete.

* Configure Typer to accept extra arguments and ignore unknown options
  (`allow_extra_args=True`, `ignore_unknown_options=True`), so Git receives
  flags and arguments intact. Examples: `git-hints explain -- git pull --rebase`
  and `git-hints explain -- git reset --hard HEAD~1`. (sbe80)

* On Windows, call the Typer entry point with `app(windows_expand_args=False)`
  to prevent Typer/Click from expanding wildcards, `~`, and environment
  variables intended for Git. This setting applies to the CLI entry point, not
  just `explain`.

* Any state needed across invocations, including counts of repeated integration
  failures, belongs under the path returned by `git rev-parse --git-path
  git-hints` so linked worktrees are handled correctly.

3. **`--help`**: Typer automatically generates help for commands and
   subcommands. Each implemented command/subcommand docstring must include at
   least one complete usage example, such as `git-hints --all` or `git-hints
   explain -- git pull`. Do not advertise unimplemented future-work commands as
   available. (jit45)

Future Work
===========

The following features are **future work; do not implement them in the initial
version**.

1. **`git-hints def <term>`**: display a short definition for a supported Git
   command or term and link to official documentation; report unsupported terms
   rather than inventing definitions. An editor such as CodeChat Editor could
   invoke `git-hints def <term>` to display an inline summary and documentation
   link when a user types a term such as `repo` or `pull`. (jit45; ewj55)

2. **`git-hints howto <task>`**: provide verified step-by-step instructions for
   supported tasks such as committing, pulling, and pushing. Report unsupported
   tasks rather than generating unverified instructions. (jit45)

3. **`git-hints --exclude <hint-id1[,hint-id2[,...]]>`**: exclude the specified
   permanent hint IDs from generated output.

4. **`git-hints --dismiss <hint-id1[,hint-id2[,...]]>`**: dismiss currently
   triggered hints. Save each hint ID and the condition values used to trigger
   it at the location returned by `git rev-parse --git-path
   git-hints/dismissals.json`. Suppress a dismissed hint in normal and `--all`
   output while those values remain unchanged. Clear the dismissal if the
   relevant values change or the condition ceases to apply; unrelated repository
   changes must not clear it. For example, fixing only a missing user name
   allows `commit-identity` to reappear if a missing email still triggers it.
   (ewj55; clarified by drj228, sbe80, and jit45)

5. **`git-hints --bug <comments> [explain -- ...]`**: collect the current
   repository state and, for `explain`, Git command output, then propose an
   issue for the project's GitHub repository. Before sending anything, preview
   the collected information, redact secrets (including tokens in remote URLs),
   and require explicit user consent; repository state can contain sensitive
   paths and identifiers.

Hint structure
==============

1. **Repository context**: in normal output and with `--all`, if `git rev-parse
   --is-inside-work-tree` reports `true`, make the first output line `Branch:
   <name>` using `git branch --show-current`. If that command returns an empty
   name (detached HEAD, including during a rebase or bisect), print `Branch:
   detached HEAD`. This line is not a hint, has no ID, and does not count toward
   the three-hint limit. Under `--ids-only`, omit it. (sbe80; clarified by
   drj228) If `git rev-parse --is-inside-work-tree` succeeds but reports `false`
   (for example, in a bare repository or inside `.git`), print `Not inside a
   working tree (bare repository or .git directory); run git-hints from the
   project directory.`, generate no working-tree hints, and exit 0; under
   `--ids-only`, print nothing. Outside a repository, use the separate
   `not-a-repo` handling specified in Implementation.

2. **Required hint fields**: every hint has a permanent ID, exactly one priority
   class, exactly one safety level, hint text containing at least one official
   documentation link, a one-sentence Git-stage explanation, at least one
   suggested command, and that command's expected result. The Git-stage sentence
   identifies the working directory, staging area, local repository, or remote
   repository as applicable. The first implementation supports the CLI; a future
   GUI may show the corresponding GUI action alongside the command. (ewj55;
   clarified by drj228)

3. **Documentation targets**: link to the specific passage of the official Git
   manual that supports a hint. Prefer the page's existing anchor. Otherwise use
   a
   [text fragment](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Fragment/Text_fragments),
   such as `#:~:text=Updates%20one%20or%20more%20branches`, quoting wording that
   appears on the page and percent-encoding reserved characters. The page must
   remain useful if the browser ignores the fragment. (ewj55)

4. **Markdown and terminal rendering**: hint source text supports plain text,
   inline code spans, and inline Markdown links of the form `[label](url
   "title")`. Each link must have a meaningful title of at most 160 Unicode code
   points, with no embedded double-quote character; longer explanations belong
   in the documentation itself. Terminal rendering removes code-span backticks,
   prints each link label inline followed by a numbered reference `[n]`, and
   after the hint text prints each link on its own line as `[n] label: title
   URL`. Do not insert the title and URL in the middle of a sentence.
   Descriptions must remain visible without hover. (drj228) For example, source
   text `Do you want to [stage](https://git-scm.com/docs/git-add "Choose changed
   files for the staging area") files?` becomes:

   ```text
   Do you want to stage [1] files?
   [1] stage: Choose changed files for the staging area https://git-scm.com/docs/git-add
   ```

5. **Priority**: assign every hint exactly one priority class based on the
   **repository state or failure the hint reports**, not the danger of its
   suggested command. Use these exact lowercase class names, highest priority
   first:

   1. `error/blocked`: a failed command, an unresolved conflict, or another
      state preventing the current operation from proceeding.

   2. `data-loss risk`: an existing state that puts work at risk of being lost,
      such as detached HEAD with commits not contained in any local branch. Name
      the work at risk. Do not classify an otherwise ordinary hint in this class
      only because its suggested command is risky.

   3. `workflow`: a useful, actionable next step based on repository state.

   4. `informational`: explanatory guidance that does not block work.

   Within a priority class, place specifically important state hints ahead of
   routine suggestions using this precedence for the named IDs when they
   coexist: `merge-conflicts`, `detached-head`, `no-commits`, `diverged`,
   `behind`, `push-ahead`, `staged-and-unstaged-changes`, `staged-changes`,
   `unstaged-changes`, `untracked-files`. This ordering applies only within a
   class; class order always wins. Other IDs sort by Unicode code point after
   the listed IDs within their class. Future IDs that require special precedence
   must be added to this list explicitly. Where detached HEAD includes commits
   not contained in any local branch (check `git for-each-ref --contains HEAD
   refs/heads`), classify `detached-head` as `data-loss risk`; otherwise
   classify it as `informational` unless its individual definition specifies a
   higher applicable class.

6. **Command safety**: apply safety labeling to **each suggested command**,
   independently of the hint's priority class. Commands that only read or add
   changes without discarding existing work need no prefix. Prefix `Caution:`
   when the command rewrites commits or moves a branch while the prior commits
   generally remain recoverable through the reflog (for example, `git pull
   --rebase` or `git commit --amend`). Prefix `Warning:` when the command can
   permanently destroy uncommitted, staged, or untracked work, a stash, or
   remote commits (for example, `git reset --hard`, `git clean -f`, `git stash
   drop`, or `git push --force`); identify what might be lost and instruct the
   user to back up first. Each hint's `safety` field is the strongest risk among
   its commands: `safe`, `caution`, or `warning`. For example, a `diverged` hint
   that suggests `Caution: git pull --rebase` has `safety: caution` even if its
   priority class is `workflow`.

7. **Operation-in-progress protection**: before recommending a workflow command,
   determine whether an operation is in progress by checking unmerged index
   entries and applicable Git paths returned by `git rev-parse --git-path`
   (`MERGE_HEAD`, `rebase-merge`, `rebase-apply`, `CHERRY_PICK_HEAD`,
   `REVERT_HEAD`, and `BISECT_START`). If any such state is detected, show an
   appropriate proactive `error/blocked` hint for an unresolved or stopped
   operation, and suppress workflow suggestions whose commands would fail or
   interfere until the operation is resolved. In particular, `merge-conflicts`
   must be available as a proactive as well as reactive hint, and staged changes
   must not cause an unconditional suggestion to commit while the index contains
   unresolved conflicts. An ongoing but healthy bisect is not necessarily an
   error: explain the state and suppress only incompatible suggestions.

8. **IDs and output blocks**: each hint must have a unique, permanent lowercase
   ASCII kebab-case ID matching `[a-z][a-z0-9]*(-[a-z0-9]+)*`, shared across
   proactive and reactive hint definitions. IDs do not depend on list positions
   or display wording and are never reused for different hints. Use the ID for
   test assertions and, in future, `--exclude` and `--dismiss`. (sbe80;
   clarified by drj228) In normal output and with `--all`, each hint starts with
   a line exactly `ID: <id>`, followed by `Priority: <class>`, its hint text and
   documentation references, `Git stage: <sentence>`, `Command: <command>`, and
   `Result: <expected outcome>`. Each block ends immediately before the next
   `ID:` or at the end of output. There is no separate title field: tests should
   identify hints by ID rather than by an incidental heading. Place any
   additional-hints notice ahead of the first hint block. With no triggered
   hints, print `No hints.` after the context line; with `--ids-only`, print
   nothing. With more than three hints in normal output, place the exact notice
   `<n> more hint(s) available; run "git-hints --all" to see them.` immediately
   after the context line, where `<n>` is the number not shown. (drj228) Example
   normal output when five hints are triggered, the first of which is `behind`:

   ```text
   Branch: main
   2 more hint(s) available; run "git-hints --all" to see them.
   ID: behind
   Priority: workflow
   As of last fetch: Do you want to pull [1] the newest remote commits?
   [1] pull: Incorporate changes from a remote repository https://git-scm.com/docs/git-pull
   Git stage: Your local repository is behind its configured remote-tracking branch.
   Command: git pull
   Result: Your local branch incorporates the incoming changes if the pull succeeds.
   ```

The example is illustrative, not a claim that `git pull` will always succeed or
that these specific five hints can coexist in every repository.

Implementation
==============

`git-hints`
-----------

Proactive hints are triggered by observable repository state when `git-hints`
runs. (jit45)

<mark>Review section 2 (jit45) begins here; see Review assignments.</mark>

#### Stage files

* Hint: Do you want to
  [stage](https://git-scm.com/docs/git-add "Also called the index; select which changed files to store in a commit")
  files?

* Git stage: Your edits are in the working directory; Git won't put them in a
  commit until you stage them.

* Command: `git add <files to stage>`; afterward, `git status` lists these files
  under "Changes to be committed."

* ID: `unstaged-changes`, priority class: workflow, safety: safe.

* Conditions: Do not display this hint while the index contains unresolved merge
  entries; check with `git diff --name-only --diff-filter=U` and suppress the
  hint if it returns any paths. Otherwise, display the hint when unstaged edits
  to tracked files exist in the repository. Run `git diff --quiet`; an exit code
  of 0 means no unstaged edits; 1 means there are unstaged edits; other return
  codes indicate an error.

* Test case:

  1. Invoke `make_temps(tmp_path_factory, 1)` to create a temporary directory.
  2. Execute the following in this temp directory:
     1. Call `config_user("user1", "user1@example.com")`.
     2. Create an empty git repo with `git init -b main`.
     3. Create a file called `foo.txt` with the content `xxx`.
     4. Add it: `git add foo.txt`.
     5. Commit it: `git commit -m "Add foo."`.
     6. Modify `foo.txt`: append `y` to it.
     7. Run `git-hints --all --ids-only` in the temp dir. Verify that
        `unstaged-changes` appears.
     8. Stage the changes: `git add foo.txt`.
     9. Run `git-hints --all --ids-only` in the temp dir. Verify that
        `unstaged-changes` is absent.

### Push (ewj55)

* Hint: Do you want to
  [push](https://git-scm.com/docs/git-push "Uploads the latest changes of your local repository (repo) to a remote repository, this allows other collaborators to download your work.")?

  Git stage: Your local repository has commits that are not contained in its
  upstream tracking branch.

  Command: `git push <remote> HEAD:<upstream-branch>`; replace `<remote>` with
  the upstream's remote and `<upstream-branch>` with its branch name. After a
  successful push, the remote branch contains the uploaded commits.

  * ID: `push-ahead`, priority class: workflow, safety: safe.

  * Conditions: Run `git status --porcelain=v2 --branch` to check the current
    branch's upstream status. Display this hint only when the current branch
    tracks a branch on a configured remote, is ahead by one or more commits, and
    is behind by zero commits. Use that upstream's remote and branch name in the
    suggested push command; do not display this hint for a local upstream. Label
    the hint "as of last fetch" unless `--fetch` succeeds.

  * Test case:

  1. **Setup** The autouse `git_setup` fixture provides the isolated
     environment. Create three temporary directories: `remote`, `local`, and
     `other`.

  2. Call `config_user("user1", "user1@foo.com")`.

  3. In `remote`, run `git init --bare -b main`.

  4. Clone `remote` into `local` using `git clone <remote> <local>`.

  5. In `local`, create `foo.txt` containing `xxx`, run `git add foo.txt`, `git
     commit -m "Add foo."`, then `git push -u origin main`.

  6. Run `git-hints --all --ids-only` in `local`. Verify that `push-ahead` is
     absent.

  7. Append `y` to `foo.txt` and run `git commit -am "Change foo."`.

  8. Run `git log origin/main..HEAD` and verify it lists exactly one commit.

  9. Run `git-hints --all --ids-only` in `local`. Verify that `push-ahead`
     appears and `behind` and `diverged` are absent. Run `git-hints --all` and
     verify that the hint is labeled "as of last fetch" and suggests `git push
     origin HEAD:main`.

  10. Clone `remote` into `other`. In that clone, create and commit a new file,
      then push the commit to `remote`. Run `git fetch` in `local` and verify
      that the local branch is both ahead of and behind its upstream.

  11. Run `git-hints --all --ids-only` in `local`. Verify that `push-ahead` is
      absent and `diverged` is present.

  12. Test different local and upstream branch names. In `local`, run `git
      switch -c dev --track origin/main` to create a local `dev` branch tracking
      `origin/main`. Create `dev.txt` containing `xxx`, stage it, and commit it
      with `git commit -m "Add dev."`. Verify that `git status --porcelain=v2
      --branch` reports `# branch.upstream origin/main` and `# branch.ab +1 -0`.
      Run `git-hints --all --ids-only` and verify that `push-ahead` appears. Run
      `git-hints --all` and verify that it suggests `git push origin HEAD:main`.

  13. Test a local-only upstream. In `local`, run `git switch main` and `git
      switch -c local-test`. Set the upstream with `git branch
      --set-upstream-to=main local-test`. Create `local.txt` containing `xxx`,
      stage it, and commit it with `git commit -m "Add local."`. Verify that
      `git status --porcelain=v2 --branch` reports `# branch.upstream main` and
      `# branch.ab +1 -0`. Run `git-hints --all --ids-only` and verify that
      `push-ahead` is absent because the upstream is a local branch.

### Clone a Repository (ewj55)

* Hint: Would you like to clone a
  [repository](https://git-scm.com/docs/git-clone "Clone a repository into a new directory")?

  Git stage: You are not inside a Git repository, you need to either clone or
  initialize a repository before you can begin tracking files.

  Command: `git clone <repository-url>`; afterward, Git creates a local copy of
  the specified repository.

* ID: `not-a-repo`, priority class: informational, safety: safe.

* Conditions: Run `git rev-parse --is-inside-work-tree` using `subprocess`. Exit
  code 0 with output `true` means the directory is inside a working tree; output
  `false` uses the separate non-working-tree handling. Trigger this hint on exit
  code 128 only when Git reports that the directory is not a repository. Treat
  other failures as inspection errors.

* Test case:

  1. The autouse `git_setup` fixture provides the isolated environment and
     `make_temps(tmp_path_factory, 1)`. Set `GIT_CEILING_DIRECTORIES` to the
     temporary directory's parent so Git cannot discover an enclosing repo.
  2. In the temporary directory, run `git rev-parse --is-inside-work-tree` and
     verify exit code 128.
  3. Run `git-hints --all --ids-only`. Verify that `not-a-repo` appears. Run
     `git-hints --all` and verify that the hint suggests `git clone
     <repository-url>`, links to the official Git documentation, and that
     `git-hints` exits normally.
  4. Run `git init -b main`, then `git-hints --all --ids-only` again. Verify
     that `not-a-repo` is absent.

#### Keep [unstaged changes](https://git-scm.com/docs/git-diff "Shows unstaged changes in the working tree.") out of this commit? **Sbe80**

* Hint: Do you want to keep unstaged changes out of this commit?
  [git commit](https://git-scm.com/docs/git-commit "Records the staged changes in a new commit.")
  records staged changes only. Review the staged changes with
  [git diff](https://git-scm.com/docs/git-diff "Shows changes staged for the next commit").

* Git stage: Some of your edits are in the staging area and will be included in
  the next commit; other edits remain in the working directory and will not be
  included.

* Command: `git diff --cached`; afterward, the displayed changes are the ones
  staged for the next commit. When ready, commit those changes with `git commit
  -m "message"`.

* ID: `staged-and-unstaged-changes`, priority class: workflow, safety: safe.

* Conditions: Do not display this hint while the index contains unresolved merge
  entries; check with `git diff --name-only --diff-filter=U` and suppress the
  hint if it returns any paths. Otherwise, display the hint when the staging
  area contains at least one staged change and the working tree contains at
  least one unstaged change to a tracked file. Run `git diff --cached --quiet`
  to check for staged changes and `git diff --quiet` to check for unstaged
  changes to tracked files. For either command, exit code 1 means changes exist,
  exit code 0 means none exist, and any other exit code indicates an error. Show
  the hint only when both commands exit with code 1; do not show it when only
  staged changes or only unstaged changes exist. (drj228; sbe80 will test)

* Test case: Staged and unstaged changes.

  1. The autouse `git_setup` fixture provides the isolated environment and
     create one temporary directory.
  2. In the temporary directory, initialize a repository with `git init -b
     main`.
  3. Call `config_user("user1", "user1@foo.com")` after initializing the
     repository.
  4. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
     commit it with `git commit -m "Add foo."`.
  5. Check the staged-only state:
     1. Append `y` to `foo.txt` and run `git add foo.txt`.
     2. Run `git-hints --all --ids-only` to check hint IDs and `git-hints --all`
        to verify the hint's content.
     3. Verify that the `staged-and-unstaged-changes` hint is absent, because
        there are no unstaged changes.
     4. Verify that the `staged-changes` hint appears. Verify that it recommends
        reviewing staged changes with `git diff --cached` and explains how to
        commit the selected changes with `git commit -m "message"`. Check the
        corresponding official Git documentation links.
  6. Check the unstaged-only state:
     1. Commit the staged change with `git commit -m "Append y."`.
     2. Append `z` to `foo.txt` without staging it.
     3. Run `git-hints --all --ids-only` and verify that both the
        `staged-and-unstaged-changes` and `staged-changes` hints are absent: the
        file has unstaged changes, but nothing is staged for the next commit.
  7. Check the staged-plus-unstaged state:
     1. Run `git add foo.txt` to stage the `z` change.
     2. Append `w` to `foo.txt` and leave this change unstaged.
     3. Run `git-hints --all --ids-only` to check hint IDs and `git-hints --all`
        to verify the hint's content.
     4. Verify that both the `staged-and-unstaged-changes` and `staged-changes`
        hints appear. Verify that the `staged-and-unstaged-changes` hint
        explains that a plain `git commit` records staged changes only and
        suggests `git diff --cached`.
     5. Verify that `staged-changes` recommends reviewing the staged changes
        with `git diff --cached` and committing the selected changes with `git
        commit -m "message"`. Confirm the two hints are distinct and include the
        corresponding official Git documentation links, including
        `https://git-scm.com/docs/git-diff` and
        `https://git-scm.com/docs/git-commit`.
* Conflict suppression test:

  1. The autouse `git_setup` fixture provides the isolated environment and
     create one temporary directory.
  2. Initialize a repository there with `git init -b main` and call
     `config_user("user1", "user1@example.com")`.
  3. Create `conflict.txt` and `other.txt`, each containing `base`. Stage both
     files and commit them with `git commit -m "Add files."`.
  4. Create a branch named `topic` with `git switch -c topic`, change
     `conflict.txt` to `topic change`, and commit it.
  5. Switch back to `main`, change `conflict.txt` to `main change`, and commit
     it. The branch histories now conflict on `conflict.txt`.
  6. Run `git merge topic` and verify that it exits nonzero and leaves
     `conflict.txt` unresolved. Verify that `git diff --name-only
     --diff-filter=U` lists `conflict.txt`.
  7. Verify that `git diff --cached --quiet` and `git diff --quiet` both exit 1
     while the merge conflict remains unresolved.
  8. Run `git-hints --all --ids-only`. Verify that both
     `staged-and-unstaged-changes` and `unstaged-changes` are absent while the
     conflict exists.
  9. Run `git merge --abort` as cleanup, including if an assertion fails.

<mark>Review section 3 (ewj55) begins here; see Review assignments.</mark>

#### Branch is behind upstream (jhg246)

* Hint: Do you want to
  [pull](https://git-scm.com/docs/git-pull "Fetches commits from the remote and integrates them into your current branch")
  the newest remote commits before you start editing? Your branch does not
  contain remote commits that were known at the last fetch.

* Git stage: You are working in the local repo, which is missing commits that
  the remote repo already has.

* Command: `git pull`; afterward, `git status` reports that your branch is up to
  date with its upstream. To preview first, run `git diff --name-only
  HEAD...@{upstream}`, which lists the files the pull would bring in.

* ID: `behind`, priority class: workflow, safety: safe.

* Conditions: The current branch has an upstream and is behind it by one or more
  commits but not ahead of it. Run `git status --porcelain=v2 --branch` and read
  `# branch.ab +<ahead> -<behind>`; the line is absent when there is no
  upstream. The hint applies when `<behind>` is above 0 and `<ahead>` is 0. If
  the branch is also ahead, the `diverged` hint applies instead. These counts
  use the last-fetched remote-tracking branch, so label the hint "as of last
  fetch" (see `git-hints --fetch`). (jhg246; adapted from jit45's personal
  experience; jhg246 and raf322 will test)

* Test case:

  1. The autouse `git_setup` fixture provides the isolated environment and
     create two temporary directories, `repo1` and `repo2`. Run every
     `git-hints` command in `repo2`.
  2. In `repo1`, initialize a repository with `git init -b main` and call
     `config_user("user1", "user1@foo.com")`.
  3. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
     commit it with `git commit -m "Add foo."`.
  4. Clone `repo1` into `repo2` with `git clone <repo1> <repo2>`.
  5. In `repo1`, append `y` to `foo.txt` and run `git commit -am "Change foo."`.
     `repo1` acts as the remote. Nothing is pushed, because `repo2` only fetches
     from it, so it does not need to be bare.
  6. In `repo2`, run `git status --porcelain=v2 --branch` and verify that it
     reports `# branch.ab +0 -0`. Run `git-hints --ids-only` and verify that
     `behind` is absent, because `repo2` has not fetched.
  7. In `repo2`, run `git fetch` and verify that the status now reports `#
     branch.ab +0 -1`.
  8. Run `git-hints --all`. Verify that the `behind` hint appears, is labeled
     "as of last fetch", recommends `git pull`, and links to the official `git
     pull` documentation. Verify that `diverged` and `push-ahead` are absent.
  9. In `repo1`, append `z` and run `git commit -am "Change foo again."`. In
     `repo2`, run `git fetch` and verify `# branch.ab +0 -2`. Run `git-hints
     --ids-only` and verify that `behind` still appears.
  10. In `repo2`, run `git pull` and verify `# branch.ab +0 -0`. Run `git-hints
      --ids-only` and verify that `behind` is absent.
  11. In `repo1`, append `w` and run `git commit -am "Change foo once more."`.
      In `repo2`, run `git-hints --ids-only` and verify that `behind` is absent,
      then run `git-hints --ids-only --fetch` and verify that `behind` appears
      even though `repo2` never ran `git fetch` itself.

#### Branch has diverged from upstream (sbe80; edited by jhg246)

* Hint: Your branch has diverged from its upstream. Do you want to integrate the
  remote commits with
  [git pull](https://git-scm.com/docs/git-pull "Fetches and integrates remote commits; --rebase replays yours on top of them.")
  and then share yours with
  [git push](https://git-scm.com/docs/git-push "Uploads local commits to the remote branch.")?

* Git stage: You are working in the local repo, which has commits that the
  remote lacks while the remote has commits that your local repo lacks.

* Command: `git pull --no-rebase`, resolve any conflicts, then `git push`;
  afterward, `git status` reports that your branch is up to date with its
  upstream. If you prefer a linear history, Caution: `git pull --rebase` replays
  your local commits on top of the remote ones, which changes them; they remain
  recoverable through the reflog. A plain `git pull` fails on diverged branches
  unless `pull.rebase` or `pull.ff` is configured.

* ID: `diverged`, priority class: workflow, safety: safe.

* Conditions: The current branch has an upstream and is both ahead of and behind
  it, as of the last fetch. Run `git status --porcelain=v2 --branch` and read `#
  branch.ab +<ahead> -<behind>`; the hint applies when both numbers are above 0.
  When it applies, do not show the `behind` or `push-ahead` hints, because this
  hint replaces them. Label the hint "as of last fetch" (see `git-hints
  --fetch`). Do not display this hint while a merge is in progress (`git
  rev-parse -q --verify MERGE_HEAD` exits 0) or while the index has unresolved
  entries (`git diff --name-only --diff-filter=U` returns paths). (sbe80; edited
  by jhg246; jhg246 will test)

* Test case:

  1. Do steps 1-5 of the `behind` hint's test case. This leaves `repo1` with a
     commit that `repo2` has not fetched.
  2. In `repo2`, create `bar.txt` containing `zzz`, stage it with `git add
     bar.txt`, and commit it with `git commit -m "Add bar."`.
  3. Run `git status --porcelain=v2 --branch` and verify `# branch.ab +1 -0`.
     Run `git-hints --ids-only` and verify that `push-ahead` appears and
     `diverged` is absent, because `repo2` has not fetched the new remote
     commit.
  4. Run `git fetch` and verify that the status now reports `# branch.ab +1 -1`.
  5. Run `git-hints --all`. Verify that the `diverged` hint appears, is labeled
     "as of last fetch", suggests `git pull` or `git pull --rebase` and then
     `git push`, and links to the official `git pull` and `git push`
     documentation. Verify that `behind` and `push-ahead` are absent.

5. Place these files in gitignore? Conditions: Files such as \_\_pycache\_\_/,
   output build directories, etc. should be flagged. Suggest that the user
   create a .gitignore file and slate those files for entry. Suggest `git rm
   --cached` if user wants to unstage a file from the commit. (raf322)

#### Configure an upstream branch? (ams2083)

* Hint: Do you want to configure an
  [upstream branch](https://git-scm.com/docs/git-branch "A remote branch that your local branch tracks")
  before pushing?

* Git stage: Your current branch has no upstream branch configured. An upstream
  allows Git to identify which remote branch your local branch tracks,
  simplifying future pushes and pulls.

* Command: `git push -u origin <branch-name>` pushes the current branch to
  `origin` and configures its upstream for future pushes and pulls.

* ID: `no-upstream-branch`, priority class: workflow, safety: safe.

* Conditions: The current branch has no upstream branch configured. Confirm that
  the repository is on a local branch, rather than in a detached HEAD state,
  using `git symbolic-ref --quiet --short HEAD`. Check for an upstream using
  `git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}"`. Confirm that
  the `origin` remote exists using `git remote`. Suggest configuring an upstream
  only when the current branch has no resolvable upstream and `origin` exists.
  Do not display the hint in detached HEAD state or when a valid upstream is
  configured.

* Test case:

1. Invoke `make_temps(tmp_path_factory, 2)` to create two temporary directories.
2. In the first directory:
   1. Initialize a repository with `git init -b main`.
   2. Call `config_user("user1", "user1@foo.com")`.
   3. Create `foo.txt` containing `xxx`.
   4. Stage it with `git add foo.txt`.
   5. Commit it with `git commit -m "Add foo."`.
   6. Create and switch to a new branch with `git switch -c feature-test`.
3. In the second directory, initialize a bare remote repository with `git init
   --bare`.
4. In the first directory, add the second repository as the `origin` remote
   using `git remote add origin <path-to-second-directory>`.
5. Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` and verify
   that it fails because no upstream is configured.
6. Run `git-hints --all`. Verify that the hint with ID `no-upstream-branch`
   appears and recommends `git push -u origin feature-test`.
7. Run `git push -u origin feature-test` to push the branch and configure its
   upstream.
8. Run `git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}"` and
   verify that it returns `origin/feature-test`.
9. Run `git-hints --all` and verify that the hint with ID `no-upstream-branch`
   is absent.

#### Review staged changes before committing? **sbe80**

* Hint: Would you like to review your
  [staged changes](https://git-scm.com/docs/git-diff "Show changes staged for the next commit")
  before committing? Use
  [git commit](https://git-scm.com/docs/git-commit "Record the staged changes in a new commit")
  when they are ready.

* Git stage: You have changes in the staging area that will be included in the
  next commit. Unstaged edits remain in the working directory and will not be
  included.

* Command: Run `git diff --cached` to review the staged changes. When they are
  ready, run `git commit -m "message"` to create a commit containing those
  staged changes.

* ID: `staged-changes`, priority class: workflow, safety: safe.

* Conditions: Display this hint when the staging area contains at least one
  change to be committed. Run `git diff --cached --quiet`; exit code 1 means
  staged changes exist, exit code 0 means none exist, and any other exit code
  indicates an error. Do not display the hint when the staging area is empty.
  This includes staged files in a repository with no commits yet. Do not display
  this hint while the index contains unresolved merge entries; check with `git
  diff --name-only --diff-filter=U`. Also suppress it while a rebase is in
  progress, using the `rebase-merge` and `rebase-apply` path checks defined by
  `detached-head`. (drj228; sbe80 will test)

* Test case:

  1. The autouse `git_setup` fixture provides the isolated environment and
     create one temporary directory.
  2. Initialize a repository in that directory with `git init -b main`.
  3. Call `config_user("user1", "user1@example.com")`.
  4. Run `git-hints --all` and verify that the `staged-changes` hint is absent.
  5. Create `foo.txt` containing `xxx` and stage it with `git add foo.txt`.
  6. Run `git-hints --all` and verify that the `staged-changes` hint appears.
     Verify that it recommends `git diff --cached` and `git commit -m
     "message"`, and includes links to the official `git diff` and `git commit`
     documentation.
  7. Commit the file with `git commit -m "Add foo."` and run `git-hints --all`
     again. Verify that the `staged-changes` hint is absent.

10. Configure your commit identity? Conditions: Check the effective Git
    configuration by running `git config --get user.name` and `git config --get
    user.email`. An exit code of 1 or an empty returned value means that setting
    is missing; other nonzero exit codes are inspection errors and must not
    trigger this hint. Trigger the hint when either setting is missing or empty.
    Explain how to set the missing value using `git config --global user.name
    "Your Name"` or `git config --global user.email "you@example.com"`.

    The `--global` option sets the default for all repositories belonging to the
    current user. Use `--local` inside a repository to configure an identity for
    that repository only. Local settings override global settings. An empty
    local override should be corrected locally. These settings identify commit
    authors; they do not sign the user into GitHub. (drj228)

<mark>Review section 4 (raf322) begins here; see Review assignments.</mark>

#### Stage or ignore untracked files (ams2083)

* Hint: Do you need to
  [stage](https://git-scm.com/docs/git-add "Add files to the staging area") or
  [ignore](https://git-scm.com/docs/gitignore "Specify intentionally untracked files that Git should ignore")
  untracked files?

  * Git stage: Your working directory contains files that Git is not currently
    tracking. Ordinary project files should be staged if you want to include
    them in a future commit. Files containing secrets, temporary files, caches,
    and generated build outputs should generally be ignored.

  * Command: Run `git status --porcelain=v1` to identify untracked files,
    indicated by lines beginning with `??`. Use `git add <filename>` to stage
    files you want to track, or add appropriate patterns to `.gitignore` for
    files that should remain untracked. Run `git status` afterward to verify the
    changes.

  * ID: `untracked-files`, priority class: workflow, safety: safe.

  * Conditions: One or more untracked files exist in the working directory. Run
    `git status --porcelain=v1` and check for lines beginning with `??`. If
    ordinary untracked files exist, suggest staging them with `git add
    <filename>`. If files commonly excluded from version control are detected,
    such as `.env`, `__pycache__/`, `*.pyc`, or generated build outputs, suggest
    adding appropriate patterns to `.gitignore`. Display the hint when at least
    one untracked file or directory exists. Do not display the hint when no
    untracked files remain.

  * Test case:

    1. The autouse `git_setup` fixture provides the isolated environment. Create
       one temporary directory.
    2. In the temporary directory, initialize a repository with `git init -b
       main`.
    3. Call `config_user("user1", "user1@foo.com")`.
    4. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
       commit it with `git commit -m "Add foo."`.
    5. Check the ordinary untracked file state:
       1. Create `notes.txt` containing `Hello world` without staging it.
       2. Run `git status --porcelain=v1` and verify that `?? notes.txt`
          appears.
       3. Run `git-hints --all`.
       4. Verify that the hint with ID `untracked-files` appears and recommends
          `git add notes.txt`.
       5. Verify that the hint includes the appropriate official Git
          documentation links.
    6. Check the staged file state:
       1. Run `git add notes.txt` to stage the untracked file.
       2. Run `git status --porcelain=v1` and verify that `notes.txt` is now
          staged rather than untracked.
       3. Run `git-hints --all`.
       4. Verify that the hint with ID `untracked-files` is absent because no
          untracked files remain.
    7. Check the untracked file that should be ignored:
       1. Create a file named `.env` containing `TEST_VARIABLE=example`.
       2. Create a directory named `__pycache__` containing a file called
          `example.pyc`.
       3. Run `git status --porcelain=v1` and verify that `.env` and
          `__pycache__/` appear as untracked.
       4. Run `git-hints --all`.
       5. Verify that the hint with ID `untracked-files` appears.
       6. Verify that the hint recommends adding appropriate patterns to
          `.gitignore` instead of staging these files. Check the corresponding
          official Git documentation links.
    8. Check the ignored file state:
       1. Create a `.gitignore` file containing patterns for `.env`,
          `__pycache__/`, and `*.pyc`.
       2. Stage `.gitignore` with `git add .gitignore`.
       3. Run `git status --porcelain` and verify that `.env` and `__pycache__/`
          no longer appear as untracked.
       4. Run `git-hints --all`.
       5. Verify that the hint with ID `untracked-files` is absent because all
          remaining files are either tracked or ignored.
       6. Run `git-hints --all`.
       7. Verify that the hint with ID `untracked-files` is absent because no
          untracked files remain.

#### Review and commit widespread changes? (jit45)

* Hint: More than half of the tracked files in this repository have changes.
  Would you like to review the changes and
  [commit](https://git-scm.com/docs/git-commit "Records staged changes as a new commit in the local repository")
  the work you want to save?

* Git stage: Changes may exist in the working directory, staging area, or both.
  A commit records staged changes in the local repository; unstaged edits are
  not included unless they are staged first.

* Command: Run `git status` to review changed files and `git diff HEAD` to
  inspect the changes relative to the last commit. Run `git add <files>` to
  stage the changes you want to save, then `git diff --cached` to review what
  will be committed. When ready, run `git commit -m "Describe your changes"`;
  afterward, Git creates a new local commit containing the staged changes.
  Verify the result with `git status`.

* ID: `many-changed-files`, priority class: workflow, safety: safe.

* Conditions: Display this hint only when more than 50% of files tracked in HEAD
  have staged, unstaged, or deleted changes relative to HEAD. The repository
  must have at least one commit and at least one tracked file in HEAD.

Run `git rev-parse --verify HEAD` to verify that HEAD resolves to a commit. If
HEAD does not resolve, do not trigger this hint.

Run `git ls-tree -r --name-only -z HEAD` to enumerate files tracked in HEAD. Let
T be the number of distinct paths returned.

Run `git diff HEAD --name-only --no-renames -z` to identify paths changed
relative to HEAD, including staged and unstaged modifications and deletions.
Count only distinct changed paths that belong to the original tracked-file set.
Let C be this count. Newly added files and untracked files do not increase C or
T. Disabling rename detection treats a renamed file's original path as changed
while avoiding double-counting the destination.

Trigger the hint exactly when T > 0 and 2\*C > T. At exactly 50%, do not trigger
it. A tracked file changed in both the index and working directory counts once.
Unexpected Git command failures must be reported separately rather than
interpreted as a triggered hint.

* Test case: Commit repo? (written by jit45; formerly Test Case 12).

  1. The autouse `git_setup` fixture provides the isolated environment and
     create one temporary directory using `make_temps(tmp_path_factory, 1)`.
  2. Initialize a repository there with `git init -b main`.
  3. Call `config_user("user1", "user1@example.com")`.
  4. Create four files, `one.txt`, `two.txt`, `three.txt`, and `four.txt`, each
     containing initial text.
  5. Run `git add one.txt two.txt three.txt four.txt` and `git commit -m "Add
     initial files."`.
  6. Run `git-hints --ids-only`. Verify `many-changed-files` is absent because
     no tracked files have changed.
  7. Modify `one.txt` and `two.txt` without staging them. Create `untracked.txt`
     without adding it.
  8. Run `git status --porcelain` and confirm that exactly two of the four
     tracked files have changes and that `untracked.txt` is untracked.
  9. Run `git-hints --ids-only`. Verify `many-changed-files` is absent: C = 2
     and T = 4, so the percentage is exactly 50%. The untracked file must not
     count.
  10. Modify `three.txt` without staging it. Confirm that three of the four
      tracked files now have changes.
  11. Run `git-hints --all`. Verify that `many-changed-files` appears because
      C = 3 and T = 4 (75%). Verify its workflow priority and that it includes
      the Git stage, commands, expected results, and official documentation
      link.
  12. Stage `one.txt` with `git add one.txt`. Run `git-hints --ids-only` and
      verify the hint remains present; staging the file does not count it a
      second time.
  13. Run `git add one.txt two.txt three.txt` and `git commit -m "Save tracked
      changes."`.
  14. Run `git-hints --ids-only`. Verify that `many-changed-files` is absent
      because the changes are now committed. `untracked.txt` remains untracked
      and must not trigger this hint.
  15. Verify that the test uses the isolated Git environment and runs the CLI
      from inside the temporary repository.
  16. Test tracked-file deletions. Create a fresh, isolated temporary repository
      using make\_temps(1) and initialize it with git init -b main. Configure
      the test Git user, create four files, stage them, and commit them. Delete
      three of the four tracked files without staging the deletions. Run
      git-hints --ids-only and verify that many-changed-files appears because
      C = 3 and T = 4 (75%). Verify that each deleted tracked file counts
      exactly once. Run all commands inside the isolated temporary repository.
  17. Test a repository without commits. Initialize a separate empty repository
      with `git init -b main`, create and stage a new file, and run `git-hints
      --ids-only`. Verify that `many-changed-files` is absent because HEAD does
      not resolve to a commit. The tool must not treat this condition as an
      unexpected application failure.

<mark>Review section 5 (jhg246) begins here; see Review assignments.</mark>

#### Detached HEAD state (jit45; revised by drj228)

* Hint: You are in
  [detached HEAD](https://git-scm.com/docs/git-switch "Switch branches or create a branch at the current commit").
  Create a branch if you want to keep working here and give your commits a
  branch name.

* Git stage: You are working in the local repository at a specific commit
  instead of on a named local branch.

* Command: `git switch -c <name>`; replace `<name>` with an unused branch name.
  Expected result: Git creates a branch at the current commit and switches to
  it, so any subsequent commits belong to that branch. This also gives commits
  already made at the current detached HEAD a branch name.

* ID: `detached-head`, priority class: informational, safety: safe.

* Conditions:

  1. Confirm that the current directory is inside a Git working tree using `git
     rev-parse --is-inside-work-tree`; require exit code 0 and output `true`.
     Handle a directory outside a working tree through the existing `not-a-repo`
     behavior. Report unexpected Git errors separately.
  2. Run `git symbolic-ref --quiet --short HEAD`. Exit code 0 means HEAD is
     attached to a branch, including a branch without its first commit; do not
     display `detached-head`. Exit code 1 means HEAD is not symbolic; continue
     the checks. Other exit codes indicate errors, not this hint.
  3. Require `git rev-parse --verify --quiet "HEAD^{commit}"` to succeed before
     treating the nonsymbolic HEAD as a usable detached commit. Report an
     invalid or unreadable HEAD separately.
  4. Obtain the operation-state paths with `git rev-parse --git-path
     rebase-merge`, `git rev-parse --git-path rebase-apply`, and `git rev-parse
     --git-path BISECT_START`. Resolve relative paths against the working
     directory used for these Git commands. Suppress this hint if any of the
     returned paths exists. If a path lookup fails, report the inspection error
     rather than assuming no operation is in progress.
  5. Display `detached-head` only when HEAD is detached at a valid commit and
     neither a rebase nor a bisect is in progress.
* Related output: In normal output and `--all`, the repository context line must
  show `detached HEAD`, even when this hint is suppressed during an operation.
  The context line is not a hint. The existing `no-upstream-branch` hint must
  remain absent while HEAD is detached.

* Test case 10: Detached HEAD state (written and revised by drj228).

  All commands run in the repository under test unless a different directory is
  specified. Use the isolated environment from the autouse `git_setup()` fixture
  and the command-list behavior defined by `make_repo()`.

  1. Create two temporary directories with `make_temps(tmp_path_factory, 2)`:
     `local` and `remote`. Call `config_user("user1", "user1@example.com")`
     before initializing the repositories.
  2. In `remote`, run `git init --bare -b main`. In `local`, run `git init -b
     main` and `git remote add origin <absolute-path-to-remote>`. No fetch or
     push is needed for this test.
  3. In `local`, create `foo.txt` containing `xxx`, stage it with `git add
     foo.txt`, and commit it with `git commit -m "Add foo."`. Change the content
     to `xxxy` and commit with `git commit -am "Append y."`. Change it to
     `xxxyz` and commit with `git commit -am "Append z."`. The history now has
     three linear commits.
  4. Precondition: `git symbolic-ref --quiet --short HEAD` exits 0 and prints
     `main`. Run `git-hints --all`; require exit code 0 and the first output
     line exactly equal to `Branch: main`. Run `git-hints --all --ids-only` and
     verify that `detached-head` is absent. Verify that `no-upstream-branch` is
     present, establishing that this related hint can trigger before detaching
     HEAD.
  5. Run `git switch --detach HEAD`.
  6. Preconditions: `git symbolic-ref --quiet --short HEAD` exits 1, and `git
     rev-parse --verify --quiet "HEAD^{commit}"` exits 0. Obtain the three
     operation-state paths specified in Conditions and verify that none exists.
  7. Run `git-hints --all` and require exit code 0. Check the output block for
     ID `detached-head`: it contains `git switch -c` and the documentation URL
     `https://git-scm.com/docs/git-switch`. Verify that the first output line is
     exactly `Branch: detached HEAD`. Run `git-hints --all --ids-only`; verify
     that `detached-head` is present and `no-upstream-branch` and `no-commits`
     are absent. Identify hints by exact ID, without requiring their descriptive
     wording to match.
  8. Run `git switch -c saved-work`. Precondition: `git symbolic-ref --quiet
     --short HEAD` exits 0 and prints `saved-work`. Run `git-hints --all
     --ids-only` and verify that `detached-head` is absent.
  9. Run `git bisect start HEAD HEAD~2`. Preconditions: `git symbolic-ref
     --quiet --short HEAD` exits 1 and the path returned by `git rev-parse
     --git-path BISECT_START` exists.
  10. During the bisect, run `git-hints --all` and require exit code 0 and the
      first output line exactly equal to `Branch: detached HEAD`. Run `git-hints
      --all --ids-only`; verify that `detached-head` and `no-upstream-branch`
      are absent. Ensure `git bisect reset` runs in cleanup even if an assertion
      fails.
  11. Precondition after cleanup: `git symbolic-ref --quiet --short HEAD` exits
      0 and prints `saved-work`; the `BISECT_START` path no longer exists.
  12. Precondition: `refs/heads/git-hints-test-missing` does not exist. Run `git
      rebase --exec "git rev-parse --verify refs/heads/git-hints-test-missing"
      HEAD~1`. Execute this command directly with `subprocess.run()` using an
      argument list, `shell=False`, and `check=False`, rather than through
      `make_repo()`. Capture its output and require a nonzero return code. The
      deliberately failing exec command must stop the rebase with a nonzero exit
      code, without a prompt. Preconditions after it stops: `git symbolic-ref
      --quiet --short HEAD` exits 1 and the path returned by `git rev-parse
      --git-path rebase-merge` exists.
  13. During the stopped rebase, run `git-hints --all` and require exit code 0
      and the first output line exactly equal to `Branch: detached HEAD`. Run
      `git-hints --all --ids-only`; verify that `detached-head` and
      `no-upstream-branch` are absent. Ensure `git rebase --abort` runs in
      cleanup even if an assertion fails.
  14. Precondition after cleanup: `git symbolic-ref --quiet --short HEAD` exits
      0 and prints `saved-work`; neither rebase-state path exists. Run `git
      switch --detach HEAD`, then `git-hints --all --ids-only` and verify that
      `detached-head` appears again. Finish with `git switch saved-work`.

#### Current branch has no commits yet (jit45; revised by drj228)

* Hint: Your current branch has no commits yet. Prepare the files you want to
  save, then create your first
  [commit](https://git-scm.com/docs/git-commit "Record staged changes as a new commit").

* Git stage: You are preparing the first saved snapshot on the current local
  branch; edits in the working directory must enter the staging area before a
  normal commit includes them, and other branches may already have history.

* Command:

  * If nothing is staged, show `git status` to review the working directory and
    explain that selected files can be staged using
    [git add](https://git-scm.com/docs/git-add "Add selected file contents to the staging area"):
    `git add <files to stage>`. Expected result: selected files are listed under
    "Changes to be committed" by `git status`. Do not show a `git commit`
    command until staged changes exist.
  * If changes are staged, show `git commit -m "Initial commit"`. Expected
    result on success: Git creates the first commit on the current branch from
    the staged changes. Commit identity must be configured; the separate
    commit-identity configuration hint handles missing settings. Do not
    automatically stage or commit files.
* ID: `no-commits`, priority class: informational, safety: safe.

* Conditions:

  1. Confirm a Git working tree with `git rev-parse --is-inside-work-tree`;
     require exit code 0 and output `true`. Do not run the remaining checks
     outside a working tree. Report unexpected Git errors separately.
  2. Run `git rev-parse --verify --quiet HEAD`. Exit code 0 means HEAD resolves
     and this hint is absent. Exit code 1 means HEAD did not resolve; continue
     the checks rather than assuming the branch is empty. Other exit codes
     indicate errors.
  3. Confirm an unborn local branch: `git symbolic-ref --quiet HEAD` must exit 0
     and return a reference under `refs/heads/`. Then run `git show-ref --verify
     --quiet <returned-full-branch-reference>`. Exit code 1 confirms that the
     branch reference does not exist yet. A nonsymbolic HEAD, an existing branch
     reference with unresolved HEAD, or an unexpected command error must not be
     classified as `no-commits`; report invalid or unreadable repository state
     separately.
  4. Run `git diff --cached --quiet`. Exit code 1 means staged changes exist, so
     include the initial-commit command. Exit code 0 means none exist, so
     include status and staging guidance without a commit command. Other exit
     codes are inspection errors, not evidence of staged changes.
* Related output: An unborn branch is attached to its branch name, so
  `detached-head` must remain absent and normal repository context must show
  that name. The existing `many-changed-files` condition requires a commit at
  HEAD; it must remain absent before the first commit, with or without staged
  files. An empty file count must not cause division by zero.

* Test case 11: Repository has no commits (written and revised by drj228).

  All commands run in the repository under test. Use the isolated environment
  from the autouse `git_setup()` fixture and the command-list behavior defined
  by `make_repo()`.

  1. Create one temporary directory with `make_temps(tmp_path_factory, 1)`. Call
     `config_user("user1", "user1@example.com")`, then initialize the repository
     with `git init -b main`.
  2. Preconditions: `git rev-parse --verify --quiet HEAD` exits 1 with empty
     standard output and standard error; `git symbolic-ref --quiet --short HEAD`
     exits 0 and prints `main`; `git show-ref --verify --quiet refs/heads/main`
     exits 1; `git diff --cached --quiet` exits 0.
  3. Run `git-hints --all`. Require exit code 0, the first output line exactly
     equal to `Branch: main`, and no crash. Verify that the `no-commits` output
     block contains `git status`, `git add`, and
     `https://git-scm.com/docs/git-add`. Verify that this block does not contain
     `git commit`.
  4. Run `git-hints --all --ids-only`. Verify that `no-commits` is present and
     `detached-head`, `many-changed-files`, and `staged-changes` are absent.
  5. Create `foo.txt` containing `xxx` without staging it. Run `git-hints --all`
     and require exit code 0 and the first output line exactly equal to `Branch:
     main`. Verify that the `no-commits` output block is present and does not
     contain `git commit`. Run `git-hints --all --ids-only`; verify that
     `no-commits` is present and `detached-head`, `many-changed-files`, and
     `staged-changes` are absent.
  6. Run `git add foo.txt`. Precondition: `git diff --cached --quiet` exits 1,
     while `git rev-parse --verify --quiet HEAD` still exits 1.
  7. Run `git-hints --all` and require exit code 0. In the `no-commits` output
     block, check for `git commit -m "Initial commit"` and
     `https://git-scm.com/docs/git-commit`. Run `git-hints --all --ids-only`;
     verify that `no-commits` and `staged-changes` are present, while
     `detached-head` and `many-changed-files` are absent.
  8. Run `git commit -m "Initial commit"` and require exit code 0.
  9. Preconditions: `git rev-parse --verify --quiet HEAD` exits 0 and prints a
     commit object ID; `git symbolic-ref --quiet --short HEAD` exits 0 and
     prints `main`; `git diff --cached --quiet` exits 0.
  10. Run `git-hints --all` and require exit code 0 and the first output line
      exactly equal to `Branch: main`. Run `git-hints --all --ids-only`; verify
      that `no-commits`, `detached-head`, `many-changed-files`, and
      `staged-changes` are absent.
  11. Run `git switch --orphan fresh`. Preconditions: `git symbolic-ref --quiet
      --short HEAD` exits 0 and prints `fresh`; `git rev-parse --verify --quiet
      HEAD` exits 1; `git show-ref --verify --quiet refs/heads/fresh` exits 1;
      `git show-ref --verify --quiet refs/heads/main` exits 0; and `git diff
      --cached --quiet` exits 0.
  12. Run `git-hints --all` and require exit code 0 and the first output line
      exactly equal to `Branch: fresh`. Verify that the `no-commits` output
      block contains `git status` and `git add`, and does not contain `git
      commit`. Run `git-hints --all --ids-only`; verify that `no-commits` is
      present and `detached-head`, `many-changed-files`, and `staged-changes`
      are absent. Ensure `git switch main` runs in cleanup even if an assertion
      fails.

15. Committing to protected/main branch? Run `git branch --show-current` to
    identify the current branch. Trigger this hint when the branch is `main` or
    `master` and there are changes. Check for other local or remote branches
    with `git for-each-ref --format='%(refname:short)' refs/heads refs/remotes`.
    If other branches exist, suggest switching to one of them. If no other
    branches exist, suggest creating one with `git switch -c <name>`. (raf322)

<mark>Review section 6 (drj228) begins here; see Review assignments.</mark>

### `git-hints explain -- git <command> [<args>...]`

Reactive hints are triggered by the result of a Git command executed through
`git-hints explain`. (jit45)

### Resolve merge conflicts? **sbe80**

* Hint: Git left
  [merge conflicts](https://git-scm.com/docs/git-merge "Join two or more development histories together")
  that need to be resolved before the merge can finish. Conflicted files:
  `<files>`.

* Git stage: The merge is in progress in the working directory; edit each
  conflicted file to choose or combine the changes, then stage the resolved
  files.

* Command: Run `git diff --name-only --diff-filter=U` to list the conflicted
  files. Edit each file to resolve its conflict markers, then run `git add
  <file>` for each resolved file and `git status` to confirm no conflicts
  remain. Complete the merge with `git commit` when Git requests a merge commit.

* ID: `merge-conflicts`, priority class: error/blocked, safety: safe.

* Conditions: A Git command executed through `git-hints explain` leaves the
  repository with one or more unresolved merge conflicts. Detect them with `git
  diff --name-only --diff-filter=U`; include the returned paths in the hint. Do
  not display this hint when the command failed without leaving unresolved
  conflicts.

* Test case: Resolving merge conflicts (written by sbe80).

  1. The autouse `git_setup` fixture provides the isolated environment and
     create two temporary directories, `repo1` and `repo2`.
  2. In `repo1`, initialize a repository with `git init -b main` and call
     `config_user("user1", "user1@foo.com")`.
  3. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
     commit it with `git commit -m "Add foo."`.
  4. Clone `repo1` into `repo2` with `git clone <repo1> <repo2>`.
  5. In `repo1`, append `y` to `foo.txt`, stage it with `git add foo.txt`, and
     commit it with `git commit -m "Append y."`.
  6. In `repo2`, call `config_user("user2", "user2@foo.com")`. Append `z` to
     `foo.txt`, stage it with `git add foo.txt`, and commit it with `git commit
     -m "Append z."`.
  7. In `repo2`, run `git-hints explain -- git pull --no-rebase` and capture its
     exit code and output.
  8. Verify that the Git command exits non-zero and leaves an unresolved merge
     conflict. Verify with `git diff --name-only --diff-filter=U` that `foo.txt`
     is conflicted.
  9. Verify that the hint with ID `merge-conflicts` appears, names `foo.txt`,
     has error/blocked priority, explains how to resolve the conflict, and links
     to official merge documentation such as
     `https://git-scm.com/docs/git-merge`.

#### Preserve local changes before pulling? (jit45)

* Hint: The attempted
  [git pull](https://git-scm.com/docs/git-pull "Fetches and integrates changes from another repository")
  was blocked because incoming changes would overwrite uncommitted local
  changes. Affected files: `<files>`. Preserve your local work before retrying
  the pull.

* Git stage: Your working directory or staging area contains uncommitted
  changes, while the remote branch contains changes Git needs to integrate into
  the local repository. Git stopped the pull to avoid overwriting local work.

* Command: Run `git status` to inspect the repository and `git diff` to review
  unstaged changes. Run `git diff --cached` to review staged changes. To
  preserve the work as a commit, stage only the files you intend to save using
  `git add <files>`, then run `git commit -m "Save local changes"`. After
  verifying that the changes are committed, retry `git pull`. If the pull later
  produces merge conflicts, resolve those conflicts separately before completing
  the integration.

```
As an alternative when a commit is not appropriate, review the changes and run `git stash push -m "Save work before pull"` to save tracked working-directory and index changes temporarily. Verify the stash using `git stash list`, then retry `git pull`. After a successful pull, run `git stash apply` to reapply the saved changes. Resolve any conflicts before continuing. Keep the stash until you have verified that all desired changes were successfully restored. Warning: `git stash drop` is not part of the recommended workflow because it removes the selected stash entry and may permanently discard changes that are not saved elsewhere. Keep the stash until all desired changes have been verified and preserved. Back up the work before considering any stash deletion. Untracked files are not saved by the default stash command.

The commands do not guarantee a conflict-free pull; they preserve the user's work before another integration attempt. Do not suggest `git reset --hard`, `git clean`, or force pushing as a remedy.
```

* ID: `pull-blocked-local-changes`, priority class: error/blocked, safety: safe.

* Conditions: Trigger only for a Git pull command executed through `git-hints
  explain -- git pull` (including supported pull arguments) that fails because
  incoming changes would overwrite uncommitted modifications to tracked files.

Execute the requested Git command using the shared `git-hints explain` execution
rules. Inspect its exit code and captured standard error. Require a nonzero exit
code and a recognized Git diagnostic indicating that local changes would be
overwritten during merge or checkout. The message may vary by Git version, so do
not rely on one complete error string.

Extract affected file paths from the diagnostic's file list when available.
Display those paths in the hint. Do not invent filenames. If affected paths
cannot be identified reliably, explain the problem without listing specific
files and recommend `git status` to inspect the changes.

Do not trigger this hint for a successful pull, a network or authentication
failure, an unrelated Git error, or an actual unresolved merge conflict. If
unresolved merge entries exist, the `merge-conflicts` hint handles that separate
state.

This hint must not discard, stage, commit, or stash the user's changes
automatically. The failed pull's actual exit code must be preserved by
`git-hints explain`. Unexpected inspection failures must be reported separately.

* Test case: Resolve pull conflicts (written by jit45; formerly Test Case 13).

  1. The autouse `git_setup` fixture provides the isolated environment and
     create three temporary directories named `remote`, `local`, and `other`
     using `make_temps(tmp_path_factory, 3)`.
  2. In `remote`, run `git init --bare -b main`.
  3. Clone `remote` into `other` using `git clone <remote> <other>`.
  4. In `other`, call `config_user("user1", "user1@example.com")`.
  5. Create `foo.txt` containing `xxx`, then run `git add foo.txt`, `git commit
     -m "Add foo."`, and `git push -u origin main`.
  6. Clone `remote` into `local` using `git clone <remote> <local>`.
  7. In `local`, append `local change` to `foo.txt` without staging or
     committing it. Save the file's current contents for comparison after the
     pull attempt.
  8. In `other`, append `remote change` to `foo.txt`, run `git commit -am
     "Update foo remotely."`, then run `git push`.
  9. In `local`, run `git status --porcelain` and verify that `foo.txt` has an
     unstaged local modification.
  10. In `local`, run `git-hints explain -- git pull` and capture the exit code
      and output.
  11. Verify that the pull fails with a nonzero exit code because the incoming
      change would overwrite the uncommitted local modification. Verify that
      `git-hints explain` returns the Git command's nonzero exit code.
  12. Verify that the hint with ID `pull-blocked-local-changes` appears, names
      `foo.txt`, and has error/blocked priority.
  13. Verify that the hint explains the working-directory or staging-area state,
      provides commands and expected results for preserving the local change,
      and includes the official `git pull` documentation link.
  14. Verify that `foo.txt` still contains the user's original uncommitted local
      change after the failed pull and that the tool did not automatically
      stage, commit, stash, or discard it.
  15. Verify with `git diff --name-only --diff-filter=U` that no unresolved
      merge entries remain from this blocked pull.
  16. As a negative check, save the local modification outside the repository,
      then restore `foo.txt` to its committed version using `git restore
      foo.txt`. Run `git-hints explain -- git pull` again. Verify that the pull
      succeeds with exit code 0, that `pull-blocked-local-changes` is absent
      from the output, and that the remote change is present in `foo.txt`.
      Verify that the previously saved local modification remains available
      outside the repository.
  17. Verify that all commands and CLI calls use the isolated test environment
      and are executed from the correct temporary repository.

3. Push failed? Conditions: `git-hints explain -- git push` fails because the
   remote branch contains commits that are not present in the local branch.
   Explain that the user should integrate the remote changes before attempting
   to push again. (jhg246)

#### Stash local changes? (sbe80)

* Hint: The attempted operation was blocked because it would overwrite tracked
  local changes. Explain that a stash temporarily saves tracked changes in the
  working tree and index so the operation can be retried.

* Git stage: The working tree or index contains tracked changes, and a `git
  merge` or `git switch` was blocked before it changed the repository state.

* Command: Show `git status` so the user can review their changes, then suggest
  `git stash push -m "Save work before retrying"` followed by the original Git
  command. After it succeeds, suggest `git stash apply` and `git stash list` so
  the user can restore and verify the saved work without deleting the stash.
  Explain that the default stash does not include untracked files; the user
  should save any needed untracked files separately. Expected result: the
  blocked operation can proceed while the tracked changes remain saved for
  restoration.

* ID: `stash-local-changes`, priority class: error/blocked, safety: safe.

* Conditions: Trigger when a `git merge` or `git switch` command executed
  through `git-hints explain` fails because tracked local changes would be
  overwritten, and no unmerged paths have been created. Do not trigger for a
  failed `git pull`; the pull-specific hint covers that case. Do not trigger
  when the command fails for another reason.

* Test case: Stashing changes that block a merge (written by sbe80).

  1. The autouse `git_setup` fixture provides the isolated environment and
     create a temporary directory named `repo`.
  2. In `repo`, run `git init -b main` and call `config_user("user1",
     "user1@foo.com")`.
  3. Create `foo.txt` containing `base`, stage it, and commit it with `git
     commit -m "Add foo."`.
  4. Create a branch named `topic` with `git switch -c topic`, replace the
     contents of `foo.txt` with `topic change`, and commit the change.
  5. Switch back to `main` and replace the contents of `foo.txt` with `local
     change`, leaving the file uncommitted.
  6. Run `git-hints explain -- git merge topic` and capture its exit code and
     output.
  7. Verify that the merge fails with a nonzero exit code because it would
     overwrite the tracked local change, and that `git-hints explain` returns
     the Git command's nonzero exit code.
  8. Verify that `foo.txt` still contains `local change`, no unmerged paths
     exist, and the hint with ID `stash-local-changes` appears with
     error/blocked priority. Verify that the hint explains how to stash, retry
     the merge, and restore the saved changes, and notes that default stashes do
     not include untracked files.
  9. Run `git restore foo.txt` and then `git-hints explain -- git merge topic`
     again. Verify that the merge succeeds and the `stash-local-changes` hint is
     absent.

<mark>Review section 4 (raf322) continues here; see Review assignments.</mark>

#### Suggest `git pull --rebase`? (sbe80)

* Hint: Five repeated failures to pull or push may be resolved by replaying the
  local commits on top of the upstream branch. Explain that rebase changes the
  local commit IDs, may cause conflicts, and should only be attempted after the
  user has verified that their local work is committed or otherwise backed up.

* Git stage: The local branch and its upstream branch have diverged, or a push
  has been rejected because the upstream branch contains commits missing from
  the local branch.

* Command: `Caution: git pull --rebase`. Explain that it fetches the upstream
  changes and replays local commits on top of them, producing a linear history.
  If conflicts occur, explain how to resolve them and continue with `git rebase
  --continue`, or abandon the operation with `git rebase --abort`. Expected
  result: the local branch contains the upstream commits followed by the
  replayed local commits and can be pushed if no other errors remain. Link to
  the official [`git pull` documentation](https://git-scm.com/docs/git-pull) and
  [`git rebase` documentation](https://git-scm.com/docs/git-rebase).

* ID: `rebase-after-repeated-integration-failures`, priority class: data-loss
  risk, safety: caution.

* Conditions: Count consecutive failed `git pull` or `git push` commands
  executed through `git-hints explain` for the current repository and branch.
  Show this hint after five failures. A successful pull or push, or any
  intervening command executed through `git-hints explain`, resets the count.
  Reset the count after showing the hint so it is not repeated on every
  subsequent failure.

* Test case: Suggesting rebase after repeated failures (written by sbe80).

  1. The autouse `git_setup` fixture provides the isolated environment and
     create three temporary directories named `remote`, `local`, and `other`
     using `make_temps(tmp_path_factory, 3)`.
  2. In `remote`, run `git init --bare -b main`. Clone it into `local` and call
     `config_user("user1", "user1@foo.com")` there.
  3. In `local`, create and commit `foo.txt`, then run `git push -u origin
     main`.
  4. Clone `remote` into `other` and call `config_user("user2",
     "user2@foo.com")` there.
  5. In `local`, make and commit a local change to `foo.txt`. In `other`, make
     and commit a different change to `foo.txt`, then run `git push`. The local
     and upstream branches now have different commits.
  6. In `local`, run `git-hints explain -- git push` four times. Capture each
     exit code and output; verify that each push fails and the hint with ID
     `rebase-after-repeated-integration-failures` is absent.
  7. Run `git-hints explain -- git push` a fifth time. Verify that it fails and
     the hint appears with data-loss risk priority. Verify that the hint
     includes the `Caution:` command, explains rebase conflicts and backing up
     local work, and links to the official `git pull` and `git rebase`
     documentation.
  8. Run `git-hints explain -- git push` once more. Verify that it fails without
     showing the hint, confirming that the count was reset after the hint
     appeared.
  9. In `local`, run `git-hints explain -- git pull --rebase`. Verify that it
     succeeds, the local commit is replayed on top of the upstream commit, and
     no rebase is left in progress.
  10. Run `git-hints explain -- git push`. Verify that it succeeds and the
      rebase hint is absent.

#### Finish or cancel the operation in progress? (raf322)

* Hint: A `<operation>` is in progress. Git paused it and is waiting for you to
  finish or cancel it. The hint has two variants.

  * Conflicts remain: "Some files have conflicts. Open each conflicted file,
    choose the final content, then
    [stage](https://git-scm.com/docs/git-add "Marks a resolved file so Git knows the conflict is fixed")
    it. When no conflicts remain, run the continue command. To cancel instead,
    run the abort command."
  * No conflicts remain: "No conflicts remain. Run the continue command to
    finish, or the abort command to cancel."

  `<operation>` is replaced by `merge`, `rebase`, `cherry-pick`, or `revert`.
  Show only the commands and the documentation link
  (`https://git-scm.com/docs/git-<operation>`) for the detected operation.

* Git stage: You are working in the local repository: Git has paused an
  operation that combines commits, and any conflicted files stay in your working
  directory and staging area until you resolve them.

* Command: Run `git status` to see which files are unmerged. Resolve each one,
  run `git add <file>`, then run the continue command for the operation:

  | Operation   | Continue                     | Abort                     |
  | ----------- | ---------------------------- | ------------------------- |
  | merge       | `git merge --continue`       | `git merge --abort`       |
  | rebase      | `git rebase --continue`      | `git rebase --abort`      |
  | cherry-pick | `git cherry-pick --continue` | `git cherry-pick --abort` |
  | revert      | `git revert --continue`      | `git revert --abort`      |

  The CLI displays only the row for the detected operation. Expected result
  after continuing: Git resumes the operation. A merge, cherry-pick, or revert
  may record a new commit, and a completed rebase updates the branch. If another
  conflict occurs, Git pauses again and this hint remains active. Once the
  entire operation completes, this hint disappears and `git status` no longer
  reports an operation in progress.

  The continue command is safe. Prefix the abort command with `Warning:`
  aborting discards the conflict resolutions you have made so far and returns to
  the state before the operation began. Git may be unable to restore uncommitted
  changes that existed before a merge started, so back up any edited files
  first.

* ID: `operation-in-progress`, priority class: error/blocked, safety: warning.

* Conditions:

  1. Confirm a Git working tree with `git rev-parse --is-inside-work-tree`;
     require exit code 0 and output `true`. Do not run the remaining checks
     outside a working tree.

  2. Detect the operation. Check in the order below and report only the first
     match, so a rebase that stops on a conflict is not reported as a
     cherry-pick:

     1. Rebase: for each of `rebase-merge` and `rebase-apply`, run `git
        rev-parse --git-path <n>` and test whether that directory exists.
        Resolve relative paths against the working directory used for these Git
        commands. Ignore `rebase-apply` if it contains an `applying` file, since
        that is `git am`, which is not supported. If a path lookup fails, report
        the inspection error rather than assuming no operation is in progress.
     2. Merge: `git rev-parse --verify --quiet MERGE_HEAD`.
     3. Cherry-pick: `git rev-parse --verify --quiet CHERRY_PICK_HEAD`.
     4. Revert: `git rev-parse --verify --quiet REVERT_HEAD`.

     For the `rev-parse --verify` checks, exit code 0 means the operation is in
     progress, exit code 1 means it is not, and any other exit code is an
     inspection error. Use `--git-path` rather than hard-coding `.git/`, so the
     checks work in worktrees and when the Git directory is elsewhere.

  3. Detect unresolved files with `git diff --name-only --diff-filter=U`. If it
     lists paths, use the "conflicts remain" variant. List paths in the order
     Git returns them (sorted by path) and name up to five; if there are more,
     append "and N more", where N is the exact number not listed. If it lists
     none, use the "no conflicts remain" variant. A merge started with
     `--no-commit` has `MERGE_HEAD` and no conflicts; the hint still applies.

  4. Keep displaying the hint until the state file or directory is gone.

  5. Limitation: a multi-commit cherry-pick or revert that stops partway is
     detected only while `CHERRY_PICK_HEAD` or `REVERT_HEAD` exists.
* Related output: This proactive hint complements the reactive `merge-conflicts`
  hint, which appears only right after a failing command run through `git-hints
  explain`; this hint persists after the terminal is closed and reopened. During
  a rebase, HEAD is detached, so the context line shows `Branch: detached HEAD`
  and `detached-head` is suppressed (see `detached-head`).

* Test case: Operation in progress (written by raf322).

  All commands run in the repository under test. The autouse `git_setup` fixture
  provides the isolated environment, including `GIT_EDITOR=true`, so no command
  waits for an editor. Collapse whitespace in hint output before searching it
  for phrases.

  1. Call `make_temps(tmp_path_factory, 1)`. In the directory: run `git init -b
     main`; call `config_user("user1", "user1@foo.com")`; create `foo.txt`
     containing `base`; stage it and commit with the message `"Add foo."`.
  2. Run `git-hints --all --ids-only`. Verify that `operation-in-progress` is
     absent in a clean repository.
  3. Run `git switch -c topic`. Change `foo.txt` to `topic` and commit it with
     `git commit -am "Topic change."`.
  4. Run `git switch main`. Change `foo.txt` to `main` and commit it with `git
     commit -am "Main change."`.
  5. Merge conflict:
     1. Run `git merge topic`. Verify that it exits nonzero, that `git rev-parse
        --verify --quiet MERGE_HEAD` exits 0, and that `git diff --name-only
        --diff-filter=U` lists `foo.txt`. Ensure `git merge --abort` runs in
        cleanup if `MERGE_HEAD` still exists, even if an assertion fails.
     2. Run `git-hints --all` and require exit code 0 and the first output line
        exactly equal to `Branch: main`. Verify that the `operation-in-progress`
        block names a merge, lists `foo.txt`, contains `git add`, `git merge
        --continue`, `git merge --abort`, and `Warning:`, and links to
        `https://git-scm.com/docs/git-merge`. Verify that it does not include
        continuation or abort commands for other operations.
     3. Run `git-hints --all --ids-only`. Verify that `operation-in-progress` is
        present.
  6. Resolved but not yet continued:
     1. Change `foo.txt` to `resolved` and run `git add foo.txt`.
     2. Run `git-hints --all`. Verify that `operation-in-progress` is still
        present (`MERGE_HEAD` still exists), that its block contains the text
        `No conflicts remain` and `git merge --continue`, and that it does not
        list `foo.txt`.
  7. Continue: run `git merge --continue` and require exit code 0. Verify that
     `git rev-parse --verify --quiet MERGE_HEAD` exits 1. Run `git-hints --all
     --ids-only` and verify that `operation-in-progress` is absent.
  8. Abort path: run `git switch -c topic2`, change `foo.txt` to `topic2`, and
     commit. Run `git switch main`, change `foo.txt` to `main2`, and commit. Run
     `git merge topic2` (exits nonzero). Verify that `operation-in-progress` is
     present, then run `git merge --abort` and verify that it is absent.
  9. Rebase: run `git switch topic2`, then `git rebase main`.
     1. Verify that `git rebase main` exits nonzero and that `git rev-parse
        --git-path rebase-merge` names an existing directory. Ensure `git rebase
        --abort` runs in cleanup if a rebase is still in progress.
     2. Run `git-hints --all`. Verify that the `operation-in-progress` block
        names a rebase (not a cherry-pick), contains `git rebase --continue` and
        `git rebase --abort`, and links to
        `https://git-scm.com/docs/git-rebase`. Verify that it does not include
        continuation or abort commands for other operations.
     3. Verify that the first output line is exactly `Branch: detached HEAD` and
        that `detached-head` is absent from `git-hints --all --ids-only`.
     4. Change `foo.txt` to `resolved2`, run `git add foo.txt`, then run `git
        rebase --continue`. Require exit code 0. Run `git-hints --all
        --ids-only` and verify that `operation-in-progress` is absent.
  10. Cherry-pick:
      1. Run `git switch main`, then `git switch -c pick-src`. Change `foo.txt`
         to `pick` and commit with `git commit -am "Pick change."`.
      2. Run `git switch main`. Change `foo.txt` to `main3` and commit with `git
         commit -am "Main change 3."`.
      3. Run `git cherry-pick pick-src`. Verify that it exits nonzero and that
         `git rev-parse --verify --quiet CHERRY_PICK_HEAD` exits 0. Ensure `git
         cherry-pick --abort` runs in cleanup if it is still in progress.
      4. Run `git-hints --all`. Verify that the `operation-in-progress` block
         names a cherry-pick, contains `git cherry-pick --continue` and `git
         cherry-pick --abort`, and links to
         `https://git-scm.com/docs/git-cherry-pick`. Verify that it does not
         include continuation or abort commands for other operations.
      5. Run `git cherry-pick --abort`, then `git-hints --all --ids-only`;
         verify that `operation-in-progress` is absent.
  11. Revert:
      1. On `main`, change `foo.txt` to `main4` and commit with `git commit -am
         "Main change 4."`.
      2. Run `git revert HEAD~1`, which reverts "Main change 3." and conflicts
         with the later change. Verify that it exits nonzero and that `git
         rev-parse --verify --quiet REVERT_HEAD` exits 0. Ensure `git revert
         --abort` runs in cleanup if it is still in progress.
      3. Run `git-hints --all`. Verify that the `operation-in-progress` block
         names a revert, contains `git revert --continue` and `git revert
         --abort`, and links to `https://git-scm.com/docs/git-revert`. Verify
         that it does not include continuation or abort commands for other
         operations.
      4. Run `git revert --abort`, then `git-hints --all --ids-only`; verify
         that `operation-in-progress` is absent.

#### Stop tracking ignored files? (raf322)

* Hint: Do you want Git to stop tracking files that match active
  [ignore rules](https://git-scm.com/docs/gitignore "Lists patterns for files Git should not track; it only affects files that are not already tracked")?
  These rules may come from `.gitignore`, `.git/info/exclude`, or a global
  excludes file. Ignoring a file does not affect files Git already tracks. To
  stop tracking a file but keep it on your disk, use
  [`git rm --cached`](https://git-scm.com/docs/git-rm "With --cached, removes a file from the index but leaves it in your working directory").
  Anyone who pulls your commit will have the file deleted, and it remains in
  earlier commits, so change any password or key it contained.

* Git stage: These files are in Git's index and may also have been saved in
  previous commits, so Git tracks them even though active ignore rules match
  their paths.

* Command: For each file, run `git rm --cached <file>` (`git rm -r --cached
  <directory>` for directories). If a matching rule was newly added or modified
  in a project `.gitignore`, stage that file with `git add .gitignore`. Review
  the staged changes with `git diff --cached`, then run `git commit -m "Stop
  tracking <file>"`. Expected result: after `git rm --cached`, previously
  committed files show `deleted: <file>` under changes to be committed in `git
  status`, and the files remain in your working directory. After the commit, the
  selected files no longer appear in `git ls-files -ci --exclude-standard`.
  Other tracked files that match active ignore rules may still be listed; this
  hint disappears only when no matching tracked files remain.

* ID: `tracked-but-ignored`, priority class: workflow, safety: safe.

* Conditions: Do not run outside a working tree; confirm with `git rev-parse
  --is-inside-work-tree` (exit code 0, output `true`). Run `git ls-files -ci
  --exclude-standard -z`. Split the output on NUL characters, which keeps names
  containing spaces or newlines intact. In this command, `-c` lists files in the
  index and `-i` keeps only those matching an ignore pattern;
  `--exclude-standard` applies `.gitignore`, `.git/info/exclude`, and the global
  excludes file. Show the hint only when at least one path is returned. A
  nonzero exit code is an inspection error, not evidence of tracked-but-ignored
  files. List paths in the order `git ls-files` returns them (sorted by path)
  and name up to five, quoted correctly in the suggested command; if there are
  more, append "and N more", where N is the exact number not listed.

  A file added deliberately with `git add -f` also matches, so keep the wording
  conditional. A file re-included with a negation pattern such as `!debug.log`
  is not ignored and must not appear.

  Related output: `untracked-files` covers files Git is not tracking; this hint
  covers files Git is tracking. The two must never report the same file. After
  `git rm --cached`, a file is untracked and ignored, so neither hint reports
  it.

* Test case: Tracked but ignored (written by raf322).

  The autouse `git_setup` fixture provides the isolated environment. Collapse
  whitespace in hint output before searching it for phrases.

  1. Call `make_temps(tmp_path_factory, 1)`. In the directory: run `git init -b
     main`; call `config_user("user1", "user1@foo.com")`; create `foo.txt`
     containing `xxx`, `debug.log` containing `log`, and `my notes.log`
     containing `notes`. Stage all three and commit with `git commit -m "Add
     files."`.
  2. Preconditions: no `.gitignore` exists, and `git ls-files -ci
     --exclude-standard` prints nothing. Run `git-hints --all --ids-only` and
     verify that `tracked-but-ignored` is absent.
  3. Create `.gitignore` containing `*.log` and leave it unstaged. Precondition:
     `git ls-files -ci --exclude-standard` lists `debug.log` and `my notes.log`
     but not `foo.txt`.
  4. Run `git-hints --all` and require exit code 0. In the `tracked-but-ignored`
     block, verify that both `debug.log` and `my notes.log` appear (the second
     one quoted correctly in the command), that `foo.txt` does not appear, and
     that the block contains `git rm --cached`, `git add .gitignore`, `git diff
     --cached`, `git commit`, `earlier commits`,
     `https://git-scm.com/docs/git-rm`, and
     `https://git-scm.com/docs/gitignore`. Run `git-hints --all --ids-only`;
     verify that `tracked-but-ignored` is present.
  5. Run `git rm --cached debug.log "my notes.log"` and require exit code 0.
     Verify that both files still exist on disk. Run `git-hints --all
     --ids-only`; verify that `tracked-but-ignored` is absent, because the files
     are now untracked and ignored. Run `git add .gitignore` and `git diff
     --cached`; verify that the ignore rule and both file removals are staged.
     Run `git commit -m "Stop tracking log files."` and verify that the commit
     includes `.gitignore` and both removals, that the files still exist
     locally, and that `tracked-but-ignored` remains absent.
  6. Negation: change `.gitignore` to contain `*.log` and `!debug.log`. Run `git
     add debug.log`, then `git-hints --all --ids-only`; verify that
     `tracked-but-ignored` is absent, because `debug.log` is no longer ignored.
  7. Many files: change `.gitignore` to contain `build/`. Create `build/a.txt`
     through `build/g.txt` (seven files) and stage them with `git add -f build`.
     Run `git-hints --all`. Verify that the block lists `build/a.txt` through
     `build/e.txt`, does not list `build/f.txt` or `build/g.txt`, and contains
     `and 2 more`.
  8. Clean up: run `git rm -r --cached build`, then `git-hints --all
     --ids-only`; verify that `tracked-but-ignored` is absent.

<mark>Review section 7 (sbe80) begins here; see Review assignments.</mark>

### Language and libraries

1. Language: Python (Minimum version of 3.10 to ensure compatibility with all
   used libraries)

2. Package manager: uv

3. Formatter/linter: ruff

4. Type checker: ty

5. CLI: Typer

Git interface: Python's built-in `subprocess` module. Use it for both repository
inspection and execution of user-supplied Git commands, with different behavior
for each mode. The existing detection conditions use Git's own commands and exit
codes, so no additional Git library is required.

* Plain `git-hints`: run the inspection commands defined by the hint conditions
  and repository-context requirements. Capture standard output, standard error,
  and exit codes to determine which hints apply. Do not execute commands
  suggested by hints. Do not fetch unless `--fetch` is supplied; follow that
  option's environment and timeout requirements.

* `git-hints explain`: validate that the user-supplied argument list starts with
  `git` (only the word `git` is accepted. No other format), then execute it
  once. Leave standard input connected to the terminal. Leave Git's standard
  output connected to the terminal in normal output; under `--ids-only`, redirect
  Git's standard output to `subprocess.DEVNULL` so it is not displayed. Capture
  standard error and display it after completion (not live). In normal output,
  display the exit code; under `--ids-only`, omit the exit-code message. Always
  return Git's exit code. Use the command, exit code, standard error, and
  inspected repository state to select reactive hints.
  Do not disable Git's terminal prompting or editor for `git-hints explain`; the
  `GIT_TERMINAL_PROMPT=0` requirement applies only to the tool's optional fetch
  and isolated test environment. Do not claim to recover the result of an
  earlier command run outside `git-hints explain`.

<p><br></p>

When git-hints explain runs a command with repository-redirection options such
as -C, --git-dir, or --work-tree, skip reactive hints that require
repository-state inspection. Hints based only on the command’s exit code or
captured standard error may still be evaluated.

For both modes, pass arguments separately with `shell=False` and `check=False`.
Interpret `returncode` according to each command's documented meaning; expected
nonzero codes are not automatically application errors. Report unexpected
failures separately and suppress hints that depend the failed commands. If Git
ran, return Git's exit code. If Git cannot be launched, report that failure
instead of inventing a Git exit code or repository condition.

Plain `git-hints` exits 0 whenever inspection completes, whether or not any hint
is triggered. It exits nonzero only when it reports an unexpected inspection
failure or that Git cannot be launched. (drj228)

`git-hints explain` should also return non zero if Git does not launch or for any
unexpected inspection failures.

Decode Git output as UTF-8 (`encoding="utf-8", errors="replace"`), not with the
locale default. When a path list is parsed, use `-z` or `-c
core.quotePath=false`.

1. Testing: Pytest

2. Git: version 2.34 or later. This applies for both running the application and
   testing.

Testing
-------

The test tool contains:

* `make_temps(tmp_path_factory, num)`: creates and returns `num` temporary
  directories using Pytest's `tmp_path_factory`. Each test that calls this
  function must request `tmp_path_factory` from pytest and pass it to
  `make_temps`.The helper does not assign names such as local or remote; each
  test should assign descriptive variable names to the returned paths.
* `make_repo(temp_dir, commands)`: runs the list of `commands` in `temp_dir` to
  create and populate the repository. Each command is either an argument list,
  such as `["git", "commit", "-m", "Add foo."]`, executed using
  `subprocess.run(cwd=temp_dir, shell=False)`, or a zero argument lambda
  function used to create, modify, or delete files. Pass each argument
  separately and keep messages containing spaces in a single list element. Do
  not join arguments into a shell string. (drj228) File-operation lambdas must
  use paths rooted at `temp_dir`—for example, `temp_dir / "foo.txt"`—and must
  not rely on or change the process’s current working directory. `make_repo()`
  does not call `os.chdir`.
* `git_setup()`: creates an isolated Git configuration for the test environment.
  The test environment shall:
  * Remove every inherited environment variable whose name starts with `GIT_`,
    plus `EMAIL` and `XDG_CONFIG_HOME`. Git sets `GIT_DIR`, `GIT_WORK_TREE`, and
    `GIT_INDEX_FILE` when Pytest runs from a Git hook, which would make tests
    act on the outer repository. `GIT_AUTHOR_*`, `GIT_COMMITTER_*`, and `EMAIL`
    override `user.name` and `user.email`. `GIT_CONFIG_PARAMETERS` and
    `GIT_CONFIG_COUNT` add configuration that bypasses the files below.
  * Set `HOME` to an empty temporary directory. Git reads some files from the
    home directory even when `GIT_CONFIG_GLOBAL` is set, such as the global
    ignore file `~/.config/git/ignore`.
  * Set
    [`GIT_CONFIG_GLOBAL`](https://git-scm.com/docs/git-config#Documentation/git-config.txt-GITCONFIGGLOBAL)
    ([more docs](https://git-scm.com/docs/git#Documentation/git.txt-GITCONFIGGLOBAL))
    to a writable temporary file containing only `[init]\ndefaultBranch = main`,
    so that the user's global Git configuration does not affect test results.
  * Set
    [`GIT_CONFIG_NOSYSTEM=1`](https://git-scm.com/docs/git#Documentation/git.txt-GITCONFIGNOSYSTEM)
    so that the system Git configuration, such as Git for Windows'
    `core.autocrlf=true`, does not affect test results.
  * Set
    [`GIT_CEILING_DIRECTORIES`](https://git-scm.com/docs/git#Documentation/git.txt-GITCEILINGDIRECTORIES)
    to Pytest's base temporary directory (`tmp_path_factory.getbasetemp()`), so
    Git never finds a repository above a test's temporary directory.
  * Set
    [`GIT_TERMINAL_PROMPT=0`](https://git-scm.com/docs/git#Documentation/git.txt-GITTERMINALPROMPT)
    and
    [`GIT_EDITOR=true`](https://git-scm.com/docs/git#Documentation/git.txt-GITEDITOR),
    so no test waits for a password or an editor.
  * Set `LC_ALL=C`, so Git's messages are in English.
* `config_user(username, email)`: Set the isolated testing Git environment's
  global `user.name` and `user.email` by writing to the global
  `GIT_CONFIG_GLOBAL` file.

The function-scoped autouse `git_setup()` fixture applies the isolated variables
to os.environ for each test and restores the prior environment afterward. Tests
do not call the fixture directly. Create temporary directories
with `make_temps()`, and use `make_repo()` to set up repositories. Run
`git-hints --all` when checking hint content, commands, and documentation links.
Use `git-hints --all --ids-only` when checking whether a hint ID is present or
absent. Compare IDs as whole lines, not substrings. Both modes must run with the
repository under test as the current working directory: set `cwd` to the same
`temp_dir` passed to `make_repo()` for that repository.

All Git commands executed as part of a test, including those that `git-hints`
runs, shall use the isolated test environment established by `git_setup()`. This
prevents test results from varying based on the Git configuration of the machine
running the tests.

Repository setup commands must exit successfully; fail the test immediately if
one does not. Run any command that is expected to fail as part of the behavior
under test separately, and explicitly verify its expected exit code and output.