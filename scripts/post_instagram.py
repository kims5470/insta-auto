"""
예약 시간이 지난 인스타 카드뉴스를 Instagram API로 게시한다.

폴더 구조:
  posts/<폴더이름>/
    1.jpg ~ 5.jpg   (캐러셀 순서대로, JPEG)
    caption.txt     (캡션 + 해시태그)
    meta.json       {"publish_at": "2026-10-23T09:40:00+09:00"}

게시 후 meta.json에 posted / media_id / posted_at 이 기록된다.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"

TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.environ.get("IG_USER_ID", "").strip() or "me"
REPO = os.environ.get("GITHUB_REPOSITORY", "kims5470/insta-auto")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
API = "https://graph.instagram.com"
MAX_ATTEMPTS = 3


def api(method, path, params):
    params = dict(params, access_token=TOKEN)
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> {e.code}: {body}") from None


def wait_finished(container_id):
    for _ in range(20):
        status = api("GET", container_id, {"fields": "status_code"}).get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container_id} status {status}")
        time.sleep(5)
    raise RuntimeError(f"container {container_id} not ready in time")


def image_url(folder, name):
    path = urllib.parse.quote(f"posts/{folder}/{name}")
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"


def publish(folder: Path):
    images = sorted(
        (p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg")),
        key=lambda p: (len(p.stem), p.stem),
    )
    if not 2 <= len(images) <= 10:
        raise RuntimeError(f"이미지 수가 {len(images)}장 (캐러셀은 2~10장)")
    caption = (folder / "caption.txt").read_text(encoding="utf-8").strip()

    children = []
    for img in images:
        res = api("POST", f"{IG_USER_ID}/media", {
            "image_url": image_url(folder.name, img.name),
            "is_carousel_item": "true",
        })
        children.append(res["id"])
    for cid in children:
        wait_finished(cid)

    carousel = api("POST", f"{IG_USER_ID}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": caption,
    })["id"]
    wait_finished(carousel)

    return api("POST", f"{IG_USER_ID}/media_publish", {"creation_id": carousel})["id"]


def main():
    if not TOKEN:
        sys.exit("IG_ACCESS_TOKEN 시크릿이 없습니다.")
    if not POSTS_DIR.exists():
        print("posts 폴더 없음 — 할 일 없음")
        return

    now = datetime.now(timezone.utc)
    failed = False
    for meta_path in sorted(POSTS_DIR.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("posted") or meta.get("attempts", 0) >= MAX_ATTEMPTS:
            continue
        publish_at = datetime.fromisoformat(meta["publish_at"])
        if publish_at.tzinfo is None:
            sys.exit(f"{meta_path}: publish_at에 시간대(+09:00)가 없습니다.")
        if publish_at > now:
            continue

        folder = meta_path.parent
        print(f"게시 시도: {folder.name}")
        try:
            media_id = publish(folder)
            meta.update(posted=True, media_id=media_id,
                        posted_at=now.isoformat(timespec="seconds"))
            meta.pop("last_error", None)
            print(f"  완료: {media_id}")
        except Exception as e:  # noqa: BLE001
            meta["attempts"] = meta.get("attempts", 0) + 1
            meta["last_error"] = str(e)[:500]
            print(f"  실패 ({meta['attempts']}/{MAX_ATTEMPTS}): {e}")
            failed = True
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
