Ideas
=====

1. If files are changed, wait a bit, then pop up a note: need to stage?

2. Have highlighted/hyperlinked items with links to definitions. Hover summary,
   click for deep info.

3. Class of hints: reactive, proactive, definition, how to

4. (Definition) Hovering over VScode GUI shows CLI git commands

5. (Proactive) How to clone a repository?

6. (Reactive) How to react to making a mistake?

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
