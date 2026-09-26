# tool

ブラウザだけで使える自作ツールの一覧です。ビルドやインストールは不要で、各HTMLファイルを直接開いて利用できます。

## ツール

### crop

`feat/crop.html`

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

`feat/wrangler_config.html`

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

## 構成

```text
.
├── index.html                 # ツール一覧
├── tools.js                   # ツール一覧のデータと描画
├── assets/
│   ├── apple-touch-icon.png   # iOS用アイコン
│   └── icon.png               # ファビコン
└── feat/
    ├── crop.html              # 画像クロップ・変換
    └── wrangler_config.html   # Wrangler設定生成
```

## 注意点

- 画像処理と設定ファイル生成はブラウザ内で行われます。画像や入力内容を外部サーバーへ送信する処理はありません。
- `wrangler_config.html` で生成した設定値は、Cloudflare Workersのプロジェクトに合わせて内容を確認してから使用してください。
