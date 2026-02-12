# Labeling Guide (Draft)

## English
Purpose
-------
Provide practical labeling rules for safety CCTV datasets. This guide aims to reduce ambiguity and improve consistency across annotators.

General Rules
-------------
- Label only visible objects; partial occlusion is still valid if class is clear.
- If class is ambiguous, mark as UNKNOWN and exclude from training (unless policy says otherwise).
- Keep bounding boxes tight to the visible object.
- Use the class taxonomy in `docs/specs/model_class_taxonomy.md`.

Class Rules (Phase 1)
----------------------
- PERSON: Any visible human figure, standing/sitting/lying. Include partial bodies if clearly human.
- ZONE_INTRUSION: Derived from PERSON + zone rules; not a raw label for bounding boxes.
- DANGER_ZONE_ENTRY: Same as ZONE_INTRUSION but for dangerous zones; not a raw label.

Class Rules (Phase 2+)
----------------------
- PPE: Identify required gear (helmet, vest). Use PPE subclass labels if taxonomy defines them.
- POSTURE: Identify unsafe posture (fall, crouch, lying). Use clear posture classes only.
- SMOKE/FIRE: Label smoke/fires as separate classes when visually obvious.
- HAZARD: Other safety hazards (define in taxonomy).

Ambiguous Cases
---------------
- Heavy occlusion: label only if class is confidently visible.
- Reflections/TV screens: avoid labeling unless explicitly required.
- Crowd scenes: label each person if distinguishable.

Quality Control
---------------
- Perform random audits (5-10% of labels).
- Track inter-annotator agreement.
- Maintain a changelog for taxonomy updates.

## 한국어
목적
-----
산업안전 CCTV 데이터셋 라벨링 규칙을 정의한다. 모호성을 줄이고 라벨러 간 일관성을 높인다.

일반 규칙
---------
- 보이는 객체만 라벨링한다. 부분 가림도 클래스가 명확하면 라벨링.
- 모호한 경우 UNKNOWN 처리 후 학습 제외(정책에 따라 다름).
- 박스는 보이는 객체에 타이트하게 맞춘다.
- 클래스 분류는 `docs/specs/model_class_taxonomy.md`를 따른다.

클래스 규칙(1단계)
-------------------
- PERSON: 서있기/앉기/누움 포함 모든 사람. 부분 신체도 명확하면 포함.
- ZONE_INTRUSION: PERSON+zone 규칙으로 파생, 박스 라벨 아님.
- DANGER_ZONE_ENTRY: 위험구역 침입 파생, 박스 라벨 아님.

클래스 규칙(2단계 이후)
------------------------
- PPE: 헬멧/조끼 등. taxonomy에 정의된 하위 라벨 사용.
- POSTURE: 위험 자세(넘어짐/쭈그림/누움). 명확한 경우만 라벨.
- SMOKE/FIRE: 육안으로 명확할 때 라벨.
- HAZARD: 기타 위험상황(분류 정의 필요).

모호한 사례
-----------
- 심한 가림: 클래스가 확실하면 라벨.
- 반사/모니터 화면: 원칙적으로 라벨 제외.
- 군중: 구분 가능한 경우 개별 라벨링.

품질 관리
---------
- 랜덤 감사(5-10%) 수행.
- 라벨러 간 일치도 추적.
- taxonomy 변경 기록 유지.
