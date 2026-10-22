# insta-auto

내일은 출근 블로그 카드뉴스를 블로그 발행 시간에 맞춰 인스타그램에 자동 게시하는 저장소.

## 게시물 올리는 법

`posts/<날짜_기업명>/` 폴더에 아래 파일을 넣어 push 하면 된다.

| 파일 | 내용 |
|---|---|
| `1.jpg` ~ `5.jpg` | 카드뉴스 이미지 (JPEG, 같은 비율, 순서대로) |
| `caption.txt` | 캡션 + 해시태그 (2,200자·해시태그 30개 이내) |
| `meta.json` | `{"publish_at": "2026-10-23T09:40:00+09:00"}` — 블로그 발행 시간 |

GitHub Actions가 15분마다 확인해서 `publish_at`이 지난 게시물을 올리고,
`meta.json`에 `posted: true`와 `media_id`를 기록한다. 실패하면 `last_error`에 이유가 남고 최대 3번 재시도한다.

## 필요한 시크릿 (Settings → Secrets and variables → Actions)

- `IG_ACCESS_TOKEN` — Instagram 장기 액세스 토큰
- `IG_USER_ID` — Instagram 계정 ID (비워두면 `me` 사용)
- `GH_PAT` — 토큰 자동 갱신용 GitHub 토큰 (Secrets 쓰기 권한)
