# tool

ブラウザだけで使える自作ツールの置き場です。ビルドやインストールは不要で、各HTMLファイルを直接開いても利用できます。

- トップページ: `docs/index.html`（分類ごとのツール一覧・更新ボタン）
- 公開 URL: https://tool.taka1156.site/
  （`docs/CNAME` の独自ドメイン。canonical / OGP の URL もここから自動で決まります）

## ツール

| 分類 | 名前 | パス | 内容 |
| --- | --- | --- | --- |
| 画像系 | compress | `docs/feat/compress.html` | 画像の圧縮とフォーマット変換 |
| 画像系 | crop | `docs/feat/crop.html` | 背景透過・画像のリサイズ・フォーマット変換 |
| 画像系 | favicon | `docs/feat/favicon_gen.html` | 画像から favicon.ico・apple-touch-icon・PWAアイコン・manifest.json を一括生成 |
| 画像系 | ogp | `docs/feat/ogp_gen.html` | タイトルと背景から 1200×630 のOGP画像と meta タグを生成 |
| ドキュメント系 | markdown | `docs/feat/gfm_md.html` | マークダウン編集・プレビュー・PDF化 |
| ドキュメント系 | mermaid | `docs/feat/mermaid.html` | Mermaid図の編集・プレビュー・SVG/PNG保存 |
| ドキュメント系 | article memo | `docs/feat/article_memo.html` | 対話形式の質問に答えて記事メモを作成（Zenn風・Qiita風・完全自由の frontmatter）・プレビュー・Markdown入出力・質問設定のJSON書き出し |
| その他 | wrangler config | `docs/feat/wrangler_config.html` | フォーム入力から wrangler.jsonc / wrangler.toml を生成 |
| その他 | vite plus check | `docs/feat/vite_plus_check.html` | チェックリストに答えて、Vite+ への移行が完全移行・部分的・非推奨のどれに向くかを判定 |
| その他 | prompt guard | `docs/feat/prompt_guard.html` | AIに送る前のプロンプトから個人情報・社内情報・認証情報を検出して警告・マスク |

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

### article memo

`docs/feat/article_memo.html`

質問に順番に答えて、記事を書く前の「記事メモ」を作るウィザードです。最初に形式を選びます。

