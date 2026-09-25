---
name: research-experiment-preflight
description: "LLMATCHのqualificationやproduction実験の直前に、入力・code・model・runtime・推論条件・出力境界を確認する。"
---

# research-experiment-preflight

対象の実験契約と既存の承認範囲を読む。`experiment_preflight.py` で宣言された入力と条件を検査する。
技術的準備、実機qualification、実行承認を区別する。helperは実験を起動せず、承認を作らない。
承認が既に対象runの同じ範囲に存在すれば重複確認しない。契約で必要な承認が未取得なら、確認可能な準備と検査を済ませてから、その具体的runについてのみ承認を求める。
DO_NOT_RERUN等の再実行禁止を守る。許可済みの再現試験は元出力を保持し別run・新規出力で行う。retry/fallbackを足して通過させない。

## 共通helperの呼出し

共通LLMATCH rootは `C:\Users\daich\OneDrive\LLM\LLMATCH`、WSLでは `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`。
子repositoryから起動していても、helperは共通rootの `scripts/research/experiment_preflight.py` を使う。対象rootと明示policyを渡し、引数は `--help` または共通rootの `docs/research_contracts/CLI.md` で確認する。
stdoutを既定とし、保存するときだけ新規 `--output` を指定する。既存の研究ファイルを入力形式に合わせて編集しない。

詳細が必要な場合にだけ [EXPERIMENT_GATE.md](references/EXPERIMENT_GATE.md) を読む。
