`git-hints` specification
=========================

`git-hints` is a Python command-line tool that helps Git learners see where they
are and what to do next. Run with no arguments, it inspects the current
repository's state then displays up to three proactive hints (or every hint with
`--all`), ordered from blocking errors through data-loss risks and workflow
suggestions to informational notes. Run as `git-hints explain <git command>`, it
executes the Git command, captures its exit code and standard error, and offers
explanatory hints for failures such as merge conflicts, pulls blocked by
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

   2. `--exclude`: exclude the following list of `git-hint` ids from the
      generated hints.

   3. `git-hints --dismiss <hint-id>`: dismiss a currently triggered hint.
      **Future work. Do not implement.**

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
2. `git-hints def <command>`: display a short definition of the requested Git
   command, explain what it does, and provide a link to the official Git
   documentation. If the command is unknown, report that it is unsupported.
   (jit45) **Future work. Do not implement.**

3. `git-hints howto <task>`: give step-by-step instructions for supported tasks
   such as committing, pulling, and pushing. If the requested task is unknown,
   report that it is unsupported instead of generating unverified instructions.
   (jit45) **Future work. Do not implement.**

4. `git-hints explain <git command>`: execute the specified Git command and
   capture its exit code and standard error. Use this information to select an
   appropriate reactive hint. Standard output should remain connected to the
   terminal so commands that open an interactive editor continue to function
   normally. The tool cannot reliably recover the result of a Git command that
   was run outside the tool. (drj228)

5. `git-hints [explain] --bug <user comments explaining why the hint was
   wrong>`: Gather the current repo state and (for `explain`) git command output
   then post an issue in the Github repo. **Future work. Do not implement.**

6. Typer automatically generates `--help` for commands and subcommands. Each
   command and subcommand docstring must include at least one usage example so
   the generated help is useful. Examples should use the complete command names,
   such as `git-hints def status` and `git-hints howto commit`. (jit45)

<h2 id="cc-SbouyCXTsP">Hint structure</h2>

1. Each actionable hint must show the terminal command and explain its expected
   result. The initial implementation will support the CLI. If a GUI is added
   later, show the equivalent GUI action alongside the terminal command. (ewj55;
   clarified by drj228)

2. Each hint should include a 1-sentence breakdown of what Git stage the user is
   currently in (Working in the directory, staging area, local repo, or remote),
   so the user learns the Git mental model while working (ewj55)

3. Every hint about a specific task and command links to the official docs for
   more information (ewj55)

4. Maybe highlight sections from the docs to show where that specific hint came
   from (ewj55) **TODO: ewj55 will clarify.**

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

   2. Data-loss risk: warnings associated with potentially destructive or highly
      destructive actions.

   3. Workflow: actionable next-step suggestions based on repository state.

   4. Informational: status or explanatory guidance that does not block work.

   If two triggered hints have the same priority class, order them by their
   permanent hint ID.

7. Give every hint one safety level, shown in its output. **Safe**: read-only or
   only adds (no label). **Potentially destructive**: recoverable through the
   reflog (prefix "Caution:"). **Highly Destructive**: can lose work the reflog
   cannot restore (uncommitted changes, untracked files, others' remote
   commits), e.g. `reset --hard`, `clean -fd`, `push --force` (prefix
   "Warning:", say what will be lost, and tell the user to back up first).
   (sbe80; edited by jhg246) **(sbe80 will remove/clarify)**

8. Every hint must have a unique, permanent text ID, such as `diverged`,
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

  Git stage: Your edits are in the working directory; Git won't put them in a
  commit until you stage them.

  Command: `git add <files to stage>`; afterward, `git status` lists these files
  under "Changes to be committed."

* ID: `unstaged-changes`, priority class: workflow, safety: safe.

* Conditions: Unstaged edits to tracked files exist in the repository. Run `git
  diff --quiet`; an exit code of 0 means no unstaged edits; 1 means there are
  unstaged edits; other return codes indicate an error.

* Test case:

  1. Perform `git_setup()`.
  2. Create one temp directory.
  3. Execute the following in this temp directory:
     1. Call `config_user("user1", "user1@foo.com")`.
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

