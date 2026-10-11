from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.routers.dependencies import require_roles
from app.schemas import Role, TeamCreate, TeamJoin
from app.store import audit, hackathons, save_store, teams

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("")
def list_teams(user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT, Role.ORGANIZER, Role.JUDGE, Role.ADMIN))]) -> list[dict]:
    if user["role"] == Role.PARTICIPANT:
        return [team for team in teams.values() if user["id"] in team.get("members", [])]
    return list(teams.values())


@router.get("/{team_id}")
def get_team(team_id: str) -> dict:
    team = teams.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT))]) -> dict:
    if payload.hackathon_id not in hackathons:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    team = {"id": str(uuid4()), "name": payload.name, "description": payload.description, "hackathon_id": payload.hackathon_id, "leader_id": user["id"], "members": [user["id"]], "invite_code": uuid4().hex[:8].upper()}
    teams[team["id"]] = team
    hackathons[payload.hackathon_id]["teams"] += 1
    save_store()
    audit(user["id"], "CREATE", "team", team["id"], f"Created team {team['name']}")
    return team


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(team_id: str, member_id: str, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT))]) -> dict:
    team = teams.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if user["id"] != team["leader_id"]:
        raise HTTPException(status_code=403, detail="Only the team leader can invite members")
    if member_id in team["members"]:
        raise HTTPException(status_code=409, detail="Member is already in the team")
    maximum = hackathons[team["hackathon_id"]]["max_team_size"]
    if len(team["members"]) >= maximum:
        raise HTTPException(status_code=422, detail="Team has reached its maximum size")
    team["members"].append(member_id)
    save_store()
    audit(user["id"], "ADD_MEMBER", "team", team_id, f"Added member {member_id}")
    return team


@router.post("/join", status_code=status.HTTP_200_OK)
def join_team(payload: TeamJoin, user: Annotated[dict, Depends(require_roles(Role.PARTICIPANT))]) -> dict:
    team = next((item for item in teams.values() if item["invite_code"].lower() == payload.invite_code.lower()), None)
    if not team:
        raise HTTPException(status_code=404, detail="Invalid team invite code")
    if user["id"] in team["members"]:
        return team
    maximum = hackathons[team["hackathon_id"]]["max_team_size"]
    if len(team["members"]) >= maximum:
        raise HTTPException(status_code=422, detail="Team has reached its maximum size")
    team["members"].append(user["id"])
    hackathons[team["hackathon_id"]]["participants"] += 1
    save_store()
    audit(user["id"], "JOIN", "team", team["id"], f"Joined team {team['name']}")
    return team
