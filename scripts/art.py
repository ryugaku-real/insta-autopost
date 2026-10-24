"""リール用の動くイラスト（コードで描くフラットなベクター風）。reel.py から使う。

  mascot(t, mouth, hop)  キャラクター（まばたき・口パク・ゆれ）。mouth は 0〜1（口の開き）
  icon(name, t)          小物（coin / card / plane / books / bubble / cap / mail / bookmark / check / globe）
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

SS = 3   # 描画は3倍の大きさで行い、縮小してなめらかにする
NAVY, RED, YELLOW, WHITE = (20, 33, 61), (214, 40, 57), (255, 214, 77), (255, 255, 255)
SKIN, HAIR, BLUSH = (255, 224, 196), (74, 52, 44), (255, 160, 150)
OUTLINE = (10, 16, 34)


def _canvas(w: int, h: int):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _done(im: Image.Image, w: int, h: int) -> Image.Image:
    return im.resize((w, h), Image.LANCZOS)


def _ell(d, cx, cy, rx, ry, **kw):
    d.ellipse(((cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS), **kw)


def _poly(d, pts, **kw):
    d.polygon([(x * SS, y * SS) for x, y in pts], **kw)


def _rr(d, x0, y0, x1, y1, r, **kw):
    d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), radius=r * SS, **kw)


def _line(d, pts, width, fill):
    d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=int(width * SS), joint="curve")


# ------------------------------------------------------------------ キャラクター
def mascot(t: float, mouth: float = 0.0, hop: float = 0.0) -> Image.Image:
    """卒業帽をかぶった留学生キャラ。360x360。下半分は体（画面の下からのぞく想定）。"""
    w = h = 360
    im, d = _canvas(w, h)
    bob = 5 * math.sin(t * 3.2) - 40 * hop
    cx, cy = 180, 190 + bob
    # 体（ネイビーのジャケットと白いシャツ）
    _poly(d, [(70, 360), (95, 285 + bob * 0.4), (265, 285 + bob * 0.4), (290, 360)], fill=NAVY)
    _poly(d, [(150, 285 + bob * 0.4), (180, 335), (210, 285 + bob * 0.4)], fill=WHITE)
    _poly(d, [(172, 300 + bob * 0.4), (188, 300 + bob * 0.4), (194, 345), (180, 360), (166, 345)], fill=RED)
    # 手を振る腕（話しているあいだ少し動く）
    ang = math.sin(t * 7) * 0.35 * min(1, mouth * 2 + 0.2)
    ax, ay = 300 + 18 * math.sin(ang), 300 - 38 * math.cos(ang) + bob * 0.4
    _line(d, [(278, 330), (ax, ay)], 26, NAVY)
    _ell(d, ax, ay - 8, 17, 17, fill=SKIN)
    # 首・顔
    _rr(d, 160, 262 + bob * 0.5, 200, 292 + bob * 0.4, 10, fill=SKIN)
    _ell(d, cx, cy, 92, 86, fill=SKIN)
    # 髪（顔の上と横）
    _ell(d, cx, cy - 30, 96, 66, fill=HAIR)
    _ell(d, cx, cy - 6, 92, 70, fill=SKIN)                       # 顔でおでこを戻す
    _poly(d, [(cx - 92, cy - 12), (cx - 40, cy - 52), (cx + 30, cy - 62), (cx + 92, cy - 12), (cx + 60, cy - 70), (cx - 60, cy - 70)], fill=HAIR)
    _ell(d, cx - 88, cy + 8, 16, 40, fill=HAIR)
    _ell(d, cx + 88, cy + 8, 16, 40, fill=HAIR)
    # ほっぺ
    _ell(d, cx - 54, cy + 30, 18, 11, fill=BLUSH + (150,))
    _ell(d, cx + 54, cy + 30, 18, 11, fill=BLUSH + (150,))
    # 目（まばたき）
    blink = (t % 3.6) < 0.13
    for ex in (-34, 34):
        if blink:
            _line(d, [(cx + ex - 14, cy + 6), (cx + ex + 14, cy + 6)], 5, OUTLINE)
        else:
            _ell(d, cx + ex, cy + 6, 11, 15, fill=OUTLINE)
            _ell(d, cx + ex + 4, cy, 4, 4, fill=WHITE)
    # 口：しゃべっている間は開く
    m = max(0.0, min(1.0, mouth))
    if m < 0.12:
        d.arc(((cx - 22) * SS, (cy + 28) * SS, (cx + 22) * SS, (cy + 58) * SS), 20, 160, fill=OUTLINE, width=5 * SS)
    else:
        _ell(d, cx, cy + 42, 16 + 6 * m, 6 + 20 * m, fill=OUTLINE)
        _ell(d, cx, cy + 42 + 8 * m, 10 + 3 * m, 5 + 6 * m, fill=(230, 90, 100))
    # 卒業帽
    ty = cy - 88
    _rr(d, cx - 56, ty - 4, cx + 56, ty + 30, 10, fill=NAVY)
    _poly(d, [(cx - 120, ty - 6), (cx, ty - 50), (cx + 120, ty - 6), (cx, ty + 22)], fill=(52, 74, 126))
    _poly(d, [(cx - 120, ty - 6), (cx, ty - 50), (cx + 120, ty - 6), (cx, ty - 14)], fill=(70, 96, 160))
    sw = math.sin(t * 4) * 6
    _line(d, [(cx + 100, ty - 6), (cx + 106 + sw, ty + 40)], 5, YELLOW)
    _ell(d, cx + 106 + sw, ty + 46, 9, 12, fill=YELLOW)
    out = _done(im, w, h)
    return out.rotate(2.5 * math.sin(t * 2.1), resample=Image.BICUBIC, center=(180, 360))


# ------------------------------------------------------------------ 小物
def icon(name: str, t: float) -> Image.Image:
    return _ICONS[name](t)


def _coin(t):
    w = h = 300
    im, d = _canvas(w, h)
    y = 150 - 14 * abs(math.sin(t * 3))                  # ぴょんぴょん
    sx = abs(math.cos(t * 2.4)) * 0.85 + 0.15            # くるくる回転
    rx = 100 * sx
    _ell(d, 150, 262, 70 * (1 - 0.15 * abs(math.sin(t * 3))), 12, fill=(0, 0, 0, 60))
    _ell(d, 150, y, rx + 10 * sx, 110, fill=(214, 160, 20))
    _ell(d, 150, y, rx, 100, fill=YELLOW)
    if sx > 0.35:
        _ell(d, 150, y, rx * 0.78, 78, outline=(214, 160, 20), width=6 * SS)
        d.text((150 * SS, y * SS), "$", fill=(190, 135, 10), anchor="mm", font=_font(int(120 * SS * min(1, sx + 0.2))))
    return _done(im, w, h)


def _card(t):
    w = h = 300
    im, d = _canvas(w, h)
    _rr(d, 28, 70, 272, 220, 22, fill=(60, 110, 230))
    _rr(d, 28, 98, 272, 128, 0, fill=NAVY)
    _rr(d, 48, 160, 118, 188, 6, fill=YELLOW)
    for i in range(4):
        _rr(d, 150 + i * 28, 172, 168 + i * 28, 184, 4, fill=WHITE)
    out = _done(im, w, h)
    return out.rotate(8 * math.sin(t * 2.2), resample=Image.BICUBIC).transform(out.size, Image.AFFINE, (1, 0, 0, 0, 1, -12 * math.sin(t * 3)), resample=Image.BICUBIC)


def _plane(t):
    w = h = 300
    im, d = _canvas(w, h)
    for i in range(3):                                   # 雲
        cx = (80 + i * 110 - t * 60) % 360 - 30
        _ell(d, cx, 230 - i * 6, 34, 14, fill=(255, 255, 255, 120))
    _poly(d, [(40, 150), (260, 100), (190, 205), (150, 170), (125, 215), (115, 165)], fill=WHITE)
    _poly(d, [(115, 165), (150, 170), (125, 215)], fill=(200, 210, 230))
    _poly(d, [(150, 170), (260, 100), (190, 205)], fill=(225, 232, 245))
    out = _done(im, w, h)
    return out.rotate(-7 + 6 * math.sin(t * 2), resample=Image.BICUBIC).transform(out.size, Image.AFFINE, (1, 0, 0, 0, 1, -14 * math.sin(t * 2.6)), resample=Image.BICUBIC)


def _books(t):
    w = h = 300
    im, d = _canvas(w, h)
    cols = [RED, (60, 110, 230), YELLOW, (60, 170, 120)]
    for i, c in enumerate(cols[:3]):
        dy = -8 * max(0, math.sin(t * 3 - i * 0.9))       # 順番にぴょこっと
        y = 230 - i * 48 + dy
        _rr(d, 50 + (i % 2) * 14, y - 40, 250 - (i % 2) * 10, y, 8, fill=c)
        _rr(d, 62 + (i % 2) * 14, y - 28, 236 - (i % 2) * 10, y - 12, 4, fill=(255, 255, 255, 190))
    return _done(im, w, h)


def _bubble(t):
    w = h = 300
    im, d = _canvas(w, h)
    s = 1 + 0.04 * math.sin(t * 4)
    _rr(d, 150 - 120 * s, 150 - 78 * s, 150 + 120 * s, 150 + 62 * s, 44, fill=WHITE)
    _poly(d, [(86, 200), (70, 262), (140, 208)], fill=WHITE)
    for i in range(3):                                   # 「…」が順番にはねる
        _ell(d, 100 + i * 50, 148 - 16 * max(0, math.sin(t * 6 - i * 0.8)), 15, 15, fill=NAVY)
    return _done(im, w, h)


def _cap(t):
    w = h = 300
    im, d = _canvas(w, h)
    y = 150 + 10 * math.sin(t * 3)
    _rr(d, 90, y, 210, y + 60, 16, fill=NAVY)
    _poly(d, [(20, y - 4), (150, y - 62), (280, y - 4), (150, y + 34)], fill=(70, 96, 160))
    sw = 12 * math.sin(t * 4)
    _line(d, [(250, y - 2), (258 + sw, y + 70)], 7, YELLOW)
    _ell(d, 258 + sw, y + 80, 12, 16, fill=YELLOW)
    return _done(im, w, h)


def _mail(t):
    w = h = 300
    im, d = _canvas(w, h)
    y = 160 + 10 * math.sin(t * 3)
    _rr(d, 40, y - 70, 260, y + 70, 14, fill=WHITE)
    _line(d, [(46, y - 62), (150, y + 12), (254, y - 62)], 10, (200, 208, 226))
    _ell(d, 250, y - 74, 24, 24, fill=RED)
    return _done(im, w, h)


def _bookmark(t):
    w = h = 300
    im, d = _canvas(w, h)
    drop = 1 - min(1.0, (t % 2.4) / 0.5)
    y = 40 - 220 * drop ** 2 + (-10 * math.sin((t % 2.4) * 8) * (1 - min(1, (t % 2.4) / 1.2)))
    _poly(d, [(95, y), (205, y), (205, y + 220), (150, y + 170), (95, y + 220)], fill=RED)
    _poly(d, [(150, y + 56), (160, y + 80), (186, y + 82), (166, y + 98), (173, y + 124), (150, y + 110), (127, y + 124), (134, y + 98), (114, y + 82), (140, y + 80)], fill=WHITE)
    return _done(im, w, h)


def _check(t):
    w = h = 300
    im, d = _canvas(w, h)
    s = min(1.0, (t % 2.4) / 0.35)
    r = 105 * (1 + 0.8 * (1 - s) * 0.0) * (0.6 + 0.4 * s)
    _ell(d, 150, 150, r, r, fill=(60, 170, 120))
    p = max(0.0, min(1.0, ((t % 2.4) - 0.2) / 0.4))
    pts = [(90, 155), (135, 200), (215, 105)]
    if p > 0:
        seg1 = min(1.0, p * 2)
        e1 = (pts[0][0] + (pts[1][0] - pts[0][0]) * seg1, pts[0][1] + (pts[1][1] - pts[0][1]) * seg1)
        path = [pts[0], e1]
        if p > 0.5:
            s2 = (p - 0.5) * 2
            path.append((pts[1][0] + (pts[2][0] - pts[1][0]) * s2, pts[1][1] + (pts[2][1] - pts[1][1]) * s2))
        _line(d, path, 22, WHITE)
    return _done(im, w, h)


def _globe(t):
    w = h = 300
    im, d = _canvas(w, h)
    _ell(d, 150, 150, 112, 112, fill=(60, 110, 230))
    off = (t * 40) % 220
    for (x, y, rx, ry) in [(60, 110, 40, 28), (170, 90, 34, 30), (130, 200, 46, 26), (230, 170, 30, 36)]:
        for k in (0, 1):
            cx = (x + off - 110 + k * 220) % 440 - 110
            if (cx - 150) ** 2 + (y - 150) ** 2 < 100 ** 2:
                _ell(d, cx, y, rx, ry, fill=(60, 170, 120))
    _ell(d, 150, 150, 112, 112, outline=WHITE, width=6 * SS)
    _ell(d, 112, 106, 26, 16, fill=(255, 255, 255, 90))
    return _done(im, w, h)


_FONT = {}


def _font(size: int):
    from PIL import ImageFont
    if size not in _FONT:
        import render as R
        _FONT[size] = ImageFont.truetype(R.BOLD, size, index=0)
    return _FONT[size]


_ICONS = {"coin": _coin, "card": _card, "plane": _plane, "books": _books, "bubble": _bubble,
          "cap": _cap, "mail": _mail, "bookmark": _bookmark, "check": _check, "globe": _globe}
