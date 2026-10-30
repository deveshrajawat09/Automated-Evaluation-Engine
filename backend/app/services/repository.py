from dataclasses import asdict, dataclass
import base64
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
    api_root = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        response = httpx.get(api_root, headers=headers, timeout=12)
        if response.status_code == 404:
            raise ValueError("GitHub repository was not found or is private.")
        response.raise_for_status()
        metadata = response.json()
        languages_response = httpx.get(f"{api_root}/languages", headers=headers, timeout=12)
        languages_response.raise_for_status()
        raw_languages = languages_response.json()
        tree_response = httpx.get(
            f"{api_root}/git/trees/{metadata.get('default_branch', 'main')}",
            params={"recursive": "1"},
            headers=headers,
            timeout=20,
        )
        tree_response.raise_for_status()
        tree_items = tree_response.json().get("tree", [])
        files = [item for item in tree_items if item.get("type") == "blob"]
        commits_response = httpx.get(
            f"{api_root}/commits",
            params={"per_page": 1},
            headers=headers,
            timeout=12,
        )
        commits_response.raise_for_status()
        commits = _total_from_link_header(commits_response) or len(commits_response.json())
        contributors_response = httpx.get(
            f"{api_root}/contributors",
            params={"anon": "true", "per_page": 100},
            headers=headers,
            timeout=12,
        )
        contributors_response.raise_for_status()
        contributors = _total_from_link_header(contributors_response) or len(contributors_response.json())
        readme_response = httpx.get(f"{api_root}/readme", headers=headers, timeout=12)
        readme_response.raise_for_status()
        readme_quality = _readme_quality(readme_response.json())
    except httpx.HTTPError as error:
        raise ValueError("GitHub API is unavailable. Try again or configure GITHUB_TOKEN.") from error
    total_bytes = sum(raw_languages.values()) or 1
    dependency_files = {
        "package.json", "requirements.txt", "pyproject.toml", "pom.xml",
        "build.gradle", "go.mod", "Cargo.toml", "Gemfile",
    }
    dependency_count = sum(
        1 for item in files if item.get("path", "").rsplit("/", 1)[-1] in dependency_files
    )
    report = RepositoryReport(
        url=url,
        provider="GitHub",
        languages={name: round(value * 100 / total_bytes, 1) for name, value in raw_languages.items()},
        files=len(files),
        lines_of_code=0,
        commits=commits,
        contributors=contributors,
        readme_quality=readme_quality,
        dependency_count=dependency_count,
        health_score=_health_score(metadata, commits, contributors, readme_quality),
        notes=[
            f"Repository has {metadata.get('open_issues_count', 0)} open issues.",
            f"Last push: {metadata.get('pushed_at') or 'not available'}.",
            f"GitHub reports {len(files)} tracked files, {commits} commits, and {contributors} contributors.",
            "Lines of code are not reported because the GitHub API does not expose a repository-wide LOC metric.",
        ],
    )
    return asdict(report)


def _total_from_link_header(response: httpx.Response) -> int:
    link = getattr(response, "headers", {}).get("link", "")
    for part in link.split(","):
        if 'rel="last"' in part and "page=" in part:
            return int(part.split("page=")[1].split(">")[0].split("&")[0])
    return 0


def _readme_quality(payload: dict) -> int:
    encoded = payload.get("content", "")
    if not encoded:
        return 0
    try:
        content = base64.b64decode(encoded).decode("utf-8", errors="ignore")
    except (ValueError, UnicodeDecodeError):
        return 0
    score = 25
    score += min(25, len(content) // 400)
    score += 15 if "## " in content else 0
    score += 15 if "install" in content.lower() or "usage" in content.lower() else 0
    score += 10 if "license" in content.lower() else 0
    score += 10 if "http" in content.lower() else 0
    return min(100, score)


def _health_score(metadata: dict, commits: int, contributors: int, readme_quality: int) -> int:
    score = 35
    score += min(25, commits // 10)
    score += min(15, contributors * 3)
    score += readme_quality // 10
    score += 10 if not metadata.get("archived") else -25
    score -= min(10, int(metadata.get("open_issues_count", 0)) // 20)
    return max(0, min(100, score))
