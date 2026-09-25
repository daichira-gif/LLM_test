---
name: research-source-lineage
description: "LLMATCHのSourceUnit・TypedFact・KG・評価結果について、宣言されたsourceからtargetまでのID・hash・parentを確認する。"
---

# research-source-lineage

対象targetと必要な導出経路を明示する。authorityが曖昧なnodeは先に正本を解決する。
`verify_lineage.py` でnodeのhash、ID重複、期待parentとedge、欠落、循環を検査する。結果はsource→targetの順で説明する。
同名・同件数・似た内容をlineageとして扱わず、欠落したparentやmetadataを自動生成しない。未検証の変換実行を再現済みと報告しない。

## 共通helperの呼出し

共通LLMATCH rootは `C:\Users\daich\OneDrive\LLM\LLMATCH`、WSLでは `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`。
子repositoryから起動していても、helperは共通rootの `scripts/research/verify_lineage.py` を使う。対象rootと明示policyを渡し、引数は `--help` または共通rootの `docs/research_contracts/CLI.md` で確認する。
stdoutを既定とし、保存するときだけ新規 `--output` を指定する。既存の研究ファイルを入力形式に合わせて編集しない。

詳細が必要な場合にだけ [LINEAGE_CONTRACT.md](references/LINEAGE_CONTRACT.md) を読む。
