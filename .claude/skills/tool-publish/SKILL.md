---
name: tool-publish
description: Claude が作ったブラウザツールの HTML（貼り付け・添付・アーティファクト・既存ファイル）を tool リポジトリに登録する。「tool に入れて」「ツールに追加」「これ保存して」と言われたとき、または tool-from-chat / tool-style の最後の工程で使う。崩れチェック・メタ情報付与・一覧更新・README 追記・commit/push まで行う。
---

# tool-publish

ツール HTML 1 枚を tool として登録する手順。

## 前提

- ツールは `scripts/tool.py`（標準ライブラリのみ）。**どのディレクトリから実行してもよい**。
- ツールの置き場所（`docs/feat/`）はスクリプトが管理する。スキル側でパスを組み立てず、**ツールは名前で指定する**（例: `crop`）。実際のパスが必要なときは `tool.py path NAME` で取得する。
- 以下のコマンドは、まずリポジトリのルートに移動してから実行する。

```bash
cd "$(git rev-parse --show-toplevel)"
```

## 1. HTML を受け取る

- 貼り付け / 添付 / アーティファクト（`Artifact` の read）/ 既存ファイル、のどれか。
- **中身を最後まで読んでから**次に進む。中身を見ずに登録しない。特に、入力内容を外部へ送信する処理（`fetch` / `XMLHttpRequest` / フォーム送信 / 解析タグ）がないか確認する。あればユーザーに確認する。
- 貼り付けやアーティファクトの場合は、いったんスクラッチパッドに保存する。Markdown のコードブロック（```html …```）で渡されても、手順 3 で囲いは自動で外れる。

## 2. 名前を決める

- 英小文字・数字・アンダースコアの短い名前（既存に合わせて `_` 区切り。例: `ogp_gen`, `wrangler_config`, `json_fmt`）。`.html` は付けても付けなくてもよい。
- 公開 URL が `/feat/NAME.html` になるので、後から変えない前提で選ぶ。
- `python3 scripts/tool.py list` で既存のツールを確認し、同名がある場合:
  - 同じツールの改訂版なら、ユーザーに「上書きするか、別名にするか」を確認する。
  - 別ツールなら名前を変える。
- `index` は使えない（スクリプトが拒否する）。

## 3. 取り込む

```bash
python3 scripts/tool.py add <受け取ったファイル> NAME          # 上書きするときは --force
```

`docs/feat/NAME.html` として保存され、そのパスが表示される。すでに置き場所にあるファイルなら不要。

## 4. 崩れチェックと修正（lint）

```bash
python3 scripts/tool.py lint NAME --fix --backlink
```

自動で直すもの:
- `<style>` 内の全角クォート、`* {` の化け
- `<!DOCTYPE html>` / charset / viewport の欠落
- ページ下部フッターに「← 一覧に戻る」ボタンを追加（`--backlink`。印刷時は非表示）
- canonical・ファビコン・iOS アイコン・OGP の `<head>` タグ（`<!-- tool:head -->` ブロック）を追加／更新。手書きの旧タグは取り除かれる

報告だけのもの（`[要対応]`）:
- JS 内の全角クォート疑い → 文字列の区切りに使われていれば半角に直す。
- 説明・短い名前・追加日の欠落 → 次の手順で付ける。

規約（tool-style）から大きく外れている点（テーマ切替がない、`localStorage` を try/catch なしで使っている、外部 CDN が規定外など）に気づいたら、ユーザーに伝えて直すか確認する。

## 5. メタ情報を付ける

```bash
python3 scripts/tool.py meta NAME \
  --name "ogp" \
  --desc "タイトルと背景から 1200×630 のOGP画像と meta タグを生成" \
  --date
```

- **name**: 一覧カードの見出し。英小文字の短い名前（例: `markdown`, `wrangler config`）。
- **desc**: 一覧に出る説明。何ができるかを名詞止めで 1 文（〜50 字）。og:description にも使われる。
- **title**: `<title>` が適切ならそのまま（`--title` は省略）。og:title は「title | tool」になる。
- **date**: `--date` を値なしで渡すと今日。一覧は新しい順。
- `<!-- tool:head -->` 〜 `<!-- /tool:head -->` は手で編集しない。

## 6. 動作確認・一覧を更新

```bash
python3 scripts/tool.py lint NAME   # OK になること
```

可能なら `docs/` で `python3 -m http.server` を立て、Playwright でトップページ → ツール → 「一覧に戻る」を開いて、コンソールエラーがないこと・スマホ幅で崩れないことを見る（CDN に届かない環境ではライブラリ読み込みエラーは無視してよい）。

```bash
python3 scripts/tool.py build       # トップページの一覧を再生成
python3 scripts/tool.py list
```

トップページの `// TOOLS:BEGIN` 〜 `// TOOLS:END` は自動生成なので手で編集しない。

## 7. README に追記

`README.md` の「ツール」の表に 1 行（名前・パス・説明）を追加する。機能が多いツールは、既存の crop / wrangler config のように見出しを立てて機能を箇条書きにする。

## 8. commit / push

```bash
git fetch origin master            # 遅れていれば rebase
git add -A docs README.md
git commit -m "Add tool: <名前>"
git push origin HEAD:master
```

push 後に GitHub Actions も一覧を再生成するが、ローカルで build 済みなら差分は出ない。

## 9. 報告

ユーザーには短く伝える:
- 追加した名前・説明
- lint で直した点（あれば 1 行で）
- 公開 URL: `python3 scripts/tool.py url NAME` の出力（URL を手で組み立てない）
