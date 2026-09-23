Ideas
=====

This file records the initial design of the git-hints tool.

Requirements
------------

1. The tool will be initially implemented using a CLI for command-line use of
   Git.
2. The tool should offer hints in the following categories:
   1. Reactive
      1. [Stage](https://www.w3schools.com/git/git_staging_environment.asp "Also called the index; select which files changes to store in a commit")
         files? Conditions: changed files in repo.
      2. Undo these changes? Conditions: If you are making a commit and do not
         want to include unstaged changes.
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
   3. Definitions
   4. How to
   5. For every command, implement a terminal command alongside the GUI (for
      example show how to clone on the GUI as well as on the terminal) (ewj55)
   6. Implement how the underlying logic work so the user knows what exactly
      they are doing or what they are about to do. (ewj55)
   7. every hint about a specific task and command links to the official docs
      for more information (ewj55)
   8. maybe highlight sections from the docs to show where that specific hint
      came from (ewj55)
   9. Find a balance between hints that doesn't overwhelm the user, causing them
      to get lost in information and a useful tool for users who are still new
      to git (ewj55)
   10. automatically when you type a command like "repo" into codechat editor is
       displays the hyperlink and summarized definition to remind user what it
       does (ewj55)
3. Hints should consists of Markdown text. Links must include a title which
   gives a summary of the term. For example: "Do you want to clone a
   [repo](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository "A Git repository tracks changes to files over time in discrete units called commits.")?"
4. The tool should display at most 3 hints.

Implementation
--------------

1. Determining git/repo conditions:
   1. Changed files.
   2. Error from last git execution?
   3. The local branch has commits that have not been pushed to the remote
      branch.
   4. No repo exists in the current directory: git status (sbe80)
2. Estimate user intent: how?
3. Language and libraries:
   1. Language: Python
   2. Package manager: uv
   3. Formatter/linter: ruff
   4. Type checker: ty
   5. CLI: Typer
   6. Git interface: GitPython

Personal experience
-------------------

Here are examples of Git situations that confused me/caused me to
struggle/didn't do what I expected:

* TODO. (jhg246) When starting out with git it can be very easy to make a mess
  of a repository if you dont understand how to navigate branches and merges.
  This happened to me and it was very confusing and frustrating. The solution
  was to use ' git reset ' to return to a version of the repository that was
  functional. Maybe we could warn the user if they are in a branch that has no
  remote source and they are making changes/staging changes?

(sbe80) I had a lot of confusion regarding conflicts. Theres many ways to fix
them and all are potential confusion points.
