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

      1. Files? Conditions: changed files in repo. Detect [status](https://git-scm.com/docs/git-statusand) with `git status` suggest reviewing the listed files and using `git add <filename>` to stage the changes.
          **bj147 will test.**
      
      
      
      
      
      
      


      2. Resolve merge conflicts? Conditions: a git pull fails because of merge
         conflicts. Suggest using the [git diff](https://git-scm.com/docs/git-diff) command `git diff --name-only --diff-filter=U` to identify the conflicting files and explain how to resolve
         them. **sbe80 will test**
      3. Resolve pull conflicts? Conditions: a `git pull` fails because of uncommitted changes. Suggest identifying the conflicting files then explain [stashes](https://git-scm.com/docs/git-stash) and how to use them to temporarily save changes.
      

      4. Push local commits? Conditions: the current branch is ahead of its upstream branch by one or more commits and is not behind the upstream branch. Detect [status](https://git-scm.com/docs/git-status) with `git status -sb`. Explain that the commits currently exist only in the local repository and suggest git push to send them to the remote repository.
         **test ewj55** 
      
      
      5. Push failed? Conditions: the user attempted a push and it failed due to the remote having more recent commits. Suggest [git pull](https://git-scm.com/docs/git-pull "Fetches and integrates commits from the remote.") first, then `git push` again. (jhg246) **ams2083 will test**
      
      
      
      
      
      
      
      
      
      
      6. Rebasing? Conditions: the user has five failed `git pull` or `git push` commands in a row.
          Suggest [git pull --rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)
          and explain that rebasing may cause merge conflicts and that the user
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
         [git config](https://git-scm.com/docs/git-config "Reads and updates Git settings, including the name and email recorded in commits.")
         with `git config user.name "Your Name"` or `git config user.email
         "you@example.com"`. These settings identify the author of local
         commits; they do not sign the user into GitHub. (drj228)

      






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
          future commits. (jit45)

      12. This repository does not have any commits yet? Conditions: the current
          directory is a Git repository, but HEAD does not yet resolve to a
          commit. Use `git rev-parse --verify HEAD` to confirm and explain that the local repository has no saved commit yet. If
          files are staged, suggest
          [git commit -m "Initial commit"](https://git-scm.com/docs/git-commit "Creates a new commit from the staged changes.")
          to create the first commit. (jit45)

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

   4. Give every hint one sefety level, shown in its output. *Safe*: read-only
      or only adds (no label). *Potentially destructive*: recoverable through
      the reflog (prefix "Caution:"). *Highly Destructive*: can lose work the
      reflog cannot restore (uncommitted changes, untracked files, others'
      remote commits), ex. `reset --hard`, `clean -fd`, `push --force` (prefix
      "Warning:", say what will be lost, and tell the user to back up first).
      (sbe80; edited by jhg246)

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
      commits exist that are not yet public.

4. No repo exists in the current directory:
      [Git status](https://www.geeksforgeeks.org/git/git-status "Shows current state of working directory")
      (sbe80), could also be detected by the standard non-zero exit exception
      from `GitPython` when running commands outside a Git directory

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

### Test case 1: files are changed. *(Written by bj147)*

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
1. use the termnial to navigate to the local repo directory tracking a remote branch ('origin/main')
2. Execute command (`git fetch origin`) and ensure local track references are up to date 
3. Make a minor edit to the file, stage the change (`git add .`), then commit locally ('git commit -m "Test commit"')
**Condition Checks:**
   4. run `git log origin/main..HEAD` into terminal
   5. If command returns one or more comit SHAs, set `Test4_condition == 1`.
**Output/Expected Execution**
   6. If `Test4_condition == 1`, execute `git-hints` CLI tool on terminal
   7. Confirm reactive hint 'Push?' is displayed in terminal output.
   8. If `git-hints` output contains `"Push?"` string AND `'git push'` command, then Test 4 has passed.

### Test Case 5: Repo Test (ewj55)
0. Initialize `Test5_condition = 0`
1. execute `mkdir test_folder && cd test_folder`

**Condition Checks**
2. Run `git status`
3. If terminal output contains `fatal: not a git repository (or any of the parent directories): .git` OR `fatal: not a git repository`, set `Test5_condition = 1` display git-hint associated with repo cloning.

**Output / Expected Execution:**
4. If `Test5_condition == 1`, run `git-hints` CLI tool
5. Verify git-hint `How to clone a repo` is displayed as terminal output
6.  If `git-hints` output string contains `"clone"` AND command `'git clone'`, Test 5 passed.

// create a setup where the LLM makes code that will popup quick sentences for
every git command. Create a way how to display a setup. Do a step by step in how
this setup should work for the model.

// chess board setup: Here is a place where the repo is in, and when the repo is
in X state, display X hint. After that verify that X hint was displayed. Check
the reactive or proactive sections plan through how to accomplish X tasks.

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
