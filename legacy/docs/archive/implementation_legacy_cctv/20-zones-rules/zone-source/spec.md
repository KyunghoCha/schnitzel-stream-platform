# Zone Source - Spec

## English
Behavior
--------
- If source=api, fetch zones via backend endpoint and cache.
- If source=file, read zones from JSON/YAML file and cache with TTL.
- If source=none, skip zone loading and return empty list.

Config
------
- zones.source
- zones.file_path
- zones.api.base_url
- zones.api.get_path_template
- zones.api.timeout_sec
- zones.api.cache_ttl_sec
- zones.api.error_backoff_sec
- zones.api.max_failures

Edge Cases
----------
- API error -> use cached zones if available, and apply backoff when failures repeat.
- API error is logged.
- API failure logs mask credentials in URLs.
- File missing -> return empty list (cache if available).

Status
------
Implemented in `src/ai/rules/zones.py`.

Code Mapping
------------
- Zone source load: `src/ai/rules/zones.py`

## 한국어
동작
----
- source=api이면 백엔드에서 zone을 가져와 캐시한다.
- source=file이면 JSON/YAML 파일에서 zone을 읽고 TTL 캐시한다.
- source=none이면 zone 로딩을 생략하고 빈 리스트를 반환한다.

설정
----
- zones.source
- zones.file_path
- zones.api.base_url
- zones.api.get_path_template
- zones.api.timeout_sec
- zones.api.cache_ttl_sec
- zones.api.error_backoff_sec
- zones.api.max_failures

엣지 케이스
----------
- API 오류 시 캐시가 있으면 캐시 사용하고, 반복 실패 시 백오프를 적용.
- API 오류는 로그로 남긴다.
- API 실패 로그의 URL은 자격 정보를 마스킹한다.
- 파일이 없으면 빈 리스트를 반환(캐시가 있으면 캐시 사용).

상태
----
`src/ai/rules/zones.py`에 구현됨.

코드 매핑
---------
- zone 소스 로드: `src/ai/rules/zones.py`
