#!/usr/bin/env python3
"""Instagram 自動投稿スクリプト（Instagram API with Instagram Login 用）

使い方:
  python scripts/ig.py publish [--dry-run]   予約時刻を過ぎた投稿を公開する
  python scripts/ig.py check                 トークンとアカウントの接続テスト
  python scripts/ig.py refresh --out FILE    長期トークンを更新して FILE に書き出す
  python scripts/ig.py validate              posts/ の中身をチェックするだけ

必要な環境変数:
  IG_ACCESS_TOKEN   長期アクセストークン（GitHub Secrets に保存）
  IG_USER_ID        InstagramのユーザーID（check で確認できる）
  IMAGE_BASE_URL    画像を公開しているURLの先頭（ワークフローが自動で設定）
任意:
  IG_API_BASE       既定 https://graph.instagram.com
  IG_API_VERSION    既定 v23.0
  DEFAULT_TZ        既定 America/Chicago（publish_at に時差がないときに使う）
  LATE_LIMIT_HOURS  既定 24（これ以上遅れた投稿は公開しない）
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
STATE_FILE = ROOT / "published.json"

API_BASE = os.environ.get("IG_API_BASE", "https://graph.instagram.com").rstrip("/")
API_VERSION = os.environ.get("IG_API_VERSION", "v23.0")
DEFAULT_TZ = ZoneInfo(os.environ.get("DEFAULT_TZ", "America/Chicago"))
LATE_LIMIT = dt.timedelta(hours=float(os.environ.get("LATE_LIMIT_HOURS", "24")))

MAX_CAPTION = 2200
MAX_HASHTAGS = 30
MAX_IMAGES = 10
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


class ApiError(Exception):
    pass


# ---------------------------------------------------------------- API helpers
def _token() -> str:
    t = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not t:
        sys.exit("IG_ACCESS_TOKEN が設定されていません（GitHub Secrets を確認）")
    return t


def _redact(text: str) -> str:
    t = os.environ.get("IG_ACCESS_TOKEN", "")
    return text.replace(t, "***") if t else text


def api(method: str, path: str, params: dict | None = None, versioned: bool = True) -> dict:
    params = dict(params or {})
    params["access_token"] = _token()
    url = f"{API_BASE}/{API_VERSION}/{path}" if versioned else f"{API_BASE}/{path}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise ApiError(_redact(f"{method} {path} -> HTTP {e.code}: {body}")) from None
    except urllib.error.URLError as e:
        raise ApiError(_redact(f"{method} {path} -> 接続エラー: {e.reason}")) from None


def wait_ready(container_id: str, timeout_s: int = 300) -> None:
    """コンテナの処理完了（FINISHED）を待つ。"""
    deadline = time.time() + timeout_s
    delay = 3
    while True:
        st = api("GET", container_id, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code in (None, "FINISHED", "PUBLISHED"):
            return
        if code in ("ERROR", "EXPIRED"):
            raise ApiError(f"メディア処理に失敗: {st}")
        if time.time() > deadline:
            raise ApiError(f"メディア処理がタイムアウト: {st}")
        time.sleep(delay)
        delay = min(delay * 2, 20)


# ---------------------------------------------------------------- posts
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_time(s: str) -> dt.datetime:
    t = dt.datetime.fromisoformat(s.strip().replace(" ", "T"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=DEFAULT_TZ)
    return t


def load_posts() -> list[dict]:
    posts = []
    for f in sorted(POSTS_DIR.glob("*/post.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        p["_dir"] = f.parent
        p["_key"] = f.parent.name
        posts.append(p)
    return posts


def validate(p: dict) -> list[str]:
    errs = []
    d: Path = p["_dir"]
    if not SAFE_NAME.match(d.name):
        errs.append(f"フォルダ名は半角英数字・-・_ だけにしてください: {d.name}")
    try:
        parse_time(p.get("publish_at", ""))
    except Exception:
        errs.append("publish_at の形式が正しくありません（例: 2026-10-05 19:00）")
    cap = p.get("caption", "")
    if len(cap) > MAX_CAPTION:
        errs.append(f"キャプションが長すぎます（{len(cap)}/{MAX_CAPTION}文字）")
    if cap.count("#") > MAX_HASHTAGS:
        errs.append(f"ハッシュタグが多すぎます（最大{MAX_HASHTAGS}個）")
    imgs = p.get("images", [])
    if not 1 <= len(imgs) <= MAX_IMAGES:
        errs.append(f"画像は1〜{MAX_IMAGES}枚にしてください（今{len(imgs)}枚）")
    for name in imgs:
        if not SAFE_NAME.match(name):
            errs.append(f"画像ファイル名は半角英数字にしてください: {name}")
        if not name.lower().endswith((".jpg", ".jpeg")):
            errs.append(f"画像はJPEGだけ使えます（CanvaでJPGで書き出し）: {name}")
        if not (d / name).exists():
            errs.append(f"画像が見つかりません: {d.name}/{name}")
    return errs


def image_url(p: dict, name: str) -> str:
    base = os.environ.get("IMAGE_BASE_URL", "").rstrip("/")
    if not base:
        sys.exit("IMAGE_BASE_URL が設定されていません")
    rel = (p["_dir"] / name).relative_to(ROOT).as_posix()
    return f"{base}/{rel}"


def already_on_instagram(ig_id: str, caption: str) -> dict | None:
    """同じキャプションの投稿が最近あれば返す（二重投稿防止）。"""
    try:
        res = api("GET", f"{ig_id}/media", {"fields": "id,caption,permalink,timestamp", "limit": 10})
    except ApiError as e:
        print(f"  (確認をスキップ: {e})")
        return None
    head = caption.strip()[:200]
    for m in res.get("data", []):
        if (m.get("caption") or "").strip()[:200] == head:
            return m
    return None


def publish_post(ig_id: str, p: dict) -> dict:
    caption = p.get("caption", "")
    imgs = p["images"]
    if len(imgs) == 1:
        c = api("POST", f"{ig_id}/media", {"image_url": image_url(p, imgs[0]), "caption": caption})
        creation_id = c["id"]
    else:
        children = []
        for name in imgs:
            c = api("POST", f"{ig_id}/media", {"image_url": image_url(p, name), "is_carousel_item": "true"})
            children.append(c["id"])
            print(f"  画像アップ: {name}")
        for cid in children:
            wait_ready(cid)
        c = api("POST", f"{ig_id}/media",
                {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption})
        creation_id = c["id"]
    wait_ready(creation_id)
    res = api("POST", f"{ig_id}/media_publish", {"creation_id": creation_id})
    media_id = res["id"]
    info = {}
    try:
        info = api("GET", media_id, {"fields": "permalink,timestamp"})
    except ApiError:
        pass
    return {"media_id": media_id, "permalink": info.get("permalink")}


# ---------------------------------------------------------------- commands
def cmd_validate(_args) -> int:
    bad = 0
    for p in load_posts():
        if p.get("draft"):
            print(f"[下書き] {p['_key']}")
            continue
        errs = validate(p)
        print(f"[{'NG' if errs else 'OK'}] {p['_key']}  公開: {p.get('publish_at')}")
        for e in errs:
            print(f"    - {e}")
        bad += bool(errs)
    return 1 if bad else 0


def cmd_publish(args) -> int:
    ig_id = os.environ.get("IG_USER_ID", "").strip()
    if not ig_id and not args.dry_run:
        sys.exit("IG_USER_ID が設定されていません")
    now = dt.datetime.now(dt.timezone.utc)
    state = load_state()
    failures = 0
    for p in load_posts():
        key = p["_key"]
        if key in state or p.get("draft"):
            continue
        when = parse_time(p["publish_at"])
        if when > now:
            continue
        if now - when > LATE_LIMIT:
            print(f"[スキップ] {key}: 予定時刻から{LATE_LIMIT.total_seconds()/3600:.0f}時間以上遅れたので公開しません（publish_at を直してください）")
            continue
        errs = validate(p)
        if errs:
            print(f"[エラー] {key}")
            for e in errs:
                print(f"    - {e}")
            failures += 1
            continue
        print(f"[公開] {key}（予定 {when.astimezone(DEFAULT_TZ):%m/%d %H:%M}）")
        if args.dry_run:
            for name in p["images"]:
                print(f"  {image_url(p, name) if os.environ.get('IMAGE_BASE_URL') else name}")
            print("  （テスト実行なので投稿しません）")
            continue
        try:
            dup = already_on_instagram(ig_id, p.get("caption", ""))
            if dup:
                print(f"  すでに投稿済みでした: {dup.get('permalink')}")
                state[key] = {"media_id": dup["id"], "permalink": dup.get("permalink"), "note": "detected"}
            else:
                res = publish_post(ig_id, p)
                print(f"  完了: {res.get('permalink') or res['media_id']}")
                state[key] = {**res, "published_at": now.isoformat(timespec="seconds")}
            save_state(state)  # 1件ごとに保存（二重投稿防止）
        except ApiError as e:
            print(f"  失敗: {e}")
            failures += 1
    return 1 if failures else 0


def cmd_check(_args) -> int:
    me = api("GET", "me", {"fields": "user_id,username,account_type,media_count"})
    print(f"ユーザー名: @{me.get('username')}")
    print(f"アカウント種別: {me.get('account_type')}")
    print(f"IG_USER_ID にはこれを入れる: {me.get('user_id') or me.get('id')}")
    set_id = os.environ.get("IG_USER_ID", "").strip()
    if set_id and set_id not in (str(me.get("user_id")), str(me.get("id"))):
        print("⚠️ いま設定されている IG_USER_ID と違います")
        return 1
    print("接続OK")
    return 0


def cmd_refresh(args) -> int:
    res = api("GET", "refresh_access_token",
              {"grant_type": "ig_refresh_token"}, versioned=False)
    new = res.get("access_token")
    if not new:
        raise ApiError(f"更新に失敗: {res}")
    days = int(res.get("expires_in", 0)) // 86400
    Path(args.out).write_text(new, encoding="utf-8")
    print(f"トークンを更新しました（あと約{days}日有効）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("publish")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("check")
    sub.add_parser("validate")
    r = sub.add_parser("refresh")
    r.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        return {"publish": cmd_publish, "check": cmd_check,
                "validate": cmd_validate, "refresh": cmd_refresh}[args.cmd](args)
    except ApiError as e:
        print(f"エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
