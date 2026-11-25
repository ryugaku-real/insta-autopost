import os

from flask import Flask, jsonify, request, send_from_directory

import llm
import stats

app = Flask(__name__, static_folder="static")
MAX_CHARS = 20000


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/analyze")
def analyze():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if len(text) < 50:
        return jsonify(error="50文字以上の文章を入力してください"), 400
    if len(text) > MAX_CHARS:
        return jsonify(error=f"{MAX_CHARS}文字までです"), 400

    result = {"stats": stats.analyze(text), "llm": None, "llm_error": None}
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            result["llm"] = llm.judge(text)
        except Exception as e:  # 統計だけでも返す
            result["llm_error"] = str(e)
    else:
        result["llm_error"] = "ANTHROPIC_API_KEY が未設定のため、文体統計のみ表示しています"
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
