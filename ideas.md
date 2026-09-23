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
      5. Explain definition of modified mode and editor mode Conditions: When you click on a .md file and you are unable to edit it. (ewj55)
      6. The CLI tool will print a color-coded status bar in the terminal (e.g. [LOCAL ONLY -2 unpushed commits]) in red, [FULLY SYNCED WITH REMOTE] in green. If the current branch has any unpushed local commits (ahead of origin/(branch)). Red indicates local-only changes exist; green indicates the local branch is fully synchronized with the remote server. 
      Conditions: when you open a md file and begin making tweaks to the file letting the user know when the changes are affecting the public repo. (ewj55)
   3. Definitions
   4. How to
3. <a id="cc-SbouyCXTsP"></a>For every command, implement a terminal command
   alongside the GUI (for example show how to clone on the GUI as well as on the
   terminal) (ewj55)
4. Each hint should include a 1-sentence breakdown of what Git stage the user is currently in (Working in the directory, staging area, local repo, or remote), so the user learns the Git mental model while working (ewj55)
5. every hint about a specific task and command links to the official docs for
   more information (ewj55)
6. maybe highlight sections from the docs to show where that specific hint came
   from (ewj55)
7. Find a balance between hints that doesn't overwhelm the user, causing them to
   get lost in information and a useful tool for users who are still new to git
   (ewj55)
8. automatically when you type a command like "repo" into codechat editor is
   displays the hyperlink and summarized definition to remind user what it does
   (ewj55)
9. Hints should consists of Markdown text. Links must include a title which
   gives a summary of the term. For example: "Do you want to clone a
   [repo](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository "A Git repository tracks changes to files over time in discrete units called commits.")?"
10. The tool should display at most 3 hints.

Implementation
--------------

1. Determining git/repo conditions: <mark>\[Homework: add to this section.
   Include a condition from the <xref ref="cc-Xi1o6gL4Lb"></xref> section,
   followed by which Git command produces this information. See the example in
   item 1 below.\]</mark>
   1. Changed files: `git status`.
   2. Error from last git execution? Difficult to get this.
   3. The local branch has commits that have not been pushed to the remote
      branch.
   4. No repo exists in the current directory: git status (sbe80)
   5. See if the file changes are only local or public: git status -sb (ewj55)
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
struggle/didn't do what I expected: <mark>\[Homework: add to this
section.\]</mark>

* TODO. (jhg246) When starting out with git it can be very easy to make a mess
  of a repository if you dont understand how to navigate branches and merges.
  This happened to me and it was very confusing and frustrating. The solution
  was to use ' git reset ' to return to a version of the repository that was
  functional. Maybe we could warn the user if they are in a branch that has no
  remote source and they are making changes/staging changes?

(sbe80) I had a lot of confusion regarding conflicts. Theres many ways to fix them and all are potential confusion points.

* (ewj55) I tend to be uncertain about whether the changes I made are local or pushed to the remote repository. If someone is editing shared code, they should be clearly aware of whether their changes are local-only or affecting the upstream repo.