from app.services.evaluation import evaluate_submission
from app.services.fraud import create_fraud_report
from app.services.repository import analyze_repository


class FakeResponse:
    def __init__(self, body):
        self.body = body
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


def fake_github_get(url, **kwargs):
    if url.endswith("/languages"):
        return FakeResponse({"Python": 800, "TypeScript": 200})
    return FakeResponse({"size": 42, "stargazers_count": 7, "subscribers_count": 3, "has_wiki": True, "archived": False, "open_issues_count": 1, "pushed_at": "2025-01-01T00:00:00Z"})


def test_repository_report_is_explainable(monkeypatch):
    monkeypatch.setattr("app.services.repository.httpx.get", fake_github_get)
    report = analyze_repository("https://github.com/example/project")
    assert report["health_score"] >= 78
    assert report["notes"]


def test_evaluation_and_risk_are_bounded(monkeypatch):
    monkeypatch.setattr("app.services.repository.httpx.get", fake_github_get)
    repository = analyze_repository("https://github.com/example/project")
    submission = {"project_description": "A sufficiently detailed project description that explains the solution and the expected outcomes."}
    evaluation = evaluate_submission(submission, repository)
    fraud = create_fraud_report(repository, submission["project_description"])
    assert 0 <= evaluation["overall_score"] <= 100
    assert fraud["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
