# MacBook Air Phase 0 手動実行ガイド

対象環境は次のとおりです。

```text
hostname: daichi-macbook
作業workspace: ~/develop
target repo: ~/develop/LLMATCH-KG-v3
Claude Code: 2.1.281
installer reported path: ~/.local/bin/claude
```

Mac側では `LLMATCH` フォルダを作りません。

目的は、`~/develop/LLMATCH-KG-v3` を正式なMac開発場所として用意し、その後Claude Research Environment V001の実装前監査を**変更なし**で実行することです。

この工程ではまだ `AGENTS.md`、`CLAUDE.md`、`.claude/`、Skill、hook、sandbox設定を書き込みません。

## Step 1 — Claude Codeのインストール状態を読み戻す

新しいTerminalウィンドウを開いた上で、次を実行してください。

```bash
hostname
command -v claude
claude --version
echo "$PATH" | tr ':' '\n' | grep -F "$HOME/.local/bin" || true
```

期待値は概ね:

```text
daichi-macbook
/Users/daich/.local/bin/claude
2.1.281
```

です。

### command -v claude が何も返さない場合

インストール自体をやり直さず、まず現在のshellへPATHを追加します。

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v claude
claude --version
```

これで動く場合は、恒久PATH設定を後工程で安全に整理します。Phase 0ではdotfileを書き換えません。

## Step 2 — develop workspaceを作る

```bash
mkdir -p "$HOME/develop"
cd "$HOME/develop"
pwd
```

期待値:

```text
/Users/daich/develop
```

## Step 3 — Gitを確認する

```bash
command -v git
git --version
```

ここでGit自体が見つからない場合は、cloneへ進まず結果をこのチャットへ返してください。

## Step 4 — private repositoryへの認証方法を確認する

まずGitHub CLIが既にあるか確認します。

```bash
command -v gh || true
```

### A. gh が見つかった場合

```bash
gh auth status
```

認証済みなら次のclone方法を使います。

```bash
gh repo clone daichira-gif/LLMATCH-KG-v3 "$HOME/develop/LLMATCH-KG-v3"
```

### B. gh がない、またはgh未認証の場合

既存のGit認証が使えるか、まずcloneを試します。

```bash
git clone https://github.com/daichira-gif/LLMATCH-KG-v3.git "$HOME/develop/LLMATCH-KG-v3"
```

private repositoryの認証を求められた場合、passwordやtokenをこのチャットへ貼らないでください。

認証エラーになった場合は、その**エラーメッセージだけ**を返してください。こちらで次の安全な認証手順へ切り分けます。

### 既に同名directoryが存在する場合

cloneを重ねず、まず:

```bash
ls -la "$HOME/develop/LLMATCH-KG-v3"
```

だけ実行して結果を確認します。

## Step 5 — clone後のrepository identityを確認する

cloneに成功したら:

```bash
cd "$HOME/develop/LLMATCH-KG-v3"

pwd
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short --branch
```

この段階ではbranch変更、pull、checkout、resetを行いません。

## Step 6 — Phase 0監査scriptを/tmpへ取得する

研究repository内には保存しません。

```bash
curl -fsSL \
  https://raw.githubusercontent.com/daichira-gif/LLM_test/main/claude-research-v001/tools/mac_phase0_audit.sh \
  -o /tmp/mac_phase0_audit.sh
```

## Step 7 — 実行前に監査scriptを確認する

```bash
sed -n '1,360p' /tmp/mac_phase0_audit.sh
```

確認ポイント:

- 研究ファイルを `rm` しない
- 研究ファイルを `mv` / `cp` で変更しない
- `git commit` / `git push` / `git reset` / `git clean` を実行しない
- report以外を書き出さない
- report先は `${TMPDIR:-/tmp}`

## Step 8 — 非破壊Phase 0監査を実行する

```bash
chmod 700 /tmp/mac_phase0_audit.sh
/tmp/mac_phase0_audit.sh "$HOME/develop/LLMATCH-KG-v3"
```

最後に:

```text
No research artifact was modified by this audit.
Report: /.../claude_research_phase0_....txt
```

と表示されます。

## Step 9 — Claude Code自身の診断を行う

repository rootから起動します。

```bash
cd "$HOME/develop/LLMATCH-KG-v3"
claude
```

Claude Code内で:

```text
/status
```

次に:

```text
/doctor
```

を実行します。

`/doctor` が修復や変更を提案しても、このPhase 0では実行せず結果だけ確認してください。

続いて通常のClaudeメッセージとして、次を入力します。

```text
読み取り専用で、Bashを使って次の3点だけ確認してください。
1. pwd
2. git rev-parse --show-toplevel
3. CLAUDE_PROJECT_DIR が設定されているか。設定されていれば値を表示。
ファイル変更はしないでください。
```

V001は `CLAUDE_PROJECT_DIR` 単独に依存しません。この確認は、インストール済み2.1.281での実挙動を記録するためです。

## Step 10 — ここへ返す情報

以下を貼り付けてください。

1. Step 1 の4コマンドの結果
2. cloneが成功した場合、Step 5 の結果
3. `mac_phase0_audit.sh` のreport全文
4. `/doctor` の WARN / FAIL があれば該当部分
5. Claude内で確認した:
   - `pwd`
   - Git root
   - `CLAUDE_PROJECT_DIR`

貼らないもの:

- GitHub token
- API key
- OAuth token
- password
- `.env` 内容
- `~/.claude.json` 全文
- sealed holdout本文
- private Gold本文

## 次工程

Phase 0 PASS後に、初めて以下を書き込みます。

1. `.gitignore` にClaudeローカル状態のignoreを追加
2. 共有研究規約 `AGENTS.md`
3. 最小 `CLAUDE.md -> @AGENTS.md` bridge
4. 6 research skills
5. Claude固有rules
6. protected-path hook
7. sandbox/local settings generator
8. 2 read-only subagents
9. readonly / safe / online profiles
10. synthetic qualification
11. read-only real-project qualification

Phase 0で不整合があれば、実装より前に設計を修正します。
