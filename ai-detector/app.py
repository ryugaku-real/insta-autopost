import os

from flask import Flask, jsonify, request, send_from_directory

import llm
import extract as extractor
import stats
import style

import hmac
import time
from collections import defaultdict, deque

from flask import Response

app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024
MAX_CHARS = 20000

# 公開時の保護。APP_PASSWORD を設定すると、全ページに合言葉(Basic認証)が掛かる
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
# 1分あたりのAPI呼び出し上限(IPごと)。Claude API の料金暴走を防ぐ
RATE_PER_MIN = int(os.environ.get("RATE_PER_MIN", "10"))
_hits: dict[str, deque] = defaultdict(deque)


@app.before_request
def guard():
    if request.path == "/healthz":
        return None
    if APP_PASSWORD:
        a = request.authorization
        if not a or not hmac.compare_digest((a.password or "").encode(), APP_PASSWORD.encode()):
            return Response("合言葉が必要です", 401, {"WWW-Authenticate": 'Basic realm="ai-detector"'})
    if request.path.startswith("/api/"):
        ip = (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()
        q, now = _hits[ip], time.time()
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE_PER_MIN:
            return jsonify(error="アクセスが多すぎます。1分ほど待ってください"), 429
        q.append(now)


@app.get("/healthz")
def healthz():
    return "ok"


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


@app.post("/api/extract")
def extract_file():
    f = request.files.get("file")
    if not f:
        return jsonify(error="ファイルがありません"), 400
    try:
        text = extractor.extract(f.filename or "", f.read())
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception:
        return jsonify(error="ファイルを読み込めませんでした(壊れているか暗号化されています)"), 400
    return jsonify(text=text[:MAX_CHARS], truncated=len(text) > MAX_CHARS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
