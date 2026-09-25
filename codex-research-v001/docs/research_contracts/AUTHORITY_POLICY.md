# Authority

入力manifestは利用者が明示した照合契約です。helperが正本を発見・任命するものではありません。
target ID（必要ならrole/version）で候補を絞り、一意性、状態、実bytesのSHA-256を検証します。
最新mtime、最大V番号、似たファイル名、同件数では代用しません。
遠隔pointerしかない、bytesがない、未検証、superseded、複数候補、不一致はexactとして通しません。
既存masterやauthority registryは独自の意味を持つため、V001 schemaへ暗黙に変換しません。
