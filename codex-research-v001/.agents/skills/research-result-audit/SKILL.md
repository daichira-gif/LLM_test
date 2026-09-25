---
name: research-result-audit
description: "LLMATCHの完了・部分完了runを、実行・保存・構造・意味・科学的受入の別々の結果として確認する。"
---

# research-result-audit

対象runのauthority/lineage/contract/receiptを固定し、`audit_result.py` を実行する。receipt内のPASSを鵜呑みにせず、実出力のhashとschema検証結果を読む。
execution、persistence、structural、semantic、scientificの5層を別に報告する。意味・科学評価が未実施ならNOT_ASSESSEDを保持する。
必要な層をcontractが定義していない場合は単一の『実験成功』へまとめない。成功済みgenerationと最終KG受入を分ける。

## 共通helperの呼出し

共通LLMATCH rootは `C:\Users\daich\OneDrive\LLM\LLMATCH`、WSLでは `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`。
子repositoryから起動していても、helperは共通rootの `scripts/research/audit_result.py` を使う。対象rootと明示policyを渡し、引数は `--help` または共通rootの `docs/research_contracts/CLI.md` で確認する。
stdoutを既定とし、保存するときだけ新規 `--output` を指定する。既存の研究ファイルを入力形式に合わせて編集しない。

詳細が必要な場合にだけ [RESULT_ACCEPTANCE_LEVELS.md](references/RESULT_ACCEPTANCE_LEVELS.md) を読む。
