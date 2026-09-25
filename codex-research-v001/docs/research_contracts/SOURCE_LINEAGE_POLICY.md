# Source lineage

宣言されたnode ID、file hash、期待parent、edgeを照合します。ID重複、親欠落、循環、hash不一致は停止対象です。
チェック結果は宣言された導出契約との整合です。metadataだけで実際の変換実行や意味的な正しさを証明しません。
同名・同じ行数・似た内容を系譜の証拠にせず、壊れたlineageを自動修復しません。
既存SourceUnitやTypedFactのIDを付け直す処理は含みません。
