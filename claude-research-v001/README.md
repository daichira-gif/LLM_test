# Claude Research Environment V001

Status: **DESIGN_ONLY_NOT_IMPLEMENTED**

This directory is the design authority for the Claude Code adaptation of the research-agent environment already implemented under `../codex-research-v001/`.

The target environment is a MacBook Air running Claude Code. The design intentionally does **not** copy the Codex adapter verbatim. Shared research semantics remain common, while Claude-specific controls use native Claude Code mechanisms such as project skills, rules, subagents, hooks, permissions, and macOS sandboxing.

## Design goals

1. Keep research policy shared across Codex and Claude wherever possible.
2. Preserve deterministic helper scripts, schemas, manifests, and research contracts as the common authority.
3. Avoid hidden or implicit state as research authority.
4. Prevent accidental mutation of Gold, sealed holdout, authority artifacts, frozen inputs, and prior production outputs.
5. Separate development, qualification, production operation, and post-run audit.
6. Use Claude-specific hard controls where available instead of relying only on prompt instructions.
7. Keep `AGENTS.md` as the semantic source of truth while providing Claude Code with a minimal `CLAUDE.md` bridge that imports `@AGENTS.md`.

## Design correction before implementation

The initial design assumed Claude Code would natively fall back to `AGENTS.md`. The current official Claude Code documentation explicitly documents `CLAUDE.md` as the always-loaded project instruction file and supports `@path` imports. Therefore Claude V001 will include a minimal bridge:

```markdown
# Claude Code project instructions

@AGENTS.md
```

The research policy remains single-sourced in `AGENTS.md`; the bridge contains no duplicated policy text.

## Planned Claude-specific layer

```text
AGENTS.md                         # shared research-policy source
CLAUDE.md                         # minimal Claude bridge: @AGENTS.md
.claude/
  settings.json                  # shared Claude controls
  settings.local.json            # Mac-local generated protections; not committed
  rules/
    research-agent-behavior.md
  skills/
    research-authority-check/
    research-source-lineage/
    research-experiment-preflight/
    research-gold-protection/
    research-result-audit/
    research-handoff/
  agents/
    research-investigator.md
    research-auditor.md
  hooks/
    protect_research_artifacts.py
config/claude/
  research-readonly.settings.json
  research-safe.settings.json
  research-online.settings.json
scripts/research/
  generate_claude_local_settings.py
```

## Important implementation note

The existing Codex V001 skills contain Windows/WSL-specific helper roots such as:

- `C:\\Users\\daich\\OneDrive\\LLM\\LLMATCH`
- `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`

Those paths must **not** be copied into the Mac Claude adapter. The Claude version should resolve repository-local helpers through `${CLAUDE_PROJECT_DIR}` or an explicitly generated local configuration.

## Source implementation

The Codex implementation used as the semantic baseline is:

- `../codex-research-v001/`

Claude adaptation must preserve the research meaning of the six skills while changing only host-specific invocation, frontmatter, permissions, hooks, sandbox controls, and path resolution.

## Phase 0 helper

Before implementation on the Mac, use:

- `tools/mac_phase0_audit.sh`
- `PHASE0_TERMINAL_GUIDE_JA.md`

The audit is non-destructive and writes its report only to the Mac temporary directory.

See:

- `DESIGN.md`
- `IMPLEMENTATION_PLAN.md`
- `QUALIFICATION_CHECKLIST.md`
- `STATUS.json`
