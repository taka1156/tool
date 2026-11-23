# vendor

ツールが使う外部ライブラリ・フォントを、外部 CDN に頼らず同じドメインから配信するための置き場です。
npm の配布物を**手を加えずに**コピーし、各フォルダにライセンス文を同梱しています。

- 台帳: `vendor.json`（名前・版・ライセンス・ライセンス文・配布元）
- 一覧ページ: `../licenses.html`（`python3 scripts/tool.py build` が台帳と各ツールの参照から自動生成）
- 追加・更新・削除のルールと手順: `.claude/skills/tool-vendor/SKILL.md`

```bash
python3 scripts/tool.py vendor add marked@12.0.2 --file marked.min.js   # 追加（npm pack → コピー → 台帳登録）
python3 scripts/tool.py vendor list                                     # 一覧と使っているツール
python3 scripts/tool.py vendor check                                    # ファイル・ライセンス文・未使用の確認
python3 scripts/tool.py vendor remove marked@12.0.2                     # 削除（使われている間は拒否）
```

フォルダは `<名前>/<版>/`（フォントは `fonts/<名前>/<版>/`）。版を上げるときは新しいフォルダを足し、参照を切り替えてから古いほうを消します。

例外: `fonts/zen-kaku-gothic-new/5.3.1/zen-kaku-gothic-new.css` は fontsource の `400.css` / `500.css` / `700.css` を連結し、同梱しない `.woff` へのフォールバック指定を除いたものです（フォント本体は無加工）。
