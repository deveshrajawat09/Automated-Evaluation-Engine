"""Restricted execution worker.

This service is intended to run as a separate, unprivileged container. The
API sends an uploaded source file identifier; the worker never accepts shell
commands from callers and only executes fixed language toolchains.
"""

from pathlib import Path
import shutil
import subprocess
import tempfile
from os import getenv

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="HackEval Isolated Runner")
INPUT_ROOT = Path("/sandbox-inputs")
TIMEOUT_SECONDS = 10


class RunRequest(BaseModel):
    language: str
    source_archive_id: str = Field(min_length=3, max_length=200, pattern=r"^[A-Za-z0-9._-]+$")
    tests: list[dict] = Field(min_length=1, max_length=20)


def _run(command: list[str], cwd: Path, stdin: str = "") -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "Execution timed out."
    return completed.returncode, completed.stdout[-4000:], completed.stderr[-4000:]


def _execute(language: str, source: Path, workdir: Path, stdin: str) -> tuple[int, str, str]:
    if language == "python":
        return _run(["python", str(source)], workdir, stdin)
    if language == "javascript":
        return _run(["node", str(source)], workdir, stdin)
    if language == "java":
        compiled = _run(["javac", str(source)], workdir)
        if compiled[0]:
            return compiled
        return _run(["java", "-cp", str(workdir), source.stem], workdir, stdin)
    if language == "cpp":
        binary = workdir / "program"
        compiled = _run(["g++", "-O2", "-std=c++17", str(source), "-o", str(binary)], workdir)
        if compiled[0]:
            return compiled
        return _run([str(binary)], workdir, stdin)
    raise HTTPException(status_code=422, detail="Unsupported language")


@app.post("/runs")
def run(request: RunRequest, runner_token: str | None = Header(default=None, alias="X-Runner-Token")) -> dict:
    expected_token = getenv("SANDBOX_RUNNER_TOKEN", "")
    if expected_token and runner_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid runner credentials")
    results = []
    with tempfile.TemporaryDirectory(dir="/tmp") as temporary_dir:
        workdir = Path(temporary_dir)
        copied_source = workdir / request.source_archive_id
        bucket_name = getenv("GCS_BUCKET", "")
        if bucket_name:
            from google.cloud import storage

            blob = storage.Client().bucket(bucket_name).blob(f"uploads/{request.source_archive_id}")
            if not blob.exists():
                raise HTTPException(status_code=404, detail="Source artifact was not found in object storage")
            if blob.size and blob.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Source artifact exceeds the 10 MB runner limit")
            blob.download_to_filename(str(copied_source))
        else:
            source = INPUT_ROOT / request.source_archive_id
            if not source.is_file():
                raise HTTPException(status_code=404, detail="Source artifact was not found in the runner input volume")
            if source.stat().st_size > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Source artifact exceeds the 10 MB runner limit")
            shutil.copyfile(source, copied_source)
        for index, test in enumerate(request.tests):
            stdin = test.get("stdin", "")
            if not isinstance(stdin, str) or len(stdin) > 100_000:
                raise HTTPException(status_code=422, detail=f"Test {index} has invalid stdin")
            code, stdout, stderr = _execute(request.language, copied_source, workdir, stdin)
            expected = test.get("expected_stdout")
            results.append({
                "index": index,
                "passed": code == 0 and (expected is None or stdout.strip() == str(expected).strip()),
                "exit_code": code,
                "stdout": stdout,
                "stderr": stderr,
            })
            if code != 0:
                break
    return {
        "status": "completed",
        "source_archive_id": request.source_archive_id,
        "language": request.language,
        "tests": results,
        "passed": bool(results) and all(item["passed"] for item in results),
    }
