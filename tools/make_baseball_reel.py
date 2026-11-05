#!/usr/bin/env python3
"""日米大学野球リール（動く図解版）を作る。Pillow + ffmpeg だけ。

  python tools/make_baseball_reel.py                書き出し（posts/<FOLDER>/reel.mp4）
  python tools/make_baseball_reel.py --stills 3 9 12 20 30 37
                                                    指定した秒の静止画だけ /tmp に出す（確認用）

動画の仕様: 1080x1920 / 30fps / H.264 / 声（voice.mp3）入り / 約37秒
上の約250px・下の約380pxはインスタのUIで隠れるので、文字は置かない。
"""
from __future__ import annotations

import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import render as R  # noqa: E402  フォントと色を共有する
from reel_audio import make_track  # noqa: E402  効果音とBGM

FOLDER = "2026-11-13-07-us-japan-baseball"
W, H, FPS, DUR = 1080, 1920, 30, 41.75

NAVY, RED, CREAM, WHITE, SOFT = R.NAVY, R.RED, R.CREAM, R.WHITE, R.SOFT
INK = (28, 36, 66)        # 文字
MUTED = (105, 113, 135)   # 補足の文字
LINE = (176, 186, 210)    # 枠線
PANEL = (255, 255, 255)
PANEL2 = (232, 237, 247)
GOLD = (214, 134, 10)
GREEN = (36, 150, 96)


# ------------------------------------------------------------------ 動きの部品
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_io(x):
    return 3 * x * x - 2 * x ** 3


def back(x):  # 少し行き過ぎて戻る（ポンと出る動き）
    c = 1.70158
    x = clamp(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


PHOTO = ROOT / "assets" / "reel-bg-photo.jpg"
VOICE = ROOT / "posts" / FOLDER / "voice.mp3"
PAD_W, PAD_H = 1242, 2208   # 少し大きく作って、ゆっくり動かす（パン）


def build_bg(overlay: float) -> Image.Image:
    """写真を縦長に拡大してぼかし、生成り色を overlay の濃さでかぶせる"""
    from PIL import ImageFilter
    im = Image.open(PHOTO).convert("RGB")
    sc = max(PAD_W / im.width, PAD_H / im.height)
    im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    x, y = (im.width - PAD_W) // 2, (im.height - PAD_H) // 2
    im = im.crop((x, y, x + PAD_W, y + PAD_H)).filter(ImageFilter.GaussianBlur(4))
    return Image.blend(im, Image.new("RGB", im.size, CREAM), overlay).convert("RGBA")


BG_PHOTO = build_bg(0.55)   # 冒頭: 写真をしっかり見せる
BG_CLEAN = build_bg(0.86)   # 図の場面: 図が読みやすいよう淡く


def bg_frame(treal: float, tn: float) -> Image.Image:
    ox = int(60 + 50 * math.sin(treal * 0.35))
    oy = int(min(PAD_H - H, 40 + treal * 5.5))
    box = (ox, oy, ox + W, oy + H)
    w = clamp((tn - 3.6) / 1.0)   # 日本の場面に入るころ、写真を淡くする
    return Image.blend(BG_PHOTO.crop(box), BG_CLEAN.crop(box), w)


def show(img, t, s, e, box, fn, dur=0.5, dy=44, pop=False):
    """時間 s で下からふわっと出て、e でフェードアウトする部品。fn(d) が描く"""
    if t < s or t >= e + 0.4:
        return
    x = clamp((t - s) / dur)
    pin = ease_out(x)
    a = pin * (1 - clamp((t - e) / 0.35))
    if a <= 0:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(lay))
    x0, y0, x1, y1 = box
    reg = lay.crop(box)
    reg.putalpha(reg.getchannel("A").point(lambda v: int(v * a)))
    off = int((1 - (back(x) if pop else pin)) * dy)
    img.alpha_composite(reg, (x0, max(0, min(H - (y1 - y0), y0 + off))))


def text(d, xy, s, size, fill, bold=True):
    d.text(xy, s, font=R.font(bold, size), fill=fill, anchor="mm")


