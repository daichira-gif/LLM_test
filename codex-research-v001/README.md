# Codex研究環境 V001

LLMATCH研究環境向けに作成したCodex設定・6 Skill・検査helperのスナップショットです。合成fixtureとスモークテストを含みます。研究データや実行結果は含みません。

- `AGENTS.md`: 研究上の共通原則
- `.agents/skills/`: 正本、系譜、実験前確認、保護対象、結果監査、handoffの6 Skill
- `config/codex/`: `research-readonly`、`research-safe`、`research-online`のprofile配布用TOML
- `scripts/research/` と `schemas/research/`: オフラインの決定論的な検査helperと入力schema
- `docs/research_contracts/`: 保護パス、CLI、結果解釈、profileの利用説明
- `fixtures/research/basic/` と `tests/`: 実研究データを含まない検証用fixtureと26件のテスト

このスナップショットのパスと保護規則は作者のLLMATCHディレクトリ向けです。別環境で使用するときは `config/codex/`、`AGENTS.md`、`docs/research_contracts/protected_paths.v001.json` の対象パスを、実際の研究契約に合わせて確認してください。profileの選択とスモークテストの実行例は `docs/research_contracts/PROFILE_USAGE.md` と `CLI.md` にあります。

要件: Python 3.10以上、`jsonschema>=4.18,<5`。検査helperは実験、GPU、モデル、ネットワークを実行しません。
