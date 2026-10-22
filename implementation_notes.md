Claude Opus 5.5, extra high effort, prompt: Implement @spec.md.

I've implemented the `git-hints` spec as a uv/Typer package. All 58 tests pass,
covering every test case in the spec plus extra checks for the CLI and
rendering. I ran them on Windows with Git 2.56, under both Python 3.14 and 3.10.
Ruff and ty report no problems. Nothing is committed.

**Layout**

* src/git\_hints/: cli.py, proactive.py, reactive.py, hint.py and git.py.
* tests/: the spec's four helpers
  (`make_temps`, `make_repo`, `git_setup`, `config_user`) are
  in git\_test\_tools.py, and the tests are grouped into five files.
* The code follows the literate style from your CodeChat Editor
  guidance. toc.md now lists the new files.
* Run the tool with `uv run git-hints` and the tests with `uv run pytest`. Tests
  run in parallel by default (about 95 s); pass `-n 0` to run them one at a
  time.

<strong>Speed:</strong> each Git process takes about 60 ms on this machine, and
one inspection needs about 23 of them. The hint checks run in parallel threads
and share each Git command's result, which brings one run down from about 1.8 s
to about 0.8 s.

**Decisions you may want to revisit**

1. <strong>`commit-identity` priority:</strong> the spec doesn't give one. I
   chose `workflow`, so it sorts after the change-related hints and can fall
   outside the three-hint limit.
2. <strong>New `bisect-in-progress` hint:</strong> the spec says to explain a
   healthy bisect but defines no hint for it, so I added an informational one.
3. <strong>Broader suppression:</strong> `behind` and `diverged` are hidden
   during any paused merge, rebase, cherry-pick or revert, because `git
   pull` refuses to run then. `tracked-but-ignored` is hidden while conflicts
   exist, because its commit step would fail.
4. <strong>Small additions:</strong>
   * `not-a-repo` also suggests `git init`.
   * `merge-conflicts` lists at most five files, then "and N more".
   * A failed `explain` with no recognized error prints `No hints.`
   * An inspection failure, or Git failing to start, exits with code 1.
5. <strong>Shell quoting:</strong> file names go in double quotes, which work in
   bash, PowerShell and cmd. Single quotes are used only when a name contains a
   character that double quotes can't protect.
6. <strong>Documentation links:</strong> these are the spec's URLs, mostly whole
   pages. I didn't add the passage-level anchors or text fragments the spec
   prefers, because each one has to quote wording on the page and I couldn't
   check that.
7. <strong>Not done:</strong> I didn't add CodeChat fragment/gather markup
   to `spec.md`.