def rrect(d, box, r, fill, outline=None, w=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=w)


def pill(d, cx, cy, s, bg, fg=WHITE, size=44):
    tw = d.textlength(s, font=R.font(True, size))
    rrect(d, (cx - tw / 2 - 36, cy - size * 0.95, cx + tw / 2 + 36, cy + size * 0.95), int(size), bg)
    text(d, (cx, cy), s, size, fg)


def chip(d, cx, cy, label, fill=PANEL2, outline=None, w=170, h=100, size=46, sub=None):
    rrect(d, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 24, fill, outline, 6 if outline else 0)
    if sub:
        text(d, (cx, cy - 16), label, int(size * 0.85), INK)
        text(d, (cx, cy + 22), sub, 26, MUTED, False)
    else:
        text(d, (cx, cy), label, size, INK)


def arrow(d, cx, cy, up, color, h=80, w=46, shaft=18):
    """上下の太い矢印（昇格・降格用）"""
    sgn = -1 if up else 1
    tip = cy + sgn * h / 2
    base = cy - sgn * h / 2
    neck = tip - sgn * w * 0.8
    d.rectangle((cx - shaft / 2, min(base, neck), cx + shaft / 2, max(base, neck)), fill=color)
    d.polygon([(cx - w / 2, neck), (cx + w / 2, neck), (cx, tip)], fill=color)


def xmark(d, cx, cy, r=24):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED)
    k = r * 0.45
    d.line((cx - k, cy - k, cx + k, cy + k), fill=WHITE, width=7)
    d.line((cx - k, cy + k, cx + k, cy - k), fill=WHITE, width=7)


def flag_jp(d, cx, cy, w=72, h=48):
    x0, y0 = cx - w / 2, cy - h / 2
    d.rectangle((x0, y0, x0 + w, y0 + h), fill=WHITE, outline=LINE, width=2)
    r = h * 0.3
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(205, 30, 52))


def flag_us(d, cx, cy, w=72, h=48):
    x0, y0 = cx - w / 2, cy - h / 2
    sh = h / 7
    for i in range(7):
        d.rectangle((x0, y0 + i * sh, x0 + w, y0 + (i + 1) * sh), fill=(190, 40, 55) if i % 2 == 0 else WHITE)
    d.rectangle((x0, y0, x0 + w * 0.46, y0 + sh * 4), fill=(40, 60, 130))
    for gx in range(3):
        for gy in range(2):
            px, py = x0 + w * 0.09 + gx * w * 0.14, y0 + sh * 1.1 + gy * sh * 1.8
            d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=WHITE)
    d.rectangle((x0, y0, x0 + w, y0 + h), outline=LINE, width=2)


def title_pill(d, cx, cy, jp, en, flag, size=44):
    f = R.font(True, size)
    label = f"{jp}  {en}"
    tw = d.textlength(label, font=f)
    total = tw + 72 + 100
    left = cx - total / 2
    rrect(d, (left, cy - size * 1.05, left + total, cy + size * 1.05), int(size * 1.05), RED)
    flag(d, left + 36 + 36, cy)
    text(d, (left + 36 + 100 + tw / 2, cy), label, size, WHITE)


def ball(d, cx, cy, r=60):
    """野球ボール（白い球に赤い縫い目）"""
    d.ellipse((cx + 4 - r, cy + 6 - r, cx + 4 + r, cy + 6 + r), fill=(215, 210, 198))  # 影
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=(120, 128, 150), width=5)
    d.arc((cx - r * 1.55, cy - r * 0.9, cx - r * 0.35, cy + r * 0.9), -62, 62, fill=RED, width=6)
    d.arc((cx + r * 0.35, cy - r * 0.9, cx + r * 1.55, cy + r * 0.9), 118, 242, fill=RED, width=6)


def en(d, xy, s, size=34, fill=MUTED):
    text(d, xy, s, size, fill, False)


