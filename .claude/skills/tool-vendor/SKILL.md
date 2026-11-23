---
name: tool-vendor
description: tool リポジトリのツールで外部ライブラリ・フォントを使うとき（追加・版の更新・削除）のルールと手順。「〜ライブラリを使いたい」「フォントを入れたい」「〜を最新版に上げて」と言われたとき、または tool-style / tool-publish でツールが外部ライブラリを必要としたときに必ず使う。外部 CDN からは読み込まず docs/vendor/ に置き、ライセンスページは自動生成する。
---

# tool-vendor

tool のツールは **外部 CDN・Google Fonts などの外部ドメインから一切読み込まない**。
外部ライブラリ・フォントは npm の配布物を改変せずに `docs/vendor/` に置き、同じドメインから配信する。
理由: CDN やドメインの乗っ取り・売却（polyfill.io の事例）で、配信される中身を差し替えられるのを防ぐため。

台帳は `docs/vendor/vendor.json`。`python3 scripts/tool.py build` が台帳とツールの参照から
`docs/licenses.html` の一覧（使っているツールも自動判定）を生成するので、**licenses.html は手で編集しない**。

以下のコマンドはリポジトリのルートで実行する。

```bash
cd "$(git rev-parse --show-toplevel)"
```

## なぜこの形か（判断の理由）

- **守りたいもの**: ① HTML 1 枚をそのまま開けば動く PoC 的な軽さ（ビルド・インストール不要）、② 処理がブラウザ内で閉じていて、入力内容が外部に送られないこと（README の約束）。
- **CDN をやめた理由**: CDN のドメインがドロップキャッチ・売却・乗っ取りに遭うと、配信される JS を差し替えられる（polyfill.io, 2024）。差し替えられた JS は入力内容を外部に送れるので、② が崩れる。大手 CDN でも「大丈夫なはず」は保証にならない。
- **ビルドツール（npm install + バンドラ）にしなかった理由**: ① の軽さが失われる。各 HTML を単体で開いても動かなくなる。
- **SRI（integrity）だけにしなかった理由**: 版を固定していないもの（`@11` など）や Google Fonts の CSS（ブラウザごとに中身が変わる）には付けられない。CDN が落ちる・消えると動かなくなる点も残る。
- **Google Fonts も自前にした理由**: CSS は改ざんされても JS ほど危なくないが、ページを開くたびに閲覧者の IP が Google に送られ、② の「外部に送らない」と相性が悪い。
- **結果**: ビルドはせず、npm の配布物を無加工で `docs/vendor/` に置いて同じドメインから配信する。ページが読み込むのはサイト自身のファイルだけ。
- **CSP で裏付ける**: 全ページの CSP（`tool.py` の `CSP_POLICY`）で、同じドメイン以外への読み込み・送信をブラウザに禁止させている。ライブラリが内部で外部に通信しようとしても止まるので、入れたら CSP 違反が出ないかを必ず確認する。

## 1. 本当に要るか

- ブラウザ標準 API（`Intl` / `Canvas` / `CompressionStream` / `structuredClone` など）や数十行の自作で足りるなら入れない。
- 同じ用途のものがすでに台帳にあれば、それを使う（`python3 scripts/tool.py vendor list`）。
- 重いもの（数百 KB 超）は `loadScript()` で使うときに遅延読み込みする。

## 2. ライセンスを確認する

npm の `license`（`npm view <パッケージ>@<版> license`）と、パッケージ内の LICENSE の中身の両方を見る。

| ライセンス | 扱い |
| --- | --- |
| MIT / ISC / BSD-2-Clause / BSD-3-Clause / 0BSD / Apache-2.0 / Unlicense / CC0-1.0 / Zlib / OFL-1.1 | そのまま使ってよい（`tool.py` の `ALLOWED_LICENSES`） |
| デュアル（例: `MIT OR GPL-3.0`） | 許可リストにあるほうを `--license` で選び、`--note` に「〜から〜を選択」と書く |
| GPL / LGPL / AGPL / MPL 単独 / CC-BY 系 / 独自ライセンス / 表記なし | **入れる前にユーザーに確認**。了承を得たら `--allow-license <了承日>` を付ける |
| ライセンス文（LICENSE / COPYING / NOTICE / OFL）がパッケージにない | 入れない。配布元のリポジトリで確認し、ユーザーに相談 |

