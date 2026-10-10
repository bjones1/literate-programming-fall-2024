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

CLI commands
------------

1. `git-hints`: inspect observable repository state and display up to three
   currently triggered proactive hints in priority order. If more than three
   hints are triggered, inform the user that additional hints are available.
   (jit45)

   1. `--all`: display every currently triggered proactive hint instead of
      applying the normal three-hint display limit. (jit45)

   2. `--exclude <hint-id1[,hint-id2[,...]]>`: exclude the list of `git-hints`
      ids from the generated hints. **Future work. Do not implement.**

   3. `--dismiss <hint-id1[,hint-id2[,...]]>`: dismiss one or more currently
      triggered hints. **Future work. Do not implement.**

      Save the hint ID and the values used to detect its condition in
      `git-hints/dismissals.json` inside the repository's Git directory.

      Exclude dismissed hints from normal output and `git-hints --all` while
      those values remain unchanged.

      Clear the dismissal when those values change or when the tool observes
      that the condition no longer exists. Show the hint again only if its
      condition applies. Unrelated repository changes do not clear a dismissal.

      For example, configuring a missing user name while the email is still
      missing allows the commit-identity hint to appear again.

      (ewj55; clarified by drj228, sbe80, and jit45)

   4. `--ids-only` outputs only the IDs of hints; typically used for testing.

   5. `--fetch`: run `git fetch` before inspecting the repository, with
      `GIT_TERMINAL_PROMPT=0` and a timeout, so that ahead/behind hints use
      current remote information. Without this option, never fetch (a fetch is
      slow, needs the network, and can hang on a credential prompt) and label
      the ahead/behind hints "as of last fetch". (jhg246)
2. `git-hints def <command>`: display a short definition of the requested Git
   command, explain what it does, and provide a link to the official Git
   documentation. If the command is unknown, report that it is unsupported.
   (jit45) **Future work. Do not implement.**

3. `git-hints howto <task>`: give step-by-step instructions for supported tasks
   such as committing, pulling, and pushing. If the requested task is unknown,
   report that it is unsupported instead of generating unverified instructions.
   (jit45) **Future work. Do not implement.**

4. `git-hints explain -- <git command>`: execute the specified Git command and
   capture its exit code and standard error, printing both back to the console
   but also including hints on how to resolve this error; it returns the same
   exit code that `git` produced. It uses this information to select an
   appropriate reactive hint. The `<git command>` must start with `git`,
   producing an error otherwise. If running the Git command produces no error,
   `git-hints` adds a note saying no error was detected, instead generating an
   appropriate hint.

   Implementation note: on Windows, disable expansion via
   `windows_expand_args=False` since Typer/Click expands wildcards, `~`, and
   environment variables that `git` should instead interpret.

5. `git-hints --bug <user comments explaining why the hint was wrong>
   [explain -- ...]`: Gather the current repo state and (for `explain`) git
   command output then post an issue in the GitHub repo. **Future work. Do not
   implement.**

6. Typer automatically generates `--help` for commands and subcommands. Each
   command and subcommand docstring must include at least one usage example so
   the generated help is useful. Examples should use the complete command names,
   such as `git-hints def status` and `git-hints howto commit`. (jit45)

Future Work
-----------

1. CodeChat Editor automatically displays a hyperlink and a summarized definition whenever specific commands such as "repo" or "pull" are typed out. Purpose of this feature is to serve an inline reminder of command functions, giving users immediate context while they work directly within the IDE. (ewj55)

<h2 id="cc-SbouyCXTsP">Hint structure</h2>

### Repository context

On each run inside a Git working tree, display the current branch name as a
context line outside the hint list. Detect it with `git branch --show-current`.
If the command returns an empty value because HEAD is detached, display
`detached HEAD`. This context line is not a hint and does not count toward the
three-hint limit. (sbe80)

1. Each actionable hint must show the terminal command and explain its expected
   result. The initial implementation will support the CLI. If a GUI is added
   later, show the equivalent GUI action alongside the terminal command. (ewj55;
   clarified by drj228)

2. Each hint should include a 1-sentence breakdown of what Git stage the user is
   currently in (Working in the directory, staging area, local repo, or remote),
   so the user learns the Git mental model while working (ewj55).

3. Every hint about a specific task and command links to the official docs for
   more information (ewj55).

4. Highlight sections from the docs to show where that specific hint came from (ewj55) **Example: When you see the definition for a push command that might have been simplified to "It sends your updated files from your local personal computer to a shared central computer, making them public" you can click on the link to the documentation and it will highlight the section where that summarized definition came from, which was from the quote "Updates one or more branches, tags, or other references in one or more remote repositories from your local repository, and sends all necessary data that isn’t already on the remote." Its similar to how search engines use Scroll to Text Fragment(STTF) and Featured Snippets to highlight the specifc information you are most likely looking for.**

5. Hints must consist of Markdown text. Each documentation link must include a
   title summarizing the linked term or command, limited to 160 characters. Put
   longer explanations in the linked documentation.

   The initial CLI will display hints as plain text, converting Markdown links
   into their label, URL, and title text. For example: Git status — Shows the
   working tree and staging-area status. Documentation:
   https://git-scm.com/docs/git-status

   Descriptions must be visible in the terminal without hovering over a link.
   (drj228)

6. Assign every hint exactly one priority class and display higher-priority
   classes first:

   1. Error/blocked: failed commands, unresolved merge conflicts, or another
      condition that prevents the current Git workflow from proceeding.

   2. Data-loss risk: use this class when an action may discard or overwrite
      work the user may want to keep, including uncommitted or staged changes,
      untracked files, local commits, or remote commits. Name what is at risk.
      Prefix the suggested command with `Caution:` when committed work may be
      changed but is usually recoverable through the reflog. Prefix it with
      `Warning:` when uncommitted or untracked work, or commits on a remote, may
      be permanently lost; explain what could be lost and tell the user to back
      it up first. Read-only actions need no safety prefix.
      `Warning:` when uncommitted or untracked work, or commits on a remote, may
      be permanently lost; explain what could be lost and tell the user to back
      it up first. Read-only actions need no safety prefix.

   3. Workflow: actionable next-step suggestions based on repository state.

   4. Informational: status or explanatory guidance that does not block work.

   If two triggered hints have the same priority class, order them by their
   permanent hint ID.

7. Every hint must have a unique, permanent text ID, such as `diverged`,
   `push-ahead`, or `commit-identity`. IDs must not depend on list positions or
   displayed wording. Display the ID with each hint and use it for `--exclude`
   or `--dismiss` switches and test assertions. (sbe80; clarified by drj228)

Implementation
--------------

### `git-hints`

