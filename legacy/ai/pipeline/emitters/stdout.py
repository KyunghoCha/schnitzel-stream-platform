from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class StdoutEmitter:
    # 콘솔 출력 에미터 (dry-run)
    def emit(self, payload: dict[str, Any]) -> bool:
        logger.info("DRY_RUN event=%s", payload)
        return True

    def close(self) -> None:
        pass
