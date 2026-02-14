from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass
class FileEmitter:
    # jsonl 파일 출력 에미터
    path: str

    def __post_init__(self) -> None:
        # 출력 디렉터리 생성 및 파일 오픈
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a", encoding="utf-8")

    def emit(self, payload: dict[str, Any]) -> bool:
        # 한 줄에 JSON 1개씩 기록
        self._fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._fh.flush()
        return True

    def close(self) -> None:
        # 파일 핸들 닫기
        self._fh.close()

    def __enter__(self) -> FileEmitter:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
