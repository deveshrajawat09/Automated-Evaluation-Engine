"""Minimal isolated runner service.

Run this service in a dedicated container with no network, a read-only root
filesystem, dropped capabilities, and strict CPU/memory/time limits. The API
service never executes participant code directly.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="HackEval Isolated Runner")


class RunRequest(BaseModel):
    language: str
    source_archive_id: str
    tests: list[dict] = Field(default_factory=list)


@app.post("/runs")
def run(request: RunRequest) -> dict:
    if request.language not in {"python", "javascript", "java", "cpp"}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    return {
        "status": "queued",
        "source_archive_id": request.source_archive_id,
        "language": request.language,
        "tests": len(request.tests),
        "message": "Execution must be handled by the deployment's restricted worker.",
    }
