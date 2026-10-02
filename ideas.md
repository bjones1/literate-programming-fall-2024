Ideas
=====

This file records the initial design of the git-hints tool.

<h2 id="cc-Xi1o6gL4Lb">Requirements</h2>

1. The tool will be initially implemented using a CLI for command-line use of
   Git.

2. The tool should offer hints in the following categories: <mark>\[Homework:
   add to this list. Include your netid to identify portions you
   contributed.\]</mark>

   1. Reactive

      1. [Stage](https://www.w3schools.com/git/git_staging_environment.asp "Also called the index; select which files changes to store in a commit")
         files? Conditions: changed files in repo. <mark>\[Homework: for each
         hint, follow the format discussed in [item 3](#cc-SbouyCXTsP) under
         requirements and exemplified here.\]</mark> **bj147 will test.**
      2. Keep unstaged changes out of this commit? Conditions: both staged and
         unstaged changes exist. Explain that a plain `git commit` records
         staged changes, so unrelated edits can remain unstaged without being
         discarded. Suggest
         [git diff --cached](https://git-scm.com/docs/git-diff "Shows the staged changes selected for the next commit.")
         to review the staging area before committing. (drj228) **sbe80 will
         test**
      3. Resolve merge conflicts? Conditions: a git pull fails because of merge
         conflicts, identify the conflicting files and explain how to resolve
         them. **sbe80 will test**
      4. Resolve pull conflicts? Conditions: if a git pull fails because of
         uncommitted changes, identify the conflicting files and explain how to
         resolve them.
      5. Push? Conditions: the local branch has commits that have not been
         pushed to the remote branch. **test ewj55** 
      6. Pull needed, your branch is behind! Conditions: If the user is a 1 or
         more commits behind on the current branch. (jhg246)
      7. Push failed because of conflicting file changes. Try running git diff
         *'filename'* ! Conditions: If the user attempted a push and it failed
         due to conflicting file changes. (jhg246)
      8. Explain
         [stashes](https://www.geeksforgeeks.org/git/git-stash/ "Stores the present state of the local repo")
         including: what they are, how to make one, and how to see old ones
         Condition: conflict when pulling (sbe80)<br>
      9. Place these files in gitignore? Conditions: Files such as .env,
         \_\_pycache\_\_.py, output build directories, etc. should be flagged.
         Suggest that the user create a .gitignore file and slate those files
         for entry. (raf322)<br>
      10. Suggest and explain
          [git pull --rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)
          if the user has five failed git pull or git push commands in a row.
          Explain that rebasing may cause merge conflicts and that the user
          should ensure their local work is committed or otherwise backed up
          before proceeding. (sbe80).
   
   
   2. Proactive

      1. Clone a repo? Conditions: the current directory is not inside a Git repository. Use`git rev-parse --is-inside-work-tree` to [parse through parameters](https://git-scm.com/docs/git-rev-parse/2.9.5). If the command exits with code 0 and prints `true`, the directory is inside a Git working tree. If it exits with code 128, its not inside a Git repository. If it's not inside a repository, suggest using `git clone <repository-url>` to create a local copy of an existing remote repository.
      **test ewj55**

      2. Pull remote changes? Conditions: Your local branch is behind its upstream branch by one or more commits and is not ahead of the upstream branch. Detect [status](https://git-scm.com/docs/git-status) with `git status -sb`. Suggest git pull to bring the remote commits into your local repository. **jhg246 will test**


      3. Current branch? Condition: three other hints are not in use. Detect the [current branch](https://git-scm.com/docs/git-show) using `git branch --show-current`. Display the current branch to the user as a hint until overwritten. (sbe80).

      
      4. Configure upstream branch? Condition: if the current branch does not
         have an upstream remote branch configured. [Detect](https://git-scm.com/docs/git-rev-parse/2.27.0) with `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` and suggest
         setting one before attempting to push.**ams2083 will test**
      
      5. File states and read-only mode? Conditions: When attempting to edit a file opened in a commit or different view. Suggest explaining
         [file states](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F "Files in Git move between modified, staged, and committed states.")
         and editor read-only [modes](https://git-scm.com/docs/git-status) by using `git status` to show the file's designation. (ewj55)

      




      
      6. Review staged changes before committing? Conditions: the staging area
         contains changes ready for a commit. Suggest
         [git diff --cached](https://git-scm.com/docs/git-diff "Shows the staged changes that will be included in the next commit.")so the user can check exactly what will be committed and unrelated edits can remain unstaged without being discarded. 
         Suggest [git commit](https://git-scm.com/docs/git-commit "Creates a new commit from staged changes.")
         with `git commit -m "message"` to create a new commit containing the desired staged changes so the user can commit them when they're satisfied. (drj228) **sbe80 will test**

      7. Configure your commit identity? Conditions: `user.name` or `user.email`
         is missing or empty in the effective Git configuration. Explain how to
         set the missing value using
         [git config](https://git-scm.com/docs/git-config "Reads and updates Git settings.")
         with `git config --global user.name "Your Name"` or
         `git config --global user.email "you@example.com"`.

         The `--global` option sets the default for all repositories belonging to
         the current user. Use `--local` inside a repository to configure an
         identity for that repository only. Local settings override global
         settings. An empty local override should be corrected locally.These settings identify commit authors; they do not sign the user into GitHub. (drj228) 

      
      8. Untracked files need to be sorted? Conditions: one or more untracked files exist in working directory. 
      First, detect untracked files with `git status --porcelain` before explaining Git can see the files but isn't tracking their changes. If an untracked file should normally be ignored such as .env, \_\_pycache\_\_.py, output build, and directories, suggest that the user create a .gitignore file and slate those files for entry. If an ordinary untracked file exists, suggest
          [git add](https://git-scm.com/docs/git-add "Adds file contents to the staging area.")
          with `git add filename` to move the file into the staging area(ams2083)

      
      
      
      9. Commit repo? Conditions: Repo has been changed by more than 50% (untracked files, lines of
          code, deleted files, etc.). Using `git status --porcelain` to [identify](https://git-scm.com/docs/git-status) these files and compare the number to the total number of tracked files. Suggest committing these changes if untracked exceeds 50%.

      10. Stuck? Conditions: User has made little to no changes over a set amount of time. Implement a timer to check how much progress the user has made. Compare repository [state](https://git-scm.com/docs/git-status) using `git status --porcelain`, and if the repo has
          little to no changes over a set amount of time, that means the user is
          most likely stuck.

      11. Detached HEAD state? Conditions: the repository exists,
          but HEAD is not attached to a local branch. Explain that the user is
          working in the local repository at a specific commit instead of on a
          named branch. Suggest
          [git switch -c](https://git-scm.com/docs/git-switch "Creates a new branch and switches to it.")
          to create and switch to a new branch if the user wants to preserve
          future commits. (jit45) **drj228 will test**

      12. This repository does not have any commits yet? Conditions: the current
          directory is a Git repository, but HEAD does not yet resolve to a
          commit. Use `git rev-parse --verify HEAD` to confirm and explain that the local repository has no saved commit yet. If
          files are staged, suggest
          [git commit -m "Initial commit"](https://git-scm.com/docs/git-commit "Creates a new commit from the staged changes.")
          to create the first commit. (jit45) **drj228 will test**

      13. Branch has diverged from upstream? Conditions: the local branch is both ahead and behind its upstream branch. Suggest [git pull](https://git-scm.com/docs/git-pull "Fetches and integrates remote commits; --rebase replays yours on top of them.")
          or `git pull --rebase`, then `git push`. (sbe80; edited by jhg246)
          **jhg246 will test.**

      14. Committing to protected/main branch? Conditions: the current branch is
          master/main and there are changes. If other branches exist, suggest
          other branches. If no other branches exist, suggest creating a [new branch](https://git-scm.com/docs/git-switch) with `git switch -c <name>` (raf322)
   
   3. Definitions

      1. Allow users to request a definition using `git-hints def <command>`.
         The tool should display a short definition of the requested Git
         command, explain what it does, and provide a link to the official Git
         documentation. If the command is unknown, report that it is
         unsupported. (jit45)
      2. Add a `--help` comand which details use of the `hints def` command
         (sbe80).
   4. How to

      1. Provide a `git-hints howto <task>` command that gives step-by-step
         instructions for supported tasks such as committing, pulling, and
         pushing. If the requested task is unknown, tell the user it is
         unsupported instead of generating unverified instructions. (jit45)
      2. Add a `--help` comand which details use of the `hints howto` command
         (sbe80)
   5. Explain error: git-hints explain executes the specified Git command and
      captures its exit code and standard error. The tool uses this information
      to select an appropriate hint. Standard output is not captured so that
      commands that open an interactive editor (such as git commit without -m or
      git rebase -i) continue to function normally. The tool cannot reliably
      recover the result of a Git command that was run outside the tool.
      (drj228)
3. <a id="cc-SbouyCXTsP"></a>Hint structure:

   1. Each actionable hint must show the terminal command and explain its
      expected result. The initial implementation will support the CLI. If a GUI
      is added later, show the equivalent GUI action alongside the terminal
      command. (ewj55; clarified by drj228)
   2. Each hint should include a 1-sentence breakdown of what Git stage the user
      is currently in (Working in the directory, staging area, local repo, or
      remote), so the user learns the Git mental model while working (ewj55)
   3. Every hint about a specific task and command links to the official docs
      for more information (ewj55)
   4. Maybe highlight sections from the docs to show where that specific hint
      came from (ewj55)
   5. Hints must consist of Markdown text. Each documentation link must
      include a title summarizing the linked term or command, limited to
      160 characters. Put longer explanations in the linked documentation.

      The initial CLI will display hints as plain text, converting Markdown
      links into their label, URL, and title text. For example:
      Git status — Shows the working tree and staging-area status.
      Documentation: https://git-scm.com/docs/git-status

      Descriptions must be visible in the terminal without hovering over
      a link. (drj228)
4. Hint algorithms:

   1. Display at most three hints at once. If additional hints have their
      conditions met, inform the user that more are available. Provide a
      `git-hints all` command that displays every currently triggered hint.
      (jit45)

   2. Prioritize hints that explain a failed command or an unresolved merge
      conflict before routine workflow suggestions. Display no more than three
      hints at once. Users may dismiss a currently triggered hint with
      `git-hints dismiss <hint-id>`.

      Save the hint ID and the values used to detect its condition in
      `git-hints/dismissals.json` inside the repository's Git directory.
      Exclude dismissed hints from normal output and `git-hints all` while
      those values remain unchanged.

      Clear the dismissal when those values change or when the tool observes
      that the condition no longer exists. Show the hint again only if its
      condition applies. Unrelated repository changes do not clear a dismissal.
      For example, configuring a missing user name while the email is still
      missing allows the commit-identity hint to appear again.
      (ewj55; clarified by drj228 and jit45)

   3. All hints should be given a priority, with higher priority hints being
      displayed first (sbe80)

   4. Give every hint one sefety level, shown in its output. *Safe*: read-only
      or only adds (no label). *Potentially destructive*: recoverable through
      the reflog (prefix "Caution:"). *Highly Destructive*: can lose work the
      reflog cannot restore (uncommitted changes, untracked files, others'
      remote commits), ex. `reset --hard`, `clean -fd`, `push --force` (prefix
      "Warning:", say what will be lost, and tell the user to back up first).
      (sbe80; edited by jhg246)

   5. Every hint must have a unique, permanent text ID, such as `diverged`,
      `push-ahead`, or `commit-identity`. IDs must not depend on list positions or displayed wording. Display the ID with each hint and use it for dismissal commands and test assertions. Each hint must define the condition values recorded when it is dismissed.
      (sbe80; clarified by drj228)

5. Estimate user intent:

   1. Infer likely user intent from observable repository state and commands
      executed through the tool. If the available Git state does not provide
      enough evidence, do not guess the user's intent. (jit45)

Implementation
--------------

1. Determining git/repo conditions: <mark>\[Homework: add to this section.
   Include a condition from the <xref ref="cc-Xi1o6gL4Lb"></xref> section,
   followed by which Git command produces this information. See the example in
   item 1 below.\]</mark>

   1. Changed files: `git status`.

   2. A Git command executed through `git-hints explain` failed: run the
      command using `subprocess.run()` with an argument list, `shell=False`,
      and `check=False`. Capture standard error and inspect `returncode`.
      Leave standard input and standard output connected to the terminal
      so interactive commands can operate normally. Use the command,
      exit code, and standard error to select an appropriate hint.
      The tool cannot reliably recover the result of an earlier command
      run outside the tool. (drj228)

   3. The local branch has commits that have not been pushed to the remote
      branch: run `git status -sb`. If the branch status shows that the local
      branch is ahead of its upstream branch by one or more commits, then local
      commits exist that are not yet public.

   4. Determine whether the current directory is inside a Git working tree:
      run `git rev-parse --is-inside-work-tree` using `subprocess`.
      Exit code 0 with output `true` confirms a working tree. If the command
      fails, inspect standard error to distinguish a directory outside a
      repository from other Git errors. Do not treat every failure as a
      reason to suggest cloning. (sbe80; clarified by drj228)

   5. Incoming changes: `git diff --name-only HEAD...@{upstream}` lists the
      files a pull would bring in (needs an upstream). Conflicting files, once a
      merge has stopped: `git diff --name-only --diff-filter=U`. Fetch policy
      (ahead/behind checks, items 3 and 12): never fetch by default; label
      results "as of last fetch". `git-hints --fetch` runs `git fetch` first,
      with `GIT_TERMINAL_PROMPT=0` and a timeout. (jhg246

   6. Staged changes are ready to commit: run `git diff --cached --quiet`. Exit
      code 1 means staged differences exist; exit code 0 means there are none.
      Treat other exit codes as errors instead of triggering the hint. This
      detects the condition for the staged-review hint. (drj228)

   7. Commit identity is not configured: run `git config --get user.name` and
      `git config --get user.email`. An exit code of 1 indicates that the
      requested setting is missing. Also check for an empty returned value.
      Report other command failures separately. These checks use the effective
      configuration, including repository and global settings. (drj228)

   8. Untracked files exist: run `git status --porcelain`. Lines beginning with
      `??` indicate files that Git sees in the working directory but isn't
      currently tracking. (ams2083)

   9. HEAD is detached rather than attached to a local branch: run `git
       symbolic-ref --quiet --short HEAD`. A zero exit code means HEAD is
       attached to a branch and the command prints the branch name. A non-zero
       exit code in an otherwise valid Git repository indicates that HEAD is
       detached. This detects the condition for the detached HEAD hint. (jit45)

   10. Committing to main/master: Run  `git branch --show-current` to identify
       current branch. If the branch is main, check for other remote/active
       branches with `git branch -a`. If the list contains no other branches
       besides the protected branch(es), suggest the creation of a new branch.
       Otherwise, suggest other branches on the list.(raf322)

   11. Run `git status -sb`. If the status reports that the local branch is
       ahead *and* behind its upstream branch, the branches have diverged. 
       (sbe80)
  
   12. The explain command (Requirement 5) must pass Git arguments through
       without Typer attempting to parse them as options. Configure the command
       to allow extra arguments and ignore unknown options (for example, using
       allow\_extra\_args=True and ignore\_unknown\_options=True) so commands
       such as `git-hints explain pull --rebase` and `git-hints explain reset
       --hard HEAD~1` are passed to Git correctly (sbe80).

   13. The explain command (Requirement 5) should not require the word `git`
       after the word `explain`. (sbe80)
2. Language and libraries:

   1. Language: Python
   2. Package manager: uv
   3. Formatter/linter: ruff
   4. Type checker: ty
   5. CLI: Typer
   6. Git interface: Python's built-in `subprocess` module. Run Git commands
      as argument lists with `shell=False` and `check=False`. Inspect
      `returncode` explicitly so expected nonzero results, such as exit code 1
      when checking for staged changes or a missing configuration value, are
      handled according to each command's documented meaning. Report
      unexpected failures separately instead of treating them as hint
      conditions. (drj228)
   7. Testing: Pytest

Testing
-------

The test tool contains:

* `make_temps(num)`: creates and returns `num` temporary directories. These are
  removed when the test completes.
* `make_repo(temp_dir, commands)`: runs the list of `commands` in
  `temp_dir` to create and populate the repository. Each command is
  either an argument list, such as
  `["git", "commit", "-m", "Add foo."]`, executed using
  `subprocess.run()` with `shell=False`, or a lambda function with
  no parameters used to create, modify, or delete files. Pass each
  argument separately and keep messages containing spaces in a
  single list element. Do not join arguments into a shell string.
  (drj228)
* `config_user(username, email)`: Set Git's `user.name` and `user.email`. 
* `git_setup()`: creates an isolated Git configuration for the test environment. The test environment shall:
   * use an empty temporary file for GIT_CONFIG_GLOBAL so that the user's global Git configuration does not affect test results
   * set GIT_CONFIG_NOSYSTEM=1 so that the system Git configuration does not affect test results
   * provide Git author and committer identity through environment variables so that tests do not depend on the machine's configured identity
   * initialize test repositories with git init -b main so that tests do not depend on the machine's init.defaultBranch setting.

A typical test would make temporary directories, then use these to make repos,
then set remotes. After changing to the local repo temp dir, it runs git-hints
and checks that the output is correct.

All Git commands executed as part of a test shall use the isolated test environment established by git_setup(). This prevents test results from varying based on the Git configuration of the machine running the tests.

### Test case 1: files are changed. *(Written by bj147)* // use as reference

1. Create one temp directory.
2. Execute the following in this temp directory:
   1. Call `config_user("user1", "user1@foo.com")`.
   2. Create an empty git repo with `git init -b main`.
   3. Create a file called `foo.txt` with the content `xxx`.
   4. Add it: `git add foo.txt`.
   5. Commit it: `git commit -m "Add foo."`.
   6. Modify `foo.txt`: append `y` to it.
3. Run `git-hints` in the temp dir. Expected hint:
   [Stage](https://www.w3schools.com/git/git_staging_environment.asp "Also called the index; select which files changes to store in a commit")
   files?

### Test case 2: files are changed. (Written by sbe80) -- Requirement Reactive 1

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

### Test case 3: Resolving merge conflicts. (Written by sbe80) -- Requirement Reactive 2

1. Create two temporary directories.
2. Execute the following in the first temporary directory:
   1. Call `config_user("user1", "user1@foo.com")`.
   2. Create an empty git repo with `git init -b main`.
   3. Create a file called `foo.txt` with the content `xxx`.
   4. Add it: `git add foo.txt`.
   5. Commit it: `git commit -m "Add foo."`.
3. Clone the first repo into the second using `git clone <temp_dir1> <temp_dir2>`
4. In repo 1, add `y` to `foo.txt` and commit
5. In repo 2, add `z` to `foo.txt` and commit
6. Run `git pull` in the first repo
7. Run git-hints in the first repository. Expected hint: Resolve merge
   conflicts? The output should identify foo.txt as a conflicting file and
   explain how to resolve the conflict.

### Test Case 4: Push (ewj55)
0. Initialize `Test4_condition == 0` by default
1. use the termnial to navigate to the local repo directory tracking a remote branch ('origin/main')<br>
2. Execute command (`git fetch origin`) and ensure local track references are up to date <br>
3. Make a minor edit to the file, stage the change (`git add .`), then commit locally ('git commit -m "Test commit"')
**Condition Checks:**
   4. run `git log origin/main..HEAD` into terminal
   5. If command returns one or more comit SHAs, set `Test4_condition == 1`.
**Output/Expected Execution**
   6. If `Test4_condition == 1`, execute `git-hints` CLI tool on terminal
   7. Confirm reactive hint 'Push?' is displayed in terminal output.
   8. If `git-hints` output contains `"Push?"` string AND `'git push'` command, then Test 4 has passed.

### Test Case 5: Repo Test (ewj55)

**Setup (Arrange):**
1. Create isolated tmp dir in system tmp space (outside any existing Git repo tree)
2. Using terminal, navigate into isolatd tmp dir without running the `git init`
    command: 
      - `mkdir test_folder && cd test_folder` 
**Executions and Assertions**
3\. Execute `git status` and verify terminal output contains `"fatal: not a git repository"`.
4\. Execute the `git-hints` CLI tool inside `test_folder`. 
**Assertion**
5. If `git-hints` output contains the proactive hint string `"clone"` AND the suggested command `'git clone'`, then Test 5 has passed

### Test Case 6: Pull needed, Branch is behind (jhg246) For Requirement Proactive 2

1. Call `git_setup()`. Create three temp directories: `remote`, `local`, `other`. Call
   `config_user("user1", "user1@foo.com")`.
2. In `remote`: `git init --bare -b main` (the remote must be bare).
3. In `other`: `git clone <remote> <other>`, create `foo.txt` containing `xxx`,
   `git add foo.txt`, `git commit -m "Add foo."`, `git push -u origin main`.
4. Run `git clone <remote> <local>`.
5. In `other`: append `y` to `foo.txt`, `git commit -am "Change foo."`, `git
   push`.
6. Run `git-hints` in `local`. Expected: no `behind` hint, because `local`
   hasn't fetched (`git status --porcelain=v2 --branch` shows `# branch.ab +0
   -0`).
7. In `local`, run `git fetch` (status now shows `+0 -1`), then `git-hints`.
   Expected: **Pull needed, your branch is behind!** (ID `behind`), labeled "as
   of last fetch". The `diverged` and **Push?** hints are not shown. Run Git
   commands as argv lists, and assert on hint IDs rather than exact text.

### Test case 7: Branch has diverged. (jhg246) -- For Requirement Proactive 13

1. Do steps 1-5 of Test case 6 ^
2. In `local`: create `bar.txt` containing `zzz`, `git add bar.txt`, `git commit
   -m "Add bar."`, then `git fetch` (status shows `+1 -1`).
3. Run `git-hints` in `local`. Expected: **Your branch has diverged from
   upstream.** (ID `diverged`), suggesting `git pull` or `git pull --rebase`,
   then `git push`, with a link to the
   [git pull](https://git-scm.com/docs/git-pull)
   docs. The `behind` and **Push?** hints are not shown.
4. Variant: skip the fetch in step 2 (status shows `+1 -0`). Expected: **Push?**
   is shown and `diverged` is not.

### Test case 8: Push Failed. (ams2083) -- Requirement Reactive 5

1. Call `git_setup()`. Create three temporary directories: `remote`, `local`, and `other`.
2. Call `config_user("user1", "user1@foo.com")`.
3. In `remote`, create a bare repository with `git init --bare -b main`.
4. In `other`, clone the `remote` repository using `git clone <remote> <other>`.
5. In `other`:
   1. Create `foo.txt` containing `xxx`.
   2. Run `git add foo.txt`.
   3. Run `git commit -m "Add foo."`.
   4. Run `git push -u origin main`.
6. Clone the `remote` repository into `local` using `git clone <remote> <local>`.
7. In other, modify `foo.txt`, commit the change, and push it to the remote:
   1. Append `y` to foo.txt.
   2. Run `git commit -am "Update foo."`.
   3. Run `git push`.
8. In `local`, create a different `local` commit without first pulling the newer remote commit:
   1. Create `bar.txt` containing `zzz`.
   2. Run `git add bar.txt`.
   3. Run `git commit -m "Add bar."`.
9. Run `git-hints explain push` in the `local` repository.
10. Confirm that the push fails because the `remote` branch contains commits that are not present in the `local` branch.
11. Expected hint: *Push failed?*
12. Verify that the hint explains that `remote` contains newer commits and suggests [pulling](https://git-scm.com/docs/git-pull) with `git pull` before attempting to [push](https://git-scm.com/docs/git-push) with `git push` again.

### Test case 9: Configure upstream branch. (ams2083) -- Requirement Proactive 4

1. Call `git_setup()`. Create one temporary directory.
2. Call `config_user("user1", "user1@foo.com")`.
3. In the temporary directory, create a Git repository with `git init -b main`.
4. Create `foo.txt` containing `xxx`.
5. Run `git add foo.txt`.
6. Run `git commit -m "Add foo."`.
7. Create and switch to a new local branch using `git switch -c feature-test`.
8. Do not configure an upstream remote branch for `feature-test`.
9. Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` and verify that the command fails because no upstream is configured.
10. Run `git-hints` in the local repository.
11. Expected hint: *Configure upstream branch?*
12. Verify the hint explains `feature-test` exists only as a local branch and [doesn't track](https://git-scm.com/docs/git-rev-parse/2.27.0) an upstream remote branch. 
13. Verify that the hint suggests configuring an upstream branch before attempting to push.

### Test case 10: Detached HEAD state. (Written by drj228)
For Requirement Proactive 11, written by jit45.

1. Call `git_setup()` and create one temporary directory.
2. Initialize a repository in that directory with `git init -b main`.
3. Call `config_user("user1", "user1@example.com")`.
4. Create `foo.txt` containing `xxx`, stage it, and commit it.
   Run Git commands as argument lists with `shell=False`.
5. Run `git-hints all`. Verify that the detached-HEAD hint is absent
   while HEAD is attached to `main`.
6. Run `git switch --detach HEAD`.
7. Run `git symbolic-ref --quiet --short HEAD`. Verify exit code 1,
   indicating that HEAD is detached. Confirm that no rebase or
   bisect is in progress.
8. Run `git-hints all`. Verify that the detached-HEAD hint appears,
   explains that HEAD points to a commit instead of a named branch,
   and suggests `git switch -c <name>` to preserve future commits.
   Verify that it includes a link to the official Git documentation.
   Identify the hint by its permanent ID rather than exact wording.
9. Run `git switch -c saved-work`.
10. Run `git-hints all` again. Verify that the detached-HEAD hint
    is absent because HEAD is now attached to `saved-work`.

### Test case 11: Repository has no commits. (Written by drj228)
For Requirement Proactive 12, written by jit45.

1. Call `git_setup()` and create one temporary directory.
2. Initialize a repository in that directory with `git init -b main`.
3. Call `config_user("user1", "user1@example.com")`.
   Run Git commands as argument lists with `shell=False`.
4. Run `git rev-parse --verify HEAD`. Verify that it fails because
   the repository has no commits.
5. Run `git-hints all`. Verify that the no-commits hint appears
   and explains that the repository has no saved commit yet.
   Since no files are staged, it should not suggest committing yet.
6. Create `foo.txt` containing `xxx` and run `git add foo.txt`.
7. Run `git-hints all` again. Verify that the no-commits hint
   now suggests `git commit -m "Initial commit"` and includes
   a link to the official Git commit documentation.
   Identify the hint by its permanent ID rather than exact wording.
8. Run `git commit -m "Initial commit"`.
9. Run `git rev-parse --verify HEAD`. Verify exit code 0 and
   a commit hash in the output.
10. Run `git-hints all` again. Verify that the no-commits hint
    is absent now that the repository contains a commit.

### Manual verification and LLM feedback (drj228)

Manually checked the Git conditions in a temporary repository using
PowerShell on October 2, 2026.

- Test case 8: `git symbolic-ref --quiet --short HEAD` returned
  `main` with exit code 0, then no branch name with exit code 1
  after detaching HEAD. After creating `saved-work`, it returned
  `saved-work` with exit code 0.
- Test case 9: `git rev-parse --verify HEAD` returned exit code 128
  before the first commit, both before and after staging a file.
  After the initial commit, it returned a commit hash and exit code 0.

Personal experience
------------------- 

Here are examples of Git situations that confused me/caused me to
struggle/didn't do what I expected: <mark>\[Homework: add to this
section.\]</mark>

* (jhg246) When starting out with git it can be very easy to make a mess of a
  repository if you dont understand how to navigate branches and merges. This
  happened to me and it was very confusing and frustrating. The solution was to
  use ' git reset ' to return to a version of the repository that was
  functional. Maybe we could warn the user if they are in a branch that has no
  remote source and they are making changes/staging changes?

* (sbe80) I had a lot of confusion regarding conflicts. Theres many ways to fix
  them and all are potential confusion points. Another thing I found confusing
  initially was when to keep files local and when to add them to the remote repo
  and how to properly navigate that.

* (ewj55) I tend to be uncertain about whether the changes I made are local or
  pushed to the remote repository. If someone is editing shared code, they
  should be clearly aware of whether their changes are local-only or affecting
  the upstream repo.

* (drj228) When creating a branch in VS Code, I was unsure whether I had created
  a local branch or a remote branch. I also did not understand that creating a
  local branch does not automatically publish it to GitHub. A hint explaining
  where the branch exists and whether it has an upstream branch would help me
  understand the next step.

* (ams2083) I didn't realize how difficult it would be to navigate a repository
  when you have dozens of people working and making changes. It's hard for me to
  remember what I'm working on and altering when I also have to take into
  account the additions of other people.

* (jit45) I have been unsure whether the branch I was working on had the newest
  changes from the remote repository before I started editing. In a shared
  repository, this made me worry that I might be changing an outdated version
  and create avoidable conflicts. A hint showing whether my branch is behind the
  remote would make that state clearer before I begin working.

* (raf322) For me, one of the things I have stuggled with getting used to doing
  is stashing changes and keeping track of them. There have been times where I
  have been working on a project, trying to keep track of which stash has the
  changes I want to implement, and then giving up and not using stashes at all
  when it becomes clear that the stash I'm looking for isn't the one I've
  selected.

To do
-----

1. Provide a link and tooltip text for the many hints missing these.
2. For each hint:
   1. Add the Git command used to detect when to issue this hint after the
      conditions text. See the first hint for an example.
   2. Remove the corresponding text from the implementation.
3. Verify that the testing framework is effective.
4. Convert one of your items from the Personal experience section to a hint.
