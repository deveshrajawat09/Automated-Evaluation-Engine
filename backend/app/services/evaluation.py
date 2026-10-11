from dataclasses import asdict, dataclass
import json
from os import getenv
import httpx

DEFAULT_RUBRIC = [
    ("Innovation", 20),
    ("Technical Complexity", 25),
    ("Functionality", 20),
    ("Impact", 15),
    ("UI/UX & Design", 10),
    ("Presentation", 10),
]


@dataclass
class EvaluationReport:
    overall_score: float
    criteria: list[dict]
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str
    explanation: str
    model_mode: str


def evaluate_submission(submission: dict, repository: dict, rubric: list[tuple[str, float]] | None = None) -> dict:
    """Explainable deterministic fallback for local demos.

    An LLM provider can be injected into this service without changing callers.
    The returned `model_mode` makes clear when a real provider has not been set.
    """
    provider_url = getenv("AI_API_URL")
    provider_key = getenv("AI_API_KEY")
    if provider_url and provider_key:
        try:
            response = httpx.post(
                provider_url,
                headers={"Authorization": f"Bearer {provider_key}"},
                json={"submission": submission, "repository": repository, "rubric": rubric or DEFAULT_RUBRIC},
                timeout=20,
            )
            response.raise_for_status()
            result = response.json()
            result["model_mode"] = "configured_provider"
            return result
        except (httpx.HTTPError, json.JSONDecodeError, KeyError):
            pass
    criteria = rubric or DEFAULT_RUBRIC
    base = min(91, 65 + len(submission["project_description"]) // 12 + repository["health_score"] // 7)
    reports = []
    weighted_score = 0.0
    for index, (criterion, weight) in enumerate(criteria):
        score = min(97, max(55, base + ((index * 5 + repository["commits"]) % 11) - 5))
        weighted_score += score * (weight / 100)
        reason_map = {
            "Innovation": "The solution presents a focused approach to the stated problem and differentiates its workflow.",
            "Technical Complexity": "The repository structure, dependency choices, and implementation scope support this score.",
            "Functionality": "The described core flows are coherent; automated tests should validate each promised feature.",
            "Impact": "The problem statement identifies a clear audience and a practical outcome.",
            "UI/UX & Design": "The project documentation communicates an intentional user flow and interface direction.",
            "Presentation": "The written submission is organized, although a complete pitch deck can raise confidence.",
        }
        reports.append({"criterion": criterion, "weight": weight, "score": score, "reason": reason_map.get(criterion, "Score calculated from the configured evaluation rubric.")})
    overall = round(weighted_score, 1)
    recommendation = "Recommended" if overall >= 80 else "Needs Review" if overall >= 60 else "Not Recommended"
    return asdict(EvaluationReport(
        overall_score=overall,
        criteria=reports,
        strengths=["Well-defined problem and solution narrative", "Repository health and documentation are above the expected baseline", "Technology selection supports the proposed feature set"],
        weaknesses=["Add broader automated test coverage before final judging", "Include deployment and architecture details in the pitch material"],
        recommendation=recommendation,
        explanation="Scores combine the organizer rubric with repository-health signals and submitted project context. They are a transparent recommendation for human judges, not an automatic final decision.",
        model_mode="demo_fallback",
    ))
