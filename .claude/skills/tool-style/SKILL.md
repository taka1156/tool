---
name: tool-style
description: tool リポジトリ用のブラウザツール（HTML 1 枚）を新しく作るときのデザイン規約とテンプレート。「〜するツールを作って」「tool に〜ジェネレーターを追加して」など、新規にツール HTML を書くときに必ず読む。既存 HTML を登録するだけなら tool-publish を使う。
---

# tool-style

tool の各ページを見た目・作り・挙動の面で揃えるための規約。
新規作成時は、リポジトリのルートで次を実行してテンプレートから作り、表示されたパスのファイルに中身を書く。

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/tool.py new NAME   # NAME は英小文字・数字・アンダースコア（例: json_fmt）
```

テンプレートの実体はこのフォルダの `template.html`。置き場所（`docs/feat/`）はスクリプトが決めるので、自分でパスを組み立ててコピーしない。

## 基本方針

- **HTML 1 枚で完結**。CSS / JS はインライン。ビルドやインストールは不要で、ファイルを直接開いても動くこと。
- **入力はブラウザ内で処理し、外部サーバーへ送らない**（README の約束）。送信が必要な機能は作る前にユーザーに確認する。
- 外部ライブラリは `cdnjs.cloudflare.com` か `cdn.jsdelivr.net` から読み込み、バージョンを固定する。読み込み失敗時は画面上にエラーを出す（無言で壊れない）。重いものは `loadScript()` で使うときに遅延読み込みする。
- UI の文言は**日本語**。ヘッダーの `h1` だけは「絵文字 + 英語名」（例: `🖼️ OGP Image Generator`）。
- スマホ幅（〜380px）で横スクロールが出ないこと。2 カラムは 860px 以下で 1 カラムに落とす。

## デザイントークン

既存ツール（ogp_gen / favicon_gen / mermaid / qr など）と揃える。`:root` に変数で定義し、ダークモードは **OS 設定 + 手動切替の 3 状態**（テンプレートの CSS をそのまま使う）。

| 変数 | ライト | ダーク | 用途 |
| --- | --- | --- | --- |
| `--bg` | `#f5f6f8` | `#0d1117` | 背景 |
| `--panel` | `#ffffff` | `#161b22` | ヘッダー・カード |
| `--subtle` | `#f6f8fa` | `#1c2330` | 入力欄の背景 |
| `--hover` | `#eef0f3` | `#222b38` | ボタンのホバー |
| `--border` | `#dfe3e8` | `#30363d` | 罫線 |
| `--text` | `#1f2328` | `#e6edf3` | 本文 |
| `--muted` | `#656d76` | `#8b949e` | ラベル・補足 |
| `--accent` | `#2563eb` | `#6ea8fe` | 強調・フォーカス |
| `--danger` | `#d1242f` | `#ff7b72` | エラー |

- 本文フォント: `-apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans", "Noto Sans JP", Meiryo, sans-serif`、14px、行間 1.6。
- コード・生成結果: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`。
- 主ボタン（ダウンロード・生成など 1 画面に 1 つ）は `button.primary`。

## ページ構成

1. `header.app-header`（sticky）: `h1` → spacer → テーマ切替 `#btnTheme` → ツアー `#btnHelp`（`？`）
2. `main.layout`: 左に入力・設定のカード（`① 入力` `② デザイン` のように番号付き `h2`）、右にプレビュー・結果。エディター系でフル画面にしたい場合は `body` を縦並び flex にし、本体を `flex:1; min-height:0` にする（mermaid / gfm_md を参照）。
3. ページ下部の「← 一覧に戻る」フッター（`<footer id="tool-backlink">`。テンプレートに含まれている。`tool.py lint --backlink` でも入る。固定表示にはしない）

## 挙動の共通ルール

- **テーマ**: `localStorage` の `webtools:theme`（`auto` / `light` / `dark`）。全ツール共通キーなので変えない。`<head>` の先頭スクリプトでちらつきを防ぐ。
- **設定の自動保存**: キーは `webtools:<ツール名>`。読み書きは必ず `lsGet` / `lsSet`（try/catch 済み）経由。
- **使い方ツアー**: driver.js 1.3.5。`initCommon({ steps })` に手順を渡す。`?onBoarding=1` で自動開始。
- **結果の受け渡し**: コピー（`copyText`）とダウンロード（Blob + `a[download]`）を用意する。完了時は `toast()` で知らせる。
- ファイル入力があるならドラッグ&ドロップにも対応する（ogp_gen の `setupDrop` を参照）。

## メタ情報（必須）

`<head>` に入れる。tool-publish の `tool.py meta` で後から付けてもよい。

```html
<meta name="description" content="一覧に出る説明（何ができるかを 1 文で）">
<title>OGP画像ジェネレーター</title>
<meta name="tool:name" content="ogp">
<meta name="tool:date" content="YYYY-MM-DD">
```

canonical・アイコン・OGP のタグは `tool.py` が `<!-- tool:head -->` ブロックとして自動で入れるので、自分では書かない。

## 崩れ防止（コピペ事故対策）

- CSS / JS の引用符は必ず半角 `'` `"`。
- ファイルとして直接保存する（チャットに貼ってからコピペさせない）。
- 書いたら `python3 scripts/tool.py lint NAME` で確認する。

## 書き終えたら

tool-publish の手順 4 以降（lint → meta → 動作確認 → build → README → commit/push → 報告）で登録する（`new` で作ったので取り込み手順 3 は不要）。
