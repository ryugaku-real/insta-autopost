#!/usr/bin/env python3
"""reels/<名前>/reel.json から縦型リール動画（reel.mp4）・表紙（cover.jpg）・キャプション（caption.txt）を作る。

手動投稿用。reels/ は自動投稿（posts/）とは完全に別なので、ここで作っても勝手には投稿されない。
読み上げ（Open JTalk + 音声「Mei」/ 英語は espeak-ng）とBGMつき。映像は読み上げのタイミングに合わせて動く。

  python scripts/reel.py make [--force] [NAME ...]   足りない動画を作る（--force で作り直し）
  python scripts/reel.py list                        一覧（秒数つき）

必要なもの: ffmpeg / open_jtalk（open-jtalk, open-jtalk-mecab-naist-jdic）/ espeak-ng / numpy / pillow

reel.json の書き方:
{
  "caption": "キャプション本文 #タグ",
  "voice": "happy",                      省略可。happy（既定）か normal
  "bgm": true,                           省略可。false でBGMなし
  "scenes": [
    {"type": "hook", "label": "保存推奨", "text": "留学1年目\\n!お金は何にかかる？"},
    {"type": "point", "no": 1, "text": "家賃\\n!暮らし方で大きく変わる"},
    {"type": "cta", "text": "!保存して\\n後で見返してね", "pill": "＋ フォロー"}
  ]
}
- 行頭が「!」の行は強調色（黄色）。1行ずつ、読み上げに合わせて出てくる
- アルファベットだけの行は英語音声、それ以外は日本語音声で読む
- say: "..." で読み上げ文を直接指定（"" で無音）。sec: 最低秒数。photo: 背景写真のジャンル
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render as R  # noqa: E402  フォント・折り返し・写真取得を共用

ROOT = R.ROOT
REELS = ROOT / "reels"
CACHE = ROOT / ".cache" / "tts"
VOICE_DIR = ROOT / "assets" / "voice"
JDIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
W, H, FPS, SR = 1080, 1920, 30, 48000
YELLOW = (255, 214, 77)
SAFE_TOP, SAFE_BOTTOM = 300, 1480   # アプリのUIに隠れない範囲
CREDIT = "音声: HTS Voice \"Mei\" (c) Nagoya Institute of Technology / CC BY 3.0"
KANA_NO = ["ひとつめ", "ふたつめ", "みっつめ", "よっつめ", "いつつめ", "むっつめ", "ななつめ"]
JA_RE = re.compile(r"[぀-ヿ一-鿿]")


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_back(t: float) -> float:
    """少し行き過ぎてから戻る（ポンと弾む）"""
    t = max(0.0, min(1.0, t))
    c1 = 1.9
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


# ------------------------------------------------------------------ 音声
def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{cmd[0]} が失敗しました: {r.stderr[-400:]}")


def _read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a


def _trim(a: np.ndarray, th=0.012) -> np.ndarray:
    idx = np.where(np.abs(a) > th)[0]
    if len(idx) == 0:
        return a
    return a[max(0, idx[0] - int(0.02 * SR)): idx[-1] + int(0.06 * SR)]


def speak_text(text: str) -> str:
    t = text.replace("〜", "から").replace("~", "から").replace("%", "パーセント").replace("％", "パーセント")
    t = t.replace("・", "、").replace("…", "").replace("＋", "プラス").replace("$", "ドル")
    return t.strip()


def tts(kind: str, text: str, voice: str) -> np.ndarray:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{kind}|{voice}|{text}".encode()).hexdigest()
    out = CACHE / f"{key}.wav"
    if not out.exists():
        raw = CACHE / f"{key}.raw.wav"
        if kind == "ja":
            txt = CACHE / f"{key}.txt"
            txt.write_text(speak_text(text), encoding="utf-8")
            _run(["open_jtalk", "-x", JDIC, "-m", str(VOICE_DIR / f"mei_{voice}.htsvoice"),
                  "-s", "48000", "-p", "240", "-a", "0.55", "-r", "1.12", "-fm", "1.0", "-g", "3",
                  "-ow", str(raw), str(txt)])
            txt.unlink()
        else:
            clean = re.sub(r"[○●]", "so and so", text)
            _run(["espeak-ng", "-v", "en-us+f3", "-s", "140", "-p", "60", "-w", str(raw), clean])
        _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ar", str(SR), "-ac", "1",
              "-acodec", "pcm_s16le", str(out)])
        raw.unlink()
    a = _trim(_read_wav(out))
    peak = float(np.abs(a).max()) or 1.0
    return a * (0.85 / peak)


def whoosh(dur=0.32) -> np.ndarray:
    n = int(dur * SR)
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n).astype(np.float32)
    k = np.linspace(60, 8, n)           # だんだん高い音へ
    y = np.empty_like(x)
    acc = 0.0
    for i in range(n):                  # 可変ローパス
        a = 1.0 / k[i]
        acc += a * (x[i] - acc)
        y[i] = acc
    env = np.sin(np.linspace(0, math.pi, n)) ** 2
    y = y * env
    return y / (np.abs(y).max() or 1) * 0.35


def pop(freq=880.0, dur=0.12) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * math.pi * freq * t * (1 + 0.5 * np.exp(-t * 40))) * np.exp(-t * 28) * 0.22).astype(np.float32)


def bgm(dur: float) -> np.ndarray:
    n = int(dur * SR)
    beat = 60 / 100
    bar = 4 * beat
    out = np.zeros(n, dtype=np.float32)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]   # Am F C G
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    rng = np.random.default_rng(3)
    for i in range(int(dur / bar) + 1):
        s = int(i * bar * SR)
        if s >= n:
            break
        e = min(n, int((i + 1) * bar * SR))
        tt = np.arange(e - s) / SR
        env = np.minimum(1, tt / 0.4) * np.minimum(1, (bar - tt) / 0.5)
        for m in chords[i % 4]:
            out[s:e] += 0.07 * np.sin(2 * math.pi * hz(m) * tt) * env
        for k in range(8):                                   # アルペジオ
            ns = s + int(k * beat / 2 * SR)
            ne = min(n, ns + int(0.4 * SR))
            if ns >= n:
                break
            t2 = np.arange(ne - ns) / SR
            out[ns:ne] += 0.11 * np.sin(2 * math.pi * hz(chords[i % 4][k % 3] + 12) * t2) * np.exp(-t2 * 8)
        for k in range(4):
            ns = s + int(k * beat * SR)
            ne = min(n, ns + int(0.25 * SR))
            if ns >= n:
                break
            t2 = np.arange(ne - ns) / SR
            if k in (0, 2):                                  # キック
                out[ns:ne] += 0.30 * np.sin(2 * math.pi * (50 + 90 * np.exp(-t2 * 30)) * t2) * np.exp(-t2 * 14)
            h = int(0.04 * SR)                               # ハイハット（裏拍）
            hs = ns + int(beat / 2 * SR)
            if hs + h < n:
                out[hs:hs + h] += 0.04 * rng.standard_normal(h) * np.exp(-np.arange(h) / SR * 90)
    fade = int(0.8 * SR)
    out[-fade:] *= np.linspace(1, 0, min(fade, n))
    return out / (np.abs(out).max() or 1)


# ------------------------------------------------------------------ 台本 → タイムライン
def parse_lines(scene: dict) -> list[dict]:
    lines = []
    for src in scene.get("text", "").split("\n"):
        acc = src.startswith("!")
        t = src.lstrip("!")
        lang = "en" if re.search(r"[A-Za-z]", t) and not JA_RE.search(t) else "ja"
        lines.append({"text": t, "accent": acc, "lang": lang})
    return lines


def plan(scene: dict, first: bool, voice: str, spoken: bool) -> dict:
    """読み上げの順番・開始時刻・各行の出現時刻・シーンの長さを決める。"""
    lines = parse_lines(scene)
    kind = scene.get("type", "point")
    lead = 0.15 if first else 0.34
    t = lead
    items = []   # (start, audio, line_idx or None)
    appear = [0.0] * len(lines)
    speak: list[tuple[float, float]] = [(0.0, 0.0)] * len(lines)
    badge_t = lead
    if not spoken:
        for i in range(len(lines)):
            appear[i] = lead + 0.1 + i * 0.22
        dur = max(float(scene.get("sec", 0)), appear[-1] + 1.8)
        return {"lines": lines, "appear": appear, "speak": speak, "items": items, "dur": dur, "badge_t": badge_t, "lead": lead}
    if "say" in scene:
        say = scene["say"]
        if say:
            a = tts("ja", say, voice)
            items.append((t, a, None))
            t += len(a) / SR + 0.2
        for i in range(len(lines)):
            appear[i] = lead + 0.1 + i * 0.25
            speak[i] = (lead, t)
    else:
        if kind == "point" and scene.get("no") is not None:
            n = int(scene["no"])
            a = tts("ja", KANA_NO[n - 1] if n <= len(KANA_NO) else f"{n}つめ", voice)
            items.append((t, a, None))
            t += len(a) / SR + 0.12
        for i, ln in enumerate(lines):
            a = tts(ln["lang"], ln["text"], voice)
            appear[i] = max(0.05, t - 0.1)
            speak[i] = (t, t + len(a) / SR)
            items.append((t, a, i))
            t += len(a) / SR + (0.28 if ln["lang"] == "en" else 0.18)
    dur = max(float(scene.get("sec", 0)), t + 0.45)
    return {"lines": lines, "appear": appear, "speak": speak, "items": items, "dur": dur, "badge_t": badge_t, "lead": lead}


# ------------------------------------------------------------------ 映像パーツ
def background(name: str, scene: dict, idx: int) -> Image.Image:
    """ぼかして暗くした写真（ズーム用に少し大きめ）。写真がなければネイビーのグラデ。"""
    bw, bh = int(W * 1.15), int(H * 1.15)
    tag = scene.get("photo") if isinstance(scene.get("photo"), str) else None
    got = None if scene.get("photo") is False else R.pick_photo(f"{name}-{idx}", tag)
    if got:
        im = got[0].resize((bw, int(bw * got[0].height / got[0].width)))
        if im.height < bh:
            im = im.resize((int(im.width * bh / im.height), bh))
        x, y = (im.width - bw) // 2, (im.height - bh) // 2
        im = im.crop((x, y, x + bw, y + bh)).filter(ImageFilter.GaussianBlur(3))
        return Image.blend(im, Image.new("RGB", im.size, R.NAVY), 0.68)
    im = Image.new("RGB", (bw, bh), R.NAVY)
    d = ImageDraw.Draw(im)
    for yy in range(bh):
        k = yy / bh
        d.line([(0, yy), (bw, yy)], fill=(int(20 + 18 * k), int(33 + 20 * k), int(61 + 40 * k)))
    return im


def blobs(t: float, seed: int) -> Image.Image:
    """ゆらゆら動く色の玉（小さく描いて引き伸ばす＝ふわっとぼける）"""
    sw, sh = W // 8, H // 8
    im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cols = [(214, 40, 57, 70), (255, 214, 77, 38), (90, 140, 255, 48)]
    for k, c in enumerate(cols):
        ph = seed * 1.7 + k * 2.1
        cx = sw * (0.5 + 0.38 * math.sin(t * 0.6 + ph))
        cy = sh * (0.5 + 0.42 * math.cos(t * 0.45 + ph * 1.3))
        r = sw * (0.34 + 0.06 * math.sin(t * 0.9 + ph))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    return im.filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BICUBIC)


def line_crop(text: str, f, size: int, width: int, color) -> Image.Image:
    rows = R.wrap(text, f, width)
    pad = 24
    lw = int(max(f.getlength(r) for r in rows)) + pad * 2
    lh = int(len(rows) * size * 1.32) + pad * 2
    im = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, r in enumerate(rows):
        x = (lw - f.getlength(r)) / 2
        d.text((x, pad + i * size * 1.32), r, font=f, fill=color, stroke_width=7, stroke_fill=(10, 16, 34))
    return im


class SceneCtx:
    def __init__(self, name: str, scene: dict, idx: int, pl: dict):
        self.scene, self.idx, self.pl = scene, idx, pl
        self.kind = scene.get("type", "point")
        self.bg = background(name, scene, idx)
        base = {"hook": 128, "cta": 108}.get(self.kind, 96)
        width = W - 160
        size = base
        for ln in pl["lines"]:      # 全行で同じ大きさにそろえる
            f, _, sz, _ = R.fit(ln["text"], True, base, width, 560, spacing=1.32, min_size=52)
            size = min(size, sz)
        f = R.font(True, size)
        self.crops = [line_crop(ln["text"], f, size, width, YELLOW if ln["accent"] else R.WHITE) for ln in pl["lines"]]
        gap = 14
        total_h = sum(c.height for c in self.crops) + gap * (len(self.crops) - 1)
        extra = 130 if (self.kind == "cta" and scene.get("pill", "＋ フォロー")) else 0
        top = (SAFE_TOP + SAFE_BOTTOM) // 2 - (total_h + extra) // 2 + (50 if self.kind == "point" else 0)
        self.pos, y = [], top
        for c in self.crops:
            self.pos.append((W // 2, y + c.height // 2))
            y += c.height + gap
        self.top, self.bottom = top, y
        self.size = size


def render_frame(c: SceneCtx, t: float, handle: Image.Image) -> Image.Image:
    pl, scene = c.pl, c.scene
    n_frames = max(1, int(pl["dur"] * FPS))
    z = 1.0 + 0.07 * min(1.0, t / pl["dur"])
    cw, ch = int(W * 1.15 / z), int(H * 1.15 / z)
    x0, y0 = (c.bg.width - cw) // 2, (c.bg.height - ch) // 2
    frame = c.bg.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)
    bl = blobs(t, c.idx)
    frame.paste(bl, (0, 0), bl)
    d = ImageDraw.Draw(frame)

    # 1) ラベル（hook）
    if c.kind == "hook" and scene.get("label"):
        a = ease_back((t - 0.1) / 0.4)
        if a > 0:
            lay = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
            R.pill(ImageDraw.Draw(lay), scene["label"], W // 2, 10, R.RED, R.WHITE, size=38)
            w2, h2 = int(W * a), int(120 * a)
            lay = lay.resize((max(1, w2), max(1, h2)), Image.BILINEAR)
            frame.paste(lay, ((W - w2) // 2, c.top - 150 + (120 - h2) // 2), lay)

    # 2) 番号バッジ（point）：弾んで出て、輪っかが広がる
    if c.kind == "point" and scene.get("no") is not None:
        bt = t - pl["badge_t"]
        a = ease_back(bt / 0.4)
        if a > 0:
            cx, cy, r = W // 2, c.top - 70, int(54 * a)
            ring = ease_out(bt / 0.7)
            if 0 < ring < 1:
                rr = int(54 + 80 * ring)
                d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 255, 255), width=max(1, int(6 * (1 - ring))))
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=R.RED)
            nf = R.font(True, max(10, int(60 * a)))
            s = str(scene["no"])
            b = nf.getbbox(s)
            d.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]), s, font=nf, fill=R.WHITE)

    # 3) 本文：1行ずつ弾んで出る。しゃべっている行は少し大きく
    for i, crop in enumerate(c.crops):
        age = t - pl["appear"][i]
        if age < 0:
            continue
        s = 0.55 + 0.45 * ease_back(age / 0.42)
        s_start, s_end = pl["speak"][i]
        if s_end > s_start:
            s *= 1 + 0.045 * ease_out((t - s_start) / 0.12) * (1 - ease_out((t - s_end) / 0.15))
        alpha = min(1.0, age / 0.14)
        cx, cy = c.pos[i]
        cy += int((1 - ease_out(age / 0.3)) * 50)
        im = crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))), Image.BILINEAR)
        if alpha < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        frame.paste(im, (cx - im.width // 2, cy - im.height // 2), im)
        if c.kind == "hook" and pl["lines"][i]["accent"]:       # 赤い下線がシュッと伸びる
            ul = ease_out((age - 0.25) / 0.4)
            if ul > 0:
                half = int(crop.width * 0.42 * ul)
                yy = cy + crop.height // 2 - 10
                d.rounded_rectangle((W // 2 - half, yy, W // 2 + half, yy + 12), radius=6, fill=R.RED)

    # 4) CTA：フォローのピルが脈打つ
    pill = scene.get("pill", "＋ フォロー")
    if c.kind == "cta" and pill:
        age = t - (pl["appear"][-1] + 0.3)
        if age > 0:
            a = ease_back(age / 0.4) * (1 + 0.05 * math.sin(age * 2 * math.pi * 1.6))
            lay = Image.new("RGBA", (700, 150), (0, 0, 0, 0))
            R.pill(ImageDraw.Draw(lay), pill, 350, 20, R.RED, R.WHITE, size=52)
            lay = lay.resize((max(1, int(700 * a)), max(1, int(150 * a))), Image.BILINEAR)
            frame.paste(lay, (W // 2 - lay.width // 2, c.bottom + 40 + (150 - lay.height) // 2), lay)

    frame.paste(handle, (0, 0), handle)
    # 5) シーン頭のズームパンチ
    punch = 1 + (0.06 if c.kind == "hook" else 0.035) * (1 - ease_out(t / 0.4))
    if punch > 1.001:
        w2, h2 = int(W / punch), int(H / punch)
        frame = frame.crop(((W - w2) // 2, (H - h2) // 2, (W - w2) // 2 + w2, (H - h2) // 2 + h2)).resize((W, H), Image.BILINEAR)
    return frame


def handle_layer() -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = R.font(True, 36)
    tw = f.getlength(R.HANDLE)
    ImageDraw.Draw(layer).text(((W - tw) / 2, SAFE_BOTTOM + 40), R.HANDLE, font=f, fill=(255, 255, 255, 200),
                               stroke_width=4, stroke_fill=(10, 16, 34))
    return layer


# ------------------------------------------------------------------ 組み立て
def build(name: str, spec: dict, out: Path) -> None:
    voice = spec.get("voice", "happy")
    spoken = spec.get("voice_over", True)
    scenes = spec["scenes"]
    plans = [plan(s, i == 0, voice, spoken) for i, s in enumerate(scenes)]
    total = sum(p["dur"] for p in plans)

    # --- 音声を時間軸に並べる
    mix = np.zeros(int(total * SR) + SR, dtype=np.float32)
    t0 = 0.0
    wh, pp = whoosh(), pop()
    for i, p in enumerate(plans):
        if i > 0:
            s = int((t0 + 0.02) * SR)
            mix[s:s + len(wh)] += wh * 0.8
        for j, ap in enumerate(p["appear"]):
            s = int((t0 + ap) * SR)
            mix[s:s + len(pp)] += pp * 0.5
        for start, a, _ in p["items"]:
            s = int((t0 + start) * SR)
            mix[s:s + len(a)] += a
        t0 += p["dur"]
    if spec.get("bgm", True):
        mix[: int(total * SR)] += bgm(total) * 0.12
    peak = float(np.abs(mix).max()) or 1.0
    if peak > 0.95:
        mix *= 0.95 / peak
    wav = out.parent / ".audio.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix[: int(total * SR)] * 32767).astype(np.int16).tobytes())

    # --- 映像
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    handle = handle_layer()
    prev_last = None
    elapsed = 0.0
    try:
        for i, (s, p) in enumerate(zip(scenes, plans)):
            c = SceneCtx(name, s, i, p)
            if i == 0:   # 表紙：フックの文字が全部そろった画面
                render_frame(c, max(p["appear"]) + 0.8, handle).save(out.parent / "cover.jpg", quality=92)
            nf = int(round(p["dur"] * FPS))
            last = None
            for fi in range(nf):
                t = fi / FPS
                fr = render_frame(c, t, handle)
                last = fr
                if prev_last is not None and t < 0.3:      # 下から次のシーンがスライドして入る
                    e = ease_out(t / 0.3)
                    canvas = Image.new("RGB", (W, H))
                    canvas.paste(prev_last, (0, -int(0.18 * H * e)))
                    y = int(H * (1 - e))
                    canvas.paste(fr, (0, y))
                    ImageDraw.Draw(canvas).rectangle((0, y, W, y + 10), fill=R.RED)
                    fr = canvas
                ImageDraw.Draw(fr).rectangle((0, 0, int(W * (elapsed + t) / total), 8), fill=R.RED)
                proc.stdin.write(fr.tobytes())
            prev_last = last
            elapsed += p["dur"]
    finally:
        proc.stdin.close()
        if proc.wait() != 0:
            raise SystemExit("ffmpeg が失敗しました")
        wav.unlink(missing_ok=True)


def load(d: Path) -> dict:
    return json.loads((d / "reel.json").read_text(encoding="utf-8"))


def reel_dirs(names: list[str]) -> list[Path]:
    ds = sorted(f.parent for f in REELS.glob("*/reel.json"))
    return [d for d in ds if not names or d.name in names]


def cmd_make(args) -> int:
    for tool in ("ffmpeg", "open_jtalk", "espeak-ng"):
        if not shutil.which(tool):
            sys.exit(f"{tool} が見つかりません（このファイルの先頭の「必要なもの」を参照）")
    for d in reel_dirs(args.names):
        spec = load(d)
        out = d / "reel.mp4"
        sig = hashlib.md5((json.dumps(spec, sort_keys=True, ensure_ascii=False) + Path(__file__).read_text()).encode()).hexdigest()
        sigf = d / ".sig"
        if out.exists() and not args.force and sigf.exists() and sigf.read_text() == sig:
            continue
        print(f"[リール] {d.name}")
        build(d.name, spec, out)
        cap = spec.get("caption", "").rstrip()
        if spec.get("voice_over", True):
            cap += f"\n.\n{CREDIT}"
        (d / "caption.txt").write_text(cap + "\n", encoding="utf-8")
        sigf.write_text(sig)
    return 0


def cmd_list(_args) -> int:
    for d in reel_dirs([]):
        spec = load(d)
        mark = "✅" if (d / "reel.mp4").exists() else "  "
        print(f"{mark} {d.name}  {spec['scenes'][0].get('text', '').replace(chr(10), ' ')}")
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
