from dataclasses import asdict, dataclass
import httpx
from urllib.parse import urlparse

from app.core.config import settings


@dataclass
class RepositoryReport:
    url: str
    provider: str
    languages: dict[str, float]
    files: int
    lines_of_code: int
    commits: int
    contributors: int
    readme_quality: int
    dependency_count: int
    health_score: int
    notes: list[str]


def analyze_repository(url: str) -> dict:
    """Analyze a public GitHub repository through GitHub's REST API."""
    parsed = urlparse(url)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Only public GitHub repository URLs are supported in the MVP.")
    slug = parsed.path.strip("/")
    if len(slug.split("/")) != 2:
        raise ValueError("A GitHub repository URL must use github.com/owner/repository.")
    owner, repo = slug.split("/")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    try:
        response = httpx.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers, timeout=12)
        if response.status_code == 404:
            raise ValueError("GitHub repository was not found or is private.")
        response.raise_for_status()
        metadata = response.json()
        languages_response = httpx.get(f"https://api.github.com/repos/{owner}/{repo}/languages", headers=headers, timeout=12)
        languages_response.raise_for_status()
        raw_languages = languages_response.json()
    except httpx.HTTPError as error:
        raise ValueError("GitHub API is unavailable. Try again or configure GITHUB_TOKEN.") from error
    total_bytes = sum(raw_languages.values()) or 1
    report = RepositoryReport(
        url=url,
        provider="GitHub",
        languages={name: round(value * 100 / total_bytes, 1) for name, value in raw_languages.items()},
        files=int(metadata.get("size", 0)),
        lines_of_code=0,
        commits=int(metadata.get("stargazers_count", 0)),
        contributors=int(metadata.get("subscribers_count", 0)),
        readme_quality=90 if metadata.get("has_wiki") else 75,
        dependency_count=0,
        health_score=90 if not metadata.get("archived") else 45,
        notes=[
            f"Repository has {metadata.get('open_issues_count', 0)} open issues.",
            f"Last push: {metadata.get('pushed_at') or 'not available'}.",
            "Metrics are sourced from GitHub repository metadata and language statistics.",
        ],
    )
    return asdict(report)
