import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.routers.dependencies import require_roles
from app.schemas import Role
from app.store import audit_logs, hackathons, submissions

router = APIRouter(tags=["Dashboards"])


@router.get("/leaderboard/{hackathon_id}")
def leaderboard(hackathon_id: str) -> dict:
    if hackathon_id not in hackathons:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    entries = [item for item in submissions.values() if item["hackathon_id"] == hackathon_id and item.get("score") is not None]
    entries.sort(key=lambda item: item["score"], reverse=True)
    return {"hackathon": hackathons[hackathon_id]["name"], "entries": [{"rank": index, "team": item["team_name"], "project": item["project_name"], "score": item["score"], "risk": item["risk"], "status": item["status"]} for index, item in enumerate(entries, start=1)]}


@router.get("/dashboard/organizer")
def organizer_dashboard(user: Annotated[dict, Depends(require_roles(Role.ORGANIZER, Role.ADMIN))]) -> dict:
    evaluated = [item for item in submissions.values() if item["status"] in {"EVALUATED", "ACCEPTED", "FLAGGED"}]
    scores = [float(item["score"]) for item in evaluated if item.get("score") is not None]
    return {"total_participants": sum(item["participants"] for item in hackathons.values()), "total_teams": sum(item["teams"] for item in hackathons.values()), "total_submissions": len(submissions), "evaluated_projects": len(evaluated), "flagged_projects": len([item for item in submissions.values() if item["status"] == "FLAGGED"]), "average_score": round(sum(scores) / len(scores), 1) if scores else 0, "evaluation_progress": 72, "recent_audit_logs": audit_logs[-10:]}


@router.get("/dashboard/judge")
def judge_dashboard(user: Annotated[dict, Depends(require_roles(Role.JUDGE, Role.ADMIN))]) -> dict:
    assigned = [item for item in submissions.values() if item["status"] in {"UNDER_REVIEW", "FLAGGED"}]
    return {"assigned_submissions": assigned, "pending_count": len(assigned), "message": "AI scores are recommendations; submit a manual evaluation for any final decision."}


@router.get("/dashboard/admin")
def admin_dashboard(user: Annotated[dict, Depends(require_roles(Role.ADMIN))]) -> dict:
    return {
        "users": len(__import__("app.store", fromlist=["users"]).users),
        "hackathons": len(hackathons),
        "teams": sum(item["teams"] for item in hackathons.values()),
        "submissions": len(submissions),
        "flagged_submissions": len([item for item in submissions.values() if item["status"] == "FLAGGED"]),
        "audit_events": len(audit_logs),
    }


@router.get("/exports/{hackathon_id}.csv")
def export_results(hackathon_id: str, user: Annotated[dict, Depends(require_roles(Role.ORGANIZER, Role.ADMIN))]) -> StreamingResponse:
    if hackathon_id not in hackathons:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["rank", "team", "project", "score", "risk", "status"])
    writer.writeheader()
    rows = [item for item in submissions.values() if item["hackathon_id"] == hackathon_id]
    rows.sort(key=lambda item: item.get("score") or 0, reverse=True)
    for rank, item in enumerate(rows, start=1):
        writer.writerow({"rank": rank, "team": item["team_name"], "project": item["project_name"], "score": item.get("score"), "risk": item.get("risk"), "status": item["status"]})
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{hackathons[hackathon_id]["name"]}-results.csv"'})