# ------------------------------------------------------------------ シーン
# 1部/2部の駒の位置（日本）
SLOTS = [245, 415, 585, 755]
CW = 150   # 駒の幅
ROW1, ROW2 = 660, 1040
# 例としての成績（架空）。シーズンが進むにつれて数字が増えていく
REC = {"A": (9, 1), "B": (7, 3), "C": (5, 5), "D": (1, 9), "E": (9, 1), "F": (6, 4), "G": (5, 5), "H": (3, 7)}


def rec(name: str, p: float) -> str:
    w, l = REC[name]
    return f"{round(w * p)}勝{round(l * p)}敗"
MOVE_S, MOVE_E = 9.6, 11.6


def mover_pos(t):
    """D(1部の最下位)は下へ、E(2部の1位)は上へ。横にふくらんで途中でぶつからない"""
    p = ease_io(clamp((t - MOVE_S) / (MOVE_E - MOVE_S)))
    bump = 120 * math.sin(math.pi * p)
    return (SLOTS[3] + bump, ROW1 + (ROW2 - ROW1) * p), (SLOTS[3] - bump, ROW2 + (ROW1 - ROW2) * p)


def frame_nom(t: float, treal: float) -> Image.Image:
    img = bg_frame(treal, t)
    bob = lambda i: 5 * math.sin(3.0 * t + i * 1.3)   # 駒のゆらゆら
    p = ease_io(clamp((t - 5.4) / 3.0))               # シーズンの進み具合（0→1）

    # ---- 1) フック 0 – 4.2
    show(img, t, 0.0, 4.0, (420, 330, 660, 600), lambda d: ball(d, 540, 490 - abs(math.sin(t * 3.2)) * 50, 56), dy=0)
    show(img, t, 0.0, 4.0, (40, 560, 1040, 1340), lambda d: rrect(d, (50, 570, 1030, 1320), 48, (255, 255, 255, 215)), dy=0)
    show(img, t, 0.2, 4.0, (0, 600, W, 840), lambda d: (
        text(d, (540, 690), "日本は落ちる", 134, INK), en(d, (540, 790), "Japan: teams can be relegated", 42)), pop=True)
    show(img, t, 1.5, 4.0, (0, 860, W, 1130), lambda d: (
        text(d, (540, 940), "アメリカは落ちない", 104, INK),
        rrect(d, (240, 1015, 840, 1027), 6, RED),
        en(d, (540, 1085), "USA: they can't", 42)), pop=True)
    show(img, t, 2.7, 4.0, (0, 1110, W, 1330), lambda d: (
        text(d, (540, 1200), "なぜ？", 130, RED), en(d, (540, 1290), "Why?", 38, RED)), pop=True)

    # ---- 2) 日本 4.0 – 15.4
    A, B = 4.0, 15.2
    show(img, t, A + 0.1, B, (0, 260, W, 390), lambda d: title_pill(d, 540, 325, "日本", "JAPAN", flag_jp))
    show(img, t, A + 0.5, B, (70, 400, 1010, 1280), lambda d: (
        rrect(d, (90, 420, 990, 1260), 40, PANEL, LINE, 4),
        text(d, (540, 462), "リーグ（東都・阪神など）", 44, MUTED),
        en(d, (540, 504), "League (Toto, Hanshin, etc.)", 28)))
    show(img, t, A + 1.2, B, (130, 540, 950, 790), lambda d: (
        rrect(d, (150, 560, 930, 780), 28, PANEL2),
        text(d, (225, 600), "1部", 44, GOLD), en(d, (400, 603), "1st Division", 30),
        [chip(d, x, ROW1 + 20 + bob(i), n, w=CW, sub=rec(n, p)) for i, (x, n) in enumerate(zip(SLOTS[:3], "ABC"))]))
    show(img, t, A + 1.7, B, (130, 920, 950, 1170), lambda d: (
        rrect(d, (150, 940, 930, 1160), 28, PANEL2),
        text(d, (225, 980), "2部", 44, GOLD), en(d, (400, 983), "2nd Division", 30),
        [chip(d, x, ROW2 + 20 + bob(i + 3), n, w=CW, sub=rec(n, p)) for i, (x, n) in enumerate(zip(SLOTS[:3], "FGH"))]))

    def movers(d):
        (dx, dy), (ex, ey) = mover_pos(t)
        done = t >= MOVE_E
        chip(d, dx, dy + 20, "D", outline=RED, w=CW, sub=rec("D", p))
        chip(d, ex, ey + 20, "E", outline=GREEN, w=CW, sub=rec("E", p))
        if not (MOVE_S < t < MOVE_E):   # 動いている間は、補足の文字を隠して見やすくする
            pill(d, dx, dy + 110, "降格" if done else "最下位", RED, size=32)
            en(d, (dx, dy + 160), "Relegated" if done else "Last place", 26, RED)
            pill(d, ex, ey - 70, "昇格" if done else "2部1位", GREEN, size=32)
            en(d, (ex, ey - 112), "Promoted" if done else "2nd Div. champ", 24, GREEN)
    show(img, t, A + 2.4, B, (60, 500, 1040, 1215), movers, dy=0)
    show(img, t, A + 4.6, B, (30, 790, 700, 940), lambda d: (
        pill(d, 300, 840, "入れ替え戦", GOLD, (30, 30, 40), 40), en(d, (300, 905), "Playoff", 30)), pop=True)
    show(img, t, A + 5.0, B, (430, 800, 560, 900), lambda d: (
        arrow(d, 462, 850, False, RED), arrow(d, 524, 850, True, GREEN)), pop=True)
    show(img, t, A + 8.0, B, (0, 1285, W, 1420), lambda d: (
        text(d, (540, 1325), "リーグの中に階層がある", 64, INK), en(d, (540, 1382), "Tiers live inside each league", 36)))
    show(img, t, A + 8.8, B, (0, 1425, W, 1520), lambda d: (
        text(d, (540, 1448), "※東京六大学は6校固定で入れ替えなし", 32, MUTED, False),
        en(d, (540, 1490), "Tokyo Big6: fixed 6 schools, no relegation", 28)))

    # ---- 3) アメリカ 15.4 – 28.2
    A, B = 15.4, 28.0
    show(img, t, A + 0.1, B, (0, 260, W, 390), lambda d: title_pill(d, 540, 325, "アメリカ", "USA", flag_us))
    show(img, t, A + 0.6, B, (70, 400, 1010, 880), lambda d: (
        rrect(d, (90, 420, 990, 860), 36, PANEL, GOLD, 6),
        text(d, (300, 478), "Division I", 56, GOLD), en(d, (770, 480), "NCAA top tier", 32)))
    show(img, t, A + 1.1, B, (70, 895, 1010, 1050), lambda d: (
        rrect(d, (90, 910, 990, 1030), 36, PANEL, LINE, 4), text(d, (540, 970), "Division II", 50, INK)))
    show(img, t, A + 1.6, B, (70, 1065, 1010, 1220), lambda d: (
        rrect(d, (90, 1080, 990, 1200), 36, PANEL, LINE, 4), text(d, (540, 1140), "Division III", 50, INK)))
    for i, (x, n) in enumerate(zip((255, 540, 825), ("Conference A", "Conference B", "Conference C"))):
        show(img, t, A + 2.8 + 0.35 * i, B, (x - 140, 550, x + 140, 720),
             lambda d, x=x, n=n, i=i: chip(d, x, 635 + bob(i), n, w=250, h=110, size=34), pop=True)
    show(img, t, A + 4.0, B, (0, 745, W, 845), lambda d: (
        text(d, (540, 775), "その中に Conference（リーグ）", 38, MUTED, False),
        en(d, (540, 820), "Conferences sit inside the division", 30)))
    for yy in (885, 1055):
        show(img, t, A + 5.0, B, (380, yy - 40, 1010, yy + 40), lambda d, yy=yy: (
            xmark(d, 440, yy), text(d, (610, yy), "成績では動かない", 32, RED), en(d, (860, yy), "Not by results", 28, RED)), pop=True)
    show(img, t, A + 5.4, 23.2, (0, 1235, W, 1360), lambda d: (
        text(d, (540, 1268), "競技力ではDivisionは入れ替わらない", 46, RED),
        en(d, (540, 1322), "Divisions aren't swapped by performance", 32, RED)))
    def school_move(d):
        q = ease_io(clamp((t - 23.8) / 2.2))
        x = 255 + (825 - 255) * q
        y = 727 - 22 * math.sin(math.pi * q)
        chip(d, x, y, "学校X", fill=(255, 241, 214), outline=GOLD, w=150, h=56, size=30)
    show(img, t, 23.4, B, (60, 680, 1020, 790), school_move, dy=0)
    show(img, t, 23.4, B, (0, 1235, W, 1360), lambda d: (
        text(d, (540, 1268), "Conferenceが変わってもDivisionは変わらない", 40, RED),
        en(d, (540, 1322), "Changing conferences doesn't change the division", 30, RED)), pop=True)
    show(img, t, A + 7.2, B, (0, 1375, W, 1500), lambda d: (
        text(d, (540, 1412), "階層の中にリーグがある", 64, INK), en(d, (540, 1468), "Leagues live inside the tiers", 36)))

    # ---- 4) まとめ 28.2 – 34.4
    A, B = 28.2, 34.2
    def jp_card(d):
        title_pill(d, 285, 540, "日本", "JAPAN", flag_jp, size=34)
        rrect(d, (70, 610, 500, 1060), 30, PANEL, LINE, 4)
        text(d, (285, 650), "リーグ League", 34, MUTED)
        rrect(d, (100, 695, 470, 835), 22, PANEL2)
        text(d, (285, 765), "1部", 48, GOLD)
        rrect(d, (100, 870, 470, 1010), 22, PANEL2)
        text(d, (285, 940), "2部", 48, GOLD)
        arrow(d, 285, 852, False, RED, h=44, w=30, shaft=10)
        text(d, (285, 1115), "リーグ ＞ 1部・2部", 40, INK)
        en(d, (285, 1165), "League > Tiers", 32)

    def us_card(d):
        title_pill(d, 795, 540, "アメリカ", "USA", flag_us, size=34)
        rrect(d, (580, 610, 1010, 800), 30, PANEL, GOLD, 5)
        text(d, (795, 648), "Division I", 36, GOLD)
        for i, (cx, n) in enumerate(zip((655, 795, 935), ("Conference A", "Conference B", "Conference C"))):
            chip(d, cx, 735 + bob(i), n.replace('Conference ', 'Conf. '), w=125, h=80, size=24)
        rrect(d, (580, 835, 1010, 930), 26, PANEL, LINE, 4)
        text(d, (795, 882), "Division II", 38, INK)
        rrect(d, (580, 965, 1010, 1060), 26, PANEL, LINE, 4)
        text(d, (795, 1012), "Division III", 38, INK)
        text(d, (795, 1115), "階層 ＞ リーグ", 40, INK)
        en(d, (795, 1165), "Division > Conference", 32)
    show(img, t, A + 0.1, B, (40, 500, 540, 1210), jp_card)
    show(img, t, A + 1.4, B, (540, 500, 1040, 1210), us_card)
    show(img, t, A + 3.0, B, (0, 1250, W, 1470), lambda d: (
        text(d, (540, 1320), "縦と横が逆", 130, GOLD), en(d, (540, 1415), "Opposite structures: vertical vs horizontal", 36)), pop=True)

    # ---- 5) 締め（声なし）34.4 –
    A, B = 34.4, 99.0
    show(img, t, A, B, (420, 480, 660, 750), lambda d: ball(d, 540, 610 - abs(math.sin((t - A) * 3.2)) * 50, 56), dy=0)
    show(img, t, A + 0.2, B, (0, 800, W, 1040), lambda d: (
        text(d, (540, 880), "フォローして", 110, INK), en(d, (540, 985), "Follow for more", 44)), pop=True)
    show(img, t, A + 0.7, B, (0, 1080, W, 1200), lambda d: pill(d, 540, 1140, "@ippei.hashimoto", RED, size=46), pop=True)
    return img


