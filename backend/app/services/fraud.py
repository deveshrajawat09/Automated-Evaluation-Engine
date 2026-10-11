from dataclasses import asdict, dataclass


@dataclass
class FraudReport:
    overall_risk: int
    risk_level: str
    similarity_risk: int
    commit_anomaly: int
    repository_age_signal: int
    submission_consistency: int
    reasons: list[str]
    human_review_required: bool


def create_fraud_report(repository: dict, project_text: str) -> dict:
    signal = (repository["commits"] * 3 + len(project_text)) % 28
    similarity = 18 + signal
    commit_anomaly = max(8, 42 - repository["commits"])
    repository_age = max(5, 45 - repository["contributors"] * 7)
    consistency = 16 + len(project_text) % 24
    overall = round((similarity * .4) + (commit_anomaly * .2) + (repository_age * .15) + (consistency * .25))
    level = "HIGH" if overall >= 65 else "MEDIUM" if overall >= 35 else "LOW"
    reasons = [
        "Risk is a review signal based on repository and submission patterns, not a plagiarism decision.",
        "Commit activity and repository structure are available for judge review.",
    ]
    if similarity >= 35:
        reasons.append("Token/structure similarity warrants comparison with approved reference repositories.")
    return asdict(FraudReport(overall, level, similarity, commit_anomaly, repository_age, consistency, reasons, overall >= 35))
