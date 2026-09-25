# 保護対象

`protected_paths.v001.json` はLLMATCH rootを基準とする明示的なパス契約です。ファイル本文を探索・分類しません。
protected対象の通常読込・比較は可能ですが、新規出力を含む書込、置換、移動、削除は拒否します。
sealed対象は読込・hash計算も拒否します。許可前に内容を見て安全性を判定しません。

部分文字列 `gold`、`holdout`、`authority`、`production` は判定に使いません。
例えば `golden_analysis.py`、`joint_holdout`検査コード、authority schemaは用語だけで保護対象になりません。
一方、同名のsynthetic fixtureも明示した保護パス内なら例外にしません。
親ディレクトリの移動・削除は保護された子パスとの重なりも確認します。
derived copyは保護元と出力先を別々に検査します。

この一覧は全資産の自動分類ではありません。契約が別のauthority、凍結出力、sealed内容を指定するときは、そのexact pathを対象run用policyへ加えてから使います。
名前の分からないsealed資産を探すための全内容scanはしません。従来のrestricted_data_scannerをLLMATCH全体に起動しません。
policyの変更はGoldを書き換える許可を作りません。承認済みの特殊作業でもV001 helper自身は保護対象へ書き込みません。

policy自体は検査規則を得るため先に読む信頼入力です。sealed本文をpolicyとして指定しないでください。
入力と出力にsymlinkは使用できません（root内へのsymlinkも非対応）。Windowsの大文字小文字aliasによる保護回避を防ぐため保護比較はcaseを区別しません。
