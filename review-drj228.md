Review of spec section 6 (drj228)
=================================

This section (spec.md lines 1026-1230) introduces `git-hints explain` and
specifies three reactive hints, `merge-conflicts`,
`pull-blocked-local-changes` and `stash-local-changes`, plus a one-paragraph
"Push failed?" item. The test cases are concrete, and I confirmed with Git
2.56 that their setup steps produce the states they claim. The detection
logic has gaps, though. `pull-blocked-local-changes` and
`stash-local-changes` react to byte-identical Git diagnostics, and the spec
never says how to find the subcommand that tells them apart.
`merge-conflicts` gives merge-only advice for conflicts that rebase, cherry-pick
and `git stash pop` also create. The push item is not yet a hint, and the
`pull-blocked-local-changes` entry has broken Markdown.

All experiments ran in an isolated environment matching `git_setup()` (scratch
`HOME`, `GIT_CONFIG_GLOBAL` with `init.defaultBranch = main`,
`GIT_CONFIG_NOSYSTEM=1`, `GIT_CEILING_DIRECTORIES`, `GIT_TERMINAL_PROMPT=0`,
`GIT_EDITOR=true`, `LC_ALL=C`). I used local bare remotes and captured stdout
and stderr separately.

### Correctness and detection

1. **`pull-blocked-local-changes` and `stash-local-changes` cannot be told
   apart from Git's output, and the spec never says how to find the
   subcommand that separates them.**
   * Location: `pull-blocked-local-changes` Conditions (line 1109) and
     `stash-local-changes` Conditions (line 1200); the `explain` introduction
     (line 1030) has no rule for parsing the command.
   * `git pull` runs a merge internally. It prints exactly the same stderr as
     `git merge`, including "by merge" and "before you merge", so only the
     subcommand distinguishes the two hints. A naive `argv[1]` check fails for
     `git -C dir pull`, `git -c pull.rebase=false pull` and aliases. The same
     diagnostic also comes from `git checkout <branch>`, `git cherry-pick` and
     `git stash apply`, which neither hint covers. Suggesting `git stash push`
     after a failed `git stash apply` would be wrong.
   * Verified: with an unstaged change to `foo.txt` that the incoming commit
     also changes, `git pull`, `git merge topic` and `git -C . merge topic`
     each wrote this to stderr:
     `error: Your local changes to the following files would be overwritten
     by merge:` / `<TAB>foo.txt` / `Please commit your changes or stash them
     before you merge.` / `Aborting`. `git cherry-pick topic` (exit 128) and
     `git stash apply` (exit 128) wrote the same lines. `git switch topic` and
     `git checkout topic` both wrote `... would be overwritten by checkout:`,
     exit 1.
   * Fix: add a rule to the `explain` introduction: "Identify the subcommand
     as the first argument after `git` that is not a global option. Skip
     `-C <path>`, `-c <name>=<value>`, `--git-dir`, `--work-tree`,
     `--no-pager` and other options in `git --help`. If the subcommand is an
     alias, treat it as unrecognized." Then map the subcommands explicitly:
     `pull` goes to `pull-blocked-local-changes`; `merge`, `switch` and
     `checkout` go to `stash-local-changes`. Every other subcommand that
     produces this diagnostic gets no hint, or a deliberately chosen one. Add
     `checkout` to the `stash-local-changes` Conditions and Git stage.

