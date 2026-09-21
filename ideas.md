Ideas
=====

1. If files are changed, wait a bit, then pop up a note: need to stage?

2. Have highlighted/hyperlinked items with links to definitions. Hover summary,
   click for deep info.

3. Class of hints: reactive, proactive, definition, how to

4. (Definition) Hovering over VScode GUI shows CLI git commands

5. (Proactive) How to clone a repository?

6. (Reactive) How to react to making a mistake?

7. (Proactive) Always list current the current branch

8. (Proactive) Check if the remote branch is ahead of the local branch and if
   so, suggest a git pull

9. (Reactive) If a git pull fails because of merge conflicts, identify the
   conflicting files and explain how to resolve them.

10. (Reactive) If a git pull fails because of uncommited changes, identify the
    conflicting files and explain how to resolve them.<br>

11. (Reactive) If the local branch has commits that have not been pushed to the remote branch, suggest a git push.

12. (Proactive) If the current branch does not have an upstream remote branch configured, explain this and suggest setting one before attempting to push.

Implementation
--------------

1. Language: Python
2. UI: CLI
3. Package manager: uv
4. Formatter/linter: ruff
5. Type checker: ty
6. CLI: Typer
7. Git interfact: GitPython

This is a simple CLI interface this displays one hint based on the state of the
containing git repository.
