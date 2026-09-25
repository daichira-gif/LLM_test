# Claude Research Environment V001 — Implementation Plan

Status: **PHASE0_AUDIT_PENDING**

Implementation must occur on the MacBook Air only after the current design has been reviewed against the actual local Claude Code version and the target repository layout.

## Phase 0 — Pre-implementation audit

Before writing any Claude runtime files:

1. Record:
   - macOS version and architecture,
   - Claude Code executable path and version,
   - repository absolute path,
   - Python version,
   - Git branch / HEAD / worktree state.

2. Inspect existing project metadata without printing secrets:
   - `AGENTS.md`
   - `CLAUDE.md`
   - `CLAUDE.local.md`
   - `.claude/settings.json`
   - `.claude/settings.local.json`
   - `.claude/skills/`
   - `.claude/agents/`
   - `.claude/rules/`
   - `.claude/hooks/`
   - relevant global `~/.claude/` metadata.

3. Check for conflicts:
   - pre-existing hooks,
   - project permissions,
   - sandbox configuration,
   - skill-name collisions,
   - subagent-name collisions,
   - repository-local Claude rules,
   - Git ignore behavior for local settings,
   - environment variables that materially alter Claude Code behavior.

4. Validate current official Claude Code behavior before using host-specific setting keys.

5. Re-run static review of the Codex V001 shared helpers before reuse.

6. Confirm that Windows/WSL paths are removed from all Claude-adapted skills.

7. Treat `CLAUDE_PROJECT_DIR` as optional until the installed version is tested; do not design hooks or skills that fail solely because that variable is absent.

8. Confirm the corrected instruction-loading design:
   - `AGENTS.md` remains the shared semantic source;
   - a minimal `CLAUDE.md` imports `@AGENTS.md`;
   - no duplicated policy copy is created.

Use `tools/mac_phase0_audit.sh` and `PHASE0_TERMINAL_GUIDE_JA.md`.

Do not proceed to Phase 1 if the local environment differs materially from the assumptions in `DESIGN.md` without documenting the difference.

## Phase 1 — Shared policy bridge

1. Reuse the existing research `AGENTS.md`.
2. Create a minimal project-root `CLAUDE.md` containing `@AGENTS.md`.
3. Do not duplicate research-policy text in `CLAUDE.md`.
4. Add `.claude/rules/research-agent-behavior.md`.

## Phase 2 — Port the six skills

For each Codex V001 skill:

1. preserve semantic states and stop conditions,
2. replace Windows/WSL helper roots,
3. remove Windows/WSL helper roots and implement a root resolver that validates `${CLAUDE_PROJECT_DIR}` when present and otherwise falls back to `git rev-parse --show-toplevel`,
4. add Claude-native routing metadata only after verifying support in the installed version,
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

Implement after validating the installed Claude Code setting/hook schema:

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

Create, using only setting keys confirmed for the installed Claude Code version:

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
