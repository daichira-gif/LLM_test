# Claude Research Environment V001 — Implementation Plan

Status: **NOT_STARTED**

Implementation must occur on the MacBook Air only after the current design has been reviewed against the actual local Claude Code version and the target repository layout.

## Phase 0 — Pre-implementation audit

Before writing any Claude files:

1. Record:
   - macOS version,
   - Claude Code version,
   - current model availability,
   - repository absolute path,
   - Python version,
   - Git status.

2. Inspect existing project files:
   - `AGENTS.md`
   - `CLAUDE.md`
   - `CLAUDE.local.md`
   - `.claude/settings.json`
   - `.claude/settings.local.json`
   - `.claude/skills/`
   - `.claude/agents/`
   - `.claude/rules/`
   - `.claude/hooks/`

3. Check for conflicts:
   - pre-existing hooks,
   - project permissions,
   - sandbox configuration,
   - skill-name collisions,
   - subagent-name collisions,
   - repository-local Claude rules,
   - Git ignore behavior for local settings.

4. Re-run static review of the Codex V001 shared helpers before reuse.

5. Confirm that Windows/WSL paths are removed from all Claude-adapted skills.

Do not proceed to implementation if the local environment differs materially from the assumptions in `DESIGN.md` without documenting the difference.

## Phase 1 — Shared policy reuse

1. Reuse the existing research `AGENTS.md`.
2. Do not add a duplicate full `CLAUDE.md`.
3. If Claude fails to load `AGENTS.md` in the installed version, add a minimal compatibility `CLAUDE.md` that references/imports the shared policy.
4. Add `.claude/rules/research-agent-behavior.md`.

## Phase 2 — Port the six skills

For each Codex V001 skill:

1. preserve semantic states and stop conditions,
2. replace Windows/WSL helper roots,
3. use `${CLAUDE_PROJECT_DIR}`,
4. add Claude-native routing metadata only where useful,
5. verify referenced assets and references exist,
6. ensure no skill performs hidden file mutation.

Skills:

- research-authority-check
- research-source-lineage
- research-experiment-preflight
- research-gold-protection
- research-result-audit
- research-handoff

## Phase 3 — Add hard controls

Implement:

- shared `.claude/settings.json`,
- generated local sandbox path rules,
- `.claude/hooks/protect_research_artifacts.py`,
- `scripts/research/generate_claude_local_settings.py`.

Constraints:

- deterministic only,
- no LLM calls,
- no network,
- no protected-file mutation,
- fail closed on malformed protected-path policy where necessary.

## Phase 4 — Add specialist subagents

Create:

- `.claude/agents/research-investigator.md`
- `.claude/agents/research-auditor.md`

Both should be read-only/plan-oriented.

Do not create an implementation subagent in V001.

## Phase 5 — Add three operating profiles

Create:

- `config/claude/research-readonly.settings.json`
- `config/claude/research-safe.settings.json`
- `config/claude/research-online.settings.json`

Profiles must not weaken protected-path controls.

## Phase 6 — Static checks

Before dynamic testing:

- validate JSON,
- validate YAML/frontmatter,
- compile Python files,
- scan for Windows/WSL hardcoded paths,
- scan for secrets,
- scan for unintended network calls,
- scan for production execution commands in preflight/audit helpers,
- verify every referenced file exists.

## Phase 7 — Synthetic qualification

Use only disposable fixture data.

Test:

```text
authority
  -> lineage
  -> result audit
  -> handoff
```

Also test protected writes and sealed reads.

Do not use real Gold, sealed holdout, or production outputs for destructive qualification tests.

## Phase 8 — Read-only real-project qualification

After synthetic PASS:

- point readonly/audit flows at existing real artifacts,
- do not write to them,
- verify exact authority/hash/lineage behavior,
- compare Claude output with existing Codex V001 expectations.

## Phase 9 — Acceptance and freeze

Claude V001 may be accepted only after all mandatory items in `QUALIFICATION_CHECKLIST.md` pass.

After acceptance:

- record the implementation commit,
- record Claude Code version,
- record model used for qualification,
- record Python/macOS versions,
- record test result,
- update `STATUS.json` from DESIGN_ONLY_NOT_IMPLEMENTED to the appropriate implemented state.
