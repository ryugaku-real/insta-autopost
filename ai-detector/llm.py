import json
import os
import re

MODEL = os.environ.get("DETECTOR_MODEL", "claude-sonnet-5-5")

PROMPT = """あなたは文章の書き手を分析する専門家です。次の文章が人間によって書かれたか、AI(LLM)によって生成されたかを評価してください。
手がかり: 定型的な接続表現、均一な文構造、具体的体験や固有の癖の欠如、過度に整った構成、不自然な一般論、逆に誤字・口語・個性的な言い回しは人間らしさ。
重要: 確実には判定できません。確率は慎重に、根拠が弱ければ50%付近にしてください。非ネイティブの書き手の文章を誤ってAIと判定しないこと。

文章を文単位に分け、次のJSONだけを出力してください(前置き不要):
{"ai_probability": 0-100の整数,
 "verdict": "human" | "mixed" | "ai",
 "summary": "全体の根拠を2〜3文で",
 "sentences": [{"text": "原文の文", "ai_likelihood": 0-100, "reason": "短い理由"}]}

<text>
%s
</text>"""


def judge(text: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": PROMPT % text}],
    )
    out = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"\{.*\}", out, re.S)
    if not m:
        raise ValueError("モデルの応答をJSONとして読めませんでした")
    return json.loads(m.group(0))
