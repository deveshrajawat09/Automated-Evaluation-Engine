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
    """Use a configured provider when valid, otherwise return an explainable demo score."""
    criteria = rubric or DEFAULT_RUBRIC
    provider_url = getenv("AI_API_URL")
    provider_key = getenv("AI_API_KEY")
    provider_failure = ""
    if provider_url and provider_key:
        try:
            response = httpx.post(
                provider_url,
                headers={"Authorization": f"Bearer {provider_key}", "Content-Type": "application/json"},
                json={"submission": submission, "repository": repository, "rubric": criteria},
                timeout=20,
            )
            response.raise_for_status()
            result = _provider_result(response.json(), criteria)
            result["model_mode"] = "configured_provider"
            return result
        except (httpx.HTTPError, json.JSONDecodeError, TypeError, ValueError) as error:
            provider_failure = str(error)
    elif provider_url or provider_key:
        provider_failure = "AI_API_URL and AI_API_KEY must be configured together."

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
    explanation = "Scores combine the organizer rubric with repository-health signals and submitted project context. They are a transparent recommendation for human judges, not an automatic final decision."
    if provider_failure:
        explanation += f" Configured AI provider was not used: {provider_failure}"
    return asdict(EvaluationReport(
        overall_score=overall,
        criteria=reports,
        strengths=["Well-defined problem and solution narrative", "Repository health and documentation are above the expected baseline", "Technology selection supports the proposed feature set"],
        weaknesses=["Add broader automated test coverage before final judging", "Include deployment and architecture details in the pitch material"],
        recommendation=recommendation,
        explanation=explanation,
        model_mode="demo_fallback",
    ))


def _provider_result(payload: object, rubric: list[tuple[str, float]]) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("AI provider response must be a JSON object.")
    if "choices" in payload:
        choices = payload["choices"]
        if not isinstance(choices, list) or not choices:
            raise ValueError("AI provider response contains no choices.")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise ValueError("AI provider choice does not contain message content.")
        payload = json.loads(content)
    required = {"overall_score", "criteria", "strengths", "weaknesses", "recommendation", "explanation"}
    if not required.issubset(payload):
        raise ValueError("AI provider response is missing required evaluation fields.")
    if not isinstance(payload["overall_score"], (int, float)) or not 0 <= payload["overall_score"] <= 100:
        raise ValueError("AI provider overall_score must be between 0 and 100.")
    result_criteria = payload["criteria"]
    if not isinstance(result_criteria, list) or len(result_criteria) != len(rubric):
        raise ValueError("AI provider criteria must match the configured rubric.")
    for rubric_item, result_item in zip(rubric, result_criteria):
        if not isinstance(result_item, dict) or result_item.get("criterion") != rubric_item[0]:
            raise ValueError("AI provider criteria do not match the configured rubric.")
        if not isinstance(result_item.get("score"), (int, float)) or not 0 <= result_item["score"] <= 100:
            raise ValueError("AI provider criterion scores must be between 0 and 100.")
        if not isinstance(result_item.get("reason"), str) or not result_item["reason"].strip():
            raise ValueError("AI provider criterion reasons are required.")
    for field in ("strengths", "weaknesses"):
        if not isinstance(payload[field], list) or not all(isinstance(value, str) for value in payload[field]):
            raise ValueError(f"AI provider {field} must be a list of strings.")
    if not all(isinstance(payload[field], str) and payload[field].strip() for field in ("recommendation", "explanation")):
        raise ValueError("AI provider recommendation and explanation are required.")
    return {key: payload[key] for key in required}
