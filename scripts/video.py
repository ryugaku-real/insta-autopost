#!/usr/bin/env python3
"""スライド画像（01.jpg …）から縦型のリール動画（reel.mp4）を作る。ffmpegだけを使う。

使い方:
  python scripts/video.py make [--force] [KEY ...]   指定した投稿（省略時は全部）の reel.mp4 を作る
  python scripts/video.py check                      reel.mp4 が足りない投稿があれば終了コード1

動画の仕様: 1080x1920 / 30fps / H.264 / 1枚あたり SECONDS_PER_SLIDE 秒 / 音声なし
最後のCTAスライドは短めにする（LAST_SLIDE_SECONDS）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"

SECONDS_PER_SLIDE = float(os.environ.get("SECONDS_PER_SLIDE", "3"))
LAST_SLIDE_SECONDS = float(os.environ.get("LAST_SLIDE_SECONDS", "2"))
OUT_NAME = "reel.mp4"


def posts(keys: list[str]) -> list[Path]:
    dirs = sorted(f.parent for f in POSTS_DIR.glob("*/post.json"))
    if keys:
        dirs = [d for d in dirs if d.name in keys]
    return dirs


def slides_of(d: Path) -> list[Path]:
    p = json.loads((d / "post.json").read_text(encoding="utf-8"))
    return [d / n for n in p.get("images", []) if (d / n).exists()]


def build_cmd(slides: list[Path], out: Path) -> list[str]:
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    parts = []
    for i, s in enumerate(slides):
        secs = LAST_SLIDE_SECONDS if (i == len(slides) - 1 and len(slides) > 1) else SECONDS_PER_SLIDE
        cmd += ["-loop", "1", "-t", f"{secs}", "-framerate", "30", "-i", str(s)]
        # 背景: 画像を拡大してぼかす / 前景: 画像を横幅1080に合わせて中央に置く
        parts.append(
            f"[{i}:v]split[bg{i}][fg{i}];"
            f"[bg{i}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:5,eq=brightness=-0.15[b{i}];"
            f"[fg{i}]scale=1080:-2[f{i}];"
            f"[b{i}][f{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]"
        )
    concat_in = "".join(f"[v{i}]" for i in range(len(slides)))
    graph = ";".join(parts) + f";{concat_in}concat=n={len(slides)}:v=1:a=0[out]"
    cmd += ["-filter_complex", graph, "-map", "[out]", "-r", "30", "-c:v", "libx264",
            "-preset", "medium", "-crf", "23", "-movflags", "+faststart", str(out)]
    return cmd


def cmd_make(args) -> int:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg が見つかりません")
    made = 0
    for d in posts(args.keys):
        out = d / OUT_NAME
        slides = slides_of(d)
        if not slides:
            print(f"[スキップ] {d.name}: 画像がありません")
            continue
        if out.exists() and not args.force:
            continue
        print(f"[動画] {d.name}（{len(slides)}枚）")
        r = subprocess.run(build_cmd(slides, out), capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-800:])
            return 1
        made += 1
    print(f"{made}本作りました")
    return 0


def cmd_check(_args) -> int:
    missing = [d.name for d in posts([]) if slides_of(d) and not (d / OUT_NAME).exists()]
    for m in missing:
        print(f"動画なし: {m}")
    return 1 if missing else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--force", action="store_true")
    m.add_argument("keys", nargs="*")
    m.set_defaults(fn=cmd_make)
    c = sub.add_parser("check")
    c.set_defaults(fn=cmd_check)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
