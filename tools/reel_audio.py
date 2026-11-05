"""リール用の効果音とBGMを numpy だけで作る（外部の音源は使わない）。

make_track(duration, events, path) で wav を書き出す。
events は {"pop": [秒, ...], "whoosh": [...], "ding": [...], "thud": [...], "click": [...]} の形。
声（voice.mp3）とは別のトラックなので、ffmpeg で重ねる。
"""
from __future__ import annotations

import wave

import numpy as np

SR = 44100
RNG = np.random.default_rng(7)   # 毎回同じ音になるように固定


def _t(sec: float) -> np.ndarray:
    return np.arange(int(sec * SR)) / SR


def pop() -> np.ndarray:
    t = _t(0.16)
    f = 320 + 700 * np.exp(-t * 22)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 26) * 0.55


def ding() -> np.ndarray:
    t = _t(0.9)
    y = np.sin(2 * np.pi * 988 * t) + 0.5 * np.sin(2 * np.pi * 1319 * t) + 0.25 * np.sin(2 * np.pi * 1976 * t)
    return y * np.exp(-t * 5.5) * 0.28


def thud() -> np.ndarray:
    t = _t(0.45)
    f = 48 + 90 * np.exp(-t * 14)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t * 7) * 0.95
    n = RNG.standard_normal(len(t)) * np.exp(-t * 60) * 0.15
    return y + n


def click() -> np.ndarray:
    t = _t(0.05)
    return RNG.standard_normal(len(t)) * np.exp(-t * 110) * 0.35


def whoosh() -> np.ndarray:
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    noise = RNG.standard_normal(n)
    env = np.sin(np.pi * np.clip(t / 0.55, 0, 1)) ** 2
    out = np.zeros(n)
    lp = 0.0
    for i in range(n):
        a = 0.02 + 0.5 * (i / n)          # 低い音から高い音へ（フィルターを開く）
        lp += a * (noise[i] - lp)
        out[i] = lp
    return out * env * 1.4


def bgm(duration: float, bpm: float = 92.0) -> np.ndarray:
    """やわらかいコード（Am-F-C-G）に、軽いアルペジオとキックを重ねる"""
    n = int(duration * SR)
    out = np.zeros(n)
    beat = 60.0 / bpm
    chords = [(220.00, 261.63, 329.63), (174.61, 220.00, 261.63),
              (261.63, 329.63, 392.00), (196.00, 246.94, 293.66)]
    bar = 4 * beat
    nbars = int(duration / bar) + 1
    for b in range(nbars):
        notes = chords[b % 4]
        s0 = int(b * bar * SR)
        # パッド
        seg = _t(bar)
        pad = sum(np.sin(2 * np.pi * f * seg) + 0.4 * np.sin(2 * np.pi * f * 2.003 * seg) for f in notes) / 5
        env = np.minimum(1, seg / 0.25) * np.minimum(1, (bar - seg) / 0.25)
        _add(out, s0, pad * env * 0.07)
        # アルペジオ（8分音符）
        for k in range(8):
            f = notes[k % 3] * (2 if k % 2 else 1)
            ts = _t(beat)
            pl = np.sin(2 * np.pi * f * ts) * np.exp(-ts * 9)
            _add(out, s0 + int(k * beat / 2 * SR), pl * 0.05)
        # キック（1・3拍）とハット（裏拍）
        for k in (0, 2):
            tk = _t(0.22)
            kick = np.sin(2 * np.pi * np.cumsum(46 + 90 * np.exp(-tk * 25)) / SR) * np.exp(-tk * 12)
            _add(out, s0 + int(k * beat * SR), kick * 0.16)
        for k in range(8):
            if k % 2:
                th = _t(0.05)
                hat = RNG.standard_normal(len(th)) * np.exp(-th * 90)
                _add(out, s0 + int(k * beat / 2 * SR), hat * 0.02)
    fade = np.minimum(1, np.arange(n) / (SR * 1.0)) * np.minimum(1, (n - np.arange(n)) / (SR * 1.2))
    return out * fade


def _add(buf: np.ndarray, start: int, sig: np.ndarray, gain: float = 1.0) -> None:
    if start >= len(buf):
        return
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start] * gain


def make_track(duration: float, events: dict[str, list[float]], path: str, bgm_gain: float = 1.0,
               sfx_gain: float = 1.0) -> None:
    out = bgm(duration) * bgm_gain
    makers = {"pop": pop, "ding": ding, "thud": thud, "click": click, "whoosh": whoosh}
    cache = {k: f() for k, f in makers.items()}
    for kind, times in events.items():
        for sec in times:
            _add(out, int(max(0.0, sec) * SR), cache[kind], sfx_gain)
    peak = float(np.max(np.abs(out))) or 1.0
    if peak > 0.95:
        out = out * (0.95 / peak)
    pcm = (out * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
