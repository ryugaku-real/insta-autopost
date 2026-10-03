"""営業用サンプルのスライドを作る（posts/ の外。自動投稿の対象にならない）。

  python tools/make_sample.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import render  # noqa: E402

render.HANDLE = "@your_account"
render.BRAND = "サンプル｜SNS運用のコツ"

SLIDES = [
    {"type": "cover", "label": "保存推奨", "title": "投稿ネタが\n尽きない人の\n5つの型", "sub": "今日からそのまま使える", "photo": "study"},
    {"type": "point", "no": 1, "head": "お悩み解決型", "body": "お客さんがよく聞く質問に、1投稿で答える。\n例：「よくある失敗と、その直し方」"},
    {"type": "point", "no": 2, "head": "ビフォーアフター型", "body": "変化が一目でわかる投稿は保存されやすい。\n画像1枚目に結果を出すのがコツ。"},
    {"type": "point", "no": 3, "head": "チェックリスト型", "body": "「やることリスト」は見返される。\n5〜7項目に絞ると読みやすい。"},
    {"type": "list", "head": "投稿前の最終チェック", "items": ["1枚目で何の話かわかる", "数字・固有名詞は確認済み", "PR・広告は冒頭に明記", "最後に保存・フォローの案内"]},
    {"type": "cta", "text": "SNS運用のコツを\nこれからも発信します"},
]

out = ROOT / "samples" / "instagram-carousel"
out.mkdir(parents=True, exist_ok=True)
for i, s in enumerate(SLIDES, 1):
    kind = s["type"]
    im = (render.s_cover(s, i, len(SLIDES), "sample-sns-tips") if kind == "cover"
          else render.TYPES[kind](s, i, len(SLIDES)))
    im.save(out / f"{i:02d}.jpg", quality=90, optimize=True)
    print("作成", out / f"{i:02d}.jpg")