フォントの注意:
- OFL の **予約フォント名（Reserved Font Name）** があるフォント（例: IBM Plex の "Plex"）は、サブセット化を含めて改変すると元の名前で使えない。配布元が出している分割ファイルをそのまま使う。
- 日本語フォントは 1 ウェイト数 MB になる。`@fontsource/<名前>` の分割 woff2（unicode-range 付き）を使い、ウェイトは必要なものだけにする。

## 3. 取り込む

```bash
python3 scripts/tool.py vendor add <パッケージ>@<版> --file <配布ファイル> [--file ...] \
  [--name 表示名] [--kind font] [--license SPDX] [--note 補足] [--source 配布元URL]
```

- **版は必ず固定する**（`marked@12.0.2`。`@12` や `@latest` は不可）。
- `--file` はパッケージの `package/` からの相対パス（glob 可）。中身は `npm pack <パッケージ>@<版>` して確認する。
  - ブラウザ用のビルド（`dist/*.min.js`、IIFE / UMD）を選ぶ。`import` 前提の ESM しかない場合は、そのまま `<script type="module">` で読めるか確認する。
- スクリプトがやること: `npm pack` → 指定ファイルと LICENSE / NOTICE を `docs/vendor/<名前>/<版>/`（フォントは `fonts/<名前>/<版>/`）にコピー → `vendor.json` に登録。許可リスト外・デュアル未選択・ライセンス文なしなら止まる。
- ファイルは **改変しない**（min 化・サブセット化・中身の書き換えをしない）。どうしても必要な加工（例: 同梱しない `.woff` へのフォールバック指定を CSS から外す）は、`--note` に何をしたか書く。

フォントの例（fontsource・必要なウェイトだけ）:

```bash
python3 scripts/tool.py vendor add @fontsource/zen-kaku-gothic-new@5.3.1 --kind font \
  --name "Zen Kaku Gothic New" --keep-tree \
  --file 400.css --file 700.css \
  --file "files/*-400-normal.woff2" --file "files/*-700-normal.woff2" \
  --note "@fontsource の分割 woff2（400 / 700）と CSS を無加工で配信"
```

ツールからは `../vendor/fonts/zen-kaku-gothic-new/5.3.1/400.css` などを `<link rel="stylesheet">` で読む。
CSS には `.woff` へのフォールバックも書かれているが、ブラウザは先に書かれた woff2 を使うので `.woff` は取りにいかない（同梱しなくてよい）。

## 4. ツールから読み込む

- パスは `../vendor/<dir>/<ファイル>`（`vendor add` の最後に表示される）。
- 読み込み失敗時は画面上にエラーを出す（無言で壊れない）。

## 5. 確認する

```bash
python3 scripts/tool.py vendor check   # ファイル・ライセンス文・未使用・台帳にないフォルダ
python3 scripts/tool.py lint NAME      # 外部ドメインからの読み込み・未登録の vendor 参照を検出
python3 scripts/tool.py build          # licenses.html を再生成（使っているツールも自動で入る）
```

- Playwright で **外部へのリクエストをすべて遮断した状態**（`context.route('**/*', ...)` で localhost 以外を abort）でツールを開き、エラーがなく、ライブラリが動くことを見る。
- `docs/licenses.html` に載り、「使っているツール」が正しいこと。

## 版を上げる・やめる

- 上げる: 新しい版を `vendor add` → ツールの参照を新しいパスに書き換え → 動作確認 → 古い版を `python3 scripts/tool.py vendor remove <名前>@<旧版>`。
- やめる: ツールから参照を外してから `vendor remove`（使われている間は削除を拒否する）。
- どちらも最後に `build`。

## 報告

ユーザーには、入れたもの（名前・版・ライセンス。デュアルの選択や許可リスト外なら了承の旨）と、使うツールを短く伝える。