- Zenn 風: [zenn-writing-environment の記事テンプレート](https://github.com/taka1156/zenn-writing-environment/blob/master/template/article.md) に沿った frontmatter（type / topics / emoji / title / published）
- Qiita 風: title / tags（最大 5 つ）/ private などの frontmatter
- 完全自由: キーと型を自分で決めます。初期値は brite サンプルと同じ構成（title / thumbnail / category / tags / created_at / updated_at）。型はテキスト・URL・数値・日付・日時（+09:00 などの TZ 付きで書き出し）・真偽・リスト・絵文字（単一・複数）

- 全15問のウィザード（Q番号・進捗バー・記入済み / スキップ / 未記入の件数）
- 深掘り質問のボタンで回答欄に問いを差し込み
- 質問のスキップと、未記入の項目だけを順に巡回するモード
- 記事の形のプレビューと Markdown 表示（見出しをクリックでその質問へ）
- Markdown のコピー・.md ダウンロード（ガイドコメントを残すか選択可）
- .md のインポート（ファイル選択・ドラッグ&ドロップ・貼り付け）。未記入の項目から順番に質問し、テンプレート外の見出しは保持
- 質問設定の JSON 書き出し。定義は `docs/feat/article_memo.questions.schema.json`（JSON Schema）に従う
- 質問設定の JSON 読み込み（形式・frontmatter の項目・本文の質問と見出し）。本文の項目は `group: "本文"` と `heading` を持つ質問
- AI 用プロンプトのコピー。この Schema を埋め込んだ、質問設定を AI に作らせるためのプロンプトを得られます

### prompt guard

`docs/feat/prompt_guard.html`

AI に貼り付ける前の文章から、個人情報・社内情報・認証情報っぽいものを検出して警告するツールです。ルールベース（正規表現＋検証）で、入力はブラウザ内だけで処理し、本文は保存しません。

- 検出対象: 秘密鍵・APIキー・パスワード / マイナンバー・クレジットカード・口座番号・メール・電話・郵便番号・住所・氏名・生年月日 / 機密ラベル・未公開の示唆・社員番号・社内URL・プライベートIP・業績や人事の金額
- 検証: クレカは Luhn ＋ ブランド（IIN・桁数）、マイナンバーはチェックデジット、電話番号は日本の番号体系（携帯 / IP / フリーダイヤル / 固定）
- 重大・要確認・参考の 3 段階でハイライトし、全体を 4 段階で判定
- 社内辞書（会社名・プロジェクト名など）。辞書だけ localStorage に保存
- マスク済みテキスト（`[EMAIL_1]` 形式。同じ文字列は同じ番号）のコピー
- ロジック説明タブ: 処理の流れ・検証ロジック・全ルールの正規表現（ルール定義から自動生成）。正規表現リストを JSON でコピー可能

## Claude に頼むとき

このリポジトリで作業している Claude（claude.ai でリポジトリを繋いだ会話、または Claude Code）は、`.claude/skills/` のスキルを使います。

| 言い方の例 | スキル | やること |
| --- | --- | --- |
| 「この HTML を tool に入れて」 | `tool-publish` | 崩れ修正 → 説明・名前付け → 一覧更新 → README 追記 → push |
| 「〜するツールを作って」 | `tool-style` | デザイン規約とテンプレートに沿って新規作成 |
| 「さっきの処理をツールにして」 | `tool-from-chat` | 会話内容をツール化して登録まで |
| 「〜ライブラリを使いたい」「〜を最新版に上げて」 | `tool-vendor` | ライセンス確認 → `docs/vendor/` に配置・台帳登録 → ライセンスページ再生成 |

新しい会話では最初に「taka1156/tool リポジトリで作業して」と伝えるとスキルが効きます。

## 構成

```text
.
├── docs/                      # 公開フォルダ（ここだけを公開する）
│   ├── index.html             # ツール一覧（一覧部分は自動生成）
│   ├── CNAME                  # 独自ドメイン
│   ├── licenses.html          # 使用ライブラリ・フォントとライセンスの一覧（一覧部分は自動生成）
│   ├── assets/                # favicon.ico / apple-touch-icon.png / ogp.png
│   ├── vendor/                # 外部ライブラリ・フォント（npm 配布物をそのまま。LICENSE 同梱。台帳は vendor.json）
│   └── feat/                  # 各ツールの HTML（公開 URL は /feat/NAME.html）
├── scripts/tool.py            # 取り込み・崩れチェック・メタ情報・一覧生成
├── .claude/skills/            # tool-style / tool-publish / tool-from-chat / tool-vendor
└── .github/workflows/         # push 時に一覧を再生成
```

## 仕組み

- ツール = `docs/feat/` 直下の `*.html`。一覧の情報は各ツールの `<head>` から読みます

  ```html
  <meta name="description" content="一覧に出る説明">
  <title>OGP画像ジェネレーター</title>
  <meta name="tool:name" content="ogp">
  <meta name="tool:category" content="画像系">
  <meta name="tool:date" content="2026-10-17">
  ```

- `docs/index.html` の `// TOOLS:BEGIN`〜`// TOOLS:END` は自動生成です。手で編集しません（分類ごとに見出しを付け、その中は新しい順。分類の種類と表示順は `scripts/tool.py` の `CATEGORIES`）
- 外部ライブラリ・フォントは `docs/vendor/` に置き、台帳 `docs/vendor/vendor.json` に登録します（`tool.py vendor add`）。`docs/licenses.html` の `LICENSES:BEGIN`〜`LICENSES:END` は台帳と各ツールの参照から自動生成です（使っているツールも自動判定）
- 全ページの `<!-- tool:head -->` ブロック（canonical・アイコン・OGP）も自動生成です。og:title は「title | tool」、og:description は description から作られます
- 各ツールのフッターに「← 一覧に戻る」ボタン、一覧ページに「更新」ボタン（キャッシュを避けて再読み込み）があります
- master に `docs/**/*.html` が push されると、GitHub Actions が一覧を再生成します（GitHub の画面から HTML を直接アップロードしても載ります）

## 手でやる場合

```bash
python3 scripts/tool.py add ~/Downloads/foo.html foo   # docs/feat/foo.html として取り込む
python3 scripts/tool.py new foo                        # またはテンプレートから新規作成
python3 scripts/tool.py lint foo --fix --backlink      # 崩れチェック・修正（全ツールは --all）
python3 scripts/tool.py meta foo --name foo --desc "…" --category 画像系 --date
python3 scripts/tool.py build                          # 一覧を再生成
python3 scripts/tool.py list                           # 一覧を表示
python3 scripts/tool.py vendor add marked@12.0.2 --file marked.min.js   # ライブラリを docs/vendor/ に追加
python3 scripts/tool.py vendor list | check            # 台帳の一覧・確認
```

## 注意点

- 画像処理と設定ファイル生成はブラウザ内で行われます。画像や入力内容を外部サーバーへ送信する処理はありません。
- 全ページに CSP（`<meta http-equiv="Content-Security-Policy">`）を入れ、同じドメイン以外からの読み込みや外部への通信（fetch など）をブラウザ側でも制限しています（ページ遷移による送信など、CSP で止められないものもあるため「禁止」ではなく「制限」）。`tool.py` が `<meta charset>` の直後に自動で入れます（ポリシーは `scripts/tool.py` の `CSP_POLICY`）。開発者ツールのネットワークタブで、外部への通信がないことを確認できます。
- 外部ライブラリ・フォントは外部 CDN から読み込まず、`docs/vendor/` に置いたもの（npm 配布物を無加工・LICENSE 同梱）を同じドメインから配信しています。一覧は `docs/licenses.html`（公開 URL の `/licenses.html`）。
- `wrangler_config.html` で生成した設定値は、Cloudflare Workersのプロジェクトに合わせて内容を確認してから使用してください。
