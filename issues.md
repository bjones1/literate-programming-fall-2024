Review of ideas.md
==================

This reviews [ideas.md](ideas.md) as of commit c787e3c, which merges sbe80's
commit 6daa871 with f5d4e14. All line numbers refer to that version. Each issue
names the one person assigned to fix it.

The merge lost two items
------------------------

sbe80's commit 6daa871 was based on 1f3f6b1, before f5d4e14 added the items
below. When merge c787e3c resolved the conflict in favor of 6daa871, these items
disappeared. Restore them from `git show f5d4e14:ideas.md`.

1. *(RESOLVED) Assigned: sbe80.* **raf322's "Committing to protected/main
   branch" hint (was Proactive 15).** Its implementation at
   [L241](ideas.md#L241) is still there but now implements a requirement that no
   longer exists, and "15" now belongs to the `git reset` hint. When restoring
   it:

   * Remove the trailing space inside the `git switch -c <name>` code span.
   * Its condition, "the user attempts to commit," can't be observed (see design
     problem 1). "The current branch is main/master and there are changes" can.
2. *(RESOLVED) Assigned: sbe80.* **drj228's `git-hints explain <git command>`
   (was requirement 2.5).** This is the only way the tool can see a failed
   command. Without it, reactive hints 3, 4 and 7 and the `git reset` hint have
   no way to detect their triggers. When restoring it:

   * Typer will try to parse the git command's flags (`explain pull --rebase`)
     unless you set `allow_extra_args`/`ignore_unknown_options`.
   * Say whether the argument includes the word `git`.
   * Piping stdout breaks commands that open an editor (`commit` without `-m`,
     `rebase -i`). Capturing only stderr and the exit code is probably enough.

A merge that silently drops someone else's work is a good example for the
personal-experience section, and a good test case for the tool.

Main design problems
--------------------

