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
         requirements and exemplified here.\]</mark>
      2. Keep unstaged changes out of this commit? Conditions: both staged and
         unstaged changes exist. Explain that a plain `git commit` records
         staged changes, so unrelated edits can remain unstaged without being
         discarded. Suggest
         [git diff --cached](https://git-scm.com/docs/git-diff "Shows the staged changes selected for the next commit.")
         to review the staging area before committing. (drj228)
      3. Resolve merge conflicts? Conditions: a git pull fails because of merge
         conflicts, identify the conflicting files and explain how to resolve
         them.
      4. Resolve pull conflicts? Conditions: if a git pull fails because of
         uncommitted changes, identify the conflicting files and explain how to
         resolve them.
      5. Push? Conditions: the local branch has commits that have not been
         pushed to the remote branch.
      6. Pull needed, your branch is behind! Conditions: If the user is a 1 or
         more commits behind on the current branch. (jhg246)
      7. Push failed because of conflicting file changes. Try running git diff
         *'filename'* ! Conditions: If the user attempted a push and it failed
         due to conflicting file changes. (jhg246)
      8. Explain stashes including: what they are, how to make one, and how to
         see old ones Condition: conflict when pulling (sbe80)
   2. Proactive

      1. How to clone a repo. Conditions: repo doesn't exist in the current
         directory.

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

      11. Your repo was changed by more than 50%, would you like to commit it?

      12. A timer to check how much progress the user has made. If the repo has
          little to no changes over a set amount of time, that means the user is
          most likely stuck.

      13. You are in a detached HEAD state. Conditions: the repository exists, but HEAD is
      not attached to a local branch. Explain that the user is working in the local repository
      at a specific commit instead of on a named branch. Suggest
      [git switch -c <branch-name>](https://git-scm.com/docs/git-switch "Creates a new branch and switches to it.")
      to create and switch to a new branch if the user wants to preserve future commits. (jit45)

      14. This repository does not have any commits yet. Conditions: the current directory
      is a Git repository, but HEAD does not yet resolve to a commit. Explain that the local
      repository has no saved commit yet. If files are staged, suggest
      [git commit -m "Initial commit"](https://git-scm.com/docs/git-commit "Creates a new commit from the staged changes.")
      to create the first commit. (jit45)

   3. Definitions<br>

      1. Allow users to request a definition of a Git command using `git pull
         def`. The tool should display a short definition of the command,
         explain what it does, and provide a link to the official Git
         documentation.
   4. How to

      1. Maybe add a howto command if you want instructions on how to do
         something like 'howto commit' and it would tell the user what potential
         other conditions or inputs are possible after 'commit'
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
   1. The tool should display at most 3 hints, potentially inform the user if
      more hints' conditions have been met and implement a command that will
      display ALL hints with their conditions met.
   2. Prioritize hints that explain a failed command or an unresolved merge
      conflict before routine workflow suggestions. Display no more than three
      hints at once, as specified in requirement 10, and do not repeat a
      dismissed hint until its triggering condition changes. (ewj55; clarified
      by drj228)
5. Estimate user intent:
   1. TODO.
6. Automatically when you type a command like "repo" into codechat editor is
   displays the hyperlink and summarized definition to remind user what it does
   (ewj55)

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
      branch: run git status -sb. If the branch status shows that the local
      branch is ahead of its upstream branch by one or more commits, then local
      commits exist that have not yet been pushed to the remote repository.

   4. No repo exists in the current directory: git status (sbe80), could also be
      detected by the standard non-zero exit exception from `GitPython` when
      running commands outside a Git directory

   5. See if the file changes are only local or public: git status -sb (ewj55)

   6. Use `git diff` to view differences in a file, used to help the user fix
      merge conflicts (jhg246)

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
      currently tracking. (ams2083)

   10. Commit identity is not configured: run `git config --get user.name` and
       `git config --get user.email`. An exit code of 1 indicates that the
       requested setting is missing. Also check for an empty returned value.
       Report other command failures separately. These checks use the effective
       configuration, including repository and global settings. (drj228)

   11. HEAD is detached rather than attached to a local branch: run
    `git symbolic-ref --quiet --short HEAD`. A zero exit code means HEAD
    is attached to a branch and the command prints the branch name. A
    non-zero exit code in an otherwise valid Git repository indicates
    that HEAD is detached. This detects the condition for the detached
    HEAD hint. (jit45)

2. Language and libraries:

   1. Language: Python
   2. Package manager: uv
   3. Formatter/linter: ruff
   4. Type checker: ty
   5. CLI: Typer
   6. Git interface: GitPython

Testing
-------

Ingredients:

* Multiple remote repos with branches/commits on each, made (possibly) by
  different users. Each repo can be read only or read/write for the current
  user.

* A way to purposely cause conflicts (how?)

* Local repo, possibly with stashes.

* Local files with changes/stages.

One option: use [git bundle](https://git-scm.com/docs/git-bundle) to
save/restore repo state. They can all be stored on the same machine, but two can
be "remote" (not the local repo). For the local repo,
[git stash push/git stash pop](https://git-scm.com/docs/git-stash) to save and
restore the file state.

### Test case 1: files are changed.

Expected prompt: do you want to stage changed files?

To set this up:

1. Create a text file and add content to it.

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
  them and all are potential confusion points.

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
changes from the remote repository before I started editing. In a shared repository, 
this made me worry that I might be changing an outdated version and create avoidable 
conflicts. A hint showing whether my branch is behind the remote would make that state 
clearer before I begin working.