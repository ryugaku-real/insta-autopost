#!/usr/bin/env python3
"""reels/<名前>/reel.json から縦型リール動画（reel.mp4）・表紙（cover.jpg）・キャプション（caption.txt）を作る。

手動投稿用。reels/ は自動投稿（posts/）とは完全に別なので、ここで作っても勝手には投稿されない。

  python scripts/reel.py make [--force] [NAME ...]   足りない動画を作る（--force で作り直し）
  python scripts/reel.py list                        一覧（秒数つき）

reel.json の書き方:
{
  "caption": "キャプション本文 #タグ",
  "scenes": [
    {"type": "hook", "label": "保存推奨", "text": "留学1年目\\nお金は何にかかる？", "sec": 2.8},
    {"type": "point", "no": 1, "text": "家賃\\n!月 $600〜1,200", "sec": 3},
    {"type": "cta", "text": "!保存して\\n後で見返してね"}
  ]
}
- 行頭が「!」の行は強調色（黄色）で表示
- photo: "campus" などジャンル名を書くと背景の写真を変えられる（省略時は自動）
- 音声なし。投稿するとき、アプリ内でトレンド音源を足す想定
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render as R  # noqa: E402  フォント・折り返し・写真取得を共用

ROOT = R.ROOT
REELS = ROOT / "reels"
W, H, FPS = 1080, 1920, 30
YELLOW = (255, 214, 77)
SAFE_TOP, SAFE_BOTTOM = 300, 1480   # アプリのUIに隠れない範囲
DEFAULT_SEC = {"hook": 3.0, "point": 3.2, "cta": 2.6}


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


# ------------------------------------------------------------------ background
def background(name: str, scene: dict, idx: int) -> Image.Image:
    """ぼかして暗くした写真（ズーム用に少し大きめ）。写真がなければネイビー単色のグラデ。"""
    bw, bh = int(W * 1.15), int(H * 1.15)
    tag = scene.get("photo") if isinstance(scene.get("photo"), str) else None
    got = None if scene.get("photo") is False else R.pick_photo(f"{name}-{idx}", tag)
    if got:
        im = got[0].resize((bw, int(bw * got[0].height / got[0].width)))
        if im.height < bh:
            im = im.resize((int(im.width * bh / im.height), bh))
        x, y = (im.width - bw) // 2, (im.height - bh) // 2
        im = im.crop((x, y, x + bw, y + bh)).filter(ImageFilter.GaussianBlur(3))
        shade = Image.new("RGB", im.size, R.NAVY)
        return Image.blend(im, shade, 0.68)
    im = Image.new("RGB", (bw, bh), R.NAVY)
    d = ImageDraw.Draw(im)
    for yy in range(bh):
        k = yy / bh
        d.line([(0, yy), (bw, yy)], fill=(int(20 + 18 * k), int(33 + 20 * k), int(61 + 40 * k)))
    return im


# ------------------------------------------------------------------ text layer
def text_layer(scene: dict) -> Image.Image:
    kind = scene.get("type", "point")
    lines_src = scene.get("text", "").split("\n")
    size = {"hook": 128, "cta": 108}.get(kind, 96)
    width = W - 160
    plain = "\n".join(l.lstrip("!") for l in lines_src)
    f, lines, size, h = R.fit(plain, True, size, width, SAFE_BOTTOM - SAFE_TOP - 260, spacing=1.32, min_size=52)
    # どの行が強調か（折り返し後も元の行の色を引き継ぐ）
    accent_flags, k = [], 0
    for src in lines_src:
        n = len(R.wrap(src.lstrip("!"), f, width))
        accent_flags += [src.startswith("!")] * n
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top = (SAFE_TOP + SAFE_BOTTOM) // 2 - h // 2
    if kind == "point" and scene.get("no") is not None:
        top += 40
        cx, cy, r = W // 2, top - 110, 52
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=R.RED)
        nf = R.font(True, 56)
        s = str(scene["no"])
        b = nf.getbbox(s)
        d.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]), s, font=nf, fill=R.WHITE)
    if kind == "hook" and scene.get("label"):
        R.pill(d, scene["label"], W // 2, top - 150, R.RED, R.WHITE, size=38)
    for i, ln in enumerate(lines):
        lw = f.getlength(ln)
        x, y = (W - lw) / 2, top + i * size * 1.32
        col = YELLOW if accent_flags[i] else R.WHITE
        d.text((x, y), ln, font=f, fill=col, stroke_width=7, stroke_fill=(10, 16, 34))
    if kind == "hook":   # 強調のアンダーライン
        d.rounded_rectangle((W // 2 - 90, top + h + 14, W // 2 + 90, top + h + 26), radius=6, fill=R.RED)
    return layer


def static_overlay() -> Image.Image:
    """ハンドル名。画面下の安全圏の少し上に置く。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = R.font(True, 36)
    tw = f.getlength(R.HANDLE)
    d.text(((W - tw) / 2, SAFE_BOTTOM + 40), R.HANDLE, font=f, fill=(255, 255, 255, 200),
           stroke_width=4, stroke_fill=(10, 16, 34))
    return layer


