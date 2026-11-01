# tool

ブラウザだけで使える自作ツールの置き場です。ビルドやインストールは不要で、各HTMLファイルを直接開いても利用できます。

- トップページ: `docs/index.html`（ツール一覧・更新ボタン）
- 公開 URL: https://tool.taka1156.site/
  （`docs/CNAME` の独自ドメイン。canonical / OGP の URL もここから自動で決まります）

## ツール

| 名前 | パス | 内容 |
| --- | --- | --- |
| compress | `docs/feat/compress.html` | 画像の圧縮とフォーマット変換 |
| crop | `docs/feat/crop.html` | 背景透過・画像のリサイズ・フォーマット変換 |
| markdown | `docs/feat/gfm_md.html` | マークダウン編集・プレビュー・PDF化 |
| mermaid | `docs/feat/mermaid.html` | Mermaid図の編集・プレビュー・SVG/PNG保存 |
| wrangler config | `docs/feat/wrangler_config.html` | フォーム入力から wrangler.jsonc / wrangler.toml を生成 |
| favicon | `docs/feat/favicon_gen.html` | 画像から favicon.ico・apple-touch-icon・PWAアイコン・manifest.json を一括生成 |
| ogp | `docs/feat/ogp_gen.html` | タイトルと背景から 1200×630 のOGP画像と meta タグを生成 |
| qr | `docs/feat/qr.html` | QRコード生成・読み取り・画像転送（PC⇄スマホ） |

### crop

`docs/feat/crop.html`

画像の切り抜き・リサイズ・フォーマット変換を行うツールです。

- 画像ファイルの読み込み
- アスペクト比の指定
- 回転・反転
- 出力サイズの指定
- JPEG / PNG / WebPへの変換
- 品質の調整
- 背景色の指定
- 背景透過
- 変換結果のプレビューとダウンロード

### wrangler config

`docs/feat/wrangler_config.html`

Cloudflare Workersの設定を入力し、`wrangler.jsonc` または `wrangler.toml` を生成するツールです。

#### 生成できる項目

- 基本設定: `name`、`main`、`compatibility_date`、`compatibility_flags`、`account_id`、`workers_dev`
- `vars`（文字列形式の環境変数）
- Routes（`pattern`、任意の`zone_name`）とCron Triggers
- KV、D1、R2のバインディング
- Workers Assets（`directory`、`binding`、`not_found_handling`、`run_worker_first`）
- Observability: Logs / Tracesの有効化、サンプリング率、保存設定。LogsではInvocation Logsも設定できます
- `wrangler.jsonc` / `wrangler.toml`の生成、コピー。対応環境ではダウンロード

#### 手動で追加する項目

このツールはWrangler設定全体を網羅していません。必要な項目は生成後の設定ファイルに追加し、プロジェクトに合わせて確認してください。

- Secrets: `vars`に秘密情報を入れず、`wrangler secret`や`.dev.vars`などで管理してください
- Durable Objectsのバインディングとライフサイクル設定（`migrations` / `exports`）
- Queue、Service Binding、Workflow、Hyperdriveなど、このツールに入力欄がないBindings
- `build`、`dev`、`limits`、`placement`などの追加のWrangler設定
- `zone_id`やCustom Domainなど、Routesの追加オプション

## Claude に頼むとき

このリポジトリで作業している Claude（claude.ai でリポジトリを繋いだ会話、または Claude Code）は、`.claude/skills/` のスキルを使います。

| 言い方の例 | スキル | やること |
| --- | --- | --- |
| 「この HTML を tool に入れて」 | `tool-publish` | 崩れ修正 → 説明・名前付け → 一覧更新 → README 追記 → push |
| 「〜するツールを作って」 | `tool-style` | デザイン規約とテンプレートに沿って新規作成 |
| 「さっきの処理をツールにして」 | `tool-from-chat` | 会話内容をツール化して登録まで |

新しい会話では最初に「taka1156/tool リポジトリで作業して」と伝えるとスキルが効きます。

## 構成

```text
.
├── docs/                      # 公開フォルダ（ここだけを公開する）
│   ├── index.html             # ツール一覧（一覧部分は自動生成）
│   ├── CNAME                  # 独自ドメイン
│   ├── assets/                # favicon.ico / apple-touch-icon.png / ogp.png
│   └── feat/                  # 各ツールの HTML（公開 URL は /feat/NAME.html）
├── scripts/tool.py            # 取り込み・崩れチェック・メタ情報・一覧生成
├── .claude/skills/            # tool-style / tool-publish / tool-from-chat
└── .github/workflows/         # push 時に一覧を再生成
```

## 仕組み

- ツール = `docs/feat/` 直下の `*.html`。一覧の情報は各ツールの `<head>` から読みます

  ```html
  <meta name="description" content="一覧に出る説明">
  <title>OGP画像ジェネレーター</title>
  <meta name="tool:name" content="ogp">
  <meta name="tool:date" content="2026-10-17">
  ```

- `docs/index.html` の `// TOOLS:BEGIN`〜`// TOOLS:END` は自動生成です。手で編集しません（一覧は新しい順）
- 全ページの `<!-- tool:head -->` ブロック（canonical・アイコン・OGP）も自動生成です。og:title は「title | tool」、og:description は description から作られます
- 各ツールのフッターに「← 一覧に戻る」ボタン、一覧ページに「更新」ボタン（キャッシュを避けて再読み込み）があります
- master に `docs/**/*.html` が push されると、GitHub Actions が一覧を再生成します（GitHub の画面から HTML を直接アップロードしても載ります）

## 手でやる場合

```bash
python3 scripts/tool.py add ~/Downloads/foo.html foo   # docs/feat/foo.html として取り込む
python3 scripts/tool.py new foo                        # またはテンプレートから新規作成
python3 scripts/tool.py lint foo --fix --backlink      # 崩れチェック・修正（全ツールは --all）
python3 scripts/tool.py meta foo --name foo --desc "…" --date
python3 scripts/tool.py build                          # 一覧を再生成
python3 scripts/tool.py list                           # 一覧を表示
```

## 注意点

- 画像処理と設定ファイル生成はブラウザ内で行われます。画像や入力内容を外部サーバーへ送信する処理はありません。
- `wrangler_config.html` で生成した設定値は、Cloudflare Workersのプロジェクトに合わせて内容を確認してから使用してください。
