from __future__ import annotations

from ..repositories.report_repository import get_latest_report, get_report, save_report
from ..schemas.report import FinalResponse


class ReportStorageService:
    def save(self, response: FinalResponse) -> None:
        save_report(response)

    def get(self, report_id: str) -> FinalResponse | None:
        return get_report(report_id)

    def get_latest(self) -> FinalResponse | None:
        return get_latest_report()
