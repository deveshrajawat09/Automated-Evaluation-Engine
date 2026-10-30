from app.services.evaluation import evaluate_submission
from app.services.fraud import create_fraud_report
from app.services.repository import analyze_repository
import base64


class FakeResponse:
    def __init__(self, body, headers=None):
        self.body = body
        self.status_code = 200
        self.headers = headers or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


def fake_github_get(url, **kwargs):
    if url.endswith("/languages"):
        return FakeResponse({"Python": 800, "TypeScript": 200})
    if "/git/trees/" in url:
        return FakeResponse({"tree": [{"type": "blob", "path": "README.md"}, {"type": "blob", "path": "requirements.txt"}]})
    if url.endswith("/commits"):
        return FakeResponse([{"sha": "abc"}], {"link": '<https://api.github.com/repos/example/project/commits?page=7>; rel="last"'})
    if url.endswith("/contributors"):
        return FakeResponse([{"login": "one"}, {"login": "two"}])
    if url.endswith("/readme"):
        readme = "# Project\n\n## Install\n\nRun the app.\n\n## Usage\n\nhttps://example.com\n"
        return FakeResponse({"content": base64.b64encode(readme.encode()).decode()})
    return FakeResponse({"default_branch": "main", "archived": False, "open_issues_count": 1, "pushed_at": "2025-01-01T00:00:00Z"})


def test_repository_report_is_explainable(monkeypatch):
    monkeypatch.setattr("app.services.repository.httpx.get", fake_github_get)
    report = analyze_repository("https://github.com/example/project")
    assert 0 <= report["health_score"] <= 100
    assert report["notes"]
    assert report["files"] == 2
    assert report["commits"] == 7
    assert report["contributors"] == 2
    assert report["dependency_count"] == 1


def test_evaluation_and_risk_are_bounded(monkeypatch):
    monkeypatch.setattr("app.services.repository.httpx.get", fake_github_get)
    repository = analyze_repository("https://github.com/example/project")
    submission = {"project_description": "A sufficiently detailed project description that explains the solution and the expected outcomes."}
    evaluation = evaluate_submission(submission, repository)
    fraud = create_fraud_report(repository, submission["project_description"])
    assert 0 <= evaluation["overall_score"] <= 100
    assert fraud["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


def test_configured_ai_provider_response_is_validated(monkeypatch):
    monkeypatch.setenv("AI_API_URL", "https://ai.example/evaluate")
    monkeypatch.setenv("AI_API_KEY", "secret")
    payload = {
        "overall_score": 84,
        "criteria": [
            {"criterion": name, "weight": weight, "score": 84, "reason": "Clear evidence in the submission."}
            for name, weight in [
                ("Innovation", 20), ("Technical Complexity", 25), ("Functionality", 20),
                ("Impact", 15), ("UI/UX & Design", 10), ("Presentation", 10),
            ]
        ],
        "strengths": ["Clear scope"],
        "weaknesses": ["Needs more tests"],
        "recommendation": "Recommended",
        "explanation": "The evidence supports the score.",
    }
    monkeypatch.setattr("app.services.evaluation.httpx.post", lambda *args, **kwargs: FakeResponse(payload))
    result = evaluate_submission({"project_description": "Detailed submission"}, {"health_score": 85, "commits": 10})
    assert result["model_mode"] == "configured_provider"
    assert result["overall_score"] == 84


def test_invalid_ai_provider_falls_back_explicitly(monkeypatch):
    monkeypatch.setenv("AI_API_URL", "https://ai.example/evaluate")
    monkeypatch.setenv("AI_API_KEY", "secret")
    monkeypatch.setattr("app.services.evaluation.httpx.post", lambda *args, **kwargs: FakeResponse({"overall_score": 120}))
    result = evaluate_submission({"project_description": "Detailed submission"}, {"health_score": 85, "commits": 10})
    assert result["model_mode"] == "demo_fallback"
    assert "Configured AI provider was not used" in result["explanation"]
