Tasks for the coming week
=========================

Individual
----------

1. `git-hints def` -- write LLM instructions to evaluate each common git
   command. See `git` for the list. What's a good summary sentence? Can we use
   the existing docs? Do we write/generate more? How much, what kind, etc.?
2. `git-hints howto` -- big writing task. Future work unless someone volunteers.
   But how does it involve LLMs?
3. `git-hints [explain] --bug`: need more details. Give an example of an issue
   generated, exactly how the repo state will be reported, etc.
4. Need to tag every hint with a priority class and hint ID. Part of combining
   task earlier.
5. ewj55 will clarify: "Maybe highlight sections from the docs to show where
   that specific hint came from."
6. sbe80 will remove/clarify: "Give every hint one safety level, shown in its
   output. **Safe**: read-only or only adds (no label). **Potentially
   destructive**: recoverable through the reflog (prefix "Caution:"). **Highly
   Destructive**: can lose work the reflog cannot restore (uncommitted changes,
   untracked files, others' remote commits), e.g. `reset --hard`, `clean -fd`,
   `push --force` (prefix "Warning:", say what will be lost, and tell the user
   to back up first). (sbe80; edited by jhg246)"
7. Rethink "Git interface: Python's built-in `subprocess` module." This makes
   sense for `git-hints explain`, but perhaps not for plain `git-hints`.

Everyone
--------

1. For a given hint in the "TODO: each of the following hints should be
   rewritten to follow the above hints" section, combine info from the "TODO:
   move test cases to follow the implementation of each hint." section and the
   "TODO: move test cases to follow the implementation of each hint" section.
   Make sure the hint text follows the spec's "Hint structure" section.
2. Review your changes to the spec with an LLM and address these issues.
   Continue reviewing until most LLM suggestions no longer apply.

<p><br></p>

<p><br></p>
