Ideas
=====

This file records the initial design of the git-hints tool.

Requirements
------------

1. The tool will be initially implemented using a CLI for command-line use of
   Git.
2. The tool should offer hints in the following categories:
   1. Reactive
      1. Need to stage? Conditions: changed files in repo.
      2. Undo these changes? Conditions: TODO.
      3. Resolve merge conflicts? Conditions: a git pull fails because of merge
         conflicts, identify the conflicting files and explain how to resolve
         them.
      4. Resolve pull conflicts? Conditions: if a git pull fails because of
         uncommitted changes, identify the conflicting files and explain how to
         resolve them.
      5. Push? Conditions: the local branch has commits that have not been
         pushed to the remote branch.
   2. Proactive
      1. How to clone a repo. Conditions: repo doesn't exist in the current
         directory.
      2. Pull remote changes? Conditions: remote branch is ahead of the local
         branch.
      3. The current branch is xxx. Conditions: TODO.
      4. Configure upstream branch? Conditions: if the current branch does not
         have an upstream remote branch configured, explain this and suggest
         setting one before attempting to push.
   3. Definitions
   4. How to
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
   4. No repo exists in the current directory.
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

* TODO.
