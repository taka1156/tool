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

- Worker名、エントリーポイント、互換性日付の設定
- compatibility flags、account ID、`workers_dev` の設定
- 環境変数（`vars`）の追加
- KV、D1、R2のバインディング設定
- RoutesとCron Triggersの設定
- Observability（Logs / Traces）の設定
- 設定内容のコピー
- 対応環境では設定ファイルのダウンロード

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
