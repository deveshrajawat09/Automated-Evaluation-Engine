from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class Role(str, Enum):
    PARTICIPANT = "PARTICIPANT"
    ORGANIZER = "ORGANIZER"
    JUDGE = "JUDGE"
    ADMIN = "ADMIN"


class HackathonStatus(str, Enum):
    UPCOMING = "UPCOMING"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    ONGOING = "ONGOING"
    SUBMISSION_CLOSED = "SUBMISSION_CLOSED"
    EVALUATION = "EVALUATION"
    COMPLETED = "COMPLETED"


class SubmissionStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    EVALUATED = "EVALUATED"
    FLAGGED = "FLAGGED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.PARTICIPANT


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    role: Role


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role


class RubricItem(BaseModel):
    criterion: str = Field(min_length=2, max_length=80)
    weight: float = Field(gt=0, le=100)


class HackathonCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    start_date: datetime
    end_date: datetime
    registration_deadline: datetime
    max_participants: int = Field(gt=1, le=100_000)
    max_team_size: int = Field(ge=1, le=20)
    rules: str = Field(min_length=3, max_length=10_000)
    rubric: list[RubricItem]


class HackathonOut(BaseModel):
    id: str
    name: str
    description: str
    status: HackathonStatus
    participants: int
    teams: int
    submissions: int
    start_date: datetime
    end_date: datetime


class TeamCreate(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=5, max_length=500)
    hackathon_id: str


class TeamJoin(BaseModel):
    invite_code: str = Field(min_length=4, max_length=20)


class SubmissionCreate(BaseModel):
    team_id: str
    hackathon_id: str
    project_name: str = Field(min_length=3, max_length=120)
    project_description: str = Field(min_length=30, max_length=4000)
    problem_statement: str = Field(min_length=10, max_length=2000)
    solution: str = Field(min_length=10, max_length=4000)
    technologies: list[str] = Field(min_length=1, max_length=15)
    github_url: HttpUrl
    live_demo_url: HttpUrl | None = None
    artifact_ids: list[str] = Field(default_factory=list, max_length=10)


class JudgeEvaluation(BaseModel):
    submission_id: str
    score: float = Field(ge=0, le=100)
    comments: str = Field(min_length=5, max_length=2000)
    approved: bool
    criteria: dict[str, float] = Field(default_factory=dict)


class RepositoryAnalysisRequest(BaseModel):
    github_url: HttpUrl


class EvaluationRequest(BaseModel):
    submission_id: str
    rubric: list[RubricItem] | None = None


class SandboxRunRequest(BaseModel):
    language: Literal["python", "javascript", "java", "cpp"]
    source_archive_id: str = Field(min_length=3, max_length=200)
    tests: list[dict] = Field(min_length=1, max_length=50)


class TextAnalysisRequest(BaseModel):
    text: str = Field(min_length=20, max_length=100_000)