# 声に合わせた時間変換: (実際の秒, 図を作ったときの秒) の対応表。間は直線でつなぐ
ANCHORS = [
    (0.0, 0.0),
    (0.1, 0.2),
    (4.3, 1.5),
    (7.0, 2.7),
    (8.0, 4.0),
    (8.1, 4.1),
    (8.6, 4.5),
    (10.5, 5.2),
    (11.0, 5.7),
    (11.2, 6.4),
    (12.3, 8.6),
    (12.5, 9.0),
    (12.7, 9.6),
    (14.2, 11.6),
    (14.4, 12.0),
    (15.1, 12.8),
    (16.4, 15.4),
    (16.6, 15.5),
    (17.1, 16.0),
    (17.8, 16.5),
    (18.4, 17.0),
    (20.4, 18.2),
    (20.7, 18.55),
    (21.0, 18.9),
    (21.4, 19.4),
    (23.1, 20.4),
    (23.5, 20.8),
    (24.6, 22.6),
    (26.1, 23.4),
    (29.65, 28.2),
    (30.65, 28.3),
    (33.65, 29.6),
    (36.45, 31.2),
    (38.65, 34.2),
    (38.85, 34.4),
    (41.75, 36.4),
]


def nominal(t: float) -> float:
    if t <= ANCHORS[0][0]:
        return ANCHORS[0][1]
    for (r0, n0), (r1, n1) in zip(ANCHORS, ANCHORS[1:]):
        if t <= r1:
            return n0 + (n1 - n0) * (t - r0) / (r1 - r0)
    return ANCHORS[-1][1]


