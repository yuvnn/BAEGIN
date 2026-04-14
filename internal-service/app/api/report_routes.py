from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..schemas.input import GenerateReportRequest
from ..schemas.report import FinalResponse
from ..services.pipeline_service import PipelineService
from ..services.report_storage_service import ReportStorageService
from ..services.report_stream_service import ReportStreamService

router = APIRouter(prefix="/reports", tags=["reports"])

pipeline_service = PipelineService()
storage_service = ReportStorageService()
stream_service = ReportStreamService(pipeline_service=pipeline_service, storage_service=storage_service)


class GenerateAcceptedResponse(BaseModel):
    report_id: str


@router.post("/generate", response_model=GenerateAcceptedResponse)
def generate_report(payload: GenerateReportRequest) -> GenerateAcceptedResponse:
    report_id = stream_service.start_generation(payload)
    return GenerateAcceptedResponse(report_id=report_id)


@router.get("/stream/{report_id}")
def stream_report(report_id: str) -> StreamingResponse:
    job = stream_service.get_job(report_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Report stream not found: {report_id}")

    def event_generator():
        cursor = 0
        while True:
            with job.condition:
                if cursor >= len(job.events) and not job.completed:
                    job.condition.wait(timeout=10)

                pending_events = job.events[cursor:]
                cursor = len(job.events)
                done = job.completed

            if pending_events:
                for event in pending_events:
                    yield stream_service.to_sse_message(event["event"], event["data"])
            else:
                # Keep the SSE connection alive while waiting for next section.
                yield ": keep-alive\n\n"
                time.sleep(0.2)

            if done and cursor >= len(job.events):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{report_id}", response_model=FinalResponse)
def get_report(report_id: str) -> FinalResponse:
    result = storage_service.get(report_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")
    return result