2. **`merge-conflicts` assumes every conflict comes from a merge, but rebase,
   cherry-pick and `git stash pop` leave the same unmerged entries, so the
   hint gives a wrong completion command.**
   * Location: Resolve merge conflicts, Hint and Command (lines 1035-1047).
   * The hint says "before the merge can finish" and "Complete the merge with
     `git commit`". After `git pull --rebase` the right step is
     `git rebase --continue`. After `git stash pop` no merge is in progress:
     the stash is kept and a commit is not wanted.
   * Verified: `git pull --rebase` with a conflicting local commit exited 1;
     `git diff --name-only --diff-filter=U` printed `foo.txt`; `.git` held
     `rebase-merge` and `REBASE_HEAD` but no `MERGE_HEAD`. A conflicting
     `git stash pop` exited 1, listed `foo.txt` as unmerged, printed "The
     stash entry is kept in case you need it again." and created no
     `MERGE_HEAD`.
   * Also verified: in a modify/delete conflict (`UD b.txt`) the file has no
     conflict markers to edit, so "Edit each file to resolve its conflict
     markers" does not apply. Run from a subdirectory `sub`,
     `git diff --name-only --diff-filter=U` printed `sub/a.txt`, a path
     relative to the repository root, so the suggested `git add <file>`
     fails from that directory.
   * Fix: detect the operation the same way `detached-head` does. Check
     `git rev-parse --git-path` for `MERGE_HEAD`, `rebase-merge`,
     `rebase-apply`, `CHERRY_PICK_HEAD` and `REVERT_HEAD`. Suggest
     `git commit`, `git rebase --continue`, `git cherry-pick --continue` or
     `git revert --continue` to match. If none of them exists (for example
     after a stash pop), tell the user to stage the resolved files and keep
     the stash until the work is verified. Add: "Resolve deleted-versus-
     modified files with `git add <file>` or `git rm <file>`." State that the
     listed paths are relative to the repository root, or display them with
     `git status`. Change the title to "Resolve conflicts?" and consider
     offering the abort command for each operation.

