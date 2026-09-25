# MacBook Air Claude Research V001 — Known Baseline

Date: 2026-09-25 (JST)

This file records environment facts already established before the Phase 0 audit.

## User-confirmed Mac environment

```text
hostname: daichi-macbook
shell user prompt: daich@MacBook-Air
workspace convention: ~/develop
LLMATCH parent directory: not used on this Mac
Claude Code installation method: official install script
Claude Code version: 2.1.281
Claude executable location reported by installer: ~/.local/bin/claude
```

Installation command used:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

## Target repository layout

The planned Mac workspace is:

```text
~/develop/
└── LLMATCH-KG-v3/
```

The research repository must not be placed under a Windows-compatible `LLMATCH` parent merely to match the other machine. Host-specific paths are not research authority.

## GitHub-side repository observations

Target repository:

`daichira-gif/LLMATCH-KG-v3`

Default branch: `main`

At the time this baseline was recorded, the root of `main` did not contain:

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/`

The existing `.gitignore` ignores `.agents/` and `.codex`, but does not yet ignore the planned Mac-local `.claude/settings.local.json` or `CLAUDE.local.md`.

Therefore the Claude V001 implementation should explicitly add local-Claude ignore rules before generating machine-specific settings.

## Still unverified

The following remain Phase 0 checks:

- whether `~/.local/bin` is currently on PATH in new Terminal sessions,
- actual `command -v claude` output,
- `claude --version` readback,
- Git version and authentication method for the private repository,
- actual clone HEAD and branch,
- local/global existing Claude configuration,
- `/doctor` status,
- effective project-root behavior inside Claude Code,
- installed-version support for each proposed settings/hook/frontmatter key.

Status remains pre-implementation.