# ------------------------------------------------------------------ render
def frames(name: str, spec: dict):
    scenes = spec["scenes"]
    secs = [float(s.get("sec") or DEFAULT_SEC.get(s.get("type", "point"), 3.0)) for s in scenes]
    total = sum(secs)
    overlay = static_overlay()
    t0 = 0.0
    for i, (s, sec) in enumerate(zip(scenes, secs)):
        bg, tl = background(name, s, i), text_layer(s)
        n = int(round(sec * FPS))
        for fi in range(n):
            t = fi / FPS
            z = 1.0 + 0.06 * (fi / max(1, n))              # ゆっくりズーム
            cw, ch = int(W * 1.15 / z), int(H * 1.15 / z)
            x, y = (bg.width - cw) // 2, (bg.height - ch) // 2
            frame = bg.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
            a = ease_out(t / 0.28)                          # テキストがポンと出る
            layer = tl
            if a < 1:
                dy = int((1 - a) * 46)
                shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                shifted.paste(tl, (0, dy))
                alpha = shifted.getchannel("A").point(lambda v: int(v * a))
                shifted.putalpha(alpha)
                layer = shifted
            frame.alpha_composite(layer)
            frame.alpha_composite(overlay)
            prog = int(W * (t0 + t) / total)                # 上の進行バー
            ImageDraw.Draw(frame).rectangle((0, 0, prog, 8), fill=R.RED)
            yield frame.convert("RGB")
        t0 += sec


def encode(name: str, spec: dict, out: Path) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cover_done = False
    try:
        for n, fr in enumerate(frames(name, spec)):
            if not cover_done and n >= int(0.9 * FPS):     # 表紙＝最初のフックが出そろった画面
                fr.save(out.parent / "cover.jpg", quality=92)
                cover_done = True
            p.stdin.write(fr.tobytes())
    finally:
        p.stdin.close()
        if p.wait() != 0:
            raise SystemExit("ffmpeg が失敗しました")


def load(d: Path) -> dict:
    return json.loads((d / "reel.json").read_text(encoding="utf-8"))


def duration(spec: dict) -> float:
    return sum(float(s.get("sec") or DEFAULT_SEC.get(s.get("type", "point"), 3.0)) for s in spec["scenes"])


def reel_dirs(names: list[str]) -> list[Path]:
    ds = sorted(f.parent for f in REELS.glob("*/reel.json"))
    return [d for d in ds if not names or d.name in names]


def cmd_make(args) -> int:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg が見つかりません")
    for d in reel_dirs(args.names):
        spec = load(d)
        out = d / "reel.mp4"
        sig = hashlib.md5(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        sigf = d / ".sig"
        if out.exists() and not args.force and sigf.exists() and sigf.read_text() == sig:
            continue
        print(f"[リール] {d.name}（{duration(spec):.0f}秒）")
        encode(d.name, spec, out)
        (d / "caption.txt").write_text(spec.get("caption", "") + "\n", encoding="utf-8")
        sigf.write_text(sig)
    return 0


def cmd_list(_args) -> int:
    for d in reel_dirs([]):
        spec = load(d)
        mark = "✅" if (d / "reel.mp4").exists() else "  "
        print(f"{mark} {d.name}  {duration(spec):.0f}秒  {spec['scenes'][0].get('text', '').replace(chr(10), ' ')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--force", action="store_true")
    m.add_argument("names", nargs="*")
    m.set_defaults(fn=cmd_make)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
