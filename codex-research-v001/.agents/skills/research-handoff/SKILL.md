---
name: research-handoff
description: "LLMATCHの作業を別sessionや担当者へ引き継ぐ際、検証した正本・未解決事項・再開点を短くまとめる。"
---

# research-handoff

`build_handoff.py` に元のauthority/lineage/contract/receiptを渡し、再検査した状態を出す。古いaudit JSONのPASSだけを引き継がない。
正本のexact path/ID/hash、完了した作業、未解決事項、次の一手、停止境界をまとめる。必要な追加説明には同梱templateを使う。
会話から承認や成功を補完せず、未実施・未評価を残す。private本文・Gold・secretを含めない。既存handoffへ上書きしない。

## 共通helperの呼出し

共通LLMATCH rootは `C:\Users\daich\OneDrive\LLM\LLMATCH`、WSLでは `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`。
子repositoryから起動していても、helperは共通rootの `scripts/research/build_handoff.py` を使う。対象rootと明示policyを渡し、引数は `--help` または共通rootの `docs/research_contracts/CLI.md` で確認する。
stdoutを既定とし、保存するときだけ新規 `--output` を指定する。既存の研究ファイルを入力形式に合わせて編集しない。

詳細が必要な場合にだけ [HANDOFF_TEMPLATE.md](assets/HANDOFF_TEMPLATE.md) を読む。
