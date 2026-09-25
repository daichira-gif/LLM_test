#!/bin/zsh
# Non-destructive Phase 0 audit for Claude Research Environment V001.
# Writes only to a temporary report under ${TMPDIR:-/tmp}.
set -u

TARGET_ROOT="${1:-$PWD}"
if ! cd "$TARGET_ROOT" 2>/dev/null; then
  echo "ERROR: cannot cd to target root: $TARGET_ROOT" >&2
  exit 2
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${TMPDIR:-/tmp}/claude_research_phase0_${TS}.txt"

exec > >(tee "$OUT") 2>&1

section() {
  printf "\n===== %s =====\n" "$1"
}

exists_meta() {
  local p="$1"
  if [[ -e "$p" ]]; then
    printf "PRESENT  %s" "$p"
    if [[ -f "$p" ]]; then
      local size sha
      size="$(stat -f '%z' "$p" 2>/dev/null || echo '?')"
      sha="$(shasum -a 256 "$p" 2>/dev/null | awk '{print $1}')"
      printf "  bytes=%s  sha256=%s" "$size" "$sha"
    fi
    printf "\n"
  else
    printf "ABSENT   %s\n" "$p"
  fi
}

section "AUDIT IDENTITY"
echo "audit_version=claude-research-v001.phase0.v2"
echo "timestamp_utc=$TS"
echo "target_root=$PWD"
echo "report_path=$OUT"

section "MACOS"
sw_vers 2>/dev/null || true
echo "architecture=$(uname -m 2>/dev/null || echo UNKNOWN)"
echo "shell=${SHELL:-UNKNOWN}"

section "CLAUDE CODE"
if command -v claude >/dev/null 2>&1; then
  echo "claude_path=$(command -v claude)"
  echo -n "claude_version="
  claude --version 2>&1 || true
else
  echo "claude_path=NOT_FOUND"
  echo "claude_version=NOT_AVAILABLE"
fi

section "PYTHON"
if command -v python3 >/dev/null 2>&1; then
  echo "python3_path=$(command -v python3)"
  python3 --version 2>&1 || true
else
  echo "python3_path=NOT_FOUND"
fi
if [[ -x ".venv/bin/python" ]]; then
  echo "project_venv_python=$PWD/.venv/bin/python"
  .venv/bin/python --version 2>&1 || true
else
  echo "project_venv_python=NOT_FOUND"
fi

section "GIT"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "git_toplevel=$(git rev-parse --show-toplevel)"
  echo "git_head=$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
  echo "git_branch=$(git branch --show-current 2>/dev/null || echo UNKNOWN)"
  echo "git_remotes=$(git remote 2>/dev/null | tr '\n' ',' | sed 's/,$//')"
  echo "-- git status --short --branch --"
  git status --short --branch
else
  echo "git_repo=NO"
fi

section "PROJECT INSTRUCTION FILES"
for p in   "AGENTS.md"   "CLAUDE.md"   "CLAUDE.local.md"   ".claude/CLAUDE.md"   ".claude/settings.json"   ".claude/settings.local.json"   ".mcp.json"
do
  exists_meta "$p"
done

section "PROJECT .claude FILE INDEX"
if [[ -d ".claude" ]]; then
  find .claude -type f -print | LC_ALL=C sort
else
  echo ".claude directory: ABSENT"
fi

section "PROJECT SKILL NAMES"
if [[ -d ".claude/skills" ]]; then
  find .claude/skills -name SKILL.md -print | LC_ALL=C sort
else
  echo "project skills: NONE"
fi

section "PROJECT SUBAGENT FILES"
if [[ -d ".claude/agents" ]]; then
  find .claude/agents -type f -name '*.md' -print | LC_ALL=C sort
else
  echo "project agents: NONE"
fi

section "PROJECT SETTINGS SAFE SUMMARY"
python3 - <<'PY' 2>/dev/null || true
import json
from pathlib import Path

