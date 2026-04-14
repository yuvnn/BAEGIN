from __future__ import annotations

from dataclasses import dataclass, field
from threading import Condition, Lock, Thread
from typing import Optional
from uuid import uuid4

from ..schemas.input import GenerateReportRequest
from ..schemas.report import FinalResponse
from .pipeline_service import PipelineService
from .report_storage_service import ReportStorageService


@dataclass
class ReportJob:
    report_id: str
    payload: GenerateReportRequest
    events: list[dict] = field(default_factory=list)
    completed: bool = False
    error: Optional[str] = None
    result: Optional[FinalResponse] = None
    condition: Condition = field(default_factory=Condition)


class ReportStreamService:
    def __init__(
        self,
        *,
        pipeline_service: Optional[PipelineService] = None,
        storage_service: Optional[ReportStorageService] = None,
    ) -> None:
        self.pipeline_service = pipeline_service or PipelineService()
        self.storage_service = storage_service or ReportStorageService()
        self._jobs: dict[str, ReportJob] = {}
        self._lock = Lock()

    def start_generation(self, payload: GenerateReportRequest) -> str:
        report_id = uuid4().hex
        job = ReportJob(report_id=report_id, payload=payload)
        with self._lock:
            self._jobs[report_id] = job

        thread = Thread(target=self._run_generation, args=(job,), daemon=True)
        thread.start()
        return report_id

    def get_job(self, report_id: str) -> Optional[ReportJob]:
        with self._lock:
            return self._jobs.get(report_id)

    def to_sse_message(self, event: str, data: dict) -> str:
        payload = self._serialize_data(data)
        return f"event: {event}\ndata: {payload}\n\n"

    def _run_generation(self, job: ReportJob) -> None:
        try:
            def emit(event_name: str, data: dict) -> None:
                self._append_event(job, event_name, data)

            result = self.pipeline_service.build_report(job.payload, emit=emit)
            result.report_id = job.report_id
            self.storage_service.save(result)
            job.result = result
            self._append_event(job, "completed", {"report": result.model_dump(mode="json")}, complete=True)
        except Exception as exc:
            job.error = str(exc)
            self._append_event(job, "failed", {"message": job.error}, complete=True)

    def _append_event(self, job: ReportJob, event: str, data: dict, complete: bool = False) -> None:
        with job.condition:
            job.events.append({"event": event, "data": data})
            if complete:
                job.completed = True
            job.condition.notify_all()

    def _serialize_data(self, data: dict) -> str:
        import json

        return json.dumps(data, ensure_ascii=False)
