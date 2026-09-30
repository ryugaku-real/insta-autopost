#!/usr/bin/env python3
"""post.json の "slides" からカルーセル画像（1080x1350 JPG）を作る。

  python scripts/render.py          足りない画像を全部作る
  python scripts/render.py --check  作る必要があれば終了コード1（作らない）
  python scripts/render.py --force  全部作り直す

slides の書き方（1枚ずつ）:
  {"type": "cover", "label": "保存推奨", "title": "タイトル", "sub": "サブタイトル"}
  {"type": "point", "no": 1, "head": "見出し", "body": "説明文"}
  {"type": "list",  "head": "見出し", "items": ["項目1", "項目2"]}
  {"type": "phrase", "en": "English phrase", "ja": "意味", "note": "使う場面"}
  {"type": "cta"}   最後の「保存・フォロー」スライド
改行したいところには \n を入れる。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
HANDLE = "@ryugaku_real_usa"
BRAND = "アメリカ留学のリアル"

W, H = 1080, 1350
NAVY = (20, 33, 61)
RED = (214, 40, 57)
CREAM = (250, 247, 240)
WHITE = (255, 255, 255)
INK = (40, 44, 58)
MUTED = (120, 128, 145)
SOFT = (200, 210, 230)

FONT_DIRS = ["/usr/share/fonts/opentype/noto", "/usr/share/fonts/noto-cjk",
             "/usr/share/fonts/truetype/noto", "/System/Library/Fonts"]


def _find(name: str) -> str:
    for d in FONT_DIRS:
        p = Path(d) / name
        if p.exists():
            return str(p)
    for p in Path("/usr/share/fonts").rglob(name):
        return str(p)
    raise SystemExit(f"フォントが見つかりません: {name}（fonts-noto-cjk をインストール）")


BOLD = _find("NotoSansCJK-Bold.ttc")
REG = _find("NotoSansCJK-Regular.ttc")
_cache: dict = {}


def font(bold: bool, size: int):
    k = (bold, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(BOLD if bold else REG, size, index=0)
    return _cache[k]


# ------------------------------------------------------------------ text
NO_START = set("、。，．・：；？！ー）」』】〕〉》”’ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ…‥%％,.!?:;)]}")
TOKEN = re.compile(r"[A-Za-z0-9$%'’\-\.\,/&+#@]+|\s|.", re.S)


def wrap(text: str, f, width: int) -> list[str]:
    lines = []
    for para in text.split("\n"):
        cur: list[str] = []
        for tok in TOKEN.findall(para):
            if not cur or f.getlength("".join(cur) + tok) <= width:
                if cur or not tok.isspace():
                    cur.append(tok)
                continue
            if tok[0] in NO_START and len(cur) > 1:  # 行頭禁則：前のトークンごと次の行へ
                carry = [cur.pop()]
            else:
                carry = []
            lines.append("".join(cur).rstrip())
            cur = carry + ([] if tok.isspace() else [tok])
        lines.append("".join(cur).rstrip())
    return lines


def fit(text: str, bold: bool, size: int, width: int, max_h: int, spacing=1.35, min_size=28):
    while True:
        f = font(bold, size)
        lines = wrap(text, f, width)
        h = int(len(lines) * size * spacing)
        orphan = bold and len(lines) > 1 and len(lines[-1]) <= 2 and size > 40
        if (h <= max_h and not orphan) or size <= min_size:
            return f, lines, size, h
        size -= 2


def draw_lines(d, lines, f, size, x, y, fill, align="left", width=0, spacing=1.35):
    for i, ln in enumerate(lines):
        lx = x
        if align == "center":
            lx = x + (width - f.getlength(ln)) / 2
        d.text((lx, y + i * size * spacing), ln, font=f, fill=fill)


def footer(d, idx, total, dark):
    col = SOFT if dark else MUTED
    d.text((70, H - 95), HANDLE, font=font(True, 30), fill=col)
    pg = f"{idx}/{total}"
    f = font(True, 30)
    d.text((W - 70 - f.getlength(pg), H - 95), pg, font=f, fill=col)


def pill(d, text, cx, y, bg, fg, size=34):
    f = font(True, size)
    w = f.getlength(text)
    d.rounded_rectangle((cx - w / 2 - 28, y, cx + w / 2 + 28, y + size + 30), radius=(size + 30) // 2, fill=bg)
    b = f.getbbox(text)
    d.text((cx - w / 2, y + (size + 30 - (b[3] - b[1])) / 2 - b[1]), text, font=f, fill=fg)


# ------------------------------------------------------------------ slide types
def s_cover(s, idx, total):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.text((70, 70), BRAND, font=font(True, 34), fill=SOFT)
    if s.get("label"):
        pill(d, s["label"], W / 2, 260, RED, WHITE)
    f, lines, size, h = fit(s["title"], True, 116, W - 160, 520, spacing=1.25)
    top = 380 + (520 - h) / 2
    draw_lines(d, lines, f, size, 80, top, WHITE, "center", W - 160, spacing=1.25)
    d.rounded_rectangle((W / 2 - 150, top + h + 30, W / 2 + 150, top + h + 46), radius=8, fill=RED)
    if s.get("sub"):
        f2, l2, s2, _ = fit(s["sub"], True, 50, W - 200, 170)
        draw_lines(d, l2, f2, s2, 100, top + h + 100, SOFT, "center", W - 200)
    d.text((W / 2 - font(True, 36).getlength("スワイプ →") / 2, H - 200), "スワイプ →", font=font(True, 36), fill=WHITE)
    footer(d, idx, total, True)
    return im


def _light(idx, total):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 16), fill=NAVY)
    d.text((70, 60), BRAND, font=font(True, 30), fill=MUTED)
    footer(d, idx, total, False)
    return im, d


def _center(im, top, bottom_used):
    """内容(top〜bottom_used)を上下中央に寄せる"""
    area_top, area_bot = 150, H - 140
    shift = int(((area_bot - area_top) - (bottom_used - top)) / 2 + area_top - top)
    if shift <= 0:
        return im
    band = im.crop((0, top, W, bottom_used))
    im.paste(CREAM, (0, top, W, bottom_used))
    im.paste(band, (0, top + shift))
    return im


def s_point(s, idx, total):
    im, d = _light(idx, total)
    top = y = 170
    if s.get("no") is not None:
        d.ellipse((70, y, 190, y + 120), fill=RED)
        t = str(s["no"])
        f = font(True, 70)
        d.text((130 - f.getlength(t) / 2, y + 12), t, font=f, fill=WHITE)
        y += 170
    f, lines, size, h = fit(s["head"], True, 80, W - 140, 300, spacing=1.25)
    draw_lines(d, lines, f, size, 70, y, NAVY, spacing=1.25)
    y += h + 30
    d.rounded_rectangle((70, y, 190, y + 12), radius=6, fill=RED)
    y += 60
    if s.get("body"):
        f, lines, size, h = fit(s["body"], False, 58, W - 140, H - 160 - y, spacing=1.6)
        draw_lines(d, lines, f, size, 70, y, INK, spacing=1.6)
        y += h
    return _center(im, top, y + 10)


def s_list(s, idx, total):
    im, d = _light(idx, total)
    top = 170
    f, lines, size, h = fit(s["head"], True, 76, W - 140, 250, spacing=1.25)
    draw_lines(d, lines, f, size, 70, top, NAVY, spacing=1.25)
    y = top + h + 60
    items = s.get("items", [])
    avail = H - 170 - y
    per = avail / max(len(items), 1)
    for it in items:
        fi, li, si, hi = fit(it, True, 60, W - 250, per - 30, spacing=1.35, min_size=30)
        d.ellipse((70, y + 6, 134, y + 70), fill=RED)
        d.line((87, y + 38, 99, y + 51, 119, y + 22), fill=WHITE, width=8, joint="curve")
        draw_lines(d, li, fi, si, 165, y + 2, INK, spacing=1.35)
        y += max(hi, 76) + 36
    return _center(im, top, y)


def s_phrase(s, idx, total):
    im, d = _light(idx, total)
    d.rounded_rectangle((60, 190, W - 60, 760), radius=40, fill=NAVY)
    f, lines, size, h = fit(s["en"], True, 84, W - 220, 460, spacing=1.2)
    draw_lines(d, lines, f, size, 110, 190 + (570 - h) / 2, WHITE, "center", W - 220, spacing=1.2)
    f, lines, size, h = fit(s["ja"], True, 64, W - 140, 200)
    draw_lines(d, lines, f, size, 70, 820, RED, "center", W - 140)
    if s.get("note"):
        f2, l2, s2, _ = fit(s["note"], False, 44, W - 180, 280, spacing=1.5)
        draw_lines(d, l2, f2, s2, 90, 840 + h + 30, INK, "center", W - 180, spacing=1.5)
    return im


def s_cta(s, idx, total):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    lines = [("役に立ったら", 70, WHITE), ("保存してね", 110, WHITE)]
    y = 260
    for t, sz, col in lines:
        f = font(True, sz)
        d.text(((W - f.getlength(t)) / 2, y), t, font=f, fill=col)
        y += sz * 1.4
    d.rounded_rectangle((W / 2 - 150, y + 20, W / 2 + 150, y + 36), radius=8, fill=RED)
    msg = s.get("text") or "アメリカ留学の\nお金・英語・生活のリアルを\n毎日発信中"
    f, l2, s2, h = fit(msg, True, 52, W - 200, 300, spacing=1.45)
    draw_lines(d, l2, f, s2, 100, y + 110, SOFT, "center", W - 200, spacing=1.45)
    pill(d, "フォローして見逃さない", W / 2, y + 150 + h, RED, WHITE, size=42)
    f = font(True, 46)
    d.text(((W - f.getlength(HANDLE)) / 2, H - 230), HANDLE, font=f, fill=WHITE)
    return im


def make_story(folder: Path) -> None:
    """1枚目の画像からストーリーズ用（1080x1920）の画像を作る"""
    SW, SH = 1080, 1920
    im = Image.new("RGB", (SW, SH), NAVY)
    d = ImageDraw.Draw(im)
    pill(d, "新しい投稿", SW / 2, 170, RED, WHITE, size=46)
    cover = Image.open(folder / "01.jpg").convert("RGB").resize((840, 1050))
    x, y = (SW - 840) // 2, 330
    d.rounded_rectangle((x - 14, y - 14, x + 854, y + 1064), radius=36, fill=CREAM)
    im.paste(cover, (x, y))
    f = font(True, 56)
    for i, t in enumerate(["プロフィールから", "チェックしてね"]):
        d.text(((SW - f.getlength(t)) / 2, 1490 + i * 80), t, font=f, fill=WHITE)
    f = font(True, 40)
    d.text(((SW - f.getlength(HANDLE)) / 2, 1700), HANDLE, font=f, fill=SOFT)
    im.save(folder / "story.jpg", quality=90, optimize=True)


def story_targets(force=False):
    return [pj.parent for pj in sorted(POSTS.glob("*/post.json"))
            if (pj.parent / "01.jpg").exists() and (force or not (pj.parent / "story.jpg").exists())]


TYPES = {"cover": s_cover, "point": s_point, "list": s_list, "phrase": s_phrase, "cta": s_cta}


# ------------------------------------------------------------------ main
def targets(force=False):
    out = []
    for pj in sorted(POSTS.glob("*/post.json")):
        p = json.loads(pj.read_text(encoding="utf-8"))
        slides = p.get("slides")
        if not slides:
            continue
        names = [f"{i:02d}.jpg" for i in range(1, len(slides) + 1)]
        missing = force or any(not (pj.parent / n).exists() for n in names) or p.get("images") != names
        if missing:
            out.append((pj, p, names))
    return out


def main() -> int:
    force = "--force" in sys.argv
    todo = targets(force)
    if "--check" in sys.argv:
        stories = [pj.parent for pj, _, _ in todo] + story_targets(force)
        print(f"作る必要がある投稿: {len(todo)}（ストーリーズ画像: {len(set(stories))}）")
        return 1 if (todo or stories) else 0
    for pj, p, names in todo:
        slides = p["slides"]
        for i, s in enumerate(slides, 1):
            im = TYPES[s.get("type", "point")](s, i, len(slides))
            im.save(pj.parent / names[i - 1], quality=90, optimize=True)
        if p.get("images") != names:
            p["images"] = names
            pj.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"作成: {pj.parent.name}（{len(names)}枚）")
        make_story(pj.parent)
    for folder in story_targets(force):
        make_story(folder)
        print(f"ストーリーズ画像: {folder.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