for name in [".claude/settings.json", ".claude/settings.local.json"]:
    p = Path(name)
    if not p.exists():
        continue
    print(f"[{name}]")
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print("json_parse=FAIL", type(e).__name__)
        continue
    print("json_parse=PASS")
    print("top_level_keys=" + ",".join(sorted(obj.keys())))
    print("autoMemoryEnabled=" + repr(obj.get("autoMemoryEnabled", "UNSET")))
    sandbox = obj.get("sandbox")
    if isinstance(sandbox, dict):
        print("sandbox_keys=" + ",".join(sorted(sandbox.keys())))
        for key in ("enabled", "allowUnsandboxedCommands", "failIfUnavailable"):
            if key in sandbox:
                print(f"sandbox.{key}={sandbox[key]!r}")
    perms = obj.get("permissions")
    if isinstance(perms, dict):
        print("permissions_keys=" + ",".join(sorted(perms.keys())))
        for key in ("defaultMode", "disableBypassPermissionsMode", "disableAutoMode"):
            if key in perms:
                print(f"permissions.{key}={perms[key]!r}")
        for key in ("allow", "ask", "deny"):
            val = perms.get(key)
            if isinstance(val, list):
                print(f"permissions.{key}_count={len(val)}")
    if "env" in obj:
        env = obj.get("env")
        if isinstance(env, dict):
            print("env_variable_names=" + ",".join(sorted(env.keys())))
        else:
            print("env=NON_OBJECT")
PY

section "GLOBAL CLAUDE METADATA"
for p in   "$HOME/.claude/CLAUDE.md"   "$HOME/.claude/settings.json"
do
  exists_meta "$p"
done

if [[ -d "$HOME/.claude/skills" ]]; then
  echo "-- global skills --"
  find "$HOME/.claude/skills" -name SKILL.md -print | LC_ALL=C sort
else
  echo "global skills: NONE"
fi

if [[ -d "$HOME/.claude/agents" ]]; then
  echo "-- global agents --"
  find "$HOME/.claude/agents" -type f -name '*.md' -print | LC_ALL=C sort
else
  echo "global agents: NONE"
fi

section "GLOBAL SETTINGS SAFE SUMMARY"
python3 - <<'PY' 2>/dev/null || true
import json
from pathlib import Path
p = Path.home() / ".claude" / "settings.json"
if p.exists():
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print("global_settings_json_parse=FAIL", type(e).__name__)
    else:
        print("global_settings_json_parse=PASS")
        print("global_top_level_keys=" + ",".join(sorted(obj.keys())))
        print("global_autoMemoryEnabled=" + repr(obj.get("autoMemoryEnabled", "UNSET")))
        if isinstance(obj.get("env"), dict):
            print("global_env_variable_names=" + ",".join(sorted(obj["env"].keys())))
PY

section "PROJECT ROOT RESOLUTION CANDIDATES"
echo "terminal_pwd=$PWD"
echo "git_root=$(git rev-parse --show-toplevel 2>/dev/null || echo NOT_AVAILABLE)"
echo "CLAUDE_PROJECT_DIR is intentionally not expected in a normal terminal audit."
echo "Its behavior will be verified inside Claude Code before hook/skill installation."

section "RELEVANT ENVIRONMENT VARIABLE NAMES"
python3 - <<'PY'
import os
prefixes = ("CLAUDE_", "ANTHROPIC_", "DISABLE_")
names = sorted(k for k in os.environ if k.startswith(prefixes))
for k in names:
    # Deliberately print names only, never values.
    print(k)
PY

section "GITIGNORE CHECK"
for p in ".claude/settings.local.json" "CLAUDE.local.md"; do
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "-- $p --"
    git check-ignore -v "$p" 2>/dev/null || echo "NOT_IGNORED_OR_ABSENT"
  fi
done

section "PHASE0 STATIC WARNINGS"
if [[ -f "CLAUDE.md" ]]; then
  echo "INFO: existing project CLAUDE.md detected; inspect before replacement."
fi
if [[ -f "CLAUDE.local.md" ]]; then
  echo "INFO: CLAUDE.local.md detected; it may add local project instructions."
fi
if [[ -d ".claude/hooks" ]] && find .claude/hooks -type f -print 2>/dev/null | head -n 1 | grep -q .; then
  echo "INFO: existing project hooks detected; merge/conflict review required."
fi
if [[ -d ".claude/skills" ]] && find .claude/skills -type f -name SKILL.md -print 2>/dev/null | head -n 1 | grep -q .; then
  echo "INFO: existing project skills detected; name-collision review required."
fi
if [[ ! -f "AGENTS.md" ]]; then
  echo "WARN: AGENTS.md not found at target root."
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "BLOCK: Claude Code executable not found in PATH."
fi

section "DONE"
echo "No research artifact was modified by this audit."
echo "Report: $OUT"
