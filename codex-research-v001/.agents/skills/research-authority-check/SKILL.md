---
name: research-authority-check
description: "正本のID・版・状態・SHAを照合する。LLMATCHでcanonical/frozen/current artifactに依存する調査や変更の前に使う。"
---

# research-authority-check

対象のfamilyとroleを特定し、個別研究のauthority manifestを確認する。ID、version、expected SHAの根拠を明示する。元のregistryは変更しない。
`verify_authority.py` で一意な対象と実bytesを照合し、必要なら `verify_hashes.py` を使う。欠落・不一致・複数候補・supersededなら、その資産に依存する処理を止めて原因を調べる。診断作業は継続できる。
ハッシュ一致が証明するのは宣言契約とのbytes一致であり、利用許可や科学的受入ではない。

## 共通helperの呼出し

共通LLMATCH rootは `C:\Users\daich\OneDrive\LLM\LLMATCH`、WSLでは `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`。
子repositoryから起動していても、helperは共通rootの `scripts/research/verify_authority.py` を使う。対象rootと明示policyを渡し、引数は `--help` または共通rootの `docs/research_contracts/CLI.md` で確認する。
stdoutを既定とし、保存するときだけ新規 `--output` を指定する。既存の研究ファイルを入力形式に合わせて編集しない。

詳細が必要な場合にだけ [AUTHORITY_STATES.md](references/AUTHORITY_STATES.md) を読む。