#### <mark>TODO: each of the following hints should be rewritten to follow the above hints.</mark>

2. Keep unstaged changes out of this commit? Conditions: both staged and
   unstaged changes exist. Explain that a plain `git commit` records staged
   changes, so unrelated edits can remain unstaged without being discarded.
   Suggest
   [git diff --cached](https://git-scm.com/docs/git-diff "Shows the staged changes selected for the next commit.")
   to review the staging area before committing. (drj228) **sbe80 will test**

3. Push? Conditions: the local branch has commits that have not been pushed to
   the remote branch. **test ewj55**

4. Pull needed, your branch is behind! Conditions: the local branch is one or
   more commits behind its upstream branch. (jhg246) **raf322 will test**

5. Place these files in gitignore? Conditions: Files such as \_\_pycache\_\_/,
   output build directories, etc. should be flagged. Suggest that the user
   create a .gitignore file and slate those files for entry. Suggest `git rm
   --cached` if user wants to unstage a file from the commit. (raf322)

6. Clone a repo? Conditions: the current directory is not inside a Git
   repository. Use `git rev-parse --is-inside-work-tree` to determine whether
   the current directory is inside a Git working tree. If the command exits with
   code 0 and prints `true`, the directory is inside a Git working tree. If it
   exits with code 128, it is not inside a Git repository. If it is not inside a
   repository, suggest using `git clone <repository-url>` to create a local copy
   of an existing remote repository. **test ewj55**

7. Is my branch up to date before I start editing? Conditions: the current
   branch has an upstream branch and is behind it by one or more commits while
   not being ahead of it. Detect the state with `git status -sb` using the
   latest locally known remote-tracking information. Explain that the local
   branch does not contain the newest known remote commits and suggest `git
   pull` before beginning new work. Make clear that this status is only as
   current as the most recent fetch. (jhg246; adapted from jit45 personal
   experience) **jhg246 and raf322 will test**

8. Current branch? Condition: three other hints are not in use. Detect the
   current branch using `git branch --show-current`. Display the current branch
   to the user as a hint until overwritten. (sbe80).

9. Configure upstream branch? Condition: if the current branch does not have an
   upstream remote branch configured. Detect with `git rev-parse --abbrev-ref
   --symbolic-full-name @{upstream}` and suggest setting one before attempting
   to push. **ams2083 will test**

10. Review staged changes before committing? Conditions: the staging area
    contains changes ready for a commit. Suggest `git diff --cached` so the user
    can check exactly what will be committed and unrelated edits can remain
    unstaged without being discarded. Suggest `git commit   -m    "message"` to
    create a new commit containing the desired staged changes so the user can
    commit them when they are satisfied. (drj228) **sbe80 will test**

11. Configure your commit identity? Conditions: `user.name` or `user.email` is
    missing or empty in the effective Git configuration. Explain how to set the
    missing value using `git config --global user.name "Your Name"` or `git
    config --global user.email "you@example.com"`.

    The `--global` option sets the default for all repositories belonging to the
    current user. Use `--local` inside a repository to configure an identity for
    that repository only. Local settings override global settings. An empty
    local override should be corrected locally. These settings identify commit
    authors; they do not sign the user into GitHub. (drj228)

12. Untracked files need to be sorted? Conditions: one or more untracked files
    exist in the working directory. Detect untracked files with `git    status
    --porcelain`. If an untracked file should normally be ignored, such as .env,
    **pycache**.py, output build files, and directories, suggest adding it to
    .gitignore. If an ordinary untracked file exists, suggest `git add filename`
    to move the file into the staging area. (ams2083)

13. Commit repo? Conditions: More than 50% of the repository's tracked files
    have staged, unstaged, or deleted changes relative to HEAD. Use
    `git    status --porcelain` to identify changed tracked files and compare
    that number to the total number of tracked files. Untracked files should be
    handled separately and should not count toward this percentage. If more than
    half of the tracked files have changes, suggest reviewing and committing the
    changes. (jit45) **jit45 will test**

14. Detached HEAD state? Conditions: the repository exists, HEAD is not attached
    to a local branch, and Git is not currently performing a rebase or bisect
    operation. Explain that the user is working in the local repository at a
    specific commit instead of on a named branch. Suggest `git switch -c <name>`
    to create and switch to a new branch if the user wants to preserve future
    commits. (jit45) **drj228 will test**

15. This repository does not have any commits yet? Conditions: the current
    directory is a Git repository, but HEAD does not yet resolve to a commit.
    Use `git rev-parse --verify HEAD` to confirm and explain that the local
    repository has no saved commit yet. If files are staged, suggest
    `git    commit -m "Initial commit"` to create the first commit. (jit45)
    **drj228 will test**

16. Branch has diverged from upstream? Conditions: the local branch is both
    ahead and behind its upstream branch. Suggest
    [git pull](https://git-scm.com/docs/git-pull "Fetches and integrates remote commits; --rebase replays yours on top of them.")
    or `git pull --rebase`, then
    [git push](https://git-scm.com/docs/git-push "Uploads local commits to the remote branch.").
    (sbe80; edited by jhg246) **jhg246 will test.**

17. Committing to protected/main branch? Conditions: the current branch is
    master/main and there are changes. If other branches exist, suggest other
    branches. If no other branches exist, suggest creating a new branch with
    `git switch -c <name>`. (raf322)

### `git-hints explain <git command>`

Reactive hints are triggered by the result of a Git command executed through
`git-hints explain`. (jit45)

1. Resolve merge conflicts? Conditions: a Git command executed through
   `git-hints explain` leaves the repository with unresolved merge conflicts.
   Identify the conflicting files and explain how to resolve them. **sbe80 will
   test**

2. Resolve pull conflicts? Conditions: `git-hints explain pull` fails because
   local uncommitted changes would be overwritten. Identify the affected files
   and explain how to preserve or resolve the local changes. **jit45 will test**

3. Push failed? Conditions: `git-hints explain push` fails because the remote
   branch contains commits that are not present in the local branch. Explain
   that the user should integrate the remote changes before attempting to push
   again. (jhg246)

4. Explain
   [stashes](https://www.geeksforgeeks.org/git/git-stash/ "Stores the present state of the local repo")
   including: what they are, how to make one, and how to see old ones.
   Condition: a command executed through `git-hints explain` reports a conflict
   where temporarily setting aside local changes would help. (sbe80)

5. Suggest and explain
   [git pull --rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) if
   five failed `git pull` or `git push` commands have been executed through
   `git-hints explain` in a row. Explain that rebasing may cause merge conflicts
   and that the user should ensure their local work is committed or otherwise
   backed up before proceeding. (sbe80).

### Language and libraries:

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

5. Incoming changes: `git diff --name-only HEAD...@{upstream}` lists the files a
   pull would bring in (needs an upstream). Conflicting files, once a merge has
   stopped: `git diff --name-only --diff-filter=U`. Fetch policy (ahead/behind
   checks): never fetch by default; label results "as of last fetch". `git-hints
   --fetch` runs `git fetch` first, with `GIT_TERMINAL_PROMPT=0` and a timeout.
   (jhg246

6. Staged changes are ready to commit: run `git diff --cached --quiet`. Exit
   code 1 means staged differences exist; exit code 0 means there are none.
   Treat other exit codes as errors instead of triggering the hint. This detects
   the condition for the staged-review hint. (drj228)

7. Commit identity is not configured: run `git config --get user.name` and `git
   config --get user.email`. An exit code of 1 indicates that the requested
   setting is missing. Also check for an empty returned value. Report other
   command failures separately. These checks use the effective configuration,
   including repository and global settings. (drj228)

8. Untracked files exist: run `git status --porcelain`. Lines beginning with
   `??` indicate files that Git sees in the working directory but isn't
   currently tracking. (ams2083)

9. HEAD is detached rather than attached to a local branch: run `git
   symbolic-ref --quiet --short HEAD`. A zero exit code means HEAD is attached
   to a branch and the command prints the branch name. A non-zero exit code in
   an otherwise valid Git repository means HEAD is detached.

   Before triggering the detached-HEAD hint, also verify that Git is not
   currently performing a rebase or bisect. Check the paths returned by `git
   rev-parse --git-path rebase-merge`, `git rev-parse --git-path rebase-apply`,
   and `git rev-parse --git-path BISECT_START`.

   If any corresponding operation state exists, suppress the detached-HEAD hint.
   (jit45)

10. Committing to main/master: Run `git branch --show-current` to identify
    current branch. If the branch is main, check for other remote/active
    branches with `git for-each-ref --format='%(refname:short)'
    refs/heads   refs/remotes`. If the list contains no other branches besides
    the protected branch(es), suggest the creation of a new branch. Otherwise,
    suggest other branches on the list. (raf322)

11. Run `git status -sb`. If the status reports that the local branch is ahead
    *and* behind its upstream branch, the branches have diverged. (sbe80)

12. The `git-hints explain` command must pass Git arguments through without
    Typer attempting to parse them as options. Configure the command to allow
    extra arguments and ignore unknown options (for example, using
    allow\_extra\_args=True and ignore\_unknown\_options=True) so commands such
    as `git-hints explain pull --rebase` and `git-hints explain reset   --hard
    HEAD~1` are passed to Git correctly (sbe80).

13. The `git-hints explain` command should not require the word `git` after the
    word `explain`. (sbe80)

Testing
-------

The test tool contains:

* `make_temps(num)`: creates and returns `num` temporary directories. These are
  removed when the test completes.
* `make_repo(temp_dir, commands)`: runs the list of `commands` in `temp_dir` to
  create and populate the repository. Each command is either an argument list,
  such as `["git", "commit", "-m", "Add foo."]`, executed using
  `subprocess.run()` with `shell=False`, or a lambda function with no parameters
  used to create, modify, or delete files. Pass each argument separately and
  keep messages containing spaces in a single list element. Do not join
  arguments into a shell string. (drj228)
* `config_user(username, email)`: Set Git's `user.name` and `user.email`.
* `git_setup()`: creates an isolated Git configuration for the test environment.
  The test environment shall:
  * use an empty temporary file for GIT\_CONFIG\_GLOBAL so that the user's
    global Git configuration does not affect test results
  * set GIT\_CONFIG\_NOSYSTEM=1 so that the system Git configuration does not
    affect test results
  * provide Git author and committer identity through environment variables so
    that tests do not depend on the machine's configured identity
  * initialize test repositories with git init -b main so that tests do not
    depend on the machine's init.defaultBranch setting.

A typical test would make temporary directories, then use these to make repos,
then set remotes. After changing to the local repo temp dir, it runs git-hints
and checks that the output is correct.

All Git commands executed as part of a test shall use the isolated test
environment established by git\_setup(). This prevents test results from varying
based on the Git configuration of the machine running the tests.

### <mark>TODO: move test cases to follow the implementation of each hint.</mark>

### Test case 2: files are changed. (Written by sbe80) -- Requirement Proactive 2

1. Create one temporary directory.
2. Execute the following in this temporary directory:
   1. Call `config_user("user1", "user1@foo.com")`.
   2. Create an empty git repo with `git init -b main`.
   3. Create a file called `foo.txt` with the content `xxx`.
   4. Add it: `git add foo.txt`.
   5. Commit it: `git commit -m "Add foo."`.
   6. Modify `foo.txt`: append `y` to it.
   7. Stage the modification: `git add foo.txt`.
   8. Modify `foo.txt` again: append `z` to it, leaving this second modification
      unstaged.
3. Run `git-hints` in the temporary directory.
4. Expected hint: **Keep unstaged changes out of this commit?**
5. Verify that the output explains that a plain `git commit` records only the
   staged changes and suggests
   [`git diff --cached`](https://git-scm.com/docs/git-diff "Show changes staged for the next commit").

### Test case 3: Resolving merge conflicts. (Written by sbe80) -- Requirement Reactive 1

1. Create two temporary directories.
2. Execute the following in the first temporary directory:
   1. Call `config_user("user1", "user1@foo.com")`.
   2. Create an empty git repo with `git init -b main`.
   3. Create a file called `foo.txt` with the content `xxx`.
   4. Add it: `git add foo.txt`.
   5. Commit it: `git commit -m "Add foo."`.
3. Clone the first repo into the second using `git clone <temp_dir1>
   <temp_dir2>`
4. In repo 1, add `y` to `foo.txt` and commit
5. In repo 2, add `z` to `foo.txt` and commit
6. Run `git pull` in the first repo
7. Run git-hints in the first repository. Expected hint: Resolve merge
   conflicts? The output should identify foo.txt as a conflicting file and
   explain how to resolve the conflict.

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

### Test Case 6: Pull needed, Branch is behind (jhg246) For Requirement Proactive 7

Run in one PowerShell terminal (`$t` and the helpers must persist). Setup, steps
1-5:

```powershell
$env:GIT_CONFIG_GLOBAL=(New-TemporaryFile).FullName; $env:GIT_CONFIG_NOSYSTEM=1   # git_setup()
$env:GIT_AUTHOR_NAME=$env:GIT_COMMITTER_NAME="user1"; $env:GIT_AUTHOR_EMAIL=$env:GIT_COMMITTER_EMAIL="user1@foo.com"   # config_user()
$t=(New-Item -ItemType Directory (Join-Path ([IO.Path]::GetTempPath()) "t-$(Get-Random)")).FullName
function g($d) { git -C "$t/$d" @args }; function ab { g local status --porcelain=v2 --branch | Select-String branch.ab }; function hints { Push-Location "$t/local"; git-hints; Pop-Location }
New-Item -ItemType Directory "$t/remote","$t/local","$t/other" | Out-Null; g remote init --bare -b main
git clone "$t/remote" "$t/other"; Set-Content "$t/other/foo.txt" xxx; g other add foo.txt; g other commit -m "Add foo."; g other push -u origin main
git clone "$t/remote" "$t/local"; Add-Content "$t/other/foo.txt" y; g other commit -am "Change foo."; g other push
```

Checks. Step 6: `ab; hints`: `+0 -0`, no `behind` hint (no fetch yet). Step 7:
`g local fetch; ab; hints`: `+0 -1`; **Is my branch up to date before I start
editing?** (ID `behind`), labeled "as of last fetch"; no `diverged` or **Push?**
hint.

### Test case 7: Branch has diverged. (jhg246) -- For Requirement Proactive 16

Run Test 6's setup block only (a fetch beforehand would change step 3), then:

```powershell
Set-Content "$t/local/bar.txt" zzz; g local add bar.txt; g local commit -m "Add bar."   # 2
ab; hints   # 3: +1 -0, Push? shown, diverged not shown
g local fetch; ab; hints   # 4: +1 -1
```

Step 4 expected: **Your branch has diverged from upstream.** (ID `diverged`),
suggesting `git pull` or `git pull --rebase`, then `git push`, with a
[git pull](https://git-scm.com/docs/git-pull "Fetches and integrates remote commits; --rebase replays yours on top of them.")
link. No `behind` or **Push?** hint.

### Test case 8: Push Failed. (ams2083) -- Requirement Reactive 3

1. Call `git_setup()`. Create three temporary directories: `remote`, `local`,
   and `other`.
2. Call `config_user("user1", "user1@foo.com")`.
3. In `remote`, create a bare repository with `git init --bare -b main`.
4. In `other`, clone the `remote` repository using `git clone <remote> <other>`.
5. In `other`:
   1. Create `foo.txt` containing `xxx`.
   2. Run `git add foo.txt`.
   3. Run `git commit -m "Add foo."`.
   4. Run `git push -u origin main`.
6. Clone the `remote` repository into `local` using `git clone <remote>
   <local>`.
7. In other, modify `foo.txt`, commit the change, and push it to the remote:
   1. Append `y` to foo.txt.
   2. Run `git commit -am "Update foo."`.
   3. Run `git push`.
8. In `local`, create a different `local` commit without first pulling the newer
   remote commit:
   1. Create `bar.txt` containing `zzz`.
   2. Run `git add bar.txt`.
   3. Run `git commit -m "Add bar."`.
9. Run `git-hints explain push` in the `local` repository.
10. Confirm that the push fails because the `remote` branch contains commits
    that are not present in the `local` branch.
11. Expected hint: *Push failed?*
12. Verify that the hint explains that `remote` contains newer commits and
    suggests [pulling](https://git-scm.com/docs/git-pull) with `git pull` before
    attempting to [push](https://git-scm.com/docs/git-push) with `git push`
    again.

### Test case 9: Configure upstream branch. (ams2083) -- Requirement Proactive 9

1. Call `git_setup()`. Create one temporary directory.
2. Call `config_user("user1", "user1@foo.com")`.
3. In the temporary directory, create a Git repository with `git init -b main`.
4. Create `foo.txt` containing `xxx`.
5. Run `git add foo.txt`.
6. Run `git commit -m "Add foo."`.
7. Create and switch to a new local branch using `git switch -c feature-test`.
8. Do not configure an upstream remote branch for `feature-test`.
9. Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` and verify
   that the command fails because no upstream is configured.
10. Run `git-hints` in the local repository.
11. Expected hint: *Configure upstream branch?*
12. Verify the hint explains `feature-test` exists only as a local branch and
    [doesn't track](https://git-scm.com/docs/git-rev-parse/2.27.0) an upstream
    remote branch.
13. Verify that the hint suggests configuring an upstream branch before
    attempting to push.

### Test case 10: Detached HEAD state. (Written by drj228)

For Requirement Proactive 14, written by jit45.

1. Call `git_setup()` and create one temporary directory.
2. Initialize a repository in that directory with `git init -b main`.
3. Call `config_user("user1", "user1@example.com")`.
4. Create `foo.txt` containing `xxx`, stage it, and commit it. Run Git commands
   as argument lists with `shell=False`.
5. Run `git-hints all`. Verify that the detached-HEAD hint is absent while HEAD
   is attached to `main`.
6. Run `git switch --detach HEAD`.
7. Run `git symbolic-ref --quiet --short HEAD`. Verify exit code 1, indicating
   that HEAD is detached. Confirm that no rebase or bisect is in progress.
8. Run `git-hints all`. Verify that the detached-HEAD hint appears, explains
   that HEAD points to a commit instead of a named branch, and suggests `git
   switch -c <name>` to preserve future commits. Verify that it includes a link
   to the official Git documentation. Identify the hint by its permanent ID
   rather than exact wording.
9. Run `git switch -c saved-work`.
10. Run `git-hints all` again. Verify that the detached-HEAD hint is absent
    because HEAD is now attached to `saved-work`.

### Test case 11: Repository has no commits. (Written by drj228)

For Requirement Proactive 15, written by jit45.

1. Call `git_setup()` and create one temporary directory.
2. Initialize a repository in that directory with `git init -b main`.
3. Call `config_user("user1", "user1@example.com")`. Run Git commands as
   argument lists with `shell=False`.
4. Run `git rev-parse --verify HEAD`. Verify that it fails because the
   repository has no commits.
5. Run `git-hints all`. Verify that the no-commits hint appears and explains
   that the repository has no saved commit yet. Since no files are staged, it
   should not suggest committing yet.
6. Create `foo.txt` containing `xxx` and run `git add foo.txt`.
7. Run `git-hints all` again. Verify that the no-commits hint now suggests `git
   commit -m "Initial commit"` and includes a link to the official Git commit
   documentation. Identify the hint by its permanent ID rather than exact
   wording.
8. Run `git commit -m "Initial commit"`.
9. Run `git rev-parse --verify HEAD`. Verify exit code 0 and a commit hash in
   the output.
10. Run `git-hints all` again. Verify that the no-commits hint is absent now
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
10. Run `git-hints all`.
11. Verify that the **Commit repo?** hint is absent because exactly 50% of the
    tracked files are changed. The untracked file must not count toward the
    percentage.
12. Modify `three.txt`, leaving the change unstaged.
13. Run `git status --porcelain` again and verify that three of the four tracked
    files are now changed.
14. Run `git-hints all`.
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
15. In `local`, run `git-hints explain pull`.
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
