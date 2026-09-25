# Codex研究環境 V001

研究コードを安全に実装・検証するための小さな共通ツール群です。検査helperはオフラインで動き、実験、GPU、モデル、ネットワーク、Git更新、既存資産の修復を実行しません。

## 適用先

共通rootは `C:\Users\daich\OneDrive\LLM\LLMATCH`（WSL: `/mnt/c/Users/daich/OneDrive/LLM/LLMATCH`）。
独立した子リポジトリ `LLMATCH_secure_git`（GitHub KG-v3）と `LLMATCH_GraphRAG` にも短い入口と6 Skillを配置します。
旧worktreeのAGENTSと設定は保持します。research profileには共通指示への参照があり、旧worktreeからも必要なSkillを明示的に読めます。Skill選択欄への自動登録とは別です。

## 最小手順

1. 対象runの既存契約と正本を特定する。旧registryのstatusをV001用に推測変換しない。
2. V001の入力形式が必要な場合は、元の正本を変更せず、新しい検査用manifestにexact IDとSHAを明示する。
3. 必要なhelperだけ実行する。各CLIの `--help` と [CLI仕様](CLI.md)を参照。
4. JSONの技術検査結果と、意味・科学的評価の未評価を区別する。runの実行許可は元の実験契約とユーザー指示に従う。

helperはPython 3.10以上と `jsonschema` を使用します。依存が不足しても自動インストールしません。
Python起動は `python -B` を推奨します（検査でbytecodeを作らないため）。
既定の出力はstdout。`--output`は既存親ディレクトリ内の新規ファイルだけを許可し、上書きしません。`--dry-run`はファイルを作りません。
exit codeは `0`=要求した技術検査の合格、`1`=不一致・未検証・保護境界で停止、`2`=入力形式・パス・I/O等のエラーです。
既存joint_holdout等のCLIとはexit codeの体系が異なり、そのまま差し替える共通runnerではありません。

## 既存研究との接続

現行研究を辿る入口は[GitHubの固定main索引](https://github.com/daichira-gif/LLMATCH-KG-v3/blob/825d0f42a6c6e197119dde6dd3f60212674c2226/docs/research/current/README.md)。これは監査時点の索引で、以後の承認を固定しません。
ローカル `LLMATCH_secure_git` は別branchの旧状態であり、上の索引がローカルにも存在するとは仮定しません。

- 再現性masterは正本への入口です。manifest自体のhash一致から各assetの科学的受入や実験許可を推定しません。
- Stage A/Bの生成完了は最終KGの受入完了と別です。凍結済みrunを再実行しません。
- Section36のsource-free qualification許可を研究SourceUnit読込・generationへ流用しません。
- Goldと予測DG、developmentとholdout、retrieval到達と回答精度を区別します。

profileは [PROFILE_USAGE.md](PROFILE_USAGE.md)、保護対象は [GOLD_PROTECTION_POLICY.md](GOLD_PROTECTION_POLICY.md)を参照。
