# Claude Research Environment V001 — Design

## 1. Architecture

The Claude adapter is divided into five layers.

```text
Layer 0  Claude Code permissions / sandbox / hooks
Layer 1  Shared research policy in AGENTS.md, loaded through minimal CLAUDE.md bridge
Layer 2  Claude project skills in .claude/skills/
Layer 3  Claude rules and read-only specialist subagents
Layer 4  Shared deterministic helpers / schemas / research contracts
```

The design deliberately avoids installing gstack, ECC, or Super Skills initially. Native Claude Code mechanisms plus the six project research skills are sufficient for V001. Additional packs may be considered only after a repeated capability gap is observed.

## 2. Instruction authority

### Shared semantic authority

Keep the repository `AGENTS.md` as the single semantic research-policy source shared with the Codex adapter.

Claude Code's current documented project-memory mechanism is `CLAUDE.md`. Claude V001 must therefore create a minimal project-root `CLAUDE.md` containing an import of the shared policy:

```markdown
# Claude Code project instructions

@AGENTS.md
```

Do not duplicate the research policy text in `CLAUDE.md`. Any research-policy edit should be made in `AGENTS.md`.

This corrects the earlier assumption that Claude Code would automatically use `AGENTS.md` without a bridge.

### Claude-only behavior

Place Claude-specific behavior in:

`.claude/rules/research-agent-behavior.md`

This file should cover only host-specific concerns such as:

- when to delegate to subagents,
- treating auto memory as non-authoritative,
- development vs production role separation,
- avoiding unnecessary parallel delegation,
- stopping a frozen run instead of repairing it in place.

## 3. Skills

Claude receives the same six research skills as the Codex adapter:

1. `research-authority-check`
2. `research-source-lineage`
3. `research-experiment-preflight`
4. `research-gold-protection`
5. `research-result-audit`
6. `research-handoff`

The semantic contract remains aligned with the Codex V001 versions.

Claude-specific changes:

- install under `.claude/skills/<skill>/SKILL.md`;
- remove Windows/WSL hardcoded paths;
- resolve the helper root defensively: prefer a valid `${CLAUDE_PROJECT_DIR}` when present, otherwise use `git rev-parse --show-toplevel`, and verify `scripts/research/` exists before execution;
- add concise Claude-native routing metadata only when verified against the installed Claude Code version;
- use higher effort for independent audit/investigation where supported;
- do not make experiment execution automatic merely because preflight passes.

### Skill boundary

Skills control workflow and semantic interpretation.

They do not replace deterministic helpers for:

- SHA-256 computation,
- schema validation,
- authority resolution from explicit manifests,
- lineage graph checks,
- protected-path checks,
- experiment preflight checks,
- result-layer classification,
- handoff machine-state collection.

## 4. Memory policy

Claude auto memory must be disabled for the research repository.

Persistent research state must come from explicit artifacts:

- Git state,
- manifests,
- hashes,
- execution receipts,
- frozen contracts,
- handoff documents.

Claude memory may not become research authority.

## 5. Permission and sandbox model

Claude on macOS should use native sandboxing with failure-closed behavior where supported by the installed version.

Shared settings should:

- enable sandboxing,
- reject or avoid unsandboxed fallback,
- disable permission-bypass mode,
- avoid automatic broad permission modes,
- require confirmation for destructive Git operations,
- block common secret files such as `.env`.

Exact setting keys must be validated against the installed Claude Code version during Phase 0 before committing runtime configuration.

### Project-root resolution

Do not make `CLAUDE_PROJECT_DIR` a single point of failure. Released Claude Code versions have had macOS and worktree cases where the variable was empty, stale, or pointed at the main repository rather than the active worktree.

Use this resolution order for project-local helper invocation:

1. use `CLAUDE_PROJECT_DIR` only when non-empty and it contains the expected `scripts/research/` directory;
2. otherwise use `git rev-parse --show-toplevel`;
3. only as a final non-Git fallback use the current working directory;
4. fail closed if the expected helper path is still absent.

Subagents and hooks must use the same resolver rather than assuming they inherit identical working-directory state.

The design uses three protection layers for sensitive research artifacts:

```text
1. AGENTS.md policy, loaded through CLAUDE.md
2. PreToolUse hook for Edit/Write/NotebookEdit
3. macOS sandbox filesystem restrictions
```

The third layer is intended to protect against writes performed indirectly through Bash, Python, subprocesses, or other child processes.

## 6. Protected artifact classes

At minimum, preserve the existing V001 semantics for:

- Gold datasets,
- sealed holdouts,
- Oracle material,
- authority artifacts,
- frozen experiment inputs,
- archived production outputs,
- DO_NOT_RERUN runs.

