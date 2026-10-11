from __future__ import annotations

from datetime import datetime
from os import getenv
from typing import Any

from sqlalchemy import JSON, DateTime, String, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))


class HackathonRecord(Base):
    __tablename__ = "hackathons"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(30))
    participants: Mapped[int] = mapped_column(default=0)
    teams: Mapped[int] = mapped_column(default=0)
    submissions: Mapped[int] = mapped_column(default=0)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_participants: Mapped[int] = mapped_column()
    max_team_size: Mapped[int] = mapped_column()
    rules: Mapped[str] = mapped_column(String(10000))
    rubric: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class TeamRecord(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(500))
    hackathon_id: Mapped[str] = mapped_column(String(80), index=True)
    leader_id: Mapped[str] = mapped_column(String(80))
    members: Mapped[list[str]] = mapped_column(JSON, default=list)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True)


class SubmissionRecord(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    team_id: Mapped[str] = mapped_column(String(80))
    hackathon_id: Mapped[str] = mapped_column(String(80), index=True)
    team_name: Mapped[str] = mapped_column(String(80))
    project_name: Mapped[str] = mapped_column(String(120))
    project_description: Mapped[str] = mapped_column(String(4000))
    problem_statement: Mapped[str] = mapped_column(String(2000))
    solution: Mapped[str] = mapped_column(String(4000))
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    github_url: Mapped[str] = mapped_column(String(2048))
    live_demo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    artifact_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30))
    score: Mapped[float | None] = mapped_column(nullable=True)
    risk: Mapped[float | None] = mapped_column(nullable=True)
    judge_score: Mapped[float | None] = mapped_column(nullable=True)
    judge_comments: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    judge_criteria: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)


class UploadRecord(Base):
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(80), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size: Mapped[int] = mapped_column()
    path: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(30))


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _database_url() -> str:
    return getenv("DATABASE_URL", "sqlite:///./hackeval-local.db").replace("postgres://", "postgresql+psycopg://", 1)


engine = create_engine(_database_url(), pool_pre_ping=True)


def init_database() -> None:
    Base.metadata.create_all(engine)


def _record_to_dict(record: object) -> dict[str, Any]:
    return {column.name: getattr(record, column.name) for column in record.__table__.columns}


def _as_datetime(value: datetime | str) -> datetime:
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def _normalize_dates(row: dict[str, Any], *fields: str) -> dict[str, Any]:
    normalized = dict(row)
    for field in fields:
        if normalized.get(field) is not None:
            normalized[field] = _as_datetime(normalized[field])
    return normalized


def load_state() -> dict[str, Any] | None:
    init_database()
    with Session(engine) as session:
        users = [_record_to_dict(row) for row in session.scalars(select(UserRecord))]
        hackathons = [_record_to_dict(row) for row in session.scalars(select(HackathonRecord))]
        teams = [_record_to_dict(row) for row in session.scalars(select(TeamRecord))]
        submissions = [_record_to_dict(row) for row in session.scalars(select(SubmissionRecord))]
        uploads = [_record_to_dict(row) for row in session.scalars(select(UploadRecord))]
        audit_logs = [_record_to_dict(row) for row in session.scalars(select(AuditLogRecord).order_by(AuditLogRecord.created_at))]
    if not any((users, hackathons, teams, submissions, uploads, audit_logs)):
        return None
    return {
        "users": {row["id"]: row for row in users},
        "hackathons": {row["id"]: row for row in hackathons},
        "teams": {row["id"]: row for row in teams},
        "submissions": {row["id"]: row for row in submissions},
        "uploads": {row["id"]: row for row in uploads},
        "audit_logs": audit_logs,
    }


def save_state(state: dict[str, Any]) -> None:
    init_database()
    with Session(engine) as session:
        for model in (UserRecord, HackathonRecord, TeamRecord, SubmissionRecord, UploadRecord, AuditLogRecord):
            session.execute(delete(model))
        session.add_all(UserRecord(**row) for row in state.get("users", {}).values())
        session.add_all(
            HackathonRecord(**_normalize_dates(row, "start_date", "end_date", "registration_deadline"))
            for row in state.get("hackathons", {}).values()
        )
        session.add_all(TeamRecord(**row) for row in state.get("teams", {}).values())
        session.add_all(SubmissionRecord(**row) for row in state.get("submissions", {}).values())
        session.add_all(UploadRecord(**row) for row in state.get("uploads", {}).values())
        session.add_all(
            AuditLogRecord(**_normalize_dates(row, "created_at"))
            for row in state.get("audit_logs", [])
        )
        session.commit()