def frame(t: float) -> Image.Image:
    return frame_nom(nominal(t), t)


def real_of(n: float) -> float:
    """nominal() の逆変換: 図を作ったときの秒 n が、実際の動画では何秒か"""
    for (r0, n0), (r1, n1) in zip(ANCHORS, ANCHORS[1:]):
        if n0 <= n <= n1 and n1 > n0:
            return r0 + (n - n0) * (r1 - r0) / (n1 - n0)
    return ANCHORS[-1][0]


SFX_NOMINAL = {
    "pop": [0.2, 1.5, 5.2, 5.7, 8.6, 16.0, 16.5, 17.0, 18.2, 18.55, 18.9, 20.8, 23.4, 28.3, 29.6, 34.6, 35.1],
    "whoosh": [4.0, 9.6, 15.4, 23.8, 28.2],
    "ding": [2.7, 11.6, 31.2],
    "thud": [11.6],
    "click": [20.4, 20.5],
}


def sfx_events() -> dict[str, list[float]]:
    return {k: [real_of(n) - (0.2 if k == "whoosh" else 0.0) for n in v] for k, v in SFX_NOMINAL.items()}


def main() -> int:
    if "--stills" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:]]
        for t in ts:
            frame(t).convert("RGB").save(f"/tmp/baseball_{t:05.1f}.jpg", quality=90)
            print(f"/tmp/baseball_{t:05.1f}.jpg")
        return 0
    out = ROOT / "posts" / FOLDER / "reel.mp4"
    track = Path(tempfile.mkdtemp()) / "sfx_bgm.wav"
    make_track(DUR, sfx_events(), str(track))
    mix = ("[1:a]aformat=sample_rates=44100:channel_layouts=mono[v];"
           "[2:a]aformat=sample_rates=44100:channel_layouts=mono[m];"
           "[v][m]amix=inputs=2:normalize=0:duration=longest,"
           f"afade=t=out:st={DUR - 0.3}:d=0.3,alimiter=limit=0.95[o]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(VOICE), "-i", str(track),
           "-filter_complex", mix, "-map", "0:v", "-map", "[o]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-t", str(DUR), "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(frame(i / FPS).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() != 0:
        return 1
    print(f"作成: {out}（{n}フレーム）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
