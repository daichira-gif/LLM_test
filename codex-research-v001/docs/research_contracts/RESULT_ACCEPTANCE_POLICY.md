# Result acceptance

次の5層を独立して報告します。

| 層 | V001が確認すること |
|---|---|
| execution | receiptの実行状態。申告の照合であり実行過程を独立観測した証明ではない |
| persistence | 出力が存在し、実bytesのSHAがreceiptと一致すること |
| structural | 実出力を宣言schemaに対して検証した結果 |
| semantic | V001の決定論helperでは評価しない。NOT_ASSESSED |
| scientific | V001の決定論helperでは評価しない。NOT_ASSESSED |

authority/lineage確認は別の検査結果です。
receiptに書かれたPASSだけで保存・構造をPASSにしません。
科学的受入には個別実験の固定評価規則、Gold境界、metric/thresholdなどの評価が必要です。
JSONがparseできること、generationが終わったこと、schema合格は意味評価の代用になりません。
