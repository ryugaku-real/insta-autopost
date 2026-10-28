#!/usr/bin/env python3
"""プロフィール画像（アイコン）を作る。 python3 -I business/samples/make_icon.py
丸く切り抜かれても欠けないよう、文字と図形は中央の円の中に収めている。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))

import render as R  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

S = 800
NAVY, ACC, YEL, WHITE = (20, 33, 61), (232, 62, 90), (255, 214, 90), (255, 255, 255)


def card(w, h, angle, fill):
    pad = 40
    c = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad + 4, pad + 14, pad + w + 4, pad + h + 14), radius=22, fill=(0, 0, 0, 90))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(c).rounded_rectangle((pad, pad, pad + w, pad + h), radius=22, fill=fill)
    return c.rotate(angle, expand=True, resample=Image.BICUBIC)


def main() -> None:
    im = Image.new("RGB", (S, S), NAVY)
    px = im.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            px[x, y] = (int(20 + 22 * t), int(33 + 28 * t), int(61 + 45 * t))
    base = im.convert("RGBA")
    # カルーセルのカード3枚（左右は薄い色・中央が前面）。中心座標で配置する
    def put(c, cx, cy):
        base.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))
    cw, ch, cyc = 170, 215, 215
    put(card(cw, ch, 11, (214, 222, 245, 255)), S / 2 + 105, cyc + 10)
    put(card(cw, ch, -11, (214, 222, 245, 255)), S / 2 - 105, cyc + 10)
    put(card(cw + 20, ch + 20, 0, (255, 255, 255, 255)), S / 2, cyc)
    d = ImageDraw.Draw(base)
    x0, y0 = S / 2 - (cw + 20) / 2, cyc - (ch + 20) / 2
    d.ellipse((x0 + 18, y0 + 18, x0 + 62, y0 + 62), fill=ACC)
    d.line((x0 + 28, y0 + 40, x0 + 37, y0 + 50, x0 + 53, y0 + 29), fill=WHITE, width=6, joint="curve")
    for i, hgt in enumerate([50, 85, 120]):
        x = x0 + 24 + i * 50
        d.rounded_rectangle((x, y0 + 205 - hgt, x + 34, y0 + 205), radius=8, fill=(ACC if i == 2 else NAVY))
    # 文字：SNS図解ラボ（円で切り抜かれても欠けない位置）
    f1, f2 = R.font(True, 104), R.font(True, 40)
    t1, t2 = "SNS図解ラボ", "Instagram投稿制作"
    d.text(((S - f1.getlength(t1)) / 2, 420), t1, font=f1, fill=WHITE)
    d.rounded_rectangle((S / 2 - 230, 560, S / 2 + 230, 574), radius=7, fill=YEL)
    d.text(((S - f2.getlength(t2)) / 2, 602), t2, font=f2, fill=(200, 210, 235))
    base.convert("RGB").save(HERE / "profile_icon.png", optimize=True)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S - 1, S - 1), fill=255)
    prev = Image.new("RGB", (S, S), (240, 240, 240))
    prev.paste(base.convert("RGB"), (0, 0), mask)
    prev.resize((300, 300)).save(HERE / "profile_icon_preview_round.png")
    print("作成: profile_icon.png / profile_icon_preview_round.png")


if __name__ == "__main__":
    main()
