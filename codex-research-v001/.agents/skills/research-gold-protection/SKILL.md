---
name: research-gold-protection
description: "LLMATCHのGold・sealed holdout・authority・凍結済み出力に関わる読込、派生コピー、変更の前に対象パスと操作を確認する。"
---

# research-gold-protection

読込元、書込先、移動・削除で影響する親子パスを列挙する。元の研究契約からsealed境界を確認し、内容を読んで判定しない。
`check_protected_paths.py` に明示policyとoperationを渡す。derived copyはsource/destinationを分ける。
通常protectedの読込・比較と、sealedの読込禁止を区別する。保護対象への変更は一般的な『修正して』という依頼から推定しない。
検査結果は明示policyの範囲に限る。未登録資産の安全性を推定せず、該当runが宣言するexact pathを確認する。

## 共通helperの呼出し

共通LLMATCH rootは `C:\Users\daich\OneDrive\LLM\LLMATCH`、WSLでは `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`。
子repositoryから起動していても、helperは共通rootの `scripts/research/check_protected_paths.py` を使う。対象rootと明示policyを渡し、引数は `--help` または共通rootの `docs/research_contracts/CLI.md` で確認する。
stdoutを既定とし、保存するときだけ新規 `--output` を指定する。既存の研究ファイルを入力形式に合わせて編集しない。

詳細が必要な場合にだけ [PROTECTED_ARTIFACT_POLICY.md](references/PROTECTED_ARTIFACT_POLICY.md) を読む。
