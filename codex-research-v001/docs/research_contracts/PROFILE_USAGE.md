# Codex research profiles V001

Codex 0.134.0以降を対象とする3つの独立した設定ファイルです。既存の
`config.toml` を書き換えず、利用するCodexの実際の `CODEX_HOME` 直下へ
`research-*.config.toml` を配置します。同名ファイルがあれば上書きせず内容を確認します。
WindowsアプリとWSL CLIの設定保存先は別の場合があります。

| Profile | 用途 | 書込 | コマンド通信 | Web検索 | 承認 |
|---|---|---|---|---|---|
| research-readonly | 読み取り・静的点検 | read-only | sandboxの既定制限 | 無効 | never |
| research-safe | 通常の実装とfixture検証 | workspace-write | 無効 | 無効 | on-request |
| research-online | ネットワークが必要な作業 | workspace-write | 有効 | live | on-request |

例: `codex --profile research-safe -C <作業ディレクトリ>`。
既存タスクの権限はファイル配置だけでは変更されません。

全profileは `gpt-6-astra` / `high`、メモリ生成・利用無効、Skillの不足MCP依存の
自動導入無効を指定します。利用可能なモデルと管理ポリシーは実行環境に従います。
profileは基本ユーザー設定の上、project設定・CLI引数の下に重なります。
project設定による上書きを起動時の状態で確認してください。
`default_permissions` を使う設定とは、今回の `sandbox_mode` /
`sandbox_workspace_write` を混在させません。

`developer_instructions` は、現在の作業対象が Windows の
`C:/Users/daich/OneDrive/LLM/LLMATCH` または WSL の
`/mnt/c/Users/daich/OneDrive/LLM/LLMATCH` 配下の場合に限り、共通AGENTSと必要な
研究Skillを読むよう指示します。既存repo/worktreeの指示を保持します。
これはrepo境界を越えた**必要時のファイル参照**です。Skill catalogへの自動登録や
OSによる保護対象の強制ではありません。LLMATCH外の作業では共通研究指示は適用されません。

`workspace-write` はGold、sealed holdout、authority artifact、production出力を
自動的に保護しません。研究helperの保護対象チェックと既存資産を変更しない手順を併用します。
`writable_roots` は追加の書込先であり、cwd全体を狭める許可リストではありません。
`on-request` は許可された作業を自律実行し、sandbox外操作は承認対象となり得ます。
`never` はsandbox内の実行まで禁じる設定ではありません。
Web検索設定・コマンド通信設定・MCP/connectorのアクセスは別です。
onlineはコマンドの直接外向通信を許可するため、接続先制限を意味しません。

検証: 2026-09-25取得の公式JSON Schemaと、ローカルCLI 0.149.0の隔離設定で確認。
strict検証はprofile内容を使い捨て `config.toml` としてapp-server初期化のみで読み込み、
別途 `--profile <name> mcp list --json` でprofile選択を確認します。モデル呼出しは行いません。
3件ともschema・strict初期化・profile選択を通過し、未知キーと不正TOMLの負例は拒否されました。
独立したGit repoを持つ2つの安全なfixtureでは、それぞれのAGENTSとlocal Skillが読まれ、
Git境界の外側のAGENTSは読まれないことも確認しました。実repoの配置確認とは区別します。
OS sandboxの隔離効果とアカウントのモデル利用可否は、この設定読込試験の対象外です。

公式資料: [profilesと設定優先順位](https://learn.chatgpt.com/docs/config-file/config-advanced)、
[設定リファレンス](https://learn.chatgpt.com/docs/config-file/config-reference)、
[Skill探索範囲](https://learn.chatgpt.com/docs/build-skills)、
[JSON Schema](https://learn.chatgpt.com/docs/config-schema.json)。
