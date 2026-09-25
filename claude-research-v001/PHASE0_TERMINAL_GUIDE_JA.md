# MacBook Air Phase 0 手動実行ガイド

目的は、Claude Research Environment V001 を実装する前に、MacBook Air上の実環境を**変更せずに**確認することです。

この工程ではまだ `CLAUDE.md`、`.claude/`、Skill、hook、sandbox設定を書き込みません。

## 0. 先に確認している設計修正

現行のClaude Code公式仕様では、プロジェクト常時指示は `CLAUDE.md` として明示されています。

そのため実装時は:

```text
AGENTS.md
  = Codex/Claudeで共有する研究規約の意味上の正本

CLAUDE.md
  = Claude Codeが読む最小ブリッジ
    @AGENTS.md をimportするだけ
```

とします。

## 1. ターミナルを開く

macOSの「ターミナル」を開きます。

この段階ではClaude Codeを起動する必要はありません。

## 2. LLMATCH-KG-v3 のローカル場所を探す

場所が分かっている場合は、そのディレクトリへ移動してください。

分からない場合はまず:

```bash
mdfind "kMDItemFSName == 'LLMATCH-KG-v3'c"
```

を実行します。

候補が出なければ、macOS標準 `find` で:

```bash
find "$HOME" -type d -name 'LLMATCH-KG-v3' -prune 2>/dev/null
```

を実行します。

※ macOS標準のBSD `find` にはGNU版の `-maxdepth` がないため、今回の手順と監査scriptでは `-maxdepth` を使いません。

### 重要

まだcloneされていない場合、この段階では勝手に新規cloneしません。
その事実を監査結果として扱い、保存場所を決めてから導入します。

## 3. 対象repositoryへ移動

例:

```bash
cd "/Users/daich/.../LLMATCH-KG-v3"
```

移動後:

```bash
pwd
git status
```

を確認します。

## 4. Phase 0監査スクリプトを一時領域へ取得

研究repository内へ直接保存せず、`/tmp` 相当へ取得します。

```bash
curl -fsSL \
  https://raw.githubusercontent.com/daichira-gif/LLM_test/main/claude-research-v001/tools/mac_phase0_audit.sh \
  -o /tmp/mac_phase0_audit.sh
```

## 5. 実行前に内容を確認

以下を実行してください。

```bash
sed -n '1,320p' /tmp/mac_phase0_audit.sh
```

確認ポイント:

- `rm` で研究ファイルを削除していない
- `mv` や `cp` で研究ファイルを書き換えていない
- `git commit` / `git push` を実行していない
- 出力先が `${TMPDIR:-/tmp}` の監査reportだけになっている

## 6. スクリプトを実行

```bash
chmod 700 /tmp/mac_phase0_audit.sh
/tmp/mac_phase0_audit.sh "$PWD"
```

最後に:

```text
No research artifact was modified by this audit.
Report: /.../claude_research_phase0_....txt
```

と表示されます。

## 7. Claude Code自身の診断とproject-root情報を確認

監査scriptでは対話的な診断を起動しません。

次にClaude Codeを起動:

```bash
claude
```

起動後、以下を順に入力してください。

```text
/status
/doctor
```

`/doctor` で修正を提案されても、この段階では自動修復キーを押さず、結果だけ確認してください。

続けて、Claudeへの通常のメッセージとして次を入力してください。

```text
読み取り専用で、Bashを使って次の3点だけ確認してください。
1. pwd
2. git rev-parse --show-toplevel
3. CLAUDE_PROJECT_DIR が設定されているか。設定されていれば値を表示。
ファイル変更はしないでください。
```

これは `CLAUDE_PROJECT_DIR` が実際のインストールで信頼できるか確認するためです。V001実装ではこの変数単独には依存せず、Git rootをfallbackとして使います。

その後 `/exit` または通常の終了操作で終了します。

## 8. こちらへ返してほしいもの

次の2点をこのチャットへ貼り付けてください。

1. `mac_phase0_audit.sh` が最後に示したreportの全文
2. `/doctor` で WARN / FAIL が出た場合、その該当行
3. Claude内で確認した `pwd` / Git root / `CLAUDE_PROJECT_DIR` の3行

### 貼らないもの

以下は貼らないでください。

- APIキー
- OAuth token
- password
- `.env` の中身
- sealed holdoutの中身
- private Gold本文
- `~/.claude.json` の全文

監査scriptは環境変数について**名前だけ**を表示し、値は表示しません。

## 9. 次工程

Phase 0結果を受けて以下を確定します。

1. 実際のClaude Code versionに有効なsettings schema
2. 既存Claude設定との競合
3. `CLAUDE.md -> @AGENTS.md` bridge
4. 6 SkillのMac移植
5. hook / sandbox保護
6. readonly/safe/online profile
7. synthetic qualification

Phase 0で問題が見つかった場合は、実装より先に設計を修正します。
