Review of ideas.md
==================

This reviews the working copy of [ideas.md](ideas.md), including the
uncommitted edits: the restructured def/howto/explain items and the new Testing
section.

Main design problems
--------------------

1. **Several conditions can't be seen by a CLI you run on demand.** Item 2.5
   says the tool can't recover results of commands run outside it, but these
   hints depend on exactly that:

   - "A git pull fails…" ([L27](ideas.md#L27), [L30](ideas.md#L30))
   - "push failed…" ([L37](ideas.md#L37))
   - "the user attempts to commit" ([L122](ideas.md#L122))
   - editing in a diff view, which is an editor event ([L61](ideas.md#L61))
   - a timer, which needs a background process ([L103](ideas.md#L103))

   Each one should either be tied to `git-hints explain`, rewritten as a state
   condition, or moved to a future-work/GUI list. Merge conflicts don't need
   the failed pull at all: they show up in repo state as unmerged paths
   (`git diff --name-only --diff-filter=U`) plus `MERGE_HEAD` or the rebase
   directories.

2. **Duplicate hints.** With a cap of three hints, these crowd out everything
   else:

   - Push ([L33](ideas.md#L33)) is the same as sync indicator
     ([L66](ideas.md#L66)). The implementation also repeats itself: items 1.2
     and 1.4 both use `git status -sb`.
   - Pull needed ([L35](ideas.md#L35)) is the same as Pull remote changes
     ([L51](ideas.md#L51)).
   - Review staged ([L71](ideas.md#L71)) and Commit staged
     ([L85](ideas.md#L85)) fire on the same condition, and
     [L21](ideas.md#L21) also suggests `git diff --cached`.
   - Pull-with-uncommitted-changes ([L30](ideas.md#L30)) and stashes
     ([L40](ideas.md#L40)) share a trigger.
   - gitignore ([L42](ideas.md#L42)) and untracked files
     ([L92](ideas.md#L92)) overlap.

3. **"Behind" is stale without a fetch.** Ahead/behind is measured against the
   last-fetched remote-tracking branch. The doc needs a fetch policy. Fetching
   on every run is slow, needs network, and can hang on a credential prompt
   (use `GIT_TERMINAL_PROMPT=0` plus a timeout). The alternative is to label
   the result "as of last fetch".

4. **No priority order.** Item 4.2 only puts failures and conflicts first. With
   about 25 hints and a cap of three, every hint needs a rank, for example:
   error/blocked → risk of losing data → workflow → informational.

5. **Dismissal isn't specified.** Item 4.2 needs:

   - a dismiss command
   - stable hint IDs
   - somewhere to store state (such as `.git/git-hints/`)
   - a definition of when a "triggering condition changes"

6. **The category list mixes hints and commands.** Items 2.3–2.5 are
   subcommands, `git-hints all` is buried in 4.1, and plain `git-hints` isn't
   specified at all. A separate "CLI commands" requirement would fix this.
   "Reactive" and "proactive" are also never defined, and the reactive list
   includes pure state checks (items 1, 2, 5, 6, 9). One natural split:

   - **Reactive:** triggered by a command's result, via `explain`.
   - **Proactive:** triggered by repo state.

Technical corrections
---------------------

- **[L37](ideas.md#L37):** a push isn't rejected for "conflicting file
  changes". It's rejected as non-fast-forward because the remote has commits
  you don't. The fix is pull, then push; `git diff filename` doesn't help.
- **[L43](ideas.md#L43):** `__pycache__.py` should be `__pycache__/`. Also, if
  `.env` is already tracked, adding it to `.gitignore` does nothing; the hint
  also needs `git rm --cached`.
- **[L81](ideas.md#L81):** without `--global`, `git config user.name` applies
  to the current repo only. Students almost always want `--global`.
- **[L107](ideas.md#L107):** HEAD is normally detached during a rebase or
  bisect. Exclude those cases, or the tool will wrongly suggest `git switch -c`
  in the middle of a rebase.
- **[L199](ideas.md#L199):** `git diff HEAD...@{upstream}` shows what a pull
  would bring in, not help with conflicts, and it names no file.
- **[L193](ideas.md#L193):** GitPython's `Repo()` raises
  `InvalidGitRepositoryError` when it's constructed, not a command exit code.
- **[L223](ideas.md#L223):** `git branch -a` output is awkward to parse
  (`remotes/origin/HEAD -> origin/main`, `*` markers).
  `git for-each-ref --format='%(refname:short)' refs/heads refs/remotes` is
  cleaner.
- **Exit codes and GitPython (1.6, 1.7, 1.9):** these checks rely on exit
  codes, but GitPython raises `GitCommandError` on any non-zero exit unless you
  pass `with_exceptions=False`. More broadly, the doc specifies raw CLI
  commands everywhere, which makes GitPython add little over `subprocess`. Pick
  one approach.
- **One status call covers most checks.**
  `git status --porcelain=v2 --branch --show-stash -z` returns:

  - the branch name, or `(detached)`
  - `(initial)` for a repo with no commits
  - the upstream (missing means proactive 4 applies)
  - ahead/behind counts
  - staged, unstaged, untracked and unmerged entries
  - the stash count

  That covers about eight conditions in one parse (checked against git 2.55).
- **Missing implementations:** conflicts, behind, no upstream, no commits yet,
  gitignore candidates, stash.
- **3.5 vs. the CLI:** link titles are tooltips, and a terminal has nowhere to
  show them. Decide how the Markdown gets rendered.
- **3.2:** a user is often in several "stages" at once, and "stage" collides
  with "staging". Try "area" (the area the hint is about). For 3.4,
  text-fragment links (`#:~:text=`) would make the idea concrete.
- **`explain` ([L137](ideas.md#L137)):**
  - Typer will try to parse the git command's flags (`explain pull --rebase`)
    unless you set `allow_extra_args`/`ignore_unknown_options`.
  - Say whether the argument includes the word `git`.
  - Piping stdout breaks commands that open an editor (`commit` without `-m`,
    `rebase -i`). Capturing only stderr and the exit code is probably enough.
- **Intent vs. hints:** 5.1 (estimate intent) isn't used by any hint, while
  [L100](ideas.md#L100) and [L103](ideas.md#L103) guess intent anyway. Also,
  [L100](ideas.md#L100) doesn't define "50% of what?"

Testing section
---------------

- **Isolate tests from the machine's git config.** Otherwise results vary by
  machine:

  - The identity hint fires or not depending on the global config.
  - The main/master hint depends on `init.defaultBranch`; on some machines
    `git init` creates `master`.

  Fix this with `GIT_CONFIG_GLOBAL` pointing to a temp file,
  `GIT_CONFIG_NOSYSTEM=1`, the identity env vars, and `git init -b main`.
- **Remotes must be bare.** Pushing to a non-bare repo's checked-out branch is
  refused. Also, `git remote add` neither fetches nor sets an upstream; it's
  often simpler to `git clone` the remote.
- **Shell strings aren't portable** ([L245](ideas.md#L245)). On Windows,
  `shell=True` runs cmd.exe, where `git commit -m 'msg here'` splits at the
  space. Use argv lists.
- **Avoid changing directories.** Add a `-C <path>` option like git's, or use
  `monkeypatch.chdir`, and invoke through `typer.testing.CliRunner`.
  `make_temps` can wrap `tmp_path_factory`.
- **Bundles can't capture the hard cases.** A bundle stores only refs and
  objects: no remotes, upstream config or index. `git stash` refuses when there
  are unmerged paths, so conflict states can't be cached this way. It also
  needs `-u` for untracked files and `pop --index`.
  - **Answer to the TODO:** zip the whole temp tree, with remotes stored as
    relative paths (`../remote-1`) so it can be moved. Key the cache on a hash
    of the command list, and replace the lambdas with data such as
    `("write", "a.txt", "text")` so the list can be hashed.
  - Measure first, though: replaying about 20 git commands likely takes only a
    second or two, so caching may not be worth it.
- **Numbered steps:** steps 1 and 3 are future work mixed in with current
  steps. Split them out.
- **Test case 1 is wrong** ([L271](ideas.md#L271)). It has no `git init`, and
  a new file in a new repo is untracked, so it triggers the untracked-files
  hint and "no commits yet", not "stage changed files". It should init, commit,
  then modify the file. Assert on hint IDs rather than exact text.

Nits
----

- **Typos:** [L35](ideas.md#L35) "a 1 or more", [L246](ideas.md#L246)
  "populate", [L286](ideas.md#L286) "dont", [L293](ideas.md#L293) "Theres",
  [L318](ideas.md#L318) "stuggled".
- **Spacing and punctuation:** double spaces at [L132](ideas.md#L132) and
  [L223](ideas.md#L223); a double colon at [L137](ideas.md#L137); a trailing
  space inside the code span at [L125](ideas.md#L125); no space before
  "(raf322)" at [L227](ideas.md#L227).
- **Stray `<br>` and mixed list spacing** at [L41](ideas.md#L41),
  [45](ideas.md#L45), [120](ideas.md#L120), [215](ideas.md#L215). This looks
  like an editor round-trip artifact.
- **`set_remotes(local, repo 1, repo 2)`:** use `repo1, repo2`, and say which
  remote name each one gets.
- **Hint template and links:** many hints skip the "Question? Conditions:"
  format or leave out the command and doc link that 3.1/3.3 require. Proactive
  11 and 12 have no author.
- **Deleted CodeChat idea:** the uncommitted diff removes ewj55's CodeChat
  idea. To keep their credit, move it (along with [L61](ideas.md#L61)) to a
  future-work/GUI section instead.