Proactive hints are triggered by observable repository state when `git-hints`
runs. (jit45)

#### Stage files

* Hint: Do you want to
  [stage](https://git-scm.com/docs/git-add "Also called the index; select which changed files to store in a commit")
  files?

* Git stage: Your edits are in the working directory; Git won't put them in a
  commit until you stage them.

* Command: `git add <files to stage>`; afterward, `git status` lists these files
  under "Changes to be committed."

* ID: `unstaged-changes`, priority class: workflow, safety: safe.

* Conditions: Unstaged edits to tracked files exist in the repository. Run `git
  diff --quiet`; an exit code of 0 means no unstaged edits; 1 means there are
  unstaged edits; other return codes indicate an error.

* Test case:

  1. Invoke `make_temps(1)` to create a temporary directory.
  2. Execute the following in this temp directory:
     1. Call `config_user("user1", "user1@example.com")`.
     2. Create an empty git repo with `git init -b main`.
     3. Create a file called `foo.txt` with the content `xxx`.
     4. Add it: `git add foo.txt`.
     5. Commit it: `git commit -m "Add foo."`.
     6. Modify `foo.txt`: append `y` to it.
     7. Run `git-hints --all` in the temp dir. Expected hint ID:
        `unstaged-changes`.
     8. Stage the changes: `git add foo.txt`.
     9. Run `git-hints --all` in the temp dir. Hint ID: `unstaged-changes` must
        not appear.

### Push (ewj55)

* Hint: Do you want to [push](https://git-scm.com/docs/git-push "Uploads the latest changes of your local repository (repo) to a remote repository, this allows other collaborators to download your work.")?

  Git Stage: You are working in the local repo. You have commits that have not been pushed to the remote branch.

  Command: `git push <remote> <name of local branch>:<name of remote branch>`; afterward, displays push output (most likely in tabular format) output: stderr progress report followed by: `<flag> <summary> <from> -> <to> (<reason>)`

  * ID: `push-ahead`, priority class: workflow, safety: safe.

  * Conditions: local repository was changed and looks different from remote repository. Run `git status -sb`. If the branch status shows that the local branch is ahead of its upstream branch by one or more commits, then the local commits exist that are not yet public. Label results "as of last fetch".

  * Test case:
   1. **Setup** Call `git_setup()`. Create two temporary directories: `remote` and `local`.
   2. Call `config_user("user1", "user1@foo.com")`.
   3. In `remote`, run `git init --bare -b main`.
   4. Clone `remote` into `local` using `git clone <remote> <local>`.
   5. In `local`, create `foo.txt` containing `xxx`, run `git add foo.txt`,
      `git commit -m "Add foo."`, then `git push -u origin main`.
   6. Run `git-hints all` in `local`. Verify the  `push-ahead` hint is absent.
   7. Append `y` to `foo.txt` and run `git commit -am "Change foo."`.
   8. Run `git log origin/main..HEAD` and verify it lists exactly one commit.
   9. Run `git-hints all` in `local`. 
      Expected hint: **Push?** (ID `push-ahead`),
      labeled "as of last fetch" and suggesting `git push`. Verify that the
      `behind` and `diverged` hints are absent.

### Clone a Repository (ewj55)

* Hint: Would you like to clone
  [repo](https://git-scm.com/book/en/v2/GitHub-Maintaining-a-Project.html#_creating_a_new_repository "A collection of snapshots tracking a project's history, where people can download a local copy to modify.")?

  Git stage: You are not inside a Git repository, you need to either clone or initialize a repository before you can begin tracking files.

  Command: `git clone <repository-url>`

* ID: `not-a-repo`, priority class: Informational, safety: safe.

* Conditions: Determine if current directory is inside a Git working tree by running `git rev-parse --is-inside-work-tree` using `subprocess`. Exit code 0 with output `true` means it is inside a working tree. Exit code 128 means its outside a Git repository, which triggers this hint." Avoid suggesting cloning hint for other unexpected Git errors.

* Test case:

   1. Call `git_setup()` and `make_temps(1)`. Set `GIT_CEILING_DIRECTORIES` to
      the temporary directory's parent so Git cannot discover an enclosing repo.
   2. In the temporary directory, run `git rev-parse --is-inside-work-tree` and
      verify exit code 128.
   3. Run `git-hints all`. Expected hint: **Clone a repo?**, identified by its
      permanent ID, suggesting `git clone <repository-url>` with a link to the
      official documentation. Verify that `git-hints` exits normally.
   4. Run `git init -b main`, then `git-hints all` again. Verify the clone hint is absent.


#### <mark>TODO: each of the following hints should be rewritten to follow the above hints.</mark>

#### Keep [unstaged changes](https://git-scm.com/docs/git-diff "Shows unstaged changes in the working tree.") out of this commit? **Sbe80**

   * Hint: Do you want to keep unstaged changes out of this commit? [git commit](https://git-scm.com/docs/git-commit "Records the staged changes in a new commit.") records staged changes only.

   * Git stage: Some of your edits are in the staging area and will be included
     in the next commit; other edits remain in the working directory and will
     not be included.

   * Command: `git diff --cached`; afterward, the displayed changes are the
     ones staged for the next commit. When ready, commit those changes with
     `git commit -m "message"`.

   * ID: `staged-and-unstaged-changes`, priority class: workflow, safety: safe.

   * Conditions: Display this hint when the staging area contains at least one staged change and the working tree contains at least one unstaged change to a tracked file. Run `git diff --cached --quiet` to check for staged changes and `git diff --quiet` to check for unstaged changes to tracked files. For either command, exit code 1 means changes exist, exit code 0 means none exist, and any other exit code indicates an error. Show the hint only when both commands exit with code 1; do not show it when only staged changes or only unstaged changes exist. (drj228; sbe80 will test)

   * Test case: Staged and unstaged changes.

     1. Call `git_setup()` and create one temporary directory.
     2. In the temporary directory, initialize a repository with `git init -b main`.
     3. Call `config_user("user1", "user1@foo.com")` after initializing the
        repository.
     4. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
        commit it with `git commit -m "Add foo."`.
     5. Check the staged-only state:
        1. Append `y` to `foo.txt` and run `git add foo.txt`.
        2. Run `git-hints --all`.
        3. Verify that the `staged-and-unstaged-changes` hint is absent,
           because there are no unstaged changes.
        4. Verify that the `staged-changes` hint appears. Verify that it
           recommends reviewing staged changes with `git diff --cached` and
           explains how to commit the
           selected changes with `git commit -m "message"`. Check the
           corresponding official Git documentation links.
     6. Check the unstaged-only state:
        1. Commit the staged change with `git commit -m "Append y."`.
        2. Append `z` to `foo.txt` without staging it.
        3. Run `git-hints --all` and verify that both the
           `staged-and-unstaged-changes` and `staged-changes` hints are absent:
           the file has unstaged changes, but nothing is staged for the next
           commit.
     7. Check the staged-plus-unstaged state:
        1. Run `git add foo.txt` to stage the `z` change.
        2. Append `w` to `foo.txt` and leave this change unstaged.
        3. Run `git-hints --all`.
        4. Verify that both the `staged-and-unstaged-changes` and
           `staged-changes` hints appear. Verify that the
           `staged-and-unstaged-changes` hint explains that a plain `git commit`
           records staged changes only and suggests `git diff --cached`.
        5. Verify that `staged-changes` recommends reviewing the staged changes
           with `git diff --cached` and committing the selected changes with
           `git commit -m "message"`. Confirm the two hints are distinct and
           include the corresponding official Git documentation links,
           including `https://git-scm.com/docs/git-diff` and
           `https://git-scm.com/docs/git-commit`.


#### Branch is behind upstream (jhg246)

* Hint: Do you want to
  [pull](https://git-scm.com/docs/git-pull "Fetches commits from the remote and integrates them into your current branch")
  the newest remote commits before you start editing? Your branch does not
  contain remote commits that were known at the last fetch.

* Git stage: You are working in the local repo, which is missing commits that
  the remote repo already has.

* Command: `git pull`; afterward, `git status` reports that your branch is up
  to date with its upstream. To preview first, run `git diff --name-only
  HEAD...@{upstream}`, which lists the files the pull would bring in.

* ID: `behind`, priority class: workflow, safety: safe.

* Conditions: The current branch has an upstream and is behind it by one or
  more commits but not ahead of it. Run `git status --porcelain=v2 --branch` and
  read `# branch.ab +<ahead> -<behind>`; the line is absent when there is no
  upstream. The hint applies when `<behind>` is above 0 and `<ahead>` is 0. If
  the branch is also ahead, the `diverged` hint applies instead. These counts
  use the last-fetched remote-tracking branch, so label the hint "as of last
  fetch" (see `git-hints --fetch`). (jhg246; adapted from jit45's personal
  experience; jhg246 and raf322 will test)

* Test case:

  1. Call `git_setup()` and create two temporary directories, `repo1` and
     `repo2`. Run every `git-hints` command in `repo2`.
  2. In `repo1`, initialize a repository with `git init -b main` and call
     `config_user("user1", "user1@foo.com")`.
  3. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
     commit it with `git commit -m "Add foo."`.
  4. Clone `repo1` into `repo2` with `git clone <repo1> <repo2>`.
  5. In `repo1`, append `y` to `foo.txt` and run `git commit -am "Change foo."`.
     `repo1` acts as the remote. Nothing is pushed, because `repo2` only
     fetches from it, so it does not need to be bare.
  6. In `repo2`, run `git status --porcelain=v2 --branch` and verify that it
     reports `# branch.ab +0 -0`. Run `git-hints --ids-only` and verify that
     `behind` is absent, because `repo2` has not fetched.
  7. In `repo2`, run `git fetch` and verify that the status now reports
     `# branch.ab +0 -1`.
  8. Run `git-hints --all`. Verify that the `behind` hint appears, is labeled
     "as of last fetch", recommends `git pull`, and links to the official
     `git pull` documentation. Verify that `diverged` and `push-ahead` are
     absent.
  9. In `repo1`, append `z` and run `git commit -am "Change foo again."`. In
     `repo2`, run `git fetch` and verify `# branch.ab +0 -2`. Run
     `git-hints --ids-only` and verify that `behind` still appears.
  10. In `repo2`, run `git pull` and verify `# branch.ab +0 -0`. Run
      `git-hints --ids-only` and verify that `behind` is absent.
  11. In `repo1`, append `w` and run `git commit -am "Change foo once more."`.
      In `repo2`, run `git-hints --ids-only` and verify that `behind` is
      absent, then run `git-hints --ids-only --fetch` and verify that `behind`
      appears even though `repo2` never ran `git fetch` itself.

#### Branch has diverged from upstream (sbe80; edited by jhg246)

* Hint: Your branch has diverged from its upstream. Do you want to integrate
  the remote commits with
  [git pull](https://git-scm.com/docs/git-pull "Fetches and integrates remote commits; --rebase replays yours on top of them.")
  and then share yours with
  [git push](https://git-scm.com/docs/git-push "Uploads local commits to the remote branch.")?

* Git stage: You are working in the local repo, which has commits that the
  remote lacks while the remote has commits that your local repo lacks.

* Command: `git pull`, resolve any conflicts, then `git push`; afterward,
  `git status` reports that your branch is up to date with its upstream. If you
  prefer a linear history, Caution: `git pull --rebase` replays your local
  commits on top of the remote ones, which changes them; they remain
  recoverable through the reflog.

* ID: `diverged`, priority class: workflow, safety: safe.

* Conditions: The current branch has an upstream and is both ahead of and
  behind it, as of the last fetch. Run `git status --porcelain=v2 --branch` and
  read `# branch.ab +<ahead> -<behind>`; the hint applies when both numbers are
  above 0. When it applies, do not show the `behind` or `push-ahead` hints,
  because this hint replaces them. Label the hint "as of last fetch" (see
  `git-hints --fetch`). (sbe80; edited by jhg246; jhg246 will test)

* Test case:

  1. Do steps 1-5 of the `behind` hint's test case. This leaves `repo1` with a
     commit that `repo2` has not fetched.
  2. In `repo2`, create `bar.txt` containing `zzz`, stage it with
     `git add bar.txt`, and commit it with `git commit -m "Add bar."`.
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


**ams2083**
* Hint: Do you want to configure an [upstream branch](https://git-scm.com/docs/git-branch "A remote branch that your local branch tracks") before pushing?

* Git stage: Your current branch has no upstream branch configured. An upstream allows Git to identify which remote branch your local branch tracks, simplifying future pushes and pulls.

* Command: `git push -u origin <branch-name>` pushes the current branch to `origin` and configures its upstream for future pushes and pulls.

* ID: `no-upstream-branch`, priority class: workflow, safety: safe.

* Conditions: The current branch has no upstream branch configured. Confirm that the repository is on a local branch, rather than in a detached HEAD state, using `git symbolic-ref --quiet --short HEAD`. Check for an upstream using `git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}"`. Confirm that the `origin` remote exists using `git remote`. Suggest configuring an upstream only when the current branch has no resolvable upstream and `origin` exists. Do not display the hint in detached HEAD state or when a valid upstream is configured.

* Test case:

1. Invoke `make_temps(2)` to create two temporary directories.
2. In the first directory:
   1. Initialize a repository with `git init -b main`.
   2. Call `config_user("user1", "user1@foo.com")`.
   3. Create `foo.txt` containing `xxx`.
   4. Stage it with `git add foo.txt`.
   5. Commit it with `git commit -m "Add foo."`.
   6. Create and switch to a new branch with `git switch -c feature-test`.
3. In the second directory, initialize a bare remote repository with `git init --bare`.
4. In the first directory, add the second repository as the `origin` remote using `git remote add origin <path-to-second-directory>`.
5. Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` and verify that it fails because no upstream is configured.
6. Run `git-hints --all`. Verify that the hint with ID `no-upstream-branch` appears and recommends `git push -u origin feature-test`.
7. Run `git push -u origin feature-test` to push the branch and configure its upstream.
8. Run `git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}"` and verify that it returns `origin/feature-test`.
9. Run `git-hints --all` and verify that the hint with ID `no-upstream-branch` is absent.

#### Review staged changes before committing? **sbe80**

   * Hint: Would you like to review your [staged changes](https://git-scm.com/docs/git-diff "Show changes staged for the next commit") before committing? Use [git commit](https://git-scm.com/docs/git-commit "Record the staged changes in a new commit") when they are ready.

   * Git stage: You have changes in the staging area that will be included in the next commit. Unstaged edits remain in the working directory and will not be included.

   * Command: Run `git diff --cached` to review the staged changes. When they are ready, run `git commit -m "message"` to create a commit containing those staged changes.

   * ID: `staged-changes`, priority class: workflow, safety: safe.

   * Conditions: Display this hint when the staging area contains at least one change to be committed. Run `git diff --cached --quiet`; exit code 1 means staged changes exist, exit code 0 means none exist, and any other exit code indicates an error. Do not display the hint when the staging area is empty. This includes staged files in a repository with no commits yet. (drj228; sbe80 will test)

   * Test case:

     1. Call `git_setup()` and create one temporary directory.
     2. Initialize a repository in that directory with `git init -b main`.
     3. Call `config_user("user1", "user1@example.com")`.
     4. Run `git-hints --all` and verify that the `staged-changes` hint is absent.
     5. Create `foo.txt` containing `xxx` and stage it with `git add foo.txt`.
     6. Run `git-hints --all` and verify that the `staged-changes` hint appears. Verify that it recommends `git diff --cached` and `git commit -m "message"`, and includes links to the official `git diff` and `git commit` documentation.
     7. Commit the file with `git commit -m "Add foo."` and run `git-hints --all` again. Verify that the `staged-changes` hint is absent.

10. Configure your commit identity? Conditions: `user.name` or `user.email` is
    missing or empty in the effective Git configuration. Explain how to set the
    missing value using `git config --global user.name "Your Name"` or `git
    config --global user.email "you@example.com"`.

    The `--global` option sets the default for all repositories belonging to the
    current user. Use `--local` inside a repository to configure an identity for
    that repository only. Local settings override global settings. An empty
    local override should be corrected locally. These settings identify commit
    authors; they do not sign the user into GitHub. (drj228)

**ams2083**
* Hint: Do you need to [stage](https://git-scm.com/docs/git-add "Add files to the staging area") or [ignore](https://git-scm.com/docs/gitignore "Specify intentionally untracked files that Git should ignore") untracked files?
  
  * Git stage: Your working directory contains files that Git is not currently tracking. Ordinary project files should be staged if you want to include them in a future commit. Files containing secrets, temporary files, caches, and generated build outputs should generally be ignored.

  * Command: Run `git status --porcelain=v1` to identify untracked files, indicated by lines beginning with `??`. Use `git add <filename>` to stage files you want to track, or add appropriate patterns to `.gitignore` for files that should remain untracked. Run `git status` afterward to verify the changes.

  * ID: `untracked-files`, priority class: workflow, safety: safe.

  * Conditions: One or more untracked files exist in the working directory. Run `git status --porcelain=v1` and check for lines beginning with `??`. If ordinary untracked files exist, suggest staging them with `git add <filename>`. If files commonly excluded from version control are detected, such as `.env`, `__pycache__/`, `*.pyc`, or generated build outputs, suggest adding appropriate patterns to `.gitignore`. Display the hint when at least one untracked file or directory exists. Do not display the hint when no untracked files remain.

  * Test case:

    1. Call `git_setup()`. Create one temporary directory.
    2. In the temporary directory, initialize a repository with `git init -b main`.
    3. Call `config_user("user1", "user1@foo.com")`.
    4. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and commit it with `git commit -m "Add foo."`.
    5. Check the ordinary untracked file state:
       1. Create `notes.txt` containing `Hello world` without staging it.
       2. Run `git status --porcelain=v1` and verify that `?? notes.txt` appears.
       3. Run `git-hints --all`.
       4. Verify that the hint with ID `untracked-files` appears and recommends `git add notes.txt`.
       5. Verify that the hint includes the appropriate official Git documentation links.
    6. Check the staged file state:
       1. Run `git add notes.txt` to stage the untracked file.
       2. Run `git status --porcelain=v1` and verify that `notes.txt` is now staged rather than untracked.
       3. Run `git-hints --all`.
       4. Verify that the hint with ID `untracked-files` is absent because no untracked files remain.
    7. Check the untracked file that should be ignored:
       1. Create a file named `.env` containing `TEST_VARIABLE=example`.
       2. Create a directory named `__pycache__` containing a file called `example.pyc`.
       3. Run `git status --porcelain=v1` and verify that `.env` and `__pycache__/` appear as untracked.
       4. Run `git-hints --all`.
       5. Verify that the hint with ID `untracked-files` appears.
       6. Verify that the hint recommends adding appropriate patterns to `.gitignore` instead of staging these files. Check the corresponding official Git documentation links.
    8. Check the ignored file state:
       1. Create a `.gitignore` file containing patterns for `.env`, `__pycache__/`, and `*.pyc`.
       2. Stage `.gitignore` with `git add .gitignore`.
       3. Run `git status --porcelain` and verify that `.env` and `__pycache__/` no longer appear as untracked.
       4. Run `git-hints --all`.
       5. Verify that the hint with ID `untracked-files` is absent because all remaining files are either tracked or ignored.
       3. Run `git-hints --all`.
       4. Verify that the hint with ID `untracked-files` is absent because no untracked files remain.

11. Commit repo? Conditions: More than 50% of the repository's tracked files
    have staged, unstaged, or deleted changes relative to HEAD. Use
    `git    status --porcelain` to identify changed tracked files and compare
    that number to the total number of tracked files. Untracked files should be
    handled separately and should not count toward this percentage. If more than
    half of the tracked files have changes, suggest reviewing and committing the
    changes. (jit45) **jit45 will test**

12. Detached HEAD state? Conditions: the repository exists, HEAD is not attached
    to a local branch, and Git is not currently performing a rebase or bisect
    operation. Explain that the user is working in the local repository at a
    specific commit instead of on a named branch. Suggest `git switch -c <name>`
    to create and switch to a new branch if the user wants to preserve future
    commits. (jit45) **drj228 will test**

13. This repository does not have any commits yet? Conditions: the current
    directory is a Git repository, but HEAD does not yet resolve to a commit.
    Use `git rev-parse --verify HEAD` to confirm and explain that the local
    repository has no saved commit yet. If files are staged, suggest
    `git    commit -m "Initial commit"` to create the first commit. (jit45)
    **drj228 will test**

15. Committing to protected/main branch? Conditions: the current branch is
    master/main and there are changes. If other branches exist, suggest other
    branches. If no other branches exist, suggest creating a new branch with
    `git switch -c <name>`. (raf322)

### `git-hints explain -- git <command> [<args>...]`

Reactive hints are triggered by the result of a Git command executed through
`git-hints explain`. (jit45)

1. Resolve merge conflicts? **sbe80**

   * Hint: Git left [merge conflicts](https://git-scm.com/docs/git-merge
     "Join two or more development histories together") that need to be resolved
     before the merge can finish. Conflicted files: `<files>`.

   * Git stage: The merge is in progress in the working directory; edit each
     conflicted file to choose or combine the changes, then stage the resolved
     files.

   * Command: Run `git diff --name-only --diff-filter=U` to list the conflicted
     files. Edit each file to resolve its conflict markers, then run `git add
     <file>` for each resolved file and `git status` to confirm no conflicts
     remain. Complete the merge with `git commit` when Git requests a merge
     commit.

   * ID: `merge-conflicts`, priority class: error/blocked, safety: safe.

   * Conditions: A Git command executed through `git-hints explain` leaves the
     repository with one or more unresolved merge conflicts. Detect them with
     `git diff --name-only --diff-filter=U`; include the returned paths in the
     hint. Do not display this hint when the command failed without leaving
     unresolved conflicts.

   * Test case: Resolving merge conflicts (written by sbe80).

     1. Call `git_setup()` and create two temporary directories, `repo1` and
        `repo2`.
     2. In `repo1`, initialize a repository with `git init -b main` and call
        `config_user("user1", "user1@foo.com")`.
     3. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
        commit it with `git commit -m "Add foo."`.
     4. Clone `repo1` into `repo2` with `git clone <repo1> <repo2>`.
     5. In `repo1`, append `y` to `foo.txt`, stage it with `git add foo.txt`,
        and commit it with `git commit -m "Append y."`.
     6. In `repo2`, call `config_user("user2", "user2@foo.com")`. Append `z` to
        `foo.txt`, stage it with `git add foo.txt`, and commit it with `git
        commit -m "Append z."`.
     7. In `repo2`, run `git-hints explain -- git pull --no-rebase` and capture
        its exit code and output.
     8. Verify that the Git command exits non-zero and leaves an unresolved
        merge conflict. Verify with `git diff --name-only --diff-filter=U`
        that `foo.txt` is conflicted.
     9. Verify that the hint with ID `merge-conflicts` appears, names `foo.txt`,
        has error/blocked priority, explains how to resolve the conflict, and
        links to official merge documentation such as
        `https://git-scm.com/docs/git-merge`.

2. Resolve pull conflicts? Conditions: `git-hints explain -- git pull` fails
   because local uncommitted changes would be overwritten. Identify the affected
   files and explain how to preserve or resolve the local changes. **jit45 will
   test**

3. Push failed? Conditions: `git-hints explain -- git push` fails because the
   remote branch contains commits that are not present in the local branch.
   Explain that the user should integrate the remote changes before attempting
   to push again. (jhg246)

4. Explain
   [stashes](https://git-scm.com/docs/git-stash "Save changes temporarily in the stash")
   [stashes](https://git-scm.com/docs/git-stash "Allows you to modify a working directory while saving your current state of your local directory.")
   including: what they are, how to make one, and how to see old ones.
   Condition: a command executed through `git-hints explain` reports a conflict
   where temporarily setting aside local changes would help. (sbe80)

5. Suggest and explain
   [git pull --rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) if
   five failed `git pull` or `git push` commands have been executed through
   `git-hints explain` in a row. Explain that rebasing may cause merge conflicts
   and that the user should ensure their local work is committed or otherwise
   backed up before proceeding. (sbe80).

### Language and libraries

1. Language: Python
2. Package manager: uv
3. Formatter/linter: ruff
4. Type checker: ty
5. CLI: Typer
6. Git interface: Python's built-in `subprocess` module. Run Git commands as
   argument lists with `shell=False` and `check=False`. Inspect `returncode`
   explicitly so expected nonzero results, such as exit code 1 when checking for
   staged changes or a missing configuration value, are handled according to
   each command's documented meaning. Report unexpected failures separately
   instead of treating them as hint conditions. (drj228) TODO: rethink -- makes
   sense for `git-hints explain`, but perhaps not for plain `git-hints`.
7. Testing: Pytest
8. Git: version 2.32 or later, which added `GIT_CONFIG_GLOBAL`.

## <mark>TODO -- these should be merged with specific implementations above</mark>

2. A Git command executed through `git-hints explain` failed: run the command
   using `subprocess.run()` with an argument list, `shell=False`, and
   `check=False`. Capture standard error and inspect `returncode`. Leave
   standard input and standard output connected to the terminal so interactive
   commands can operate normally. Use the command, exit code, and standard error
   to select an appropriate hint. The tool cannot reliably recover the result of
   an earlier command run outside the tool. (drj228)

3. The local branch has commits that have not been pushed to the remote branch:
   run `git status -sb`. If the branch status shows that the local branch is
   ahead of its upstream branch by one or more commits, then local commits exist
   that are not yet public.

4. Determine whether the current directory is inside a Git working tree: run
   `git rev-parse --is-inside-work-tree` using `subprocess`. Exit code 0 with
   output `true` confirms a working tree. If the command fails, inspect standard
   error to distinguish a directory outside a repository from other Git errors.
   Do not treat every failure as a reason to suggest cloning. (sbe80; clarified
   by drj228)


6. Staged changes are ready to commit: run `git diff --cached --quiet`. Exit
   code 1 means staged differences exist; exit code 0 means there are none.
   Treat other exit codes as errors instead of triggering the hint. This detects
   the condition for the staged-review hint. (drj228)

7. Commit identity is not configured: run `git config --get user.name` and `git
   config --get user.email`. An exit code of 1 indicates that the requested
   setting is missing. Also check for an empty returned value. Report other
   command failures separately. These checks use the effective configuration,
   including repository and global settings. (drj228)

8. HEAD is detached rather than attached to a local branch: run `git
   symbolic-ref --quiet --short HEAD`. A zero exit code means HEAD is attached
   to a branch and the command prints the branch name. A non-zero exit code in
   an otherwise valid Git repository means HEAD is detached.

   Before triggering the detached-HEAD hint, also verify that Git is not
   currently performing a rebase or bisect. Check the paths returned by `git
   rev-parse --git-path rebase-merge`, `git rev-parse --git-path rebase-apply`,
   and `git rev-parse --git-path BISECT_START`.

   If any corresponding operation state exists, suppress the detached-HEAD hint.
   (jit45)

9. Committing to main/master: Run `git branch --show-current` to identify
    current branch. If the branch is main, check for other remote/active
    branches with `git for-each-ref --format='%(refname:short)'
    refs/heads   refs/remotes`. If the list contains no other branches besides
    the protected branch(es), suggest the creation of a new branch. Otherwise,
    suggest other branches on the list. (raf322)


11. The `git-hints explain` command must pass Git arguments through without
    Typer attempting to parse them as options. Configure the command to allow
    extra arguments and ignore unknown options (for example, using
    allow\_extra\_args=True and ignore\_unknown\_options=True) so commands such
    as `git-hints explain -- git pull --rebase` and `git-hints explain -- git reset --hard
    HEAD~1` are passed to Git correctly (sbe80).

12. The `git-hints explain` command requires the command after `explain` to begin
    with `git`. Use the `--` separator, as in `git-hints explain -- git status`;
    report an error if the command does not begin with `git`. (sbe80)

Testing
-------

The test tool contains:

* `make_temps(num)`: creates and returns `num` temporary directories using
  pytest's `tmp_path_factory`.
* `make_repo(temp_dir, commands)`: runs the list of `commands` in `temp_dir` to
  create and populate the repository. Each command is either an argument list,
  such as `["git", "commit", "-m", "Add foo."]`, executed using
  `subprocess.run()` with `shell=False`, or a lambda function with no parameters
  used to create, modify, or delete files. Pass each argument separately and
  keep messages containing spaces in a single list element. Do not join
  arguments into a shell string. (drj228) Lambdas run with `temp_dir` as the
  current working directory, so they can use relative paths; `make_repo`
  restores the previous working directory before returning.
* `config_user(username, email)`: Set Git's global `user.name` and `user.email`.
* `git_setup()`: creates an isolated Git configuration for the test environment.
  The test environment shall:
  * Remove every inherited environment variable whose name starts with `GIT_`,
    plus `EMAIL` and `XDG_CONFIG_HOME`. Git sets `GIT_DIR`, `GIT_WORK_TREE`, and
    `GIT_INDEX_FILE` when pytest runs from a Git hook, which would make tests
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
    to pytest's base temporary directory (`tmp_path_factory.getbasetemp()`), so
    Git never finds a repository above a test's temporary directory.
  * Set
    [`GIT_TERMINAL_PROMPT=0`](https://git-scm.com/docs/git#Documentation/git.txt-GITTERMINALPROMPT)
    and
    [`GIT_EDITOR=true`](https://git-scm.com/docs/git#Documentation/git.txt-GITEDITOR),
    so no test waits for a password or an editor.
  * Set `LC_ALL=C`, so Git's messages are in English.

A typical test calls `git_setup()` (provided as an autouse fixture), creates
temporary directories with `make_temps()`, and uses `make_repo()` to set up
repositories. Run `git-hints --all` when checking hint content, commands, and
documentation links. Use `git-hints --ids-only` when checking whether a hint ID
is present or absent. Both modes must run with the repository under test as the
current working directory.

All Git commands executed as part of a test, including those that `git-hints`
runs, shall use the isolated test environment established by `git_setup()`. This
prevents test results from varying based on the Git configuration of the machine
running the tests. This should be implemented as a PyTest autouse fixture which
applies to all tests.

### <mark>TODO: move test cases to follow the implementation of each hint.</mark>

### Test Case 4: Push (ewj55)

1. Initialize `Test4_condition == 0` by default
2. use the termnial to navigate to the local repo directory tracking a remote
   branch ('origin/main')<br>
3. Execute command (`git fetch origin`) and ensure local track references are up
   to date <br>
4. Make a minor edit to the file, stage the change (`git add .`), then commit
   locally ('git commit -m "Test commit"') **Condition Checks:** 4. run `git log
   origin/main..HEAD` into terminal 5. If command returns one or more comit
   SHAs, set `Test4_condition == 1`. **Output/Expected Execution** 6. If
   `Test4_condition == 1`, execute `git-hints` CLI tool on terminal 7. Confirm
   proactive hint 'Push?' is displayed in terminal output. 8. If `git-hints`
   output contains `"Push?"` string AND `'git push'` command, then Test 4 has
   passed.

### Test Case 5: Repo Test (ewj55)

**Setup (Arrange):**

1. Create isolated tmp dir in system tmp space (outside any existing Git repo
   tree)
2. Using terminal, navigate into isolatd tmp dir without running the `git init`
   command:
   * `mkdir test_folder && cd test_folder` **Executions and Assertions** 3.
     Execute `git status` and verify terminal output contains `"fatal: not a git
     repository"`. 4. Execute the `git-hints` CLI tool inside `test_folder`.
     **Assertion**
3. If `git-hints` output contains the proactive hint string `"clone"` AND the
   suggested command `'git clone'`, then Test 5 has passed
### Test case 2: Staged and unstaged changes. (Written by sbe80) -- Requirements Proactive 2 and 10

1. Call `git_setup()` and create one temporary directory.
2. In the temporary directory, initialize a repository with `git init -b main`.
3. Call `config_user("user1", "user1@foo.com")` after initializing the
   repository.
4. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
   commit it with `git commit -m "Add foo."`.
5. Check the staged-only state:
   1. Append `y` to `foo.txt` and run `git add foo.txt`.
   2. Run `git-hints --all`.
   3. Verify that the Proactive 2 hint is absent, because there are no unstaged
      changes.
   4. Verify that the Proactive 10 hint appears, identified by its own permanent
      hint ID. Verify that it recommends reviewing staged changes with `git diff
      --cached` and explains how to commit the selected changes with `git commit
      -m "message"`. Check the corresponding official Git documentation links.
6. Check the unstaged-only state:
   1. Commit the staged change with `git commit -m "Append y."`.
   2. Append `z` to `foo.txt` without staging it.
   3. Run `git-hints --all` and verify both the Proactive 2 and Proactive 10
      hints are absent: the file has unstaged changes, but nothing is staged for
      the next commit.
7. Check the staged-plus-unstaged state:
   1. Run `git add foo.txt` to stage the `z` change.
   2. Append `w` to `foo.txt` and leave this change unstaged.
   3. Run `git-hints --all`.
   4. Verify that both Proactive 2 and Proactive 10 appear, each identified by
      its own permanent hint ID. Verify that Proactive 2 explains a plain `git
      commit` records staged changes only and suggests `git diff --cached`.
   5. Verify that Proactive 10 recommends reviewing the staged changes with `git
      diff --cached` and committing the selected changes with `git commit -m
      "message"`. Confirm the two hints are distinct and include the
      corresponding official Git documentation links, including
      `https://git-scm.com/docs/git-diff` and
      `https://git-scm.com/docs/git-commit`.

### Test case 3: Resolving merge conflicts. (Written by sbe80) -- Requirement Reactive 1

1. Call `git_setup()` and create two temporary directories, `repo1` and `repo2`.
2. In `repo1`, initialize a repository with `git init -b main` and call
   `config_user("user1", "user1@foo.com")`.
3. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
   commit it with `git commit -m "Add foo."`.
4. Clone `repo1` into `repo2` with `git clone <repo1> <repo2>`.
5. In `repo1`, append `y` to `foo.txt`, stage it with `git add foo.txt`, and
   commit it with `git commit -m "Append y."`.
6. In `repo2`, call `config_user("user2", "user2@foo.com")`. Append `z` to
   `foo.txt`, stage it with `git add foo.txt`, and commit it with `git commit -m
   "Append z."`.
7. In `repo2`, run `git-hints explain pull --no-rebase` and capture its exit
   code and output.
8. Verify that the Git command exits non-zero and leaves an unresolved merge
   conflict. Verify with `git diff --name-only --diff-filter=U` that `foo.txt`
   is conflicted.
9. Verify that the reactive merge-conflict hint appears, identified by its
   permanent hint ID. Verify that it:
   1. Names `foo.txt` as a conflicted file.
   2. Has the Error/blocked priority class.
   3. Explains how to resolve the conflict.
   4. Includes a link to the official Git documentation for merging, such as
      `https://git-scm.com/docs/git-merge`.



### Test Case 6: Pull needed, Branch is behind (jhg246)

1. Call `git_setup()` and create two temporary directories, `repo1` and
     `repo2`. Run every `git-hints` command in `repo2`.
  2. In `repo1`, initialize a repository with `git init -b main` and call
     `config_user("user1", "user1@foo.com")`.
  3. Create `foo.txt` containing `xxx`, stage it with `git add foo.txt`, and
     commit it with `git commit -m "Add foo."`.
  4. Clone `repo1` into `repo2` with `git clone <repo1> <repo2>`.
  5. In `repo1`, append `y` to `foo.txt` and run `git commit -am "Change foo."`.
     `repo1` acts as the remote. Nothing is pushed, because `repo2` only
     fetches from it, so it does not need to be bare.
  6. In `repo2`, run `git status --porcelain=v2 --branch` and verify that it
     reports `# branch.ab +0 -0`. Run `git-hints --ids-only` and verify that
     `behind` is absent, because `repo2` has not fetched.
  7. In `repo2`, run `git fetch` and verify that the status now reports
     `# branch.ab +0 -1`.
  8. Run `git-hints --all`. Verify that the `behind` hint appears, is labeled
     "as of last fetch", recommends `git pull`, and links to the official
     `git pull` documentation. Verify that `diverged` and `push-ahead` are
     absent.
  9. In `repo1`, append `z` and run `git commit -am "Change foo again."`. In
     `repo2`, run `git fetch` and verify `# branch.ab +0 -2`. Run
     `git-hints --ids-only` and verify that `behind` still appears.
  10. In `repo2`, run `git pull` and verify `# branch.ab +0 -0`. Run
      `git-hints --ids-only` and verify that `behind` is absent.
  11. In `repo1`, append `w` and run `git commit -am "Change foo once more."`.
      In `repo2`, run `git-hints --ids-only` and verify that `behind` is
      absent, then run `git-hints --ids-only --fetch` and verify that `behind`
      appears even though `repo2` never ran `git fetch` itself.

### Test case 7: Branch has diverged. (jhg246) -- For Requirement Proactive 16

1. Do steps 1-5 of the `behind` hint's test case. This leaves `repo1` with a
     commit that `repo2` has not fetched.
  2. In `repo2`, create `bar.txt` containing `zzz`, stage it with
     `git add bar.txt`, and commit it with `git commit -m "Add bar."`.
  3. Run `git status --porcelain=v2 --branch` and verify `# branch.ab +1 -0`.
     Run `git-hints --ids-only` and verify that `push-ahead` appears and
     `diverged` is absent, because `repo2` has not fetched the new remote
     commit.
  4. Run `git fetch` and verify that the status now reports `# branch.ab +1 -1`.
  5. Run `git-hints --all`. Verify that the `diverged` hint appears, is labeled
     "as of last fetch", suggests `git pull` or `git pull --rebase` and then
     `git push`, and links to the official `git pull` and `git push`
     documentation. Verify that `behind` and `push-ahead` are absent.

### Test case 10: Detached HEAD state. (Written by drj228)

For Requirement Proactive 14, written by jit45.

1. Call `git_setup()` and create one temporary directory.
2. Initialize a repository in that directory with `git init -b main`.
3. Call `config_user("user1", "user1@example.com")`.
4. Create `foo.txt` containing `xxx`, stage it, and commit it. Run Git commands
   as argument lists with `shell=False`.
5. Run `git-hints --all`. Verify that the detached-HEAD hint is absent while HEAD
   is attached to `main`.
6. Run `git switch --detach HEAD`.
7. Run `git symbolic-ref --quiet --short HEAD`. Verify exit code 1, indicating
   that HEAD is detached. Confirm that no rebase or bisect is in progress.
8. Run `git-hints --all`. Verify that the detached-HEAD hint appears, explains
   that HEAD points to a commit instead of a named branch, and suggests `git
   switch -c <name>` to preserve future commits. Verify that it includes a link
   to the official Git documentation. Identify the hint by its permanent ID
   rather than exact wording.
9. Run `git switch -c saved-work`.
10. Run `git-hints --all` again. Verify that the detached-HEAD hint is absent
    because HEAD is now attached to `saved-work`.

### Test case 11: Repository has no commits. (Written by drj228)

For Requirement Proactive 15, written by jit45.

1. Call `git_setup()` and create one temporary directory.
2. Initialize a repository in that directory with `git init -b main`.
3. Call `config_user("user1", "user1@example.com")`. Run Git commands as
   argument lists with `shell=False`.
4. Run `git rev-parse --verify HEAD`. Verify that it fails because the
   repository has no commits.
5. Run `git-hints --all`. Verify that the no-commits hint appears and explains
   that the repository has no saved commit yet. Since no files are staged, it
   should not suggest committing yet.
6. Create `foo.txt` containing `xxx` and run `git add foo.txt`.
7. Run `git-hints --all` again. Verify that the no-commits hint now suggests `git
   commit -m "Initial commit"` and includes a link to the official Git commit
   documentation. Identify the hint by its permanent ID rather than exact
   wording.
8. Run `git commit -m "Initial commit"`.
9. Run `git rev-parse --verify HEAD`. Verify exit code 0 and a commit hash in
   the output.
10. Run `git-hints --all` again. Verify that the no-commits hint is absent now
    that the repository contains a commit.

### Test case 12: Commit repo? (Written by jit45) -- Requirement Proactive 13

1. Call `git_setup()` and create one temporary directory.
2. Call `config_user("user1", "user1@example.com")`.
3. Initialize a repository in the temporary directory with `git init -b main`.
4. Create four tracked files named `one.txt`, `two.txt`, `three.txt`, and
   `four.txt`, each containing initial text.
5. Run `git add one.txt two.txt three.txt four.txt`.
6. Run `git commit -m "Add initial files."`.
7. Modify `one.txt` and `two.txt`, leaving both changes unstaged.
8. Create an untracked file named `untracked.txt`.
9. Run `git status --porcelain` and verify that exactly two of the four tracked
   files are changed and that `untracked.txt` appears as untracked.
10. Run `git-hints --all`.
11. Verify that the **Commit repo?** hint is absent because exactly 50% of the
    tracked files are changed. The untracked file must not count toward the
    percentage.
12. Modify `three.txt`, leaving the change unstaged.
13. Run `git status --porcelain` again and verify that three of the four tracked
    files are now changed.
14. Run `git-hints --all`.
15. Verify that the **Commit repo?** hint appears because more than 50% of the
    tracked files have staged, unstaged, or deleted changes relative to HEAD.
16. Verify that the hint suggests reviewing and committing the changes.
17. Identify the hint by its permanent hint ID rather than relying on exact
    displayed wording once the permanent ID is assigned.

### Test case 13: Resolve pull conflicts. (Written by jit45) -- Requirement Reactive 2

1. Call `git_setup()` and create three temporary directories named `remote`,
   `local`, and `other`.
2. Call `config_user("user1", "user1@example.com")`.
3. In `remote`, create a bare repository with `git init --bare -b main`.
4. In `other`, clone the remote repository using `git clone <remote> <other>`.
5. In `other`, create `foo.txt` containing `xxx`.
6. Run `git add foo.txt`.
7. Run `git commit -m "Add foo."`.
8. Run `git push -u origin main`.
9. Clone the remote repository into `local` using `git clone <remote> <local>`.
10. In `local`, modify `foo.txt` by appending `local change`, but do not stage
    or commit the change.
11. In `other`, modify `foo.txt` by appending `remote change`.
12. In `other`, run `git commit -am "Update foo remotely."`.
13. In `other`, run `git push`.
14. In `local`, run `git status --porcelain` and verify that `foo.txt` has an
    uncommitted local modification.
15. In `local`, run `git-hints explain -- git pull`.
16. Verify that the pull fails because the incoming remote change would
    overwrite the uncommitted local change to `foo.txt`.
17. Verify that the **Resolve pull conflicts?** reactive hint appears.
18. Verify that the hint identifies `foo.txt` as an affected file and explains
    how the user can preserve or resolve the local change before pulling again.
19. Verify that the repository still contains the user's uncommitted local
    change after the failed pull.
20. Identify the hint by its permanent hint ID rather than relying on exact
    displayed wording once the permanent ID is assigned.

### Test Case 14: Pull Test (raf322) -- Requirement Proactive 7

1. Call `make_temps(3)` to create three temp directories: `temp1`, `temp2` and
   `remote`. `remote` will act as a shared server between the other two.
2. In `remote`, run `git init --bare -b main`.
3. In `temp1`, execute:
   1. Create a repo with `git init -b main`.
   2. Call `config_user("user1", "user1@foo.com")`.
   3. Create a file called `foo.txt` with the content `xxx`.
   4. Add and commit it with the message `"Add foo."`.
   5. Add the `remote` directory as a remote called `origin`.
   6. Push `main` to `origin` with `git push -u origin main`.
4. In `temp2`, execute:
   1. Clone `remote` into the directory with `git clone <remote> .`.
   2. Call `config_user("user2", "user2@foo.com")`.
   3. Change `foo.txt` so that it contains `xxxy`.
   4. Commit with `git commit -am "Modify foo."` and push with `git push`.
5. Change back to `temp1` and run `git fetch`, so that it learns about the new
   commit on the remote. `temp1` is now 1 commit behind `origin/main`, with no
   commits of its own that the remote lacks and no uncommitted changes.
6. Run `git-hints` in `temp1`. Expected hint: Is my branch up to date before I
   start editing?

### Test Case 15: Branch Behind Test (raf322) -- Requirement Proactive 4

1. Call `make_temps(3)` to create three temp directories: `local1`, `local2` and
   `remote`. `remote` will act as a shared server between the other two.
2. In `remote`, run `git init --bare -b main`.
3. In `local1`, execute:
   1. Create a repo with `git init -b main`.
   2. Call `config_user("user1", "user1@foo.com")`.
   3. Create a file called `foo.txt` with the content `xxx`.
   4. Add and commit it with the message `"Add foo."`.
   5. Add the `remote` directory as a remote called `origin`.
   6. Push `main` to `origin` with `git push -u origin main`.
4. In `local2`, execute:
   1. Clone `remote` into the directory with `git clone <remote> .`.
   2. Call `config_user("user2", "user2@foo.com")`.
   3. Change `foo.txt` so that it contains `xxxy`.
   4. Commit with `git commit -am "Modify foo."`.
   5. Change `foo.txt` so that it contains `xxxyz`.
   6. Commit with `git commit -am "Modify foo again."` and push both commits
      with `git push`.
5. `cd` to `local1` and run `git fetch`, so that it learns about the new commits
   on the remote. `local1` is now 2 commits behind `origin/main`, with no
   commits of its own that the remote lacks and no uncommitted changes.
6. Run `git-hints` in `local1`. Expected hint: Pull needed, your branch is
   behind!
