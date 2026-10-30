from typing import Annotated
from uuid import uuid4

from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.routers.dependencies import require_roles
from app.schemas import EvaluationRequest, JudgeEvaluation, RepositoryAnalysisRequest, Role, SubmissionCreate
from app.schemas import SandboxRunRequest, TextAnalysisRequest
from app.services.analysis import analyze_text_artifact, static_code_analysis
from app.services.evaluation import evaluate_submission
from app.services.fraud import create_fraud_report
from app.services.repository import analyze_repository
from app.services.sandbox import SandboxUnavailable, run_in_isolated_runner
from app.services.storage import upload_artifact as store_artifact
from app.store import audit, save_store, submissions, teams, uploads

router = APIRouter(tags=["Submissions & Evaluation"])
ALLOWED_UPLOAD_TYPES = {"application/pdf", "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "video/mp4", "video/webm", "video/quicktime", "text/plain", "text/x-python", "application/javascript", "text/javascript", "text/x-java-source", "text/x-c++src"}
SOURCE_UPLOAD_TYPES = {"text/plain", "text/x-python", "application/javascript", "text/javascript", "text/x-java-source", "text/x-c++src"}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_artifact(file: UploadFile = File(...), user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT))] = None) -> dict:
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, PPT/PPTX, MP4, WebM, MOV, and supported source-text files are allowed")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds the 100 MB limit")
    upload_id = str(uuid4())
    extension = Path(file.filename or "artifact.bin").suffix.lower()
    artifact_path = store_artifact(upload_id, content, extension)
    record = {"id": upload_id, "owner_id": user["id"], "filename": file.filename or "artifact", "content_type": file.content_type, "size": len(content), "path": artifact_path, "status": "UPLOADED"}
    uploads[upload_id] = record
    save_store()
    audit(user["id"], "UPLOAD", "artifact", upload_id, f"Uploaded {record['filename']}")
    return record


@router.get("/submissions")
def list_submissions(hackathon_id: str | None = None) -> list[dict]:
    data = list(submissions.values())
    return [item for item in data if not hackathon_id or item["hackathon_id"] == hackathon_id]


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: str) -> dict:
    item = submissions.get(submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    return item


@router.post("/submissions", status_code=status.HTTP_201_CREATED)
def create_submission(payload: SubmissionCreate, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT))]) -> dict:
    team = teams.get(payload.team_id)
    if not team or team["hackathon_id"] != payload.hackathon_id:
        raise HTTPException(status_code=422, detail="Team is not registered for this hackathon")
    if user["id"] not in team["members"]:
        raise HTTPException(status_code=403, detail="Only team members can submit a project")
    unknown_artifacts = [artifact_id for artifact_id in payload.artifact_ids if artifact_id not in uploads or uploads[artifact_id]["owner_id"] != user["id"]]
    if unknown_artifacts:
        raise HTTPException(status_code=422, detail="One or more uploaded artifacts are invalid")
    item = payload.model_dump(mode="json") | {"id": str(uuid4()), "team_name": team["name"], "status": "SUBMITTED", "score": None, "risk": None}
    submissions[item["id"]] = item
    hackathons[item["hackathon_id"]]["submissions"] += 1
    save_store()
    audit(user["id"], "CREATE", "submission", item["id"], f"Submitted {item['project_name']}")
    return item


@router.post("/repositories/analyze")
def repository_analysis(payload: RepositoryAnalysisRequest, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT, Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    try:
        return analyze_repository(str(payload.github_url))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/code/analyze")
def code_analysis(payload: RepositoryAnalysisRequest, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT, Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    try:
        return static_code_analysis(analyze_repository(str(payload.github_url)))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/sandbox/run")
async def sandbox_run(payload: SandboxRunRequest, user: Annotated[dict, Depends(require_roles(Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    source = uploads.get(payload.source_archive_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source artifact not found")
    if source["content_type"] not in SOURCE_UPLOAD_TYPES:
        raise HTTPException(status_code=422, detail="Sandbox execution requires a supported source-code artifact")
    try:
        return await run_in_isolated_runner(payload.language, Path(source["path"]).name, payload.tests)
    except SandboxUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/pitch/analyze")
def pitch_analysis(payload: TextAnalysisRequest, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT, Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    return analyze_text_artifact(payload.text, "pitch_deck")


@router.post("/demo/analyze")
def demo_analysis(payload: TextAnalysisRequest, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT, Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    return analyze_text_artifact(payload.text, "demo_transcript")


@router.post("/ai/evaluate")
def ai_evaluate(payload: EvaluationRequest, user: Annotated[dict, Depends(require_roles(Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    item = submissions.get(payload.submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    repository = analyze_repository(item["github_url"])
    rubric = [(row.criterion, row.weight) for row in payload.rubric] if payload.rubric else None
    report = evaluate_submission(item, repository, rubric)
    fraud = create_fraud_report(repository, item["project_description"])
    item["score"] = report["overall_score"]
    item["risk"] = fraud["overall_risk"]
    item["status"] = "FLAGGED" if fraud["human_review_required"] else "EVALUATED"
    save_store()
    audit(user["id"], "EVALUATE", "submission", item["id"], "Generated explainable AI evaluation")
    return {"evaluation": report, "repository": repository, "fraud_report": fraud}


@router.get("/evaluations/{submission_id}")
def get_evaluation(submission_id: str, user: Annotated[dict, Depends(require_roles(Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    item = submissions.get(submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    repository = analyze_repository(item["github_url"])
    return {
        "evaluation": evaluate_submission(item, repository),
        "repository": repository,
        "fraud_report": create_fraud_report(repository, item["project_description"]),
        "audit_note": "This is an explainable decision-support report; judges retain final authority.",
    }


@router.post("/plagiarism/analyze")
def plagiarism_analysis(payload: EvaluationRequest, user: Annotated[dict, Depends(require_roles(Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> dict:
    item = submissions.get(payload.submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    return create_fraud_report(analyze_repository(item["github_url"]), item["project_description"])


@router.post("/judges/evaluate")
def judge_evaluate(payload: JudgeEvaluation, user: Annotated[dict, Depends(require_roles(Role.JUDGE, Role.ADMIN))]) -> dict:
    item = submissions.get(payload.submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    item["judge_score"] = payload.score
    item["judge_comments"] = payload.comments
    item["judge_criteria"] = payload.criteria
    item["status"] = "ACCEPTED" if payload.approved else "UNDER_REVIEW"
    item["score"] = round((float(item.get("score") or payload.score) + payload.score) / 2, 1)
    save_store()
    audit(user["id"], "JUDGE_EVALUATE", "submission", item["id"], payload.comments)
    return {"submission_id": item["id"], "final_score": item["score"], "status": item["status"], "audit_recorded": True}
