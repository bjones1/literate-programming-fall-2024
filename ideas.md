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

      8. Explain \[stashes\](https://git/git-stash/ keeps logs between
         uncommitted changes and committed changes and labels them stage or
         unstaged)

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
          before proceeding. Condition: five failed git pull or git push
          commands in a row (sbe80).
   2. Proactive

      1. How to clone a repo. Conditions: repo doesn't exist in the current
         directory. **test ewj55**

      2. Pull remote changes? Conditions: remote branch is ahead of the local
         branch.

      3. The current branch is xxx. Conditions: always as long as three hints
         are not already being displayed (sbe80).

      4. Configure upstream branch? Conditions: if the current branch does not
         have an upstream remote branch configured, explain this and suggest
         setting one before attempting to push.

      5. Explain
         [file states](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F "Files in Git move between modified, staged, and committed states.")
         and editor read-only modes? Conditions: When attempting to edit a file
         opened in a commit or diff view. (ewj55)

      6. Display
         [sync status](https://git-scm.com/docs/git-status "Shows whether your local branch is up to date or ahead of the remote repository.")
         indicator in terminal? Conditions: When local commits exist that have
         not been pushed to origin. (ewj55)

      7. Review staged changes before committing? Conditions: the staging area
         contains changes ready for a commit. Suggest
         [git diff --cached](https://git-scm.com/docs/git-diff "Shows the staged changes that will be included in the next commit.")
         so the user can check exactly what will be committed. These changes are
         in the staging area and have not yet become a commit. (drj228)

      8. Configure your commit identity? Conditions: `user.name` or `user.email`
         is missing or empty in the effective Git configuration. Explain how to
         set the missing value using
         [git config](https://git-scm.com/docs/git-config "Reads and updates Git settings, including the name and email recorded in commits.")
         with `git config user.name "Your Name"` or `git config user.email
         "you@example.com"`. These settings identify the author of local
         commits; they do not sign the user into GitHub. (drj228)

      9. Commit staged changes? Conditions: files are staged, but no commit has
         been created yet. Explain how the files are currently in staging area
         and ready to be saved to local repository. Suggest
         [git commit](https://git-scm.com/docs/git-commit "Creates a new commit from staged changes.")
         with `git commit -m "message"` to create a new commit containing the
         staged changes. (ams2083)

      10. Add untracked files to Git? Conditions: one or more untracked files
          exist in working directory. Explain Git can see the files but isn't
          tracking their changes. Suggest
          [git add](https://git-scm.com/docs/git-add "Adds file contents to the staging area.")
          with `git add filename` to move the file into the staging area or
          explain the file can be added to `.gitignore` if it shouldn't be
          tracked. (ams2083)

      11. Your repo was changed by more than 50% (untracked files, lines of
          code, deleted files, etc.), would you like to commit it?

      12. A timer to check how much progress the user has made. If the repo has
          little to no changes over a set amount of time, that means the user is
          most likely stuck.

      13. You are in a detached HEAD state. Conditions: the repository exists,
          but HEAD is not attached to a local branch. Explain that the user is
          working in the local repository at a specific commit instead of on a
          named branch. Suggest
          [git switch -c](https://git-scm.com/docs/git-switch "Creates a new branch and switches to it.")
          to create and switch to a new branch if the user wants to preserve
          future commits. (jit45)

      14. This repository does not have any commits yet. Conditions: the current
          directory is a Git repository, but HEAD does not yet resolve to a
          commit. Explain that the local repository has no saved commit yet. If
          files are staged, suggest
          [git commit -m "Initial commit"](https://git-scm.com/docs/git-commit "Creates a new commit from the staged changes.")
          to create the first commit. (jit45)

      15. <br>
      16. Warn the user that the current branch has diverged from upstream
          (sbe80).

      17. Committing to protected/main branch. Conditions: the current branch is
          master/main and there are changes. If other branches exist, suggest
          other branches. If no other branches exist, suggest creating a new
          branch with `git switch -c <name>` (raf322)
   3. Definitions<br>

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
   5. Hints must consist of Markdown text. Each documentation link must include
      a title summarizing the linked term or command. Limit each title to 160
      characters, and put longer explanations in the linked documentation.
      Example:
      [repo](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository "A Git repository stores project history as commits.")
      (drj228)
4. Hint algorithms:

   1. Display at most three hints at once. If additional hints have their
      conditions met, inform the user that more are available. Provide a
      `git-hints all` command that displays every currently triggered hint.
      (jit45)

   2. Prioritize hints that explain a failed command or an unresolved merge
      conflict before routine workflow suggestions. Display no more than three
      hints at once, as specified by the hint-display limit above, and do not
      repeat a dismissed hint until its triggering condition changes. (ewj55;
      clarified by drj228 and jit45)

   3. All hints should be given a priority, with higher priority hints being
      displayed first (sbe80)

   4. All hints should be given a classification of whether they are safe,
      potentially destructive, or highly destructive (sbe80).

   5. Every hint should be given an ID. This will make testing much easier
      (sbe80).
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

   2. A Git command executed through the tool failed: capture its exit code,
      standard output, and standard error when the tool runs it. Use this
      information to select an appropriate hint. The tool cannot reliably
      recover the result of an earlier command run outside the tool. (drj228)

   3. The local branch has commits that have not been pushed to the remote
      branch: run `git status -sb`. If the branch status shows that the local
      branch is ahead of its upstream branch by one or more commits, then local
      commits exist that have not yet been pushed to the remote repository.

   4. No repo exists in the current directory:
      [Git status](https://www.geeksforgeeks.org/git/git-status "Shows current state of working directory")
      (sbe80), could also be detected by the standard non-zero exit exception
      from `GitPython` when running commands outside a Git directory

   5. See if the file changes are only local or public: `git status -sb` (ewj55)

   6. Use `git fetch` followed by `git diff HEAD...@{upstream}` to view
      differences in a file, used to help the user fix merge conflicts (jhg246)

   7. Staged changes are ready to commit: run `git diff --cached --quiet`. Exit
      code 1 means staged differences exist; exit code 0 means there are none.
      Treat other exit codes as errors instead of triggering the hint. This
      detects the condition for the staged-review hint. (drj228)

   8. Commit identity is not configured: run `git config --get user.name` and
      `git config --get user.email`. An exit code of 1 indicates that the
      requested setting is missing. Also check for an empty returned value.
      Report other command failures separately. These checks use the effective
      configuration, including repository and global settings. (drj228)

   9. Untracked files exist: run `git status --porcelain`. Lines beginning with
      `??` indicate files that Git sees in the working directory but isn't
      currently tracking. (ams2083)<br>

   10. HEAD is detached rather than attached to a local branch: run `git
       symbolic-ref --quiet --short HEAD`. A zero exit code means HEAD is
       attached to a branch and the command prints the branch name. A non-zero
       exit code in an otherwise valid Git repository indicates that HEAD is
       detached. This detects the condition for the detached HEAD hint. (jit45)

   11. Committing to main/master: Run  `git branch --show-current` to identify
       current branch. If the branch is main, check for other remote/active
       branches with `git branch -a`. If the list contains no other branches
       besides the protected branch(es), suggest the creation of a new branch.
       Otherwise, suggest other branches on the list.(raf322)

   12. Run `git status -sb`. If the status reports that the local branch is
       ahead *and* behind its upstream branch, the branches have diverged. 
       (sbe80)

   13. The explain command (Requirement 5) must pass Git arguments through
       without Typer attempting to parse them as options. Configure the command
       to allow extra arguments and ignore unknown options (for example, using
       allow\_extra\_args=True and ignore\_unknown\_options=True) so commands
       such as `git-hints explain pull --rebase` and `git-hints explain reset
       --hard HEAD~1` are passed to Git correctly (sbe80).

   14. The explain command (Requirement 5) should not require the word `git`
       after the word `explain`. (sbe80)
2. Language and libraries:

   1. Language: Python
   2. Package manager: uv
   3. Formatter/linter: ruff
   4. Type checker: ty
   5. CLI: Typer
   6. Git interface: GitPython
   7. Testing: Pytest

Testing
-------

The test tool contains:

* `make_temps(num)`: creates and returns `num` temporary directories. These are
  removed when the test completes.
* `make_repo(temp_dir, commands)`: runs the list of `commands` in `temp_dir`,
  which creates and populate the repo. Each command is either a list of
  arguments, which is executed as a shell command (typically a git command), or
  a lambda function with no parameters, typically used to create/modify/delete
  files.
* TODO: delete me. `git clone` is probably a better approach.
  `set_remotes(local, repo 1, repo 2, ...)`: sets remotes for the local repo.
  Each parameter is the path to the repo.
* `config_user(username, email)`: Set Git's `user.name` and `user.email`. TODO:
  add a `git_setup()` function that performs the TODO below.

A typical test would make temporary directories, then use these to make repos,
then set remotes. After changing to the local repo temp dir, it runs git-hints
and checks that the output is correct.

TODO: need to isolate git behavior from global config. Fix this with
`GIT_CONFIG_GLOBAL` pointing to a temp file, `GIT_CONFIG_NOSYSTEM=1`, the
identity env vars, and `git init -b main`.

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

### Test case 2: files are changed. (Written by sbe80) -- Requirement Reactive 2

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

### Test case 3: Resolving merge conflicts. (Written by sbe80) -- Requirement Reactive 3

1. Create two temporary directories.
2. Execute the following in the first temporary directory:
   1. Call `config_user("user1", "user1@foo.com")`.
   2. Create an empty git repo with `git init -b main`.
   3. Create a file called `foo.txt` with the content `xxx`.
   4. Add it: `git add foo.txt`.
   5. Commit it: `git commit -m "Add foo."`.
3. Use `set_remotes(directory1, directory2)` to set the second temporary
   directory as the remote of the first. <mark>BAJ: probably not
   necessary.</mark>
4. Clone the first repo into the second. <mark>BAJ: give the Git command. This
   helps demonstrate the need for access to repo dirs when issuing
   commands.</mark>
5. In repo 1, add `y` to `foo.txt` and commit
6. In repo 2, add `z` to `foo.txt` and commit
7. Run `git pull` in the first repo
8. Run git-hints in the first repository. Expected hint: Resolve merge
   conflicts? The output should identify foo.txt as a conflicting file and
   explain how to resolve the conflict.

### Test Case 4: Push (ewj55)
   **SETUP (Arrange)**
1. Create two isolated tmp directories: `remote_dir` and `local_dir`
2. In `remote_dir`, initialize a bare repo: 
   - `git init --bare -b main`
3. In `local_dir`, initialize a local repo, config dummy identity, then follow provided steps:
   - `git init -b main`
   - `git config user.name "user1" && git config user.email "user1@foo.com"`
   - `git remote add origin ../remote_dir`
4. Create an initial commit and push to set upstream tracking:
   - `echo "initial" > file.txt && git add . && git commit -m "Initial commit"`
   - `git push -u origin main`
5. Create one new unpushed local commit:
   - `echo "change" >> file.txt && git add . && git commit -m "Unpushed local edit"`

   **Output/Expected Execution** 
6. Execute `git log origin/main..HEAD` in `local_dir`: If output returns 1, there is a local unpushed status
7. Execute `git-hints` CLI tool inside the local directory `local_dir`.
   **Assertion**
8. If `git-hints` output contains reactive hint string `"Push?"` AND suggested command `'git push'`, then Test 4 passes.

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
