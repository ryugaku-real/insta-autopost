import os

from flask import Flask, jsonify, request, send_from_directory

import llm
import stats
import style

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


@app.post("/api/rewrite")
def rewrite():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if len(text) < 50 or len(text) > MAX_CHARS:
        return jsonify(error=f"50〜{MAX_CHARS}文字の文章を入力してください"), 400
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return jsonify(error="ANTHROPIC_API_KEY が未設定です"), 400
    hints = [h for h in body.get("hints", []) if isinstance(h, str)]
    try:
        return jsonify(text=llm.rewrite(text, hints))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.post("/api/compare")
def compare():
    body = request.get_json(silent=True) or {}
    text, ref = body.get("text", "").strip(), body.get("reference", "").strip()
    if len(text) < 50 or len(text) > MAX_CHARS or len(ref) > MAX_CHARS * 2:
        return jsonify(error="文章の長さが範囲外です"), 400
    return jsonify(style.compare(text, ref))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