3. **The trigger rule for `merge-conflicts` contradicts the CLI's "no error
   detected" rule and fails outside a repository.**
   * Location: Resolve merge conflicts, Conditions (line 1051); CLI
     commands item 4 (line 98).
   * "Leaves the repository with ... unresolved merge conflicts" also matches
     conflicts that already existed before the command ran. Running
     `git-hints explain -- git status` during a conflict exits 0, so CLI
     item 4 requires the note "no error detected", while the Conditions
     require this hint. The spec does not say which wins. Other commands that
     run while a conflict is unresolved fail for a reason this hint explains
     well, so showing it is useful.
   * Running `git diff --name-only --diff-filter=U` outside a repository
     (for example after a failed `git-hints explain -- git clone ...`) exits
     129. Under the Language and libraries rules that is an "unexpected
     inspection failure", reported on every `explain` outside a repository.
   * Verified: while a merge conflict was unresolved, `git status` exited 0,
     `git switch topic` exited 128 ("fatal: cannot switch branch while
     merging"), and `git commit -m x` exited 128 ("Committing is not possible
     because you have unmerged files."). Outside any repository,
     `git diff --name-only --diff-filter=U` exited 129 with "warning: Not a
     git repository".
   * Fix: "Run the conflict check only when
     `git rev-parse --is-inside-work-tree` exits 0 and prints `true`. Display
     this hint whenever unmerged paths exist after the command, whatever its
     exit code. When the command exited 0, display this hint instead of the
     no-error note." Amend CLI item 4 to match.

4. **The Conditions do not say which stream each diagnostic is on. Two of
   them break under the stdout-not-captured rule.**
   * Location: all three Conditions fields and item 3; Language and
     libraries item 6 (line 1373).
   * Verified streams, with stdout and stderr redirected to separate files:
     * Merge conflicts: `Auto-merging`, `CONFLICT (content): Merge conflict
       in foo.txt` and `Automatic merge failed` go to **stdout**, and so are
       not captured. A conflicting `git stash pop` writes nothing at all to
       stderr. State-based detection with `--diff-filter=U` still works, but
       the spec should forbid matching `CONFLICT` in stderr.
     * Blocked pull, merge or switch: `error: Your local changes ...`, the
       file list and `Aborting` go to **stderr**. Only `Updating a..b` goes
       to stdout. The detection works.
     * Rejected push: `To <url>`, ` ! [rejected] main -> main (fetch first)`
       and the `hint:` lines go to **stderr**. But `git push --porcelain` moves
       the status line (`!<TAB>refs/heads/main:refs/heads/main<TAB>[rejected]
       (non-fast-forward)`) to **stdout**, leaving only `error: failed to push
       some refs` and the `hint:` lines on stderr.
   * Git also leaves out optional lines depending on configuration.
     `-c advice.commitBeforeMerge=false` removed "Please commit your changes
     or stash them before you merge." `-c advice.pushFetchFirst=false` and
     `-c advice.pushNonFFCurrent=false` removed every `hint:` line from a
     rejected push.
   * Fix: in each Conditions field, name the stream and the line that the
     detection relies on, choosing lines that advice settings cannot turn
     off: the `error: Your local changes to the following files would be
     overwritten by` header, and the ` ! [rejected] ... (fetch first)` or
     `(non-fast-forward)` status line. Say that `merge-conflicts` is purely
     state-based. Either accept that `push --porcelain` is not detected or
     exclude it.

5. **`pull-blocked-local-changes` leaves "supported pull arguments"
   undefined and misses the most common blocked-pull message.**
   * Location: `pull-blocked-local-changes` Conditions (lines 1109-1122).
   * If a pull rebases (`--rebase` or `pull.rebase=true`), Git refuses to
     run when any tracked change is unstaged, even one that does not overlap
     the incoming commits. It lists no files and prints a different message.
     Untracked files that would be overwritten produce a third message, which
     no hint covers; the default stash would not help there.
   * Verified: `git pull --rebase` with an unstaged change exited 128 with
     `error: cannot pull with rebase: You have unstaged changes.` /
     `error: Please commit or stash them.`. A fast-forward pull or merge
     blocked by local changes exited 1. A non-fast-forward `git merge topic`
     exited 2 and added `Merge with strategy ort failed.`. With an unrelated
     staged file, a non-fast-forward merge exited 2 and listed `  other.txt`
     with two spaces, not a tab, and no "Please commit" line. An untracked
     `bar.txt` produced `error: The following untracked working tree files
     would be overwritten by merge:` / `Please move or remove them before you
     merge.`
   * Fix: replace "including supported pull arguments" with an explicit
     list. Cover the rebase refusal (`cannot pull with rebase: You have
     unstaged changes` and the staged-changes variant) with wording that
     lists no files. For file extraction, take the indented lines that
     follow the header, whether they start with a tab or with spaces, and
     stop at the first line that is not indented. Don't assume a particular
     nonzero code: 1, 2 and 128 all occur. Say explicitly that untracked-file
     conflicts trigger neither hint, or give them a hint of their own.

6. **Matching English diagnostics breaks under a non-English locale, and the
   `explain` rules do not set a locale.**
   * Location: Conditions of both stderr-based hints; Language and libraries
     item 6.
   * The tests force `LC_ALL=C`, but `explain` runs in the user's
     environment. A localized Git would print translated messages, so no
     hint would match, and nothing in the spec would show it.
   * Not verified: this Git for Windows build printed English even with
     `LANG=de_DE.UTF-8 LANGUAGE=de`, so I could not observe translated
     output.
   * Fix: decide and state one of these: run the user's command with
     `LC_ALL=C` (or `LANGUAGE=C`) so that detection is reliable, at the cost
     of English output; or note that reactive hints only recognize English
     diagnostics and fall back to the no-error/unknown-error path otherwise.

### Structure and missing content

7. **Item 3 "Push failed?" is not a hint yet. It has no ID, Git stage,
   command, priority, documentation link or test case, and its numbering
   breaks the list.**
   * Location: line 1175.
   * Without an ID it cannot be tested or excluded. The obvious advice, a
     plain `git pull`, fails in the common case where both sides have new
     commits, so the command needs to be spelled out.
   * Verified: after another clone pushed, `git push` exited 1 with
     ` ! [rejected]        main -> main (fetch first)` on stderr. After
     `git fetch`, it printed `(non-fast-forward)` instead. In the same
     diverged state, a plain `git pull` exited 128 with "fatal: Need to
     specify how to reconcile divergent branches."; `git pull --no-rebase`
     worked. A remote hook rejection printed `! [remote rejected] feat ->
     feat (pre-receive hook declined)`, exit 1. A branch with no upstream
     printed "fatal: The current branch feat has no upstream branch.", exit
     128.
   * Fix: replace the item with a full hint, for example:
     * Heading: `#### Integrate remote commits before pushing? (jhg246)`.
     * Hint: "Your [git push](https://git-scm.com/docs/git-push#_note_about_fast_forwards
       "Git rejects pushes that would discard commits already on the
       remote.") was rejected because the remote branch has commits your
       branch lacks."
     * Git stage: "Your commits are in the local repository; the remote
       repository has commits your local branch does not contain yet."
     * Command: "`git pull --no-rebase`, resolve any conflicts, then
       `git push`; afterward, the push succeeds." Mention
       `Caution: git pull --rebase` as the alternative, as `diverged` does.
       Never suggest `--force`.
     * ID: `push-rejected-remote-ahead`, priority class: error/blocked,
       safety: safe.
     * Conditions: the subcommand is `push`; the exit code is nonzero; stderr
       has a ` ! [rejected] ` line ending in `(fetch first)` or
       `(non-fast-forward)`. Do not trigger for `[remote rejected]`,
       `(stale info)`, a missing upstream (that is `no-upstream-branch`'s job)
       or network and authentication failures. Say how this hint interacts
       with `rebase-after-repeated-integration-failures`, which also counts
       failed pushes; both may appear, with this one first by priority.
     * Test case: reuse the setup above. Assert the hint for both
       `(fetch first)` and `(non-fast-forward)`. Assert it is absent after
       `git pull --no-rebase` followed by a successful push, and absent for
       a push from a branch without an upstream.
   * Number it in sequence or, better, use the `####` heading and bullet
     format of the neighboring hints.

8. **A fenced code block and some unindented paragraphs break the
   `pull-blocked-local-changes` bullet list.**
   * Location: lines 1101-1105 (fence) and lines 1113-1131 (Conditions).
   * The fence sits at column 0, so it ends the bullet list. Its prose
     renders as one unwrapped monospace line about 600 characters long. Its
     inline code (`git stash push ...`) shows literal backticks, and the
     `ID:` bullet after it starts a new list. The four paragraphs after
     "Conditions:" are also at column 0. They therefore read as body text of
     the section rather than conditions, and they split the Test case off
     into a separate list.
   * Fix: delete the fence lines and indent the two paragraphs by two spaces
     so they continue the Command bullet, wrapped at 80 columns. Indent
     lines 1113-1131 by two spaces so they stay inside the Conditions bullet.

9. **The two "local changes" hints duplicate each other but disagree on what
   to do, and `pull-blocked-local-changes` misuses `Warning:`.**
   * Location: `pull-blocked-local-changes` Command (lines 1093-1104);
     `stash-local-changes` Command (line 1189).
   * Both hints respond to the same diagnostic. One recommends committing
     first and treats stashing as a fallback; the other recommends only
     stashing. The pull hint's stash paragraph repeats the stash hint almost
     word for word. The `Warning:` prefix is for a suggested command that can
     lose work (Hint structure item 6), but here it introduces
     `git stash drop`, a command the hint tells the user *not* to run. That
     draws attention to the dangerous command. The text also says the stash
     saves "index changes" and then suggests `git stash apply`. Without
     `--index`, apply does not restore what was staged.
   * Fix: give both hints the same advice in the same order (commit, or
     stash, then retry the original command, then `git stash apply`). Write
     it once and refer to it from the other hint. Delete the
     `git stash drop` sentence. Add "Staged changes come back unstaged unless
     you use `git stash apply --index`." Keeping two IDs is fine; only the
     command to retry differs between them.

10. **`stash-local-changes` has no hint text or documentation link; its
    fields are instructions to the implementer.**
    * Location: lines 1182-1196.
    * The Hint field reads "Explain that a stash temporarily saves ...", and
      the Command field says "Show `git status` ... then suggest ...". There
      is no link with a title of 160 characters or fewer, which Hint
      structure items 3 and 5 require. The test (line 1224) checks for
      content the spec never actually states.
    * Fix: write the user-facing text, for example: "Git stopped the
      `<command>` because it would overwrite your uncommitted changes to
      `<files>`. You can save them temporarily with
      [git stash](https://git-scm.com/docs/git-stash "Saves uncommitted
      changes to tracked files and restores a clean working tree.") and
      retry." Give the Command field as the literal command sequence with
      its expected result.

### Test cases

11. **The reactive tests check output that the spec never defines.**
    * Location: test steps at lines 1076, 1155, 1222.
    * The Testing section says to check presence with
      `git-hints --all --ids-only`, but `explain` has neither option, and
      running the Git command a second time to get IDs would change the
      repository. "Has error/blocked priority" cannot be tested: nothing in
      Hint structure says the class is printed. No test checks that the
      other "local changes" hint is *absent*, which is the only real check of
      finding 1. `stash-local-changes` has no `switch` case, and
      `merge-conflicts` has no negative case.
    * Verified: every setup in the three tests produced the stated state.
      `git pull --no-rebase` exited 1 with `foo.txt` unmerged. The blocked
      `git pull` exited 1, left `foo.txt` unchanged and left no unmerged
      entries; after `git restore foo.txt` the retry exited 0 and fast-
      forwarded. The blocked `git merge topic` exited 1 and kept
      `local change`. Step 7 of the merge test correctly uses
      `--no-rebase`: a plain `git pull` exits 128 there (finding 7).
    * Fix: specify how tests read IDs from `explain` output, either by
      parsing the `ID: <id>` lines that Hint structure item 7 defines or by
      adding `--ids-only` to `explain`. Replace the priority assertion with an
      ordering check, or say that the output shows the class. Add these
      cases: `pull-blocked-local-changes` asserts `stash-local-changes` is
      absent and vice versa; `git-hints explain -- git switch topic` with a
      blocking change; `merge-conflicts` absent after a failed
      `git merge nonexistent` and present after a conflicting
      `git pull --rebase` with `git rebase --continue` advice (finding 2).
      Use `make_temps()` and `make_repo()` as the Testing section asks. Drop
      the explicit `git_setup()` calls, which the autouse fixture already
      makes.

### Consistency

12. **Heading levels and author tags are inconsistent.**
    * Location: line 1033 `### Resolve merge conflicts? **sbe80**`.
    * This heading is at the same level as `### git-hints explain ...`
      (line 1028). The section's other hints use `####`, so it is not nested
      under `explain` in the outline. The bold author tag differs from the
      `(netid)` form used elsewhere.
    * Fix: `#### Resolve conflicts? (sbe80)`.

### Minor

* Line 1028: the heading form `git-hints explain -- git <command>` differs
  from CLI item 4's `git-hints explain -- <git command>`. Choose one.
* Line 1031: the introduction should point to CLI item 4 and Language and
  libraries item 6 for the shared execution rules, and should say whether
  `explain` also shows proactive hints and whether a display limit applies.
* Line 1036: the link title "Join two or more development histories
  together" describes merging, not conflicts. Link to
  `https://git-scm.com/docs/git-merge#_how_to_resolve_conflicts` instead.
* Line 1133: the test is titled "Resolve pull conflicts", but it tests a
  blocked pull that produces no conflict. Drop "formerly Test Case 13".
* Line 1187: "a `git merge` or `git switch` was blocked" should add
  `git checkout` (finding 1).
* Line 1102: "Resolve any conflicts before continuing" should say how, or
  refer to `merge-conflicts`.

---

## Final LLM review — drj228

**Model:** Claude Sonnet 5.5  
**Effort:** Medium  
**Date:** October 18, 2026  
**Scope:** Review section 6 of spec.md

I revised section 6 through multiple review rounds. The following prompt
produced the final review reproduced below. Optional suggestions and
shared-rule conflicts are retained as part of the review record.

### Exact prompt

```text
Review the attached updated spec.md, limited to drj228’s section 6.

Verify the previous corrections:
- Push destination resolution uses the explicit repository argument or Git’s
  configured push destination and fetch refspec, with placeholders if unresolved.
- Pull and stash tests cover excluded untracked-file obstructions.
- The “show both hints” rule applies only to plain inspection, and is tested.

Check for remaining relevant correctness, consistency, or test issues.
Suggest only small corrections; do not rewrite sections or expand the scope.
Keep optional improvements and conflicts owned by other reviewers separate.
Do not repeat resolved findings. If no relevant issues remain, say so explicitly.
```

### Final Claude review

**No necessary corrections remain in section 6.** The three corrections from my last review are applied, and I found no new problems in the revisions.

#### Previous necessary corrections: status

| Previous correction | Status |
| --- | --- |
| Push Command: remote name not derivable | Resolved. The Command now resolves the remote from the explicit repository argument or Git’s configured push destination, and the branch from the rejection. |
| Untracked-file negatives for pull-blocked and stash | Resolved. They are folded into pull step 8 and stash step 7. |
| “Show both hints” rule restricted to plain inspection and tested | Resolved. The rule now says “During plain `git-hints` inspection”, and merge-conflicts step 6 asserts both IDs. |

#### Verification

**Executed (Git 2.43.0, isolated environment).** I replayed your new and changed steps as written:

- **Pull-blocked steps 1–9:**
  - Step 4 exits 1 with the index clean and no stash or unmerged entries.
  - A staged pull exits 1.
  - `pull --rebase` prints `cannot pull with rebase: Your index contains uncommitted changes`.
  - Step 7 exits 0 with `remote change` in `foo.txt`.
  - A nonexistent branch exits 1.
  - The untracked `new.txt` pull exits 1 and leaves the local file unchanged.
  - Step 9’s `stash apply` exits 1, `refs/stash` is unchanged, `git stash show -p` contains `local change`, and `foo.txt` is unmerged.
- **Stash steps 2–8:**
  - A blocked merge and a blocked switch both exit 1 and create no stash.
  - After the stash, the merge exits 0.
  - A nonexistent branch exits 128.
  - The untracked-file switch exits 1 and leaves the local file unchanged.
  - `stash apply` exits 1, `refs/stash` is unchanged, and `foo.txt` is unmerged.

From earlier runs this session, the merge-conflicts, push-rejected, and unborn-orphan sequences also behave as written.

**Also checked:** `git rev-parse --abbrev-ref @{push}` returns `origin/main` normally. It fails with `fatal: cannot resolve 'simple' push to a single destination` when `branch.main.pushRemote` differs from the upstream remote. Keep your explicit resolution rule rather than switching to `@{push}`.

**Inspected only:**

- `git-hints` output and formatting, absence checks, and the `-C` skip rule, because the tool is not implemented.
- The three doc anchors (`#_how_conflicts_are_presented`, `#_description`, `#_note_about_fast_forwards`). The manual isn’t installed here and there is no network. Open each anchor.

#### Optional improvements

1. **Push resolution paragraph.**
   - The sentence “Resolve its remote-tracking ref using the configured fetch refspec” has an ambiguous “its”.
   - The explicit-argument and `pushRemote`/`pushDefault` rules are not exercised by any test. Step 7 uses `origin` only on the path that omits merge commands.
   - Either trim to the tested rule (“from the push command’s repository argument, else the current branch’s configured push remote”) or add a step that sets `remote.pushDefault`.
   - The new lines are also unwrapped past 80 columns.
2. **Explain intro (still open).** Delete the clause “display unrecognized diagnostics on stderr”. CLI command 2 already emits all stderr, and the clause implies recognized diagnostics are not shown.
3. **Redirection scope.** pull-blocked, stash, and push-rejected mix a diagnostic with a state check. Say once: “A hint whose Conditions include a state check is skipped when the command redirects the repository.”
4. **Push duplication and wording.**
   - The last Conditions sentence repeats the Command’s “For another source branch…” in different words. Keep one.
   - In step 7, “Retry the original push” should say `git-hints explain -- git push`.
5. **Stash scope.** `git checkout <branch>` produces the same diagnostic and exit 1 (executed earlier). Add it to Conditions, or add one out-of-scope sentence.
6. **Hook rejection.** The `[remote rejected]` negative for push is untested. This is optional because a hook file is OS-specific.
7. **Bundled steps.** Pull step 8, stash step 7, and merge-conflicts step 6 each combine two scenarios. Splitting them makes failures easier to localize.
8. **Pull-blocked Hint.** It hard-codes “Affected files: `<files>`” although Conditions allow omitting it. Append “(omit when unidentified)”.

#### Shared-rule conflicts (not for you to rewrite)

1. **raf322’s `operation-in-progress` Related output** still says `merge-conflicts` “appears only right after a failing command run through `git-hints explain`”. That contradicts Hint structure item 7 and your proactive `merge-conflicts`.
2. **Language and libraries** says `explain` “should also return non zero if Git does not launch or for any unexpected inspection failures”. That contradicts “Always return Git’s exit code” in the same section and CLI command 2. Your tests assume Git’s own exit codes, so they are unaffected unless inspection fails.

If you want to stop here, section 6 is ready as it stands
