"""
새벽 작업용: 인스타 카드뉴스 폴더를 posts/에 게시 대기로 추가한다.

사용:
  python3 scripts/add_post.py <원본폴더> <영문슬러그> <회사명> "<블로그 예약시각 YYYY-MM-DD HH:MM>"

원본폴더: 01.png~05.png + 원고.txt (blog1/인스타/<회사>/ 를 스테이징한 위치)
- 이미지는 크기·비율 그대로, 형식만 PNG→JPEG (API가 PNG를 받지 않음)
- 이미 같은 캡션이 posts/에 있으면(게시됨·대기 모두) 추가하지 않고 종료 코드 2
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    src, slug, company, when = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    publish_at = datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=KST)

    cap = (src / "원고.txt").read_text(encoding="utf-8").strip()
    if len(cap) > 2200 or cap.count("#") > 30:
        sys.exit(f"캡션 제한 초과: {len(cap)}자, 해시태그 {cap.count('#')}개")
    images = sorted(src.glob("0[1-9].png"))
    if not 2 <= len(images) <= 10:
        sys.exit(f"이미지 {len(images)}장 — 2~10장이어야 함")

    for meta in (ROOT / "posts").glob("*/meta.json"):
        other = meta.parent / "caption.txt"
        if other.exists() and other.read_text(encoding="utf-8").strip() == cap:
            print(f"중복: {meta.parent.name}에 같은 캡션이 이미 있음 — 추가 안 함")
            sys.exit(2)

    dest = ROOT / "posts" / f"{publish_at:%Y-%m-%d}_{slug}"
    if dest.exists():
        sys.exit(f"이미 있는 폴더: {dest.name}")
    dest.mkdir(parents=True)
    for i, img in enumerate(images, 1):
        im = Image.open(img).convert("RGB")
        im.save(dest / f"{i}.jpg", quality=95)
    (dest / "caption.txt").write_text(cap + "\n", encoding="utf-8")
    (dest / "meta.json").write_text(json.dumps(
        {"company": company, "publish_at": publish_at.isoformat()},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"추가: {dest.name} ({len(images)}장, 게시 {publish_at:%m/%d %H:%M})")


if __name__ == "__main__":
    main()
