from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from app.core.security import hash_password
from app.database import load_state, save_state as save_database_state

DATA_FILE = Path(__file__).resolve().parent.parent / "hackeval-data.json"

users: dict[str, dict] = {
    "participant-user": {
        "id": "participant-user",
        "name": "Participant User",
        "email": "participant@hackeval.ai",
        "role": "PARTICIPANT",
        "password_hash": hash_password("Participant123!"),
    },
    "admin-host-user": {
        "id": "admin-host-user",
        "name": "Admin Host",
        "email": "host@hackeval.ai",
        "role": "ORGANIZER",
        "password_hash": hash_password("HostAdmin123!"),
    },
    "judge-user": {
        "id": "judge-user",
        "name": "Judge User",
        "email": "judge@hackeval.ai",
        "role": "JUDGE",
        "password_hash": hash_password("Judge123!"),
    },
    "admin-user": {
        "id": "admin-user",
        "name": "Platform Admin",
        "email": "admin@hackeval.ai",
        "role": "ADMIN",
        "password_hash": hash_password("Admin123!"),
    },
}

hackathons: dict[str, dict] = {}
teams: dict[str, dict] = {}
submissions: dict[str, dict] = {}
uploads: dict[str, dict] = {}
audit_logs: list[dict] = []


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value: {type(value).__name__}")


def save_store() -> None:
    payload = {"hackathons": hackathons, "teams": teams, "submissions": submissions, "uploads": uploads, "audit_logs": audit_logs}
    database_url = __import__("os").getenv("DATABASE_URL", "")
    if database_url.startswith(("postgres://", "postgresql://", "postgresql+")):
        save_database_state(json.loads(json.dumps(payload, default=_json_default)))
    else:
        DATA_FILE.write_text(json.dumps(payload, default=_json_default, indent=2), encoding="utf-8")


def load_store() -> None:
    database_url = __import__("os").getenv("DATABASE_URL", "")
    payload = load_state() if database_url.startswith(("postgres://", "postgresql://", "postgresql+")) else (
        json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else None
    )
    if not payload:
        return
    hackathons.update(payload.get("hackathons", {}))
    teams.update(payload.get("teams", {}))
    submissions.update(payload.get("submissions", {}))
    uploads.update(payload.get("uploads", {}))
    audit_logs.extend(payload.get("audit_logs", []))


load_store()


def audit(actor_id: str, action: str, entity_type: str, entity_id: str, details: str) -> None:
    audit_logs.append({"id": str(uuid4()), "actor_id": actor_id, "action": action, "entity_type": entity_type, "entity_id": entity_id, "details": details, "created_at": datetime.now(timezone.utc)})
    save_store()