Recommended access policy:

| Class | Read | Write |
|---|---|---|
| normal Gold | allowed when task permits | denied |
| sealed holdout | denied unless explicitly unsealed | denied |
| frozen production output | allowed | denied |
| authority artifact | allowed | denied |
| disposable fixture | allowed | allowed |

The exact path set must be generated from explicit project policy and manifests, not guessed from content.

## 7. Local-settings generation

Add:

`scripts/research/generate_claude_local_settings.py`

Purpose:

- read the explicit protected-path policy and relevant manifests,
- resolve paths to Mac absolute paths,
- generate `.claude/settings.local.json`,
- never alter protected files,
- never infer protected status from semantic content alone.

The generated file should remain Mac-local and should not be committed if it contains machine-specific absolute paths.

## 8. PreToolUse protection hook

Add:

`.claude/hooks/protect_research_artifacts.py`

Scope:

- parse Claude hook input,
- extract the target path and operation,
- compare against explicit protected path classes,
- deny prohibited writes before the tool executes,
- do not use an LLM,
- do not inspect sealed content,
- return deterministic machine-readable denial output.

The hook is a safety control, not the research-policy authority.

## 9. Specialist subagents

Create only two V001 subagents.

### research-investigator

Purpose:

- non-trivial pipeline failure diagnosis,
- read-only root-cause analysis,
- separate implementation defects from requirement/specification defects,
- trace code, inputs, contracts, outputs, receipts,
- no file mutation,
- no acceptance-criteria changes.

Recommended mode: high-effort, plan/read-only.

### research-auditor

Purpose:

- independent audit of completed or partial runs,
- read-only,
- report execution, persistence, structural, semantic, and scientific acceptance separately,
- treat missing evidence as NOT_VERIFIED / NOT_ASSESSED rather than inventing a verdict.

Recommended mode: high-effort, plan/read-only.

Do not add a separate implementation subagent in V001. The main Claude session should retain shared implementation context.

## 10. Three Claude operating profiles

### research-readonly

Use for:

- audit,
- authority inspection,
- lineage inspection,
- root-cause diagnosis,
- handoff verification.

Expected characteristics:

- plan/read-only behavior,
- sandbox enabled,
- auto memory disabled,
- web and MCP denied unless separately required,
- no mutation.

### research-safe

Use for normal local development:

- repository edits allowed,
- sandbox enabled,
- auto memory disabled,
- destructive Git operations require approval,
- external web/network access not broadly enabled,
- protected-path hook and sandbox controls active.

### research-online

Use only when external retrieval is required:

- same local protections as research-safe,
- web search enabled where explicitly configured,
- web fetch/network requests remain narrow and explicit,
- destructive Git operations still require approval.

## 11. Development / qualification / production roles

Claude's role changes by experiment phase.

```text
Development
  diagnose / design / edit / test

Qualification
  inspect / challenge / verify

Production
  execute / observe / persist / hash / verify / report

Post-run
  audit / interpret
```

During frozen production, Claude must not opportunistically repair code, configuration, input, or evaluation logic. If repair is required, stop the production run and return to development.

## 12. Codex-to-Claude mapping

| Shared concept | Codex V001 | Claude V001 |
|---|---|---|
| repository research policy | AGENTS.md | CLAUDE.md imports @AGENTS.md |
| semantic policy source | AGENTS.md | same AGENTS.md |
| project skills | .agents/skills | .claude/skills |
| host profile | TOML profile | JSON settings/profile |
| memory control | Codex memories setting | Claude auto-memory disabled |
| write safety | sandbox + policy | macOS sandbox + permissions + hook |
| root-cause specialist | gstack/in-session flow | research-investigator subagent |
| independent audit | research skill | research-auditor subagent + research skill |
| local protected paths | config/policy | generated settings.local.json |

## 13. Shared-source future direction

V001 may copy the six skill bodies with host-specific edits, but V002 should avoid long-term drift by introducing a shared source layer:

```text
skills-src/
   shared semantic body
      |
      +--> Codex adapter -> .agents/skills/
      +--> Claude adapter -> .claude/skills/
```

Shared components:

- research semantics,
- state definitions,
- stop conditions,
- helper scripts,
- schemas,
- research contracts.

Host-specific components:

- frontmatter,
- invocation syntax,
- permissions,
- hooks,
- sandbox configuration,
- subagents,
- profile format.

## 14. Initial exclusions

Do not include in Claude V001:

- gstack,
- ECC,
- Super Skills runtime,
- broad MCP auto-approval,
- auto memory as authority,
- unrestricted shell/network access,
- automatic production authorization,
- duplicated policy text in CLAUDE.md,
- semantic guessing of protected paths.
