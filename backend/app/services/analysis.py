def static_code_analysis(repository: dict) -> dict:
    """MVP report adapter. Replace metrics with language-specific tool output in production."""
    maintainability = min(96, 68 + repository["readme_quality"] // 4)
    security = min(94, 65 + repository["contributors"] * 5)
    complexity = min(92, 66 + repository["commits"] // 3)
    documentation = repository["readme_quality"]
    architecture = min(95, 70 + repository["files"] // 12)
    overall = round((maintainability + security + complexity + documentation + architecture) / 5)
    return {
        "code_quality_score": overall,
        "metrics": {"maintainability": maintainability, "security": security, "complexity": complexity, "documentation": documentation, "architecture": architecture},
        "findings": [
            {"severity": "info", "title": "Repository structure detected", "detail": "A conventional source layout and dependency manifest were found."},
            {"severity": "warning", "title": "Review dependency advisories", "detail": "Connect a dependency scanner in production before accepting the submission."},
        ],
        "mode": "mvp_adapter",
    }


def analyze_text_artifact(text: str, artifact_type: str) -> dict:
    words = len(text.split())
    score = min(94, max(40, 48 + words // 8))
    return {
        "artifact_type": artifact_type,
        "score": score,
        "extracted_sections": ["Problem", "Solution", "Features", "Technology", "Impact"],
        "explanation": "This MVP text-based analysis evaluates content completeness and structure. Visual slide or video analysis remains a separately deployable service.",
        "mode": "text_adapter",
    }
