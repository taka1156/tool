# vendor

ツールが使う外部ライブラリ・フォントを、外部 CDN に頼らず同じドメインから配信するための置き場です。
すべて npm の配布物から**手を加えずに**コピーし、各フォルダにライセンス文を同梱しています。

| ライブラリ | 版 | パス | ライセンス | 入手元 |
| --- | --- | --- | --- | --- |
| driver.js | 1.3.5 | `driver.js/1.3.5/` | MIT | npm `driver.js` |
| marked | 12.0.2 | `marked/12.0.2/` | MIT | npm `marked` |
| DOMPurify | 3.1.6 | `dompurify/3.1.6/` | Apache-2.0 を選択（Apache-2.0 / MPL-2.0 のデュアル） | npm `dompurify` |
| Mermaid | 11.17.2 | `mermaid/11.17.2/` | MIT | npm `mermaid` |
| JSZip | 3.10.2 | `jszip/3.10.2/` | MIT を選択（MIT / GPL-3.0 のデュアル） | npm `jszip` |
| Cropper.js | 1.7.0 | `cropperjs/1.7.0/` | MIT | npm `cropperjs` |
| IBM Plex Mono | 2.5.0 | `fonts/ibm-plex-mono/2.5.0/` | SIL OFL 1.1（予約フォント名 "Plex"） | npm `@ibm/plex-mono`（IBM 公式の分割 woff2 と CSS をそのまま） |
| Zen Kaku Gothic New | 5.3.1 | `fonts/zen-kaku-gothic-new/5.3.1/` | SIL OFL 1.1 | npm `@fontsource/zen-kaku-gothic-new`（400 / 500 / 700 の woff2） |

## ルール

- パスは `vendor/<名前>/<版>/`。版を上げるときは新しいフォルダを作り、参照を切り替えてから古いフォルダを消す。
- ファイルは改変しない（min 化・サブセット化もしない）。特に IBM Plex は予約フォント名があるため、改変すると "Plex" の名前を使えなくなる。
- ライセンス文（LICENSE / NOTICE）は必ず一緒に置く。
- 例外として、Zen Kaku Gothic New の `zen-kaku-gothic-new.css` は fontsource の `400.css` / `500.css` / `700.css` を連結し、同梱しない `.woff` へのフォールバック指定だけを取り除いたもの（フォント本体は無加工）。

## 追加・更新のしかた

```bash
npm pack <パッケージ>@<版>            # 例: npm pack marked@12.0.2
tar xzf <パッケージ>-<版>.tgz          # package/ に展開される
mkdir -p docs/vendor/<名前>/<版>
cp package/<配布ファイル> package/LICENSE* docs/vendor/<名前>/<版>/
```

ツールからは `../vendor/<名前>/<版>/<ファイル>` で読み込む。
