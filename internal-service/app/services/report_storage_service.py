from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Optional

from ..schemas.report import FinalResponse


class ReportStorageService:
    def __init__(self, storage_dir: str | None = None) -> None:
        self.storage_dir = Path(storage_dir or os.getenv("REPORT_STORAGE_DIR", "/app/reports"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._cache: dict[str, FinalResponse] = {}

    def save(self, report: FinalResponse) -> FinalResponse:
        with self._lock:
            self._cache[report.report_id] = report
            path = self.storage_dir / f"{report.report_id}.json"
            path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return report

    def get(self, report_id: str) -> Optional[FinalResponse]:
        with self._lock:
            cached = self._cache.get(report_id)
            if cached is not None:
                return cached

        path = self.storage_dir / f"{report_id}.json"
        if not path.exists():
            return None

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            report = FinalResponse.model_validate(payload)
        except Exception:
            return None

        with self._lock:
            self._cache[report_id] = report
        return report
