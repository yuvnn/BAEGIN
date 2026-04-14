from __future__ import annotations

from ..schemas.report import FinalResponse


_REPORT_STORE: dict[str, FinalResponse] = {}


def save_report(response: FinalResponse) -> None:
    _REPORT_STORE[response.report_id] = response


def get_report(report_id: str) -> FinalResponse | None:
    return _REPORT_STORE.get(report_id)


def get_latest_report() -> FinalResponse | None:
    if not _REPORT_STORE:
        return None
    return max(_REPORT_STORE.values(), key=lambda item: item.updated_at)
