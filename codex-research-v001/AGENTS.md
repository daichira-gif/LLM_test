# LLMATCH research environment V001

スクリプトの設計と実装では、研究パイプライン全体の到達目標を優先する。
証跡・監査・管理機構は、誤りの発見と再現に必要な範囲に絞る。

- 明示された契約、正本ID、固定版、SHA-256を照合する。会話、最大の版番号、更新日時だけで正本を選ばない。
- 実行完了、保存、構造検証、意味評価、科学的受入を分ける。preflight成功は実験実行の承認を作らない。既に得たユーザー承認は指定された対象と範囲で有効とし、重複確認しない。
- Gold、sealed holdout、Oracle、authority artifact、凍結入力、既存production出力を変更しない。sealed内容は該当する開封許可なしに読まない。派生物は契約で許された別の新規出力先へ作る。
- DO_NOT_RERUN等で凍結・再実行禁止とされたrunを再実行しない。許可された再現試験は元出力を保持し別run・新規出力で行う。既存manifestの自動修復、欠落資産の代用、実験後の評価規則変更をしない。
- 通常のコード修正と使い捨てfixtureの試験は依頼の範囲で進める。個別研究の既存契約と下位AGENTSを尊重し、過去の状態記録を現行状態へ読み替えない。
- privateデータ・資格情報・sealed内容をGitやhandoffへ取り込まない。commit/push/公開・外部送信は別途指定された範囲に従う。

必要な工程だけ、次のSkillを使う。全Skill・全研究文書を一括読込しない。

| 工程 | Skill |
|---|---|
| 正本とbytesの照合 | `research-authority-check` |
| sourceからtargetまでの導出確認 | `research-source-lineage` |
| 実験前の技術条件確認 | `research-experiment-preflight` |
| 読込・書込先と保護境界の確認 | `research-gold-protection` |
| 完了・部分完了runの解釈 | `research-result-audit` |
| 次の担当者への再開情報 | `research-handoff` |

共通実装は、このAGENTSと同じrootの `scripts/research/`、契約説明は `docs/research_contracts/`。
子リポジトリから起動するときも、helperへのパスと検査対象 `--root` を区別する。
保護規則は `docs/research_contracts/protected_paths.v001.json` を参照する。これは明示対象の検査でありOSの書込禁止機構や全資産の自動分類ではない。
未導入のgstackやECCは必須依存にしない。
