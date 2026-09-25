# Claude Research Environment V001 — Qualification Checklist

This checklist defines minimum acceptance criteria for MacBook Air deployment.

## A. Environment identity

- [ ] macOS version recorded
- [ ] Claude Code version recorded
- [ ] Claude model used for qualification recorded
- [ ] Python version recorded
- [ ] repository root recorded
- [ ] Git commit recorded
- [ ] working tree state recorded

## B. Instruction loading

- [ ] shared `AGENTS.md` is loaded by Claude
- [ ] no conflicting full-policy `CLAUDE.md` exists
- [ ] Claude-only rules are loaded
- [ ] auto memory is disabled for the research project

## C. Skills

- [ ] all six Claude skills are discovered
- [ ] no skill-name collisions exist
- [ ] Windows path hardcodes are absent
- [ ] WSL path hardcodes are absent
- [ ] helper paths resolve from the Mac project root
- [ ] authority skill routes correctly
- [ ] lineage skill routes correctly
- [ ] preflight skill routes correctly
- [ ] Gold-protection skill routes correctly
- [ ] result-audit skill routes correctly
- [ ] handoff skill routes correctly

## D. Deterministic helper integrity

- [ ] Python files compile
- [ ] JSON schemas parse
- [ ] fixture tests pass
- [ ] helpers make no LLM calls
- [ ] helpers make no network calls unless explicitly designed
- [ ] helpers do not mutate input research artifacts
- [ ] preflight cannot manufacture human approval
- [ ] audit preserves NOT_ASSESSED / NOT_VERIFIED states

## E. Hook protection

- [ ] normal disposable fixture write is allowed
- [ ] protected Gold write is denied
- [ ] authority artifact write is denied
- [ ] frozen production output write is denied
- [ ] sealed artifact write is denied
- [ ] hook failure behavior is understood and tested
- [ ] denial message identifies the protected class/path without exposing sealed content

## F. macOS sandbox protection

- [ ] sandbox is enabled
- [ ] unsandboxed fallback is disabled
- [ ] sandbox unavailability causes failure rather than silent downgrade
- [ ] normal source/code write is allowed in safe profile
- [ ] Gold write through Bash is denied
- [ ] Gold write through Python is denied
- [ ] frozen-output write through subprocess is denied
- [ ] sealed read is denied
- [ ] `.env` or configured secret files are denied
- [ ] protection remains active in online profile

## G. Profiles

### research-readonly

- [ ] no repository mutation
- [ ] no unintended external retrieval
- [ ] audit skills function
- [ ] specialist read-only agents function

### research-safe

- [ ] normal code edits work
- [ ] local disposable tests work
- [ ] protected paths remain blocked
- [ ] destructive Git commands require explicit approval

### research-online

- [ ] external retrieval works only as intended
- [ ] local protections are unchanged
- [ ] Git destructive/push operations remain controlled

## H. Subagents

### research-investigator

- [ ] can inspect code/contracts/outputs/receipts
- [ ] cannot edit files
- [ ] distinguishes implementation defect from specification defect
- [ ] does not change acceptance criteria

### research-auditor

- [ ] cannot edit audited artifacts
- [ ] reports five acceptance layers separately
- [ ] missing evidence remains NOT_VERIFIED / NOT_ASSESSED
- [ ] does not collapse partial evidence into overall PASS

## I. End-to-end synthetic workflow

- [ ] authority verification PASS
- [ ] lineage verification PASS
- [ ] result-audit fixture PASS
- [ ] handoff generation PASS
- [ ] bad-hash fixture fails correctly
- [ ] ambiguous-authority fixture fails correctly
- [ ] missing-lineage fixture fails correctly
- [ ] protected-write fixture is blocked
- [ ] sealed-read fixture is blocked

## J. Read-only real-project verification

- [ ] an existing authority artifact can be verified without mutation
- [ ] a known lineage chain can be checked without mutation
- [ ] a historical run can be audited without rerun
- [ ] a handoff can be generated without leaking Gold/sealed/private contents
- [ ] no DO_NOT_RERUN run is executed

## K. Acceptance

Claude Research Environment V001 is accepted only if all mandatory sections A-J pass or any explicit exception is documented with:

- exact failed item,
- reason,
- risk,
- mitigation,
- approval status.

Final accepted state should record:

- implementation commit
- qualification date
- Claude Code version
- Claude model
- macOS version
- Python version
- test summary
- unresolved limitations
