from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.routers.dependencies import require_roles
from app.schemas import HackathonCreate, HackathonOut, Role, TeamCreate
from app.store import audit, hackathons, save_store, teams

router = APIRouter(prefix="/hackathons", tags=["Hackathons"])


@router.get("", response_model=list[HackathonOut])
def list_hackathons() -> list[dict]:
    return list(hackathons.values())


@router.get("/{hackathon_id}", response_model=HackathonOut)
def get_hackathon(hackathon_id: str) -> dict:
    item = hackathons.get(hackathon_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return item


@router.post("", response_model=HackathonOut, status_code=status.HTTP_201_CREATED)
def create_hackathon(payload: HackathonCreate, user: Annotated[dict, Depends(require_roles(Role.ORGANIZER, Role.ADMIN))]) -> dict:
    if payload.end_date <= payload.start_date or payload.registration_deadline > payload.start_date:
        raise HTTPException(status_code=422, detail="Check that the registration deadline precedes the start and end date")
    item = {"id": str(uuid4()), "name": payload.name, "description": payload.description, "status": "UPCOMING", "participants": 0, "teams": 0, "submissions": 0, "start_date": payload.start_date, "end_date": payload.end_date, "registration_deadline": payload.registration_deadline, "max_participants": payload.max_participants, "max_team_size": payload.max_team_size, "rules": payload.rules, "rubric": [row.model_dump() for row in payload.rubric]}
    hackathons[item["id"]] = item
    save_store()
    audit(user["id"], "CREATE", "hackathon", item["id"], f"Created {item['name']}")
    return item


@router.post("/{hackathon_id}/teams", status_code=status.HTTP_201_CREATED)
def create_team(hackathon_id: str, payload: TeamCreate, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT))]) -> dict:
    if hackathon_id != payload.hackathon_id or hackathon_id not in hackathons:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    item = {"id": str(uuid4()), "name": payload.name, "description": payload.description, "hackathon_id": hackathon_id, "leader_id": user["id"], "members": [user["id"]], "invite_code": uuid4().hex[:8].upper()}
    teams[item["id"]] = item
    hackathons[hackathon_id]["teams"] += 1
    save_store()
    audit(user["id"], "CREATE", "team", item["id"], f"Created team {item['name']}")
    return item


@router.get("/{hackathon_id}/teams")
def list_teams(hackathon_id: str) -> list[dict]:
    return [team for team in teams.values() if team["hackathon_id"] == hackathon_id]
