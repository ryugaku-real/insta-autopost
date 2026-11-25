"""本人の過去の文章との文体比較(ローカル計算)。一致度は目安であり証拠ではない。"""
import math
import re
from collections import Counter

import stats


def _profile(text: str) -> dict:
    t = re.sub(r"\s+", "", text)
    n = max(len(t), 1)
    sents = stats.split_sentences(text)
    lens = [len(s) for s in sents] or [0]
    mean = sum(lens) / len(lens)
    std = math.sqrt(sum((x - mean) ** 2 for x in lens) / len(lens))
    c = lambda pat: len(re.findall(pat, t)) / n
    return {
        "平均文長": mean,
        "文長のばらつき": std / mean if mean else 0,
        "読点の頻度": c(r"[、,]"),
        "ひらがな率": c(r"[぀-ゟ]"),
        "カタカナ率": c(r"[゠-ヿ]"),
        "漢字率": c(r"[一-鿿]"),
        "英数字率": c(r"[A-Za-z0-9]"),
        "感嘆・疑問符": c(r"[!?！？]"),
    }


def _grams(text: str, k=2) -> Counter:
    t = re.sub(r"\s+", "", text.lower())
    return Counter(t[i:i + k] for i in range(len(t) - k + 1))


def _cos(a: Counter, b: Counter) -> float:
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def compare(text: str, reference: str) -> dict:
    if len(reference.strip()) < 200:
        return {"enough": False, "message": "過去の文章は200文字以上必要です(多いほど正確)"}
    pt, pr = _profile(text), _profile(reference)
    rows = []
    for k in pt:
        a, b = pt[k], pr[k]
        diff = abs(a - b) / max(abs(a), abs(b), 1e-9)  # 0=同じ, 1=大きく違う
        rows.append({"name": k, "text": round(a, 3), "ref": round(b, 3), "diff": round(diff, 2)})
    feat_sim = 1 - sum(r["diff"] for r in rows) / len(rows)
    gram_sim = _cos(_grams(text), _grams(reference))
    score = round(100 * max(0.0, min(1.0, 0.6 * feat_sim + 0.4 * gram_sim)))
    level = "近い" if score >= 70 else "やや違う" if score >= 50 else "かなり違う"
    return {
        "enough": True,
        "similarity": score,
        "level": level,
        "rows": rows,
        "ref_chars": len(reference),
        "short_ref": len(reference) < 1000,
    }
