#!/usr/bin/env python3
"""日米大学野球リール（動く図解版）を作る。Pillow + ffmpeg だけ。

  python tools/make_baseball_reel.py                書き出し（posts/<FOLDER>/reel.mp4）
  python tools/make_baseball_reel.py --stills 3 9 12 20 30 37
                                                    指定した秒の静止画だけ /tmp に出す（確認用）

動画の仕様: 1080x1920 / 30fps / H.264 / 音声なし / 約38秒
上の約250px・下の約380pxはインスタのUIで隠れるので、文字は置かない。
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import render as R  # noqa: E402  フォントと色を共有する

FOLDER = "2026-11-13-07-us-japan-baseball"
W, H, FPS, DUR = 1080, 1920, 30, 38.0

NAVY, RED, CREAM, WHITE, SOFT = R.NAVY, R.RED, R.CREAM, R.WHITE, R.SOFT
PANEL = (32, 50, 90)
PANEL2 = (44, 66, 112)
GOLD = (246, 190, 60)
GREEN = (70, 190, 130)


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


def build_bg():
    """ゆっくり流れるドット背景の元画像（縦に80pxごとに繰り返す）"""
    im = Image.new("RGBA", (W, H + 80), NAVY + (255,))
    d = ImageDraw.Draw(im)
    for y in range(0, H + 80, 80):
        for x in range(0, W + 80, 80):
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(38, 54, 92, 255))
    return im


BG = build_bg()


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


def chip(d, cx, cy, label, fill=PANEL2, outline=None, w=170, h=100, size=46):
    rrect(d, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 24, fill, outline, 6 if outline else 0)
    text(d, (cx, cy), label, size, WHITE)


# ------------------------------------------------------------------ シーン
# 1部/2部の駒の位置（日本）
SLOTS = [245, 415, 585, 755]
CW = 150   # 駒の幅
ROW1, ROW2 = 660, 1040
MOVE_S, MOVE_E = 9.6, 11.6


def mover_pos(t):
    """D(1部の最下位)は下へ、E(2部の1位)は上へ。横にふくらんで途中でぶつからない"""
    p = ease_io(clamp((t - MOVE_S) / (MOVE_E - MOVE_S)))
    bump = 120 * math.sin(math.pi * p)
    return (SLOTS[3] + bump, ROW1 + (ROW2 - ROW1) * p), (SLOTS[3] - bump, ROW2 + (ROW1 - ROW2) * p)


def frame(t: float) -> Image.Image:
    img = BG.crop((0, int(t * 14) % 80, W, int(t * 14) % 80 + H))

    # ---- 1) フック 0 – 4.2
    show(img, t, 0.2, 4.0, (0, 600, W, 820), lambda d: text(d, (540, 700), "日本は落ちる", 134, WHITE), pop=True)
    show(img, t, 1.5, 4.0, (0, 840, W, 1060),
         lambda d: (text(d, (540, 940), "アメリカは落ちない", 104, CREAM),
                    rrect(d, (240, 1020, 840, 1032), 6, RED)), pop=True)
    show(img, t, 2.7, 4.0, (0, 1100, W, 1200), lambda d: text(d, (540, 1150), "大学野球の仕組みの違い", 50, SOFT, False))

    # ---- 2) 日本 4.0 – 15.4
    A, B = 4.0, 15.2
    show(img, t, A + 0.1, B, (0, 270, W, 380), lambda d: pill(d, 540, 325, "日本", RED))
    show(img, t, A + 0.5, B, (70, 400, 1010, 1280), lambda d: (
        rrect(d, (90, 420, 990, 1260), 40, PANEL, SOFT, 4),
        text(d, (540, 480), "リーグ（東都・阪神など）", 46, SOFT)))
    show(img, t, A + 1.2, B, (130, 540, 950, 780), lambda d: (
        rrect(d, (150, 560, 930, 780), 28, PANEL2),
        text(d, (230, 600), "1部", 44, GOLD),
        [chip(d, x, ROW1 + 20, n, w=CW) for x, n in zip(SLOTS[:3], "ABC")]))
    show(img, t, A + 1.7, B, (130, 920, 950, 1160), lambda d: (
        rrect(d, (150, 940, 930, 1160), 28, PANEL2),
        text(d, (230, 980), "2部", 44, GOLD),
        [chip(d, x, ROW2 + 20, n, w=CW) for x, n in zip(SLOTS[:3], "FGH")]))

    def movers(d):
        (dx, dy), (ex, ey) = mover_pos(t)
        done = t >= MOVE_E
        chip(d, dx, dy + 20, "D", outline=RED, w=CW)
        chip(d, ex, ey + 20, "E", outline=GREEN, w=CW)
        # 動いたあとに「降格 / 昇格」、動く前は「最下位 / 2部1位」
        pill(d, dx, dy + 110, "降格" if done else "最下位", RED, size=32)
        pill(d, ex, ey - 70, "昇格" if done else "2部1位", GREEN, size=32)
    show(img, t, A + 2.4, B, (60, 520, 1040, 1200), movers, dy=0)
    show(img, t, A + 4.6, B, (150, 800, 700, 900), lambda d: pill(d, 400, 850, "入れ替え戦", GOLD, (30, 30, 40), 40), pop=True)
    show(img, t, A + 8.0, B, (0, 1300, W, 1390), lambda d: text(d, (540, 1345), "リーグの中に階層がある", 66, WHITE))
    show(img, t, A + 8.8, B, (0, 1400, W, 1480), lambda d: text(d, (540, 1440), "※東京六大学は6校固定で入れ替えなし", 36, SOFT, False))

    # ---- 3) アメリカ 15.4 – 28.2
    A, B = 15.4, 28.0
    show(img, t, A + 0.1, B, (0, 270, W, 380), lambda d: pill(d, 540, 325, "アメリカ", RED))
    show(img, t, A + 0.6, B, (70, 400, 1010, 920), lambda d: (
        rrect(d, (90, 420, 990, 900), 36, PANEL, GOLD, 6),
        text(d, (300, 480), "Division I", 56, GOLD)))
    show(img, t, A + 1.1, B, (70, 940, 1010, 1120), lambda d: (
        rrect(d, (90, 960, 990, 1100), 36, PANEL, SOFT, 4), text(d, (540, 1030), "Division II", 50, WHITE)))
    show(img, t, A + 1.6, B, (70, 1140, 1010, 1320), lambda d: (
        rrect(d, (90, 1160, 990, 1300), 36, PANEL, SOFT, 4), text(d, (540, 1230), "Division III", 50, WHITE)))
    for i, (x, n) in enumerate(zip((255, 540, 825), ("SEC", "ACC", "Big 12"))):
        show(img, t, A + 2.8 + 0.35 * i, B, (x - 140, 560, x + 140, 720),
             lambda d, x=x, n=n: chip(d, x, 640, n, w=250, h=110, size=50), pop=True)
    show(img, t, A + 4.0, B, (0, 770, W, 860), lambda d: text(d, (540, 815), "その中に Conference（リーグ）", 40, SOFT, False))
    show(img, t, A + 5.2, B, (0, 1330, W, 1420), lambda d: text(d, (540, 1375), "競技力ではDivisionは入れ替わらない", 48, RED))
    show(img, t, A + 7.2, B, (0, 1430, W, 1520), lambda d: text(d, (540, 1475), "階層の中にリーグがある", 66, WHITE))

    # ---- 4) まとめ 28.2 – 34.4
    A, B = 28.2, 34.2
    show(img, t, A + 0.1, B, (0, 440, W, 780), lambda d: (
        pill(d, 540, 520, "日本", RED), text(d, (540, 650), "リーグ ＞ 1部・2部", 84, WHITE)))
    show(img, t, A + 1.4, B, (0, 840, W, 1180), lambda d: (
        pill(d, 540, 920, "アメリカ", RED), text(d, (540, 1050), "Division ＞ Conference", 72, WHITE)))
    show(img, t, A + 3.0, B, (0, 1230, W, 1420), lambda d: text(d, (540, 1320), "縦と横が逆", 136, GOLD), pop=True)

    # ---- 5) 締め 34.4 – 38
    A, B = 34.4, 99.0
    show(img, t, A, B, (0, 700, W, 900), lambda d: text(d, (540, 800), "保存してね", 126, WHITE), pop=True)
    show(img, t, A + 0.5, B, (0, 940, W, 1040), lambda d: text(d, (540, 990), "アメリカ留学のリアルを毎日発信中", 44, SOFT, False))
    show(img, t, A + 0.9, B, (0, 1070, W, 1190), lambda d: pill(d, 540, 1130, "@ryugaku_real_usa", RED, size=44))
    return img


def main() -> int:
    if "--stills" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:]]
        for t in ts:
            frame(t).convert("RGB").save(f"/tmp/baseball_{t:05.1f}.jpg", quality=90)
            print(f"/tmp/baseball_{t:05.1f}.jpg")
        return 0
    out = ROOT / "posts" / FOLDER / "reel.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
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
