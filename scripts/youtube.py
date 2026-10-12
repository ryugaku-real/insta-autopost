#!/usr/bin/env python3
"""YouTube ショート自動投稿（YouTube Data API v3）

使い方:
  python scripts/youtube.py auth            最初の1回だけ。許可してリフレッシュトークンを取得する（自分のPCで実行）
  python scripts/youtube.py check           トークンでチャンネルに接続できるか確認する
  python scripts/youtube.py publish [--dry-run]
                                            Instagramに公開済みで reel.mp4 がある投稿を、YouTubeにも出す

必要な環境変数（GitHub Secrets）:
  YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN
任意:
  YT_PRIVACY   既定 private（public / unlisted / private）。確認が済むまでは private のまま
  YT_CATEGORY  既定 27（教育）

注意: 審査前（未確認）のGoogle Cloudプロジェクトから投稿した動画は、公開設定にしても非公開に固定される。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ig  # noqa: E402  公開記録（published.json）と投稿データの読み書きを共有する

TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
REDIRECT = "http://localhost:8080"
MAX_TITLE = 100
MAX_TRIES = 3


class YtError(Exception):
    pass


def _env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"{name} が設定されていません（GitHub Secrets を確認）")
    return v


def _redact(text: str) -> str:
    for n in ("YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"):
        v = os.environ.get(n, "")
        if v:
            text = text.replace(v, "***")
    return text


def _post_form(url: str, params: dict) -> dict:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise YtError(_redact(f"HTTP {e.code}: {e.read().decode(errors='replace')}")) from None
    except urllib.error.URLError as e:
        raise YtError(_redact(f"接続エラー: {e.reason}")) from None


def access_token() -> str:
    res = _post_form(TOKEN_URL, {
        "client_id": _env("YT_CLIENT_ID"), "client_secret": _env("YT_CLIENT_SECRET"),
        "refresh_token": _env("YT_REFRESH_TOKEN"), "grant_type": "refresh_token"})
    tok = res["access_token"]
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::add-mask::{tok}")
    return tok


def title_of(p: dict) -> str:
    first = (p.get("caption", "").strip().splitlines() or [p["_key"]])[0].strip()
    suffix = " #Shorts"
    return first[: MAX_TITLE - len(suffix)] + suffix


def upload(tok: str, p: dict) -> str:
    """動画をアップして YouTube の動画IDを返す（再開可能アップロード）。"""
    video = p["_dir"] / "reel.mp4"
    desc = p.get("caption", "").replace("<", "＜").replace(">", "＞")
    if "#Shorts" not in desc:
        desc += "\n\n#Shorts"
    meta = {
        "snippet": {"title": title_of(p), "description": desc,
                    "categoryId": os.environ.get("YT_CATEGORY", "27")},
        "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "private"),
                   "selfDeclaredMadeForKids": False},
    }
    data = video.read_bytes()
    start = urllib.request.Request(
        f"{UPLOAD_URL}?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(len(data)), "X-Upload-Content-Type": "video/mp4"})
    try:
        with urllib.request.urlopen(start, timeout=60) as r:
            session = r.headers["Location"]
        put = urllib.request.Request(session, data=data, method="PUT",
                                     headers={"Content-Type": "video/mp4", "Content-Length": str(len(data))})
        with urllib.request.urlopen(put, timeout=600) as r:
            return json.loads(r.read().decode())["id"]
    except urllib.error.HTTPError as e:
        raise YtError(_redact(f"HTTP {e.code}: {e.read().decode(errors='replace')}")) from None
    except urllib.error.URLError as e:
        raise YtError(_redact(f"接続エラー: {e.reason}")) from None


# ---------------------------------------------------------------- commands
def cmd_auth(_args) -> int:
    cid = os.environ.get("YT_CLIENT_ID") or input("クライアントID: ").strip()
    secret = os.environ.get("YT_CLIENT_SECRET") or input("クライアントシークレット: ").strip()
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent"})
    print("\n1) 次のURLをブラウザで開いて、許可してください:\n\n" + url + "\n")
    print("2) 許可すると「このサイトにアクセスできません」と出ますが、それで正常です。")
    print("   アドレス欄のURLの code=... の部分（& の前まで）をコピーしてください。\n")
    code = urllib.parse.unquote(input("code: ").strip())
    res = _post_form(TOKEN_URL, {"client_id": cid, "client_secret": secret, "code": code,
                                 "redirect_uri": REDIRECT, "grant_type": "authorization_code"})
    rt = res.get("refresh_token")
    if not rt:
        print("リフレッシュトークンが返りませんでした。もう一度やり直してください。")
        return 1
    print("\nYT_REFRESH_TOKEN に入れる値（人に見せない・チャットに貼らない）:\n" + rt)
    return 0


def cmd_check(_args) -> int:
    tok = access_token()
    req = urllib.request.Request(f"{CHANNELS_URL}?part=snippet&mine=true",
                                 headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            items = json.loads(r.read().decode()).get("items", [])
    except urllib.error.HTTPError as e:
        print(_redact(f"接続NG: HTTP {e.code}: {e.read().decode(errors='replace')}"))
        return 1
    if not items:
        print("接続はできましたが、チャンネルが見つかりません（別のGoogleアカウントで許可していないか確認）")
        return 1
    print(f"接続OK: {items[0]['snippet']['title']}")
    return 0


def cmd_publish(args) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    state = ig.load_state()
    failures = 0
    tok = None
    for p in ig.load_posts():
        info = state.get(p["_key"])
        # Instagramに出した投稿だけ、12時間以内のものを対象にする（古い動画を後から大量に出さない）
        if not info or info.get("youtube_id") or info.get("youtube_tries", 0) >= MAX_TRIES:
            continue
        if not (p["_dir"] / "reel.mp4").exists():
            continue
        if "youtube" in p and not p["youtube"]:
            continue
        if now - ig.parse_time(p["publish_at"]) > dt.timedelta(hours=12):
            continue
        print(f"[YouTube] {p['_key']}  タイトル: {title_of(p)}")
        if args.dry_run:
            print("  （テスト実行なので投稿しません）")
            continue
        try:
            tok = tok or access_token()
            info["youtube_id"] = upload(tok, p)
            print(f"  完了: https://youtube.com/shorts/{info['youtube_id']}")
        except YtError as e:
            info["youtube_tries"] = info.get("youtube_tries", 0) + 1
            print(f"  失敗（{info['youtube_tries']}回目）: {e}")
            if info["youtube_tries"] >= MAX_TRIES:
                failures += 1
        ig.save_state(state)
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth").set_defaults(fn=cmd_auth)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    pu = sub.add_parser("publish")
    pu.add_argument("--dry-run", action="store_true")
    pu.set_defaults(fn=cmd_publish)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
