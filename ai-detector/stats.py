"""APIキー不要のローカル文体統計。AIらしさの"目安"でしかない。"""
import math
import re

SPLIT = re.compile(r"(?<=[。！？!?\.])\s*|\n+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SPLIT.split(text) if s and s.strip()]


def analyze(text: str) -> dict:
    sents = split_sentences(text)
    lens = [len(s) for s in sents]
    n = len(lens)
    if n < 3:
        return {"sentences": n, "enough": False}
    mean = sum(lens) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in lens) / n)
    burst = std / mean if mean else 0  # 文長のばらつき。人は大きく、AIは均一になりがち
    # 日本語は空白区切りがないので、文字2-gramで語彙の多様性を測る
    chars = re.sub(r"\s+", "", text.lower())
    tokens = [chars[i:i + 2] for i in range(len(chars) - 1)] if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", chars) else re.findall(r"\w+", text.lower())
    ttr = len(set(tokens)) / len(tokens) if tokens else 0
    # ばらつきが小さいほど高スコア（0.2以下→1、0.8以上→0）
    score = min(1.0, max(0.0, (0.8 - burst) / 0.6))
    return {
        "sentences": n,
        "enough": True,
        "avg_len": round(mean, 1),
        "burstiness": round(burst, 2),
        "lexical_diversity": round(ttr, 2),
        "heuristic_score": round(score, 2),
    }
