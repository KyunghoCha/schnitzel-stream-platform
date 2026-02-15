# Docs: docs/packs/vision/model_class_taxonomy.md
# 모델 클래스 ID를 프로토콜 이벤트/객체/심각도 필드에 매핑.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf


@dataclass(frozen=True)
class ClassMapEntry:
    event_type: str
    object_type: str
    severity: str


DEFAULT_CLASS_MAP: dict[int, ClassMapEntry] = {
    0: ClassMapEntry(event_type="ZONE_INTRUSION", object_type="PERSON", severity="LOW"),
}


def load_class_map(path: str | None) -> dict[int, ClassMapEntry]:
    if not path:
        return {}
    fpath = Path(path)
    if not fpath.exists():
        return {}
    data = OmegaConf.load(fpath)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        return {}
    raw = cont.get("class_map", [])
    if not isinstance(raw, list):
        return {}
    out: dict[int, ClassMapEntry] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        cid = item.get("class_id")
        event_type = item.get("event_type")
        object_type = item.get("object_type")
        severity = item.get("severity")
        if cid is None or event_type is None or object_type is None or severity is None:
            continue
        try:
            cid_int = int(cid)
        except (TypeError, ValueError):
            continue
        out[cid_int] = ClassMapEntry(
            event_type=str(event_type),
            object_type=str(object_type),
            severity=str(severity),
        )
    return out
