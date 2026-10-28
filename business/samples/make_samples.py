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


def listing_main(sets: dict[str, list[Image.Image]]) -> None:
    """出品ページのメイン画像（4:3, 1600x1200）"""
    apply(THEMES["study"])
    CW, CH = 1600, 1200
    NAVY, ACC, CREAM = (20, 33, 61), (214, 40, 57), (250, 247, 240)
    im = Image.new("RGB", (CW, CH), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, CW, 420), fill=NAVY)
    t1, t2 = "Instagramカルーセル投稿を制作", "保存したくなる図解を、1本から"
    f1, f2 = R.font(True, 84), R.font(True, 52)
    d.text(((CW - f1.getlength(t1)) / 2, 90), t1, font=f1, fill=(255, 255, 255))
    d.rounded_rectangle((CW / 2 - 120, 235, CW / 2 + 120, 247), radius=6, fill=ACC)
    d.text(((CW - f2.getlength(t2)) / 2, 285), t2, font=f2, fill=(200, 210, 230))
    # 実績の自分のアカウント画像は含めず、制作例（架空サンプル）を並べる
    picks = [sets["beauty"][0], sets["beauty"][1], sets["study"][0], sets["study"][2]]
    tw, th = 330, 412
    gap = (CW - tw * 4) // 5
    for i, p in enumerate(picks):
        x = gap + i * (tw + gap)
        y = 470
        d.rounded_rectangle((x - 8, y - 8, x + tw + 8, y + th + 8), radius=18, fill=(255, 255, 255))
        im.paste(p.resize((tw, th)), (x, y))
    badges = ["1080×1350 縦長", "キャプション付き", "修正2回まで"]
    f3 = R.font(True, 40)
    bx = 90
    for b in badges:
        w = f3.getlength(b) + 60
        d.rounded_rectangle((bx, 1010, bx + w, 1090), radius=40, fill=NAVY)
        d.text((bx + 30, 1022), b, font=f3, fill=(255, 255, 255))
        bx += w + 24
    f4 = R.font(False, 26)
    d.text((90, 1130), "※掲載の制作例は架空のサンプルです", font=f4, fill=(120, 128, 145))
    im.save(HERE / "listing_main.jpg", quality=90, optimize=True)


def main() -> None:
    sets = {n: render_set(n) for n in THEMES}
    listing_main(sets)
    print("作成しました:", ", ".join(sorted(p.name for p in HERE.iterdir() if p.is_dir() or p.suffix == ".jpg")))


if __name__ == "__main__":
    main()
