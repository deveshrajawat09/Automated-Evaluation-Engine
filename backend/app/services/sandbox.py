"""Safe adapter for an external, isolated code-runner service.

This module never invokes a shell, Docker daemon, or participant code.  Deploy a
separate runner service with rootless containers, a read-only filesystem, no
network, CPU/memory quotas, and a short timeout; then point SANDBOX_RUNNER_URL
at that trusted service.
"""
from os import getenv

import httpx


class SandboxUnavailable(RuntimeError):
    pass


async def run_in_isolated_runner(language: str, source_archive_id: str, tests: list[dict]) -> dict:
    runner_url = getenv("SANDBOX_RUNNER_URL")
    if not runner_url:
        raise SandboxUnavailable(
            "Sandbox execution is not configured. This API intentionally refuses to execute untrusted code on the backend host."
        )
    payload = {"language": language, "source_archive_id": source_archive_id, "tests": tests}
    try:
        headers = {"X-Runner-Token": getenv("SANDBOX_RUNNER_TOKEN", "")}
        if getenv("APP_ENV", "development").lower() in {"production", "staging"}:
            from google.auth.transport.requests import Request
            from google.oauth2.id_token import fetch_id_token

            headers["Authorization"] = f"Bearer {fetch_id_token(Request(), runner_url)}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{runner_url.rstrip('/')}/runs",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as error:
        raise SandboxUnavailable(f"Sandbox runner request failed: {error}") from error
