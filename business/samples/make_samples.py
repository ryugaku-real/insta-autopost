#!/usr/bin/env python3
"""出品ページ用の架空サンプル画像を作る。scripts/render.py の部品を再利用する。

  python3 business/samples/make_samples.py

作られるもの（すべて架空のアカウントのサンプル）:
  business/samples/beauty/01〜05.jpg   美容室向けカルーセル
  business/samples/study/01〜05.jpg    学習教室向けカルーセル
  business/samples/listing_main.jpg    出品ページのメイン画像
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))

import render as R  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

THEMES = {
    "beauty": dict(
        handle="@sample_beauty_salon（架空）", brand="サンプル美容室｜ヘアケア",
        navy=(74, 44, 52), red=(201, 90, 112), cream=(252, 246, 244),
        slides=[
            {"type": "cover", "photo": False, "label": "保存推奨", "title": "ドライヤーの\n3つのコツ", "sub": "ツヤ髪に近づく乾かし方"},
            {"type": "point", "no": 1, "head": "まずタオルで水気を取る", "body": "ゴシゴシこすらず、\nタオルで包んで押さえます。\n濡れた髪は傷みやすいので、\nやさしく扱いましょう。"},
            {"type": "point", "no": 2, "head": "根元から先に乾かす", "body": "根元を先に、毛先は最後に。\n毛先に熱を当てすぎないことで、\nパサつきを防げます。"},
            {"type": "point", "no": 3, "head": "仕上げは冷風で", "body": "最後に冷風を当てると、\n髪の表面が落ち着いて\nまとまりやすくなります。"},
            {"type": "cta", "text": "ヘアケアのコツを\n毎週発信中\n※この投稿は架空のサンプルです"},
        ]),
    "study": dict(
        handle="@sample_study_class（架空）", brand="サンプル学習教室｜家庭学習",
        navy=(24, 62, 74), red=(232, 125, 46), cream=(247, 250, 247),
        slides=[
            {"type": "cover", "photo": False, "label": "保存推奨", "title": "家庭学習が\n続く3つの工夫", "sub": "親子で無理なく習慣に"},
            {"type": "point", "no": 1, "head": "時間と場所を決める", "body": "「夕食の前に15分、リビングで」\nのように決めておきます。\n決まっていれば、\n迷わず始められます。"},
            {"type": "point", "no": 2, "head": "最初は短く始める", "body": "最初から長くやろうとせず、\n10〜15分で十分です。\n続けられたことが、\n自信につながります。"},
            {"type": "point", "no": 3, "head": "できたことを一緒に確認", "body": "点数より「昨日より進んだところ」\nをほめましょう。\nカレンダーにシールを貼るのも\nおすすめです。"},
            {"type": "cta", "text": "家庭学習のヒントを\n毎週発信中\n※この投稿は架空のサンプルです"},
        ]),
}


def apply(theme: dict) -> None:
    R.HANDLE, R.BRAND = theme["handle"], theme["brand"]
    R.NAVY, R.RED, R.CREAM = theme["navy"], theme["red"], theme["cream"]


def render_set(name: str) -> list[Image.Image]:
    th = THEMES[name]
    apply(th)
    out = HERE / name
    out.mkdir(exist_ok=True)
    ims = []
    total = len(th["slides"])
    for i, s in enumerate(th["slides"], 1):
        kind = s["type"]
        im = R.s_cover(s, i, total, name) if kind == "cover" else R.TYPES[kind](s, i, total)
        im.save(out / f"{i:02d}.jpg", quality=90, optimize=True)
        ims.append(im)
    return ims


def _card(src: Image.Image, w: int, h: int, angle: float):
    """角丸＋影つきのカードを回転させて返す（RGBA）"""
    from PIL import ImageFilter
    pad = 60
    im = src.resize((w, h)).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=26, fill=255)
    im.putalpha(mask)
    border = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, w + 23, h + 23), radius=34, fill=(255, 255, 255, 255))
    border.alpha_composite(im, (12, 12))
    canvas = Image.new("RGBA", (w + 24 + pad * 2, h + 24 + pad * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((pad + 6, pad + 24, pad + w + 18, pad + h + 42), radius=34, fill=(20, 33, 61, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(border, (pad, pad))
    return canvas.rotate(angle, expand=True, resample=Image.BICUBIC)


def listing_main(sets: dict[str, list[Image.Image]]) -> None:
    """出品ページのメイン画像（4:3, 1600x1200）"""
    apply(THEMES["study"])
    CW, CH = 1600, 1200
    NAVY, ACC = (20, 33, 61), (232, 62, 90)
    # 背景：やわらかいグラデーション
    im = Image.new("RGB", (CW, CH))
    px = im.load()
    for y in range(CH):
        for x in range(0, CW):
            t = (x / CW * 0.6 + y / CH * 0.4)
            px[x, y] = (int(255 - 18 * t), int(236 + 6 * t), int(232 + 20 * t))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse((900, -250, 1900, 750), fill=(255, 190, 200, 120))
    d.ellipse((-300, 800, 600, 1500), fill=(190, 215, 255, 130))
    # 左：見出し
    f_pill, f_h, f_sub = R.font(True, 42), R.font(True, 100), R.font(True, 50)
    pt = "Instagram投稿制作"
    w = f_pill.getlength(pt) + 70
    d.rounded_rectangle((70, 80, 70 + w, 160), radius=40, fill=NAVY)
    d.text((105, 92), pt, font=f_pill, fill=(255, 255, 255))
    # 見出し3行（2行目に蛍光ペン風のライン）
    d.text((70, 215), "保存したくなる", font=f_h, fill=NAVY)
    d.rounded_rectangle((70, 435, 70 + f_h.getlength("図解投稿を") + 10, 470), radius=14, fill=(255, 214, 90, 255))
    d.text((70, 330), "図解投稿を", font=f_h, fill=NAVY)
    d.text((70, 450), "1本から。", font=f_h, fill=ACC)
    d.text((72, 610), "画像＋キャプションまで制作", font=f_sub, fill=(70, 80, 105))
    # 右：カードを重ねて配置
    cards = [(sets["study"][1], -9, 780, 250), (sets["beauty"][1], 7, 1080, 330), (sets["beauty"][0], -2, 930, 140)]
    for src, ang, x, y in cards:
        c = _card(src, 360, 450, ang)
        im.paste(c, (x - 40, y - 20), c)
    d = ImageDraw.Draw(im, "RGBA")
    # 下：特徴バッジ
    f_b = R.font(True, 40)
    items = ["5枚構成", "縦長1080×1350", "修正2回まで"]
    bx, by = 70, 840
    for t in items:
        w = f_b.getlength(t) + 120
        d.rounded_rectangle((bx, by, bx + w, by + 96), radius=48, fill=(255, 255, 255, 255), outline=NAVY, width=4)
        d.ellipse((bx + 22, by + 26, bx + 66, by + 70), fill=ACC)
        d.line((bx + 32, by + 48, bx + 41, by + 58, bx + 57, by + 38), fill=(255, 255, 255), width=6, joint="curve")
        d.text((bx + 84, by + 20), t, font=f_b, fill=NAVY)
        bx += w + 24
    # 下の帯
    d.rectangle((0, 1040, CW, CH), fill=NAVY)
    f_t = R.font(True, 54)
    msg = "運用中アカウントの経験で、投稿づくりをお手伝い"
    d.text(((CW - f_t.getlength(msg)) / 2, 1075), msg, font=f_t, fill=(255, 255, 255))
    f_n = R.font(False, 26)
    note = "※掲載の制作例は架空のサンプルです"
    d.text(((CW - f_n.getlength(note)) / 2, 1148), note, font=f_n, fill=(190, 200, 225))
    im.save(HERE / "listing_main.jpg", quality=92, optimize=True)


def main() -> None:
    sets = {n: render_set(n) for n in THEMES}
    listing_main(sets)
    print("作成しました:", ", ".join(sorted(p.name for p in HERE.iterdir() if p.is_dir() or p.suffix == ".jpg")))


if __name__ == "__main__":
    main()
