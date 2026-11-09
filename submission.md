Project 2 submission
====================

Team members are Yerassyl, Aidana, Madi and Sanzhar. The specification consists of
the file spec.md.

Draft submission
----------------

### Contributions

* Madi: I contributed to `git-hints explain` specification review,
  focusing on command validation, clarification, invalid `--fetch` handling, and repository
  redirection.

### Compiler test

The following statements summarize LLM output on computer,
based on the prompt "Verify that you can compile and run the project in the
current git repo."

#### Madi

Yes. The project compiles and runs successfully.

Results:

python -m compileall -q src — passed.
uv build — passed; source distribution and wheel built successfully.
python -m git_hints --help — passed.
python -m pytest — 58 passed.
Suggested summary for submission.md:

The project compiled successfully, the package built successfully with uv build, the git-hints CLI ran successfully, and all 58 tests passed under Python 3.11.2.

Note: the project package had to be installed from the built wheel into the virtual environment before running the CLI and tests; otherwise the environment reported ModuleNotFoundError: No module named 'git_hints'.

### Spec review rounds

| Round | Findings | Main changes made |
| --- | --- | --- |
| 1 | 7 | Add a short clarification after the existing --fetch requirement; clarified the repository-redirection handling after overlapping behavior was discovered in text |
| 2 | 4 | Defined rejection before Git launches, exit code 2, stderr usage error, and empty stdout; clarified that --fetch after the command separator belongs to Git ; required -C, --git-dir, and --work-tree options to be processed before identifying the Git subcommand; added behavior for cases where the target repository or work tree cannot be identified reliably; removed the unconditional exclusion of redirected commands; associated integration-failure state with the repository targeted by the explained command.  |
| 3 | 3 | Consolidated repository-targeting behavior into the main git-hints explain section and removed/replaced the detached duplicate; defined how --fetch is classified when the separator is omitted: before the first git argument it belongs to git-hints; at or after git it is passed to Git; preserved exit code 2, stderr usage error, empty stdout, and no Git launch for application-level --fetch. |
| 4 | 2 | Validation now occurs after processing applicable git-hints options and the optional -- separator; defined whether --fetch belongs to git-hints or Git based on its position relative to the separator or first git argument; replaced the detached explanatory rule with a cross-reference to the main explain redirection rules; identified remaining encoding corruption in the redirection paragraph (GitвЂ™s). |

### Last LLM review

Using the GPT-5.6 Luna in VSCode Codex, medium effort with the following prompt:

    Review the updated `spec.md`.

    Scope: Only review the `git-hints explain` section.

    Pay particular attention to:

    1. Whether the issues identified in the previous review have been resolved.
    2. Whether the changes introduced new ambiguities or contradictions.
    3. Whether additional important requirements are missing.
    Do not review unrelated sections. Do not suggest unnecessary changes.

    Return findings grouped by severity. If no relevant issues remain, explicitly state that.

Last-draft output produced is:
    
    Low severity
    Encoding corruption remains in the repository-redirection paragraph

    The argument-boundary conflict is resolved: spec.md:53 now validates the Git command after processing applicable options and the optional separator.

    ~~However, spec.md:1573 still contains:

    GitвЂ™s option order

    This should be:

    Git’s option order

    The same paragraph also omits code formatting around command and option names compared with the surrounding specification, but the encoding error is the only remaining issue that could affect readability.

    Minimal clarification: Replace GitвЂ™s with Git’s. No behavioral change is required.

    Resolved previous findings
    The exact-git validation conflict is resolved by spec.md:53.
    The --fetch boundary behavior is now explicit at spec.md:57.
    The duplicated redirection rule has been replaced with a cross-reference at spec.md:2090.
    No high- or medium-severity issues remain within the git-hints explain scope.~~

Strikethrough indicates LLM output that I deemed incorrect or irrelevant.


