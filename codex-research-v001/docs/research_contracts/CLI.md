# CLI V001

共通オプションは `--root ROOT --policy ROOT内相対JSON [--output ROOT内相対file] [--dry-run]`。
`--root`以外のファイル引数はPOSIX形式の相対パス（区切り `/`）です。絶対パス、`..`、symlink、Windowsの別名となる特殊パスは拒否します。
全CLIは検査だけを行います。`check_protected_paths`のwrite/delete/rename/copyも操作の許否確認であり、操作自体は実行しません。

| helper | 追加必須引数 |
|---|---|
| verify_authority.py | `--manifest authority.json --target ID`（任意: `--role ROLE --version VERSION`） |
| verify_hashes.py | `--manifest hashes.json` |
| verify_lineage.py | `--manifest lineage.json` |
| check_protected_paths.py | `--operation read\|write\|delete\|rename\|copy --path PATH`。rename/copyには `--destination PATH` |
| experiment_preflight.py | `--authority authority.json --target ID --lineage lineage.json --contract contract.json` |
| audit_result.py | preflightと同じ引数に `--receipt receipt.json` |
| build_handoff.py | auditと同じ引数、任意 `--format json\|markdown` |

入力schemaは `schemas/research/`。全入力は `schema_version: "1"` を持ち、未知field、重複JSON key、不正数値を拒否します。
独自の旧manifestを渡すとschemaエラーになります。元の資産を編集して合わせず、検査用の新規契約として作成してください。

## 合成fixtureでの非破壊dry-run

以下はWSLの例です。作業ディレクトリに依存しません。Windowsでも同じPython引数を使用し、rootとscriptのパスだけWindows表記にします。

```bash
llmatch_root=/mnt/c/Users/daich/OneDrive/LLM/LLMATCH
fixture_root="$llmatch_root/fixtures/research/basic"
python -B "$llmatch_root/scripts/research/verify_authority.py" --root "$fixture_root" --policy policy.json --manifest authority.json --target source --dry-run
python -B "$llmatch_root/scripts/research/verify_lineage.py" --root "$fixture_root" --policy policy.json --manifest lineage.json --dry-run
python -B "$llmatch_root/scripts/research/audit_result.py" --root "$fixture_root" --policy policy.json --authority authority.json --target source --lineage lineage.json --contract contract.json --receipt receipt.json --dry-run
python -B "$llmatch_root/scripts/research/build_handoff.py" --root "$fixture_root" --policy policy.json --authority authority.json --target source --lineage lineage.json --contract contract.json --receipt receipt.json --format markdown --dry-run
```

fixtureは架空の文面・モデル代替fileのみです。実Gold、実SourceUnit、研究モデルを含みません。
このfixtureは**完了済みrun**なので、preflightは既存 `result.json` を拒否するのが正しい挙動です。fresh preflight成功は試験内で新規出力先を持つ別fixtureを使って確認します。

## 実パスの予定操作を検査する例

```bash
python -B "$llmatch_root/scripts/research/check_protected_paths.py" --root "$llmatch_root" --policy docs/research_contracts/protected_paths.v001.json --operation write --path outputs/new-result.json --dry-run
```

この例は保護された出力rootのためexit 1になります。ファイルは作りません。
実authorityやlineageを検査するときは該当runが明示するcontractを使い、sealedを読まないpolicyを選びます。

## 結果の扱い

stdout JSONは `schema_version/tool/status/technical_pass/checks/issues/data` を持ちます。判定理由はchecks/issuesを読みます。
exit 0でも科学的受入や実行承認を意味しません。意味・科学評価は `NOT_ASSESSED`、承認生成は常にfalseです。
`--output`指定時もstdoutへ同じ結果を出します。明示した新規出力先が許可されていれば、技術的な不合格（exit 1）の診断結果も保存できます。入力形式等のエラー（exit 2）はstdoutだけに返します。
`--dry-run --output ...` は予定先の許否を確認しますが保存しません。既存親directory以外を暗黙作成しません。

JSON Schemaの外部参照は解決しません。出力schemaはローカルfileとそのSHAでcontractに固定し、同一document内のreferenceのみ使います。
preflightのruntimeは検査時のPython/platformとの照合です。モデルbackend・GPU・tokenizerの実機保証は該当実験のqualificationで行ってください。
