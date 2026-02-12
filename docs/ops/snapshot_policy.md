# Snapshot Policy

## English

## Purpose

Define how snapshots are saved and exposed for the backend/front.

## Storage Layout

- Base directory: `events.snapshot.base_dir`
- Relative path: `{site_id}/{camera_id}/{timestamp}_{track_id}.jpg`
  - If `track_id` is null, `_track_id` suffix is omitted.
- Public prefix: `events.snapshot.public_prefix`

## Access

- Backend should serve public prefix path or map it to object storage.
- AI only writes files; serving is backend responsibility.

## Permissions

- Ensure write permission to base dir.
- If running in Docker, mount host volume to `/data/snapshots`.
- Default config keeps snapshots disabled; enable by setting `events.snapshot.base_dir`.

## Retention

- Not enforced by AI. Backend/ops should define retention policy.

## Code Mapping

- Snapshot path/publish: `src/ai/events/snapshot.py`
- Snapshot injection: `src/ai/pipeline/events.py`

## 한국어

## 목적

스냅샷 저장/노출 정책을 정의한다.

## 저장 레이아웃

- 기본 디렉터리: `events.snapshot.base_dir`
- 상대 경로 규칙: `{site_id}/{camera_id}/{timestamp}_{track_id}.jpg`
  - `track_id`가 null이면 `_track_id` 접미사는 생략된다.
- 공개 프리픽스: `events.snapshot.public_prefix`

## 접근

- 백엔드는 public prefix 경로를 서빙하거나 오브젝트 스토리지와 매핑해야 한다.
- AI는 파일만 쓰며, 서빙은 백엔드 책임이다.

## 권한

- 기본 디렉터리에 쓰기 권한이 있어야 한다.
- Docker 실행 시 `/data/snapshots`로 호스트 볼륨을 마운트한다.
- 기본 설정에서는 스냅샷이 비활성화되어 있으며, `events.snapshot.base_dir`를 지정해야 활성화된다.

## 보관 정책

- AI에서 보관 주기를 강제하지 않는다. 백엔드/운영에서 정의한다.

## 코드 매핑

- 스냅샷 경로/공개 경로: `src/ai/events/snapshot.py`
- 스냅샷 주입: `src/ai/pipeline/events.py`