1. *Assigned: ewj55.* **Several conditions can't be seen by a CLI you run on
   demand.** The tool sees the repo's state when it runs, but not the results of
   commands the user ran earlier. These hints depend on exactly that:

   * "a git pull fails…" ([L27](ideas.md#L27), [L30](ideas.md#L30))
   * "attempted a push and it failed" ([L37](ideas.md#L37))
   * "five failed pushes or pulls in a row" ([L128](ideas.md#L128))
   * editing in a commit or diff view, which is an editor event
     ([L65](ideas.md#L65))
   * a timer, which needs a background process ([L105](ideas.md#L105))

   Each one should either be tied to `git-hints explain` (once it's restored),
   rewritten as a state condition, or moved to a future-work/GUI list. Merge
   conflicts don't need the failed pull at all: they show up in repo state as
   unmerged paths (`git diff --name-only --diff-filter=U`) plus `MERGE_HEAD` or
   the rebase directories.

2. *RESOLVED Assigned: ams2083.* **Duplicate hints.** With a cap of three hints, these
   crowd out everything else:

   * Push ([L33](ideas.md#L33)) is the same as sync indicator
     ([L68](ideas.md#L68)). The implementation also repeats itself:
     [L205](ideas.md#L205) and [L215](ideas.md#L215) both use `git status -sb`.
   * Pull needed ([L35](ideas.md#L35)) is the same as Pull remote changes
     ([L53](ideas.md#L53)).
   * Review staged ([L73](ideas.md#L73)) and Commit staged ([L87](ideas.md#L87))
     fire on the same condition, and [L21](ideas.md#L21) also suggests `git diff
     --cached`.
   * Pull-with-uncommitted-changes ([L30](ideas.md#L30)) and stashes
     ([L40](ideas.md#L40)) share a trigger.
   * gitignore ([L44](ideas.md#L44)) and untracked files ([L94](ideas.md#L94))
     overlap.
   * When the branch has diverged ([L130](ideas.md#L130)), Push and both Pull
     hints fire too, filling all three slots. The diverged hint should replace
     them.
3. *RESOLVED Assigned: jhg246.* **"Behind" and "diverged" are stale without a fetch.**
   Ahead/behind is measured against the last-fetched remote-tracking branch. The
   doc needs a fetch policy. Fetching on every run is slow, needs network, and
   can hang on a credential prompt (use `GIT_TERMINAL_PROMPT=0` plus a timeout).
   The alternative is to label the result "as of last fetch".

4. *Assigned: jit45.* **No priority order.** 4.2 ([L175](ideas.md#L175)) only
   puts failures and conflicts first, and 4.3 ([L181](ideas.md#L181)) says hints
   have priorities without saying what they are. Merge the two and give an
   actual ranking. With about 25 hints and a cap of three, every hint needs a
   rank, for example: error/blocked → risk of losing data → workflow →
   informational.

5. *Assigned: drj228.* **Dismissal isn't specified.** 4.2 needs:

   * a dismiss command
   * stable hint IDs. 4.5 ([L187](ideas.md#L187)) now asks for IDs; make them
     fixed names like `diverged` or `push-ahead`, not list positions. The lost
     merge shows why: "Proactive 15" now points to a different hint.
   * somewhere to store state (such as `.git/git-hints/`)
   * a definition of when a "triggering condition changes"
6. *Assigned: jit45.* **The category list mixes hints and commands.** Items 2.3
   and 2.4 (`def`, `howto`) are subcommands, `git-hints all` is buried in 4.1,
   and plain `git-hints` isn't specified at all. A separate "CLI commands"
   requirement would fix this. "Reactive" and "proactive" are also never
   defined. The reactive list includes pure state checks (items 1, 2, 5, 6, 9),
   while the proactive list includes a failure-triggered hint (15, `git reset`).
   One natural split:

   * **Reactive:** triggered by a command's result, via `explain`.
   * **Proactive:** triggered by repo state.

Recent additions (6daa871)
--------------------------

* *(Updated) Assigned: sbe80.* **`git reset` hint ([L124-128](ideas.md#L124)):**
  * **It's risky advice.** It targets the most confused users at the moment
    they're most likely to have work that isn't pushed yet. Under the safety
    scale in 4.4, `reset --hard` is "highly destructive." Better options are
    `git stash`, `git pull --rebase`, or recovering through `git reflog`. If
    `reset` stays, the hint should name the mode and the target (e.g. `--hard
    @{upstream}`) and tell the user to run `git branch backup` first.
  * **The tool can't see the trigger** (see design problem 1).
  * **It's in the wrong list.** It's triggered by failures, so it belongs in
    Reactive.
* *RESOLVED Assigned: jhg246.* **Diverged hint ([L130](ideas.md#L130)):**
  * It doesn't follow the required hint format: no "Conditions:", no command, no
    doc link (3.1/3.3).
  * It should tell the user what to do: `git pull` or `git pull --rebase`, then
    `git push`.
* *RESOLVED Assigned: jhg246.* **Safety levels (4.4, [L184](ideas.md#L184)):** define the
  three levels and say what each one changes in the output. One way to draw the
  lines:
  * *safe*: read-only or only adds.
  * *potentially destructive*: recoverable through the reflog.
  * *highly destructive*: loses uncommitted work (`reset --hard`, `clean -fd`,
    `push --force`).
* *Assigned: jit45.* **`--help` items ([L139](ideas.md#L139),
  [L147](ideas.md#L147)):** Typer already generates `--help` for every command
  and subcommand from its docstring, so these come free. A more useful
  requirement would be that each docstring includes an example. Also, "hints
  def" and "hints howto" should be `git-hints def` and `git-hints howto`.
* *Assigned: ewj55.* **Links to non-official sites:** the stash, reset and
  git-status links ([L41](ideas.md#L41), [L125](ideas.md#L125),
  [L211](ideas.md#L211)) go to geeksforgeeks or w3schools, as does the older
  Stage link ([L17](ideas.md#L17)). 3.3 requires links to the official docs. The
  stash link's title, "Stores the present state of the local repo," is also
  wrong: a stash saves uncommitted changes and then resets the working tree.

Technical corrections
---------------------

* *RESOLVED Assigned: jhg246.* **[L37](ideas.md#L37):** a push isn't rejected for
  "conflicting file changes". It's rejected as non-fast-forward because the
  remote has commits you don't. The fix is pull, then push; `git diff filename`
  doesn't help.

* *Assigned: raf322.* **[L45](ideas.md#L45):** `__pycache__.py` should be
  `__pycache__/`. Also, if `.env` is already tracked, adding it to `.gitignore`
  does nothing; the hint also needs `git rm --cached`.

* *Assigned: drj228.* **[L83](ideas.md#L83):** without `--global`, `git config
  user.name` applies to the current repo only. Students almost always want
  `--global`.

* *Assigned: jit45.* **[L109](ideas.md#L109):** HEAD is normally detached during
  a rebase or bisect. Exclude those cases, or the tool will wrongly suggest `git
  switch -c` in the middle of a rebase.

* *RESOLVED Assigned: ams2083.* **[L210-213](ideas.md#L210):** this item gives a link
  where it should give a command and what its output means. `git rev-parse
  --is-inside-work-tree` exits with 128 outside a repo. GitPython's `Repo()`
  raises `InvalidGitRepositoryError` when it's constructed, not a command exit
  code.

* *RESOLVED Assigned: jhg246.* **[L217](ideas.md#L217):** `git diff HEAD...@{upstream}`
  shows what a pull would bring in, not help with conflicts, and it names no
  file.

* *Assigned: raf322.* **[L243](ideas.md#L243):** `git branch -a` output is
  awkward to parse (`remotes/origin/HEAD -> origin/main`, `*` markers). `git
  for-each-ref --format='%(refname:short)' refs/heads refs/remotes` is cleaner.

* *Assigned: drj228.* **Exit codes and GitPython ([L220](ideas.md#L220),
  [L225](ideas.md#L225), [L235](ideas.md#L235)):** these checks rely on exit
  codes, but GitPython raises `GitCommandError` on any non-zero exit unless you
  pass `with_exceptions=False`. More broadly, the doc specifies raw CLI commands
  everywhere, which makes GitPython add little over `subprocess`. Pick one
  approach.

* *Assigned: ewj55.* **One status call covers most checks.** `git status
  --porcelain=v2 --branch --show-stash -z` returns:

  * the branch name, or `(detached)`
  * `(initial)` for a repo with no commits
  * the upstream (missing means proactive 4 applies)
  * ahead/behind counts, which also detect divergence
  * staged, unstaged, untracked and unmerged entries
  * the stash count

  That covers about eight conditions in one parse (checked against git 2.55). It
  also replaces the three items that parse `git status -sb`
  ([L205](ideas.md#L205), [L215](ideas.md#L215), [L246](ideas.md#L246)).
  `--porcelain` output is guaranteed stable across Git versions and user config;
  `-s` output isn't.

* *RESOLVED Assigned: ams2083.* **Missing implementations:** conflicts, behind (only the
  diverged case at [L246](ideas.md#L246) is covered), no upstream, no commits
  yet, gitignore candidates, stash, and the failure count for the `git reset`
  hint.

* *Assigned: drj228.* **3.5 vs. the CLI:** link titles are tooltips, and a
  terminal has nowhere to show them. Decide how the Markdown gets rendered.

* *Assigned: ewj55.* **3.2:** a user is often in several "stages" at once, and
  "stage" collides with "staging". Try "area" (the area the hint is about). For
  3.4, text-fragment links (`#:~:text=`) would make the idea concrete.

* *Assigned: jit45.* **Intent vs. hints:** 5.1 (estimate intent) isn't used by
  any hint, while [L102](ideas.md#L102) and [L105](ideas.md#L105) guess intent
  anyway. Also, [L102](ideas.md#L102) doesn't define "50% of what?"

Testing section
---------------

* (RESOLVED) *Assigned: sbe80.* **Isolate tests from the machine's git config.**
  The TODO at [L277](ideas.md#L277) lists the fix, but it isn't done yet. Until
  it is, results vary by machine:

  * The identity hint fires or not depending on the global config.
  * The main/master hint depends on `init.defaultBranch`; on some machines `git
    init` creates `master`.
* *Assigned: sbe80.* **Remotes must be bare** ([L270](ideas.md#L270)). Pushing
  to a non-bare repo's checked-out branch is refused. Also, `git remote add`
  neither fetches nor sets an upstream; it's often simpler to `git clone` the
  remote.

* *Assigned: drj228.* **Shell strings aren't portable** ([L267](ideas.md#L267)).
  On Windows, `shell=True` runs cmd.exe, where `git commit -m 'msg here'` splits
  at the space. Use argv lists.

* *Assigned: sbe80.* **Avoid changing directories** ([L274](ideas.md#L274)). Add
  a `-C <path>` option like git's, or use `monkeypatch.chdir`, and invoke
  through `typer.testing.CliRunner`. `make_temps` can wrap `tmp_path_factory`.

* *Assigned: sbe80.* **Test case 1 is wrong** ([L281](ideas.md#L281)). It has no
  `git init`, and a new file in a new repo is untracked, so it triggers the
  untracked-files hint and "no commits yet", not "stage changed files". It
  should init, commit, then modify the file. Assert on hint IDs rather than
  exact text.

Nits
----

* *Assigned: raf322.* **Typos:** [L35](ideas.md#L35) "a 1 or more",
  [L124](ideas.md#L124) "explaing", [L139](ideas.md#L139) and
  [L147](ideas.md#L147) "comand", [L267](ideas.md#L267) "populate",
  [L297](ideas.md#L297) "dont", [L303](ideas.md#L303) "Theres",
  [L330](ideas.md#L330) "stuggled".
* *Assigned: raf322.* **Spacing:** non-breaking spaces (U+00A0), probably pasted
  in, at [L139](ideas.md#L139), [L147](ideas.md#L147), [L241](ideas.md#L241),
  [L246](ideas.md#L246) and [L247](ideas.md#L247); L247 also ends with a
  trailing space. No space before "(raf322)" at [L245](ideas.md#L245).
* *Assigned: ams2083.* **Stray `<br>`** at [L43](ideas.md#L43),
  [L47](ideas.md#L47), [L132](ideas.md#L132) and [L233](ideas.md#L233). This
  looks like an editor round-trip artifact.
* *Assigned: raf322.* **Implementation numbering:** the source numbers go 1, 2,
  4, 4, 5, …, 10, 12 ([L203-246](ideas.md#L203)). Markdown renumbers lists when
  rendering, so the page shows 1–11 and references like "item 1.12" don't match
  what readers see. Renumber the source, and refer to hints by ID.
* *(RESOLVED) Assigned: sbe80.* **`set_remotes(local, repo 1, repo 2)`:** use
  `repo1, repo2`, and say which remote name each one gets.
* *RESOLVED Assigned: ams2083.* **Hint template:** many hints skip the "Question?
  Conditions:" format or leave out the command and doc link that 3.1/3.3
  require; the diverged hint is the latest. Proactive 11 and 12
  ([L102](ideas.md#L102), [L105](ideas.md#L105)) have no author.
* *Assigned: ewj55.* **Deleted CodeChat idea:** f5d4e14 removed ewj55's CodeChat
  idea (was requirement 6). To keep their credit, move it, along with the editor
  read-only hint at [L63](ideas.md#L63), to a future-work/GUI section.
