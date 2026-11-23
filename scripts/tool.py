#!/usr/bin/env python3
"""tool リポジトリ用ツール（標準ライブラリのみ）

使い方（どのディレクトリから実行してもよい）:
  python3 scripts/tool.py new   NAME                  テンプレートから docs/feat/NAME.html を作る
  python3 scripts/tool.py add   SRC NAME [--force]    外部の HTML を docs/feat/NAME.html として取り込む
  python3 scripts/tool.py path  NAME                  docs/feat/NAME.html の絶対パスを表示
  python3 scripts/tool.py url   [NAME]                公開 URL を表示（docs/CNAME の独自ドメイン）
  python3 scripts/tool.py lint  TOOL... [--fix] [--backlink]   （--all で全ツール）
  python3 scripts/tool.py meta  TOOL [--title T] [--desc D] [--name N] [--category C] [--date YYYY-MM-DD]
  python3 scripts/tool.py build [--check]
  python3 scripts/tool.py list
  python3 scripts/tool.py vendor add PKG@VER --file DIST... [--kind font] [--license SPDX]
  python3 scripts/tool.py vendor list | check | remove DIR

TOOL / NAME は「crop」「crop.html」「docs/feat/crop.html」のどれでもよい。
置き場所（docs/feat/）やテンプレートの場所はこのスクリプトだけが知っている。

ツール = docs/feat/ 直下の *.html。docs/ が公開フォルダ（公開 URL は /feat/NAME.html）。
一覧（docs/index.html）の情報は各ツールの <head> 内の次のタグから読み取る:
  <title>                         ページタイトル（og:title にも使う）
  <meta name="description">       一覧に出る説明
  <meta name="tool:name">         一覧に出る短い名前（例: crop）。なければファイル名
  <meta name="tool:category">     一覧の分類（画像系 / ドキュメント系 / その他）。なければ「その他」
  <meta name="tool:date">         追加日 YYYY-MM-DD（分類の中で新しい順）

外部ライブラリ・フォントは外部 CDN から読み込まず docs/vendor/ に置く。台帳は docs/vendor/vendor.json。
build で docs/licenses.html の一覧部分（LICENSES:BEGIN〜END）も再生成する。
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"  # 公開フォルダ
FEAT = DOCS / "feat"  # ツールの置き場所
INDEX = DOCS / "index.html"
FALLBACK_URL = "https://taka1156.github.io/tool/"


def site_url() -> str:
    """公開 URL（末尾 /）。docs/CNAME があればその独自ドメインを使う。"""
    cname = DOCS / "CNAME"
    if cname.is_file():
        lines = cname.read_text(encoding="utf-8").strip().splitlines()
        if lines and lines[0].strip():
            return f"https://{lines[0].strip()}/"
    return FALLBACK_URL


SITE_URL = site_url()
SITE_NAME = "tool"
INDEX_OG_TITLE = "tool | taka1156"
OG_ALT = "Webツール集"


def asset_version(name: str) -> str:
    """画像の中身から短いハッシュを作る（差し替え時に SNS の画像キャッシュを避ける）。"""
    f = DOCS / "assets" / name
    return hashlib.sha256(f.read_bytes()).hexdigest()[:8] if f.is_file() else ""


OG_VERSION = asset_version("ogp.png")
HEAD_BEGIN = "<!-- tool:head（scripts/tool.py が自動生成。手で編集しない） -->"
HEAD_END = "<!-- /tool:head -->"
HEAD_RE = re.compile(r"[ \t]*<!-- tool:head.*?<!-- /tool:head -->\n?", re.S)
TEMPLATE = ROOT / ".claude" / "skills" / "tool-style" / "template.html"
NAME_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
# 一覧の分類と表示順。ここにない分類は末尾に追加される（新しい分類を作るときはここにも足す）
CATEGORIES = ["画像系", "ドキュメント系", "その他"]
DEFAULT_CATEGORY = "その他"
BEGIN = "// TOOLS:BEGIN"
END = "// TOOLS:END"
BACKLINK_ID = "tool-backlink"


def backlink(href: str) -> str:
    """ページ下部のフッターに置く「一覧に戻る」ボタン。
    どのページの CSS にも依存しないよう、スタイルはすべてインラインで完結させる。
    flex:none は body が縦並び flex のフル画面アプリでも潰れないようにするため。"""
    return (
        f'<style>@media print{{#{BACKLINK_ID}{{display:none!important}}}}</style>'
        f'<footer id="{BACKLINK_ID}" style="flex:none;max-width:1200px;margin:0 auto;'
        'padding:14px 16px calc(14px + env(safe-area-inset-bottom,0px));text-align:center">'
        f'<a href="{href}" style="display:inline-block;padding:6px 14px;border-radius:999px;'
        "background:rgba(127,127,127,.15);color:inherit;font:600 12px/1.4 ui-monospace,Menlo,monospace;"
        'letter-spacing:.08em;text-decoration:none;opacity:.85">&larr; 一覧に戻る</a></footer>'
    )


CURLY = "‘’“”"


# ---------------------------------------------------------------- 解析

class _Meta(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title = ""
        self._in_title = False
        self._done = False

    def handle_starttag(self, tag, attrs):
        if self._done:
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title" and not self.title:
            self._in_title = True
        elif tag == "meta" and "name" in a:
            self.meta.setdefault(a["name"].lower(), a.get("content", ""))
        elif tag == "body":
            self._done = True  # 本文中の <meta> 例示などは読まない

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "head":
            self._done = True

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse_meta(text: str) -> tuple[dict, str]:
    p = _Meta()
    p.feed(HEAD_RE.sub("", text))
    return p.meta, p.title.strip()


def rel(path: Path) -> str:
    return path.resolve().relative_to(DOCS).as_posix()


def read_meta(path: Path) -> dict:
    m, title = parse_meta(path.read_text(encoding="utf-8"))
    return {
        "href": rel(path),
        "path": path.name,
        "name": m.get("tool:name", "").strip() or path.stem,
        "category": m.get("tool:category", "").strip() or DEFAULT_CATEGORY,
        "title": title or path.stem,
        "desc": m.get("description", "").strip(),
        "date": m.get("tool:date", "").strip() or git_added_date(path),
    }


def git_added_date(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%cs", "--",
             str(path.resolve().relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        return out[-1] if out else ""
    except Exception:
        return ""


def tool_path(arg: str, must_exist: bool = True) -> Path:
    """名前やパスを docs/feat/ 内のツールのパスに解決する。"""
    p = Path(arg)
    if p.is_file():
        return p.resolve()
    name = p.name[:-5] if p.name.endswith(".html") else p.name
    if not NAME_RE.match(name):
        sys.exit(f"ファイル名は英小文字・数字・アンダースコア・ハイフンのみ: {name!r}")
    if name == "index":
        sys.exit("index はトップページ用です。ツール名に使えません")
    target = FEAT / f"{name}.html"
    if must_exist and not target.is_file():
        sys.exit(f"見つかりません: {target.relative_to(ROOT)}")
    return target


def tool_files() -> list[Path]:
    return sorted(FEAT.glob("*.html"))


def to_root(path: Path) -> str:
    """ページから docs/ 直下への相対パス（"" または "../"）。"""
    depth = len(Path(rel(path)).parts) - 1
    return "../" * depth


# ---------------------------------------------------------------- CSP（外部への通信を禁止）

# 全ページ共通。読み込み・送信先を同じドメイン（と、ページ内で作る data: / blob:）に限る。
# ツールに処理を足して違反が出たら、外部ドメインを足すのではなく、ここに必要最小限のスキーム／ディレクティブを足す。
CSP_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "media-src 'self' data: blob:",
    "connect-src 'self' data: blob:",  # data: / blob: はページ内で作ったデータの読み直し（Cropper.js の EXIF 読み取りなど）
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'none'",
])
CSP_COMMENT = "<!-- tool:csp（外部への通信をブラウザに禁止させる。scripts/tool.py が自動で入れる。手で編集しない） -->"
CSP_TAG = f'<meta http-equiv="Content-Security-Policy" content="{CSP_POLICY}">'
CSP_ANY_RE = re.compile(
    r"[ \t]*(?:" + re.escape(CSP_COMMENT) + r"[ \t]*\n?[ \t]*)?"
    r"<meta\b[^>]*\bhttp-equiv=[\"']?content-security-policy[\"'\s][^>]*>[ \t]*\n?", re.I)


def apply_csp(text: str) -> str:
    """CSP の meta を <meta charset> の直後（なければ <head> の直後）に 1 つだけ置く。
    meta の CSP はそれより後に書かれた読み込みにしか効かないので、head のできるだけ先頭に置く。"""
    body = CSP_ANY_RE.sub("", text)
    block = CSP_COMMENT + "\n" + CSP_TAG + "\n"
    m = re.search(r"<meta\b[^>]*\bcharset[^>]*>[ \t]*\n?", body, re.I) or re.search(r"<head[^>]*>[ \t]*\n?", body, re.I)
    if not m:
        return body
    end = m.end()
    if not body[m.start():end].endswith("\n"):
        block = "\n" + block
    return body[:end] + block + body[end:]


# ---------------------------------------------------------------- head（canonical・アイコン・OGP）

# 自動生成ブロックに置き換える、手書きの旧タグ（<head> 内だけを対象にする）
LEGACY_RE = re.compile(
    r"[ \t]*(?:"
    r"<link\b[^>]*\brel=[\"']?(?:canonical|icon|shortcut icon|apple-touch-icon)[\"'\s][^>]*>"
    r"|<meta\b[^>]*\bproperty=[\"']?og:[^>]*>"
    r"|<meta\b[^>]*\bname=[\"']?(?:twitter:[^\"'\s]*|apple-mobile-web-app-title)[\"'\s][^>]*>"
    r"|<!--\s*(?:Open Graph|X \(Twitter\) Card|Icons)\s*-->"
    r")[ \t]*\n?",
    re.I,
)


def head_block(text: str, path: Path) -> str:
    m, title = parse_meta(text)
    is_index = path.resolve() == INDEX.resolve()
    title = title or SITE_NAME
    og_title = INDEX_OG_TITLE if is_index else f"{title} | {SITE_NAME}"
    desc = m.get("description", "").strip()
    url = SITE_URL + ("" if is_index else rel(path))
    up = to_root(path)
    img = f"{SITE_URL}assets/ogp.png" + (f"?v={OG_VERSION}" if OG_VERSION else "")
    e = lambda v: html.escape(v, quote=True)
    lines = [
        HEAD_BEGIN,
        f'<link rel="canonical" href="{e(url)}">',
        f'<link rel="icon" href="{up}assets/favicon.ico" sizes="any">',
        f'<link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">',
        f'<meta name="apple-mobile-web-app-title" content="{SITE_NAME}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:title" content="{e(og_title)}">',
    ]
    if desc:
        lines.append(f'<meta property="og:description" content="{e(desc)}">')
    lines += [
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:image" content="{img}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{OG_ALT}">',
        '<meta property="og:locale" content="ja_JP">',
        '<meta name="twitter:card" content="summary_large_image">',
        HEAD_END,
    ]
    return "\n".join(lines) + "\n"


def apply_head(text: str, path: Path) -> str:
    return apply_csp(_apply_head(text, path))


def _apply_head(text: str, path: Path) -> str:
    block = head_block(text, path)
    if HEAD_RE.search(text):
        return HEAD_RE.sub(lambda _: block, text, count=1)
    # 初回: 手書きの canonical / OGP / Twitter / アイコンのタグを取り除いてから入れる
    hm = re.search(r"</head>", text, re.I)
    if hm:
        head, rest = text[: hm.start()], text[hm.start():]
        head = LEGACY_RE.sub("", head)
        tm = re.search(r"</title>[ \t]*\n?", head, re.I)
        if tm:
            return head[: tm.end()] + block + head[tm.end():] + rest
        return head + block + rest
    m = re.search(r"<head[^>]*>\n?", text, re.I)
    pos = m.end() if m else 0
    return text[:pos] + block + text[pos:]


# ---------------------------------------------------------------- lint

STYLE_RE = re.compile(r"(<style\b[^>]*>)(.*?)(</style>)", re.S | re.I)
SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)


def _fix_css(css: str) -> tuple[str, list[str]]:
    notes = []
    n = sum(css.count(c) for c in CURLY)
    if n:
        css = css.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
        notes.append(f"CSS 内の全角クォート {n} 個を半角に修正")
    css2, k = re.subn(r"(^|\n)([ \t]*)- \{", r"\1\2* {", css)
    if k:
        css = css2
        notes.append("CSS の `- {`（`* {` の化け）を修正")
    css2, k = re.subn(r"(^|\n)([ \t]*)\\\*", r"\1\2*", css)
    if k:
        css = css2
        notes.append("CSS の `\\*`（エスケープ化け）を修正")
    return css, notes


def lint_text(text: str, path: Path, add_backlink: bool) -> tuple[str, list[str], list[str]]:
    """returns (fixed_text, fixed_notes, problems_remaining)"""
    fixed: list[str] = []
    problems: list[str] = []

    def repl(m):
        css, notes = _fix_css(m.group(2))
        fixed.extend(notes)
        return m.group(1) + css + m.group(3)
    text = STYLE_RE.sub(repl, text)

    for js in SCRIPT_RE.findall(text):
        if re.search(r"[=(,:\[]\s*[‘“]", js):
            problems.append("JS 内で全角クォートが文字列の区切りに使われている疑い（手動確認）")
            break

    if not text.lower().lstrip().startswith("<!doctype"):
        text = "<!DOCTYPE html>\n" + text
        fixed.append("<!DOCTYPE html> を追加")

    def ensure_head(snippet: str, test: str, label: str):
        nonlocal text
        if re.search(test, text, re.I):
            return
        m = re.search(r"<head[^>]*>", text, re.I)
        if m:
            text = text[: m.end()] + "\n" + snippet + text[m.end():]
        else:
            m = re.search(r"<html[^>]*>", text, re.I)
            pos = m.end() if m else text.find("\n") + 1
            text = text[:pos] + "\n" + snippet + text[pos:]
        fixed.append(f"{label} を追加")

    ensure_head('<meta charset="UTF-8">', r"<meta[^>]+charset", "charset")
    ensure_head('<meta name="viewport" content="width=device-width, initial-scale=1">',
                r"<meta[^>]+name=[\"']?viewport", "viewport")

    new = apply_csp(text)
    if new != text:
        fixed.append("CSP（外部への通信を禁止する meta）を追加／更新")
        text = new

    is_index = path.resolve() == INDEX.resolve()
    meta, title = parse_meta(text)
    if not title:
        problems.append("<title> がない（tool.py meta --title で追加）")
    if not meta.get("description", "").strip():
        problems.append("説明（meta description）が空（tool.py meta --desc で追加）")
    if not is_index:
        if not meta.get("tool:name", "").strip():
            problems.append("一覧用の短い名前（meta tool:name）がない（tool.py meta --name で追加）")
        cat = meta.get("tool:category", "").strip()
        if not cat:
            problems.append("分類（meta tool:category）がない（tool.py meta --category で追加）")
        elif cat not in CATEGORIES:
            problems.append(f"分類「{cat}」は一覧の既定にない（{' / '.join(CATEGORIES)}。新設なら tool.py の CATEGORIES に追加）")
        if not meta.get("tool:date", "").strip():
            problems.append("追加日（meta tool:date）がない（tool.py meta --date で追加）")

        if add_backlink and BACKLINK_ID not in text:
            block = backlink(to_root(path) + "index.html")
            m = list(re.finditer(r"</body>", text, re.I))
            if m:
                i = m[-1].start()
                text = text[:i] + block + "\n" + text[i:]
            else:
                text = text.rstrip() + "\n" + block + "\n"
            fixed.append("フッターに「一覧に戻る」ボタンを追加")
        elif BACKLINK_ID not in text:
            problems.append("フッターに「一覧に戻る」ボタンがない（--backlink で追加）")

    if not is_index:
        for u in external_loads(text):
            problems.append(f"外部ドメインから読み込んでいる: {u}（docs/vendor/ に置く。tool.py vendor add）")
        problems += vendor_ref_problems(text, load_vendor())

    new = apply_head(text, path)
    if new != text:
        fixed.append("canonical・アイコン・OGP の head タグを追加／更新")
        text = new

    return text, fixed, problems


def cmd_lint(args) -> int:
    files = [str(p) for p in tool_files()] if args.all else args.files
    if not files:
        sys.exit("対象を指定してください（全ツールは --all）")
    bad = 0
    for f in files:
        path = tool_path(f)
        text = path.read_text(encoding="utf-8")
        new, fixed, problems = lint_text(text, path, args.backlink)
        print(f"== {rel(path)}")
        verb = "修正" if args.fix else "修正可能"
        for n in fixed:
            print(f"  [{verb}] {n}")
        for p in problems:
            print(f"  [要対応] {p}")
        if not fixed and not problems:
            print("  OK")
        if args.fix and new != text:
            path.write_text(new, encoding="utf-8")
        if problems or (fixed and not args.fix):
            bad = 1
    return bad


# ---------------------------------------------------------------- meta

def _set_meta(text: str, name: str, value: str) -> str:
    tag = f'<meta name="{name}" content="{html.escape(value, quote=True)}">'
    pat = re.compile(rf"<meta[^>]+name=[\"']?{re.escape(name)}[\"'\s][^>]*>", re.I)
    if pat.search(text):
        return pat.sub(lambda _: tag, text, count=1)
    m = re.search(r"([ \t]*)<title>.*?</title>[ \t]*\n?", text, re.I | re.S)
    if m:
        return text[: m.end()] + m.group(1) + tag + "\n" + text[m.end():]
    m = re.search(r"</head>", text, re.I)
    if m:
        return text[: m.start()] + tag + "\n" + text[m.start():]
    return tag + "\n" + text


def cmd_meta(args) -> int:
    path = tool_path(args.file)
    text = path.read_text(encoding="utf-8")
    if args.title is not None:
        t = html.escape(args.title, quote=False)
        if re.search(r"<title>.*?</title>", text, re.I | re.S):
            text = re.sub(r"<title>.*?</title>", lambda _: f"<title>{t}</title>", text,
                          count=1, flags=re.I | re.S)
        else:
            m = re.search(r"<head[^>]*>", text, re.I)
            pos = m.end() if m else 0
            text = text[:pos] + f"\n<title>{t}</title>" + text[pos:]
    if args.desc is not None:
        text = _set_meta(text, "description", args.desc)
    if args.name is not None:
        text = _set_meta(text, "tool:name", args.name)
    if args.category is not None:
        text = _set_meta(text, "tool:category", args.category.strip())
    if args.date is not None:
        date = args.date or dt.date.today().isoformat()
        dt.date.fromisoformat(date)
        text = _set_meta(text, "tool:date", date)
    path.write_text(apply_head(text, path), encoding="utf-8")
    print(json.dumps(read_meta(path), ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------- vendor（外部ライブラリ・フォント）

VENDOR = DOCS / "vendor"
VENDOR_JSON = VENDOR / "vendor.json"
LICENSES = DOCS / "licenses.html"
LIC_BEGIN = "<!-- LICENSES:BEGIN（scripts/tool.py build が docs/vendor/vendor.json から自動生成。手で編集しない） -->"
LIC_END = "<!-- LICENSES:END -->"
LIC_RE = re.compile(re.escape(LIC_BEGIN) + r".*?" + re.escape(LIC_END), re.S)
KINDS = {"library": "ライブラリ", "font": "フォント"}
# 確認なしで使ってよいライセンス（SPDX）。それ以外はユーザーの了承を得てから --allow-license で入れる
ALLOWED_LICENSES = {"MIT", "ISC", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "Apache-2.0",
                    "Unlicense", "CC0-1.0", "OFL-1.1", "Zlib"}
LICENSE_FILE_RE = re.compile(r"^(licen[cs]e|copying|notice|ofl)([.\-_].*)?$", re.I)
VENDOR_REF_RE = re.compile(r"vendor/([^\s\"'`()<>?#]+)")
# 外部ドメインからの読み込み（<a href> のリンクや canonical / OGP は対象外）
EXT_SCRIPT_RE = re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"']((?:https?:)?//[^\"']+)", re.I)
EXT_LINK_RE = re.compile(r"<link\b[^>]*>", re.I)
EXT_ASSET_RE = re.compile(r"[\"'`(]((?:https?:)?//[^\"'`\s)]+?\.(?:m?js|css|woff2?|ttf|otf)(?:\?[^\"'`\s)]*)?)[\"'`)]", re.I)
EXT_FONTS_RE = re.compile(r"(?:https?:)?//fonts\.(?:googleapis|gstatic)\.com[^\"'`\s)]*", re.I)


def load_vendor() -> list[dict]:
    if not VENDOR_JSON.is_file():
        return []
    return json.loads(VENDOR_JSON.read_text(encoding="utf-8")).get("entries", [])


def save_vendor(entries: list[dict]) -> None:
    data = json.loads(VENDOR_JSON.read_text(encoding="utf-8")) if VENDOR_JSON.is_file() else {}
    data["entries"] = entries
    VENDOR_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def vendor_usage(entries: list[dict]) -> dict[str, list[str]]:
    """dir → そのライブラリを参照しているツールの短い名前"""
    usage: dict[str, list[str]] = {e["dir"]: [] for e in entries}
    for p in tool_files():
        text = p.read_text(encoding="utf-8")
        name = read_meta(p)["name"]
        for e in entries:
            if f"vendor/{e['dir']}/" in text:
                usage[e["dir"]].append(name)
    return usage


def external_loads(text: str) -> list[str]:
    """外部ドメインから読み込んでいる URL（CDN・Google Fonts など）"""
    found: list[str] = []
    found += EXT_SCRIPT_RE.findall(text)
    for tag in EXT_LINK_RE.findall(text):
        rel_ = re.search(r"\brel\s*=\s*[\"']?([^\"'>]+)", tag, re.I)
        href = re.search(r"\bhref\s*=\s*[\"']((?:https?:)?//[^\"']+)", tag, re.I)
        if href and rel_ and re.search(r"stylesheet|preload|modulepreload|prefetch", rel_.group(1), re.I):
            found.append(href.group(1))
    found += EXT_ASSET_RE.findall(text)
    found += EXT_FONTS_RE.findall(text)
    return list(dict.fromkeys(found))


def vendor_ref_problems(text: str, entries: list[dict]) -> list[str]:
    """../vendor/ の参照が台帳に載っていて、ファイルも実在するか"""
    problems = []
    dirs = [e["dir"] for e in entries]
    for ref in dict.fromkeys(VENDOR_REF_RE.findall(text)):
        if not any(ref.startswith(d + "/") for d in dirs):
            problems.append(f"vendor/{ref} は docs/vendor/vendor.json に登録されていない（tool.py vendor add で追加）")
        elif not (VENDOR / ref).is_file():
            problems.append(f"vendor/{ref} のファイルがない")
    return problems


def render_licenses(entries: list[dict], usage: dict[str, list[str]]) -> str:
    e = lambda v: html.escape(str(v), quote=True)
    n_tools = len(tool_files())
    out = [LIC_BEGIN]
    for kind, label in KINDS.items():
        items = [x for x in entries if x.get("kind", "library") == kind]
        if not items:
            continue
        out.append(f'    <h2>{label}<span class="count">{len(items)}</span></h2>')
        out.append('    <ul class="libs">')
        for x in items:
            users = usage.get(x["dir"], [])
            used = "全ツール" if users and len(users) == n_tools else (" / ".join(users) or "（未使用）")
            note = f'<span class="note">{e(x["note"])}</span>' if x.get("note") else ""
            src = x.get("source", "")
            out.append("      <li>")
            out.append(f'        <div class="name">{e(x["name"])}<span class="ver">{e(x["version"])}</span></div>')
            out.append('        <ul class="meta">')
            out.append(f'          <li><span class="k">ライセンス</span>{e(x["license"])}{note}</li>')
            out.append(f'          <li><span class="k">使っているツール</span>{e(used)}</li>')
            if src:
                out.append(f'          <li><span class="k">配布元</span><a href="{e(src)}">{e(re.sub(r"^https?://", "", src))}</a></li>')
            if x.get("npm"):
                out.append(f'          <li><span class="k">npm</span>{e(x["npm"])}@{e(x["version"])}</li>')
            for lf in x.get("licenseFiles", []):
                path = f'vendor/{x["dir"]}/{lf}'
                out.append(f'          <li><span class="k">ライセンス文</span><a href="{e(path)}">{e(path)}</a></li>')
            out.append("        </ul>")
            for lf in x.get("licenseFiles", []):
                f = VENDOR / x["dir"] / lf
                body = f.read_text(encoding="utf-8", errors="replace").strip() if f.is_file() else "（ファイルがありません）"
                out.append("        <details>")
                out.append(f"          <summary>ライセンス全文を表示（{e(lf)}）</summary>")
                out.append(f"          <pre>{e(body)}</pre>")
                out.append("        </details>")
            out.append("      </li>")
        out.append("    </ul>")
    out.append("    " + LIC_END)
    return "\n".join(out)


def build_licenses(check: bool) -> bool:
    """licenses.html を再生成。変わったら True"""
    if not LICENSES.is_file():
        return False
    src = LICENSES.read_text(encoding="utf-8")
    if not LIC_RE.search(src):
        print(f"docs/licenses.html に LICENSES:BEGIN / END マーカーがありません", file=sys.stderr)
        return False
    entries = load_vendor()
    block = render_licenses(entries, vendor_usage(entries))
    new = apply_head(LIC_RE.sub(lambda _: block, src, count=1), LICENSES)
    if new == src:
        return False
    if not check:
        LICENSES.write_text(new, encoding="utf-8")
    return True


def _npm_pack(spec: str, workdir: Path) -> Path:
    """npm pack で取得して展開し、package/ のパスを返す"""
    import tarfile
    try:
        out = subprocess.run(["npm", "pack", spec, "--json"], cwd=workdir,
                             capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        sys.exit("npm が見つかりません（Node.js をインストールしてください）")
    except subprocess.CalledProcessError as ex:
        sys.exit(f"npm pack {spec} に失敗しました:\n{ex.stderr.strip()}")
    tgz = workdir / json.loads(out)[0]["filename"]
    with tarfile.open(tgz) as tf:
        try:
            tf.extractall(workdir, filter="data")
        except TypeError:  # Python < 3.12
            tf.extractall(workdir)
    return workdir / "package"


def cmd_vendor(args) -> int:
    entries = load_vendor()

    if args.vcmd == "list":
        usage = vendor_usage(entries)
        for x in entries:
            users = " / ".join(usage[x["dir"]]) or "（未使用）"
            print(f"{x.get('kind','library'):<8} {x['name']:<22} {x['version']:<9} {x['license']:<12} vendor/{x['dir']:<34} {users}")
        return 0

    if args.vcmd == "check":
        bad = 0
        usage = vendor_usage(entries)
        known = set()
        for x in entries:
            d = VENDOR / x["dir"]
            known.add(d.resolve())
            msgs = []
            if not d.is_dir():
                msgs.append(f"[要対応] フォルダがない: vendor/{x['dir']}")
            if not x.get("licenseFiles"):
                msgs.append("[要対応] licenseFiles が空")
            for lf in x.get("licenseFiles", []):
                if not (d / lf).is_file():
                    msgs.append(f"[要対応] ライセンス文がない: vendor/{x['dir']}/{lf}")
            if x["version"] not in x["dir"].split("/"):
                msgs.append(f"[要対応] dir に版（{x['version']}）が入っていない: {x['dir']}")
            if x.get("license") not in ALLOWED_LICENSES and not x.get("approved"):
                msgs.append(f"[要確認] ライセンス {x.get('license')} は許可リスト外（ユーザーの了承後、approved に了承日を入れる）")
            if not usage[x["dir"]]:
                msgs.append("[注意] どのツールからも使われていない（不要なら tool.py vendor remove）")
            print(f"== {x['name']} {x['version']}")
            for m in msgs or ["  OK"]:
                print("  " + m.strip())
            if any(m.startswith(("[要対応]", "[要確認]")) for m in msgs):
                bad = 1
        # 台帳にないフォルダ
        for d in sorted(p for p in VENDOR.rglob("*") if p.is_dir()):
            if not any(f.is_file() for f in d.iterdir()):
                continue
            if not any(d.resolve() == k or k in d.resolve().parents for k in known):
                print(f"[要対応] 台帳にないフォルダ: {d.relative_to(DOCS).as_posix()}")
                bad = 1
        return bad

    if args.vcmd == "remove":
        hit = [x for x in entries if args.target in (x["dir"], x["name"], f"{x['name']}@{x['version']}")]
        if len(hit) != 1:
            sys.exit(f"1 件に絞れません（dir で指定してください）: {[x['dir'] for x in hit] or 'なし'}")
        x = hit[0]
        users = vendor_usage(entries)[x["dir"]]
        if users and not args.force:
            sys.exit(f"まだ使われています: {' / '.join(users)}（参照を外してから。強制は --force）")
        import shutil
        shutil.rmtree(VENDOR / x["dir"], ignore_errors=True)
        save_vendor([y for y in entries if y is not x])
        print(f"削除: vendor/{x['dir']}（python3 scripts/tool.py build で licenses.html を更新）")
        return 0

    # add
    import shutil
    import tempfile
    import glob as globmod
    with tempfile.TemporaryDirectory() as tmp:
        pkg = _npm_pack(args.spec, Path(tmp))
        meta = json.loads((pkg / "package.json").read_text(encoding="utf-8"))
        npm_name, version = meta["name"], meta["version"]
        lic = args.license or meta.get("license") or ""
        if isinstance(lic, dict):
            lic = lic.get("type", "")
        if re.search(r"\b(OR|AND)\b", lic):
            sys.exit(f"ライセンスが複合指定です（{lic}）。使うものを --license で 1 つ選んでください")
        if lic not in ALLOWED_LICENSES and not args.allow_license:
            sys.exit(f"ライセンス {lic or '（不明）'} は許可リスト外です。ユーザーの了承を得てから --allow-license YYYY-MM-DD を付けてください")
        short = npm_name.split("/")[-1]
        kind = args.kind
        d = args.dir or (f"fonts/{short}/{version}" if kind == "font" else f"{short}/{version}")
        if version not in d.split("/"):
            sys.exit(f"--dir には版（{version}）を含めてください: {d}")
        if any(x["dir"] == d for x in entries) and not args.force:
            sys.exit(f"すでに登録済み: vendor/{d}（入れ直すなら --force）")
        dest = VENDOR / d
        files: list[Path] = []
        for pat in args.file:
            matched = [Path(p) for p in globmod.glob(str(pkg / pat), recursive=True) if Path(p).is_file()]
            if not matched:
                sys.exit(f"パッケージ内に見つかりません: {pat}（中身: npm pack {args.spec} して確認）")
            files += matched
        lic_files = [p for p in pkg.iterdir() if p.is_file() and LICENSE_FILE_RE.match(p.name)]
        if not lic_files:
            sys.exit("パッケージにライセンス文（LICENSE / COPYING / NOTICE / OFL）がありません。配布元から入手できるか確認してください")
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        for f in files + lic_files:
            rel_ = f.relative_to(pkg)
            # 既定ではファイル名だけで置く（--keep-tree でパッケージ内の階層を保つ）
            out = dest / (rel_ if args.keep_tree else f.name)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
        repo = meta.get("repository")
        repo = repo.get("url", "") if isinstance(repo, dict) else (repo or "")
        repo = re.sub(r"^git\+|\.git$", "", repo).replace("git://", "https://")
        if repo.startswith("github:"):
            repo = "https://github.com/" + repo[7:]
        entry = {
            "kind": kind,
            "name": args.name or npm_name,
            "npm": npm_name,
            "version": version,
            "dir": d,
            "license": lic,
            "licenseFiles": sorted(p.name for p in lic_files),
            "note": args.note or "",
            "source": args.source or repo or meta.get("homepage", ""),
        }
        if args.allow_license:
            entry["approved"] = args.allow_license
        entries = [x for x in entries if x["dir"] != d] + [entry]
        save_vendor(entries)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    print("\n配置したファイル:")
    for f in sorted(dest.rglob("*")):
        if f.is_file():
            print(f"  ../vendor/{f.relative_to(VENDOR).as_posix()}")
    print("\nツールからは上のパスで読み込み、python3 scripts/tool.py build で licenses.html を更新してください")
    return 0


# ---------------------------------------------------------------- build

def render_block(tools: list[dict]) -> str:
    cats = list(dict.fromkeys(t["category"] for t in tools))
    body = json.dumps(tools, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f"{BEGIN}（scripts/tool.py build が自動生成。手で編集しない）\nconst CATEGORIES = {json.dumps(cats, ensure_ascii=False)};\nconst TOOLS = {body};\n{END}"


def cmd_build(args) -> int:
    stale = []
    for p in tool_files():
        text = p.read_text(encoding="utf-8")
        new = apply_head(text, p)
        if new != text:
            stale.append(p.name)
            if not args.check:
                p.write_text(new, encoding="utf-8")
    if stale:
        print(("head が古い: " if args.check else "head を更新: ") + ", ".join(stale))
    tools = sorted((read_meta(p) for p in tool_files()),
                   key=lambda t: (t["date"], t["path"]), reverse=True)
    order = {c: i for i, c in enumerate(CATEGORIES)}
    tools.sort(key=lambda t: order.get(t["category"], len(CATEGORIES)))  # 安定ソート: 分類内は新しい順のまま
    src = INDEX.read_text(encoding="utf-8")
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if not pat.search(src):
        print(f"docs/index.html に {BEGIN} / {END} マーカーがありません", file=sys.stderr)
        return 2
    new = apply_head(pat.sub(lambda _: render_block(tools), src, count=1), INDEX)
    lic_changed = build_licenses(args.check)
    if lic_changed:
        print(("docs/licenses.html が古い" if args.check else "docs/licenses.html を更新"))
    if args.check:
        if new != src or stale or lic_changed:
            print("docs/index.html が古いです（python3 scripts/tool.py build を実行）")
            return 1
        print("docs/index.html は最新です")
        return 0
    if new != src:
        INDEX.write_text(new, encoding="utf-8")
        print(f"docs/index.html を更新（{len(tools)} 件）")
    else:
        print(f"変更なし（{len(tools)} 件）")
    return 0


def _strip_fence(text: str) -> str:
    m = re.search(r"```(?:html)?\s*\n(.*?)\n```", text, re.S | re.I)
    return m.group(1) if m and "<" in m.group(1) else text


def cmd_new(args) -> int:
    target = tool_path(args.name, must_exist=False)
    if target.exists():
        sys.exit(f"すでにあります: {target.relative_to(ROOT)}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    print(target)
    return 0


def cmd_add(args) -> int:
    src = Path(args.src)
    if not src.is_file():
        sys.exit(f"見つかりません: {src}")
    target = tool_path(args.name, must_exist=False)
    if target.exists() and not args.force:
        sys.exit(f"すでにあります: {target.relative_to(ROOT)}（上書きは --force）")
    if src.resolve() != target.resolve():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_strip_fence(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(target)
    return 0


def cmd_path(args) -> int:
    print(tool_path(args.name, must_exist=False))
    return 0


def cmd_url(args) -> int:
    print(SITE_URL + (rel(tool_path(args.name, must_exist=False)) if args.name else ""))
    return 0


def cmd_list(_args) -> int:
    for p in tool_files():
        t = read_meta(p)
        print(f"{t['date'] or '----------'}  {t['href']:<26} {t['name']:<16} {t['desc']}")
    return 0


# ----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="tool リポジトリ用ツール")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="テンプレートから新しいツールを作る")
    p.add_argument("name")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("add", help="外部の HTML を docs/feat/ に取り込む")
    p.add_argument("src")
    p.add_argument("name")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("path", help="ツールの絶対パスを表示")
    p.add_argument("name")
    p.set_defaults(func=cmd_path)

    p = sub.add_parser("url", help="公開 URL を表示（docs/CNAME から決まる）")
    p.add_argument("name", nargs="?")
    p.set_defaults(func=cmd_url)

    p = sub.add_parser("lint", help="崩れチェック（--fix で修正）")
    p.add_argument("files", nargs="*")
    p.add_argument("--all", action="store_true", help="全ツールを対象にする")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--backlink", action="store_true", help="フッターに「一覧に戻る」ボタンを追加")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("meta", help="タイトル・説明・短い名前・追加日を設定")
    p.add_argument("file")
    p.add_argument("--title")
    p.add_argument("--desc")
    p.add_argument("--name", help="一覧に出る短い名前（例: crop）")
    p.add_argument("--category", help="一覧の分類（" + " / ".join(CATEGORIES) + "）")
    p.add_argument("--date", nargs="?", const="", help="YYYY-MM-DD（値なしで今日）")
    p.set_defaults(func=cmd_meta)

    p = sub.add_parser("build", help="index.html の一覧を再生成")
    p.add_argument("--check", action="store_true")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("vendor", help="外部ライブラリ・フォント（docs/vendor/）の追加・確認・削除")
    vs = p.add_subparsers(dest="vcmd", required=True)
    q = vs.add_parser("add", help="npm から取得して docs/vendor/ に置き、vendor.json に登録")
    q.add_argument("spec", help="npm のパッケージと版（例: marked@12.0.2）。版は必ず固定する")
    q.add_argument("--file", action="append", required=True,
                   help="パッケージ内の配布ファイル（package/ からの相対パス。glob 可。複数指定可）")
    q.add_argument("--name", help="表示名（既定は npm のパッケージ名）")
    q.add_argument("--kind", choices=list(KINDS), default="library")
    q.add_argument("--dir", help="vendor/ 以下の置き場所（既定: <名前>/<版>、フォントは fonts/<名前>/<版>）")
    q.add_argument("--license", help="SPDX。デュアルライセンスのときは使うほうを 1 つ指定")
    q.add_argument("--allow-license", metavar="YYYY-MM-DD", help="許可リスト外のライセンスをユーザーが了承した日")
    q.add_argument("--note", help="ライセンスページに出る補足（デュアルの選択・加工の有無など）")
    q.add_argument("--source", help="配布元 URL（既定は package.json の repository）")
    q.add_argument("--keep-tree", action="store_true", help="パッケージ内のフォルダ階層を保ってコピー")
    q.add_argument("--force", action="store_true", help="同じ dir を入れ直す")
    q = vs.add_parser("list", help="登録済みの一覧と使っているツール")
    q = vs.add_parser("check", help="ファイル・ライセンス文・未使用・未登録フォルダの確認")
    q = vs.add_parser("remove", help="登録とフォルダを削除（dir か 名前@版 で指定）")
    q.add_argument("target")
    q.add_argument("--force", action="store_true", help="使われていても削除")
    p.set_defaults(func=cmd_vendor)

    p = sub.add_parser("list", help="ツール一覧を表示")
    p.set_defaults(func=cmd_list)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
