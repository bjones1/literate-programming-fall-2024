Git hints tool
==============

1. [Specification](spec.md)
   1. [Implementation notes](implementation_notes.md)
   2. [Personal experience](personal_experience.md)
2. Implementation
   1. [Overview](src/git_hints/__init__.py)
   2. [Command line](src/git_hints/cli.py)
   3. [Proactive hints](src/git_hints/proactive.py)
   4. [Reactive hints](src/git_hints/reactive.py)
   5. [Hint model and rendering](src/git_hints/hint.py)
   6. [Running Git](src/git_hints/git.py)
3. Tests
   1. [Test tools](tests/git_test_tools.py)
   2. [Command line and rendering](tests/test_cli.py)
   3. [Changes](tests/test_changes.py)
   4. [Upstream and fetching](tests/test_remote.py)
   5. [Repository state](tests/test_state.py)
   6. [Explain](tests/test_explain.py)
4. [Table of contents](toc.md)
