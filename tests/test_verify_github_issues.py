from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from global_builder_radar.cli import app
from global_builder_radar.models import CollectionResult, Opportunity, OpportunityCategory
from global_builder_radar.storage import RadarStore


def _seed_issue_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RadarStore:
    monkeypatch.setenv("GBR_DATABASE_PATH", str(tmp_path / "radar.sqlite3"))
    store = RadarStore(tmp_path / "radar.sqlite3")
    store.initialize()
    opportunities = [
        Opportunity(
            source="opire_bounties",
            category=OpportunityCategory.BOUNTY,
            external_id=str(number),
            title=f"Issue {number}",
            url=f"https://github.com/owner/repo/issues/{number}",
        )
        for number in (1, 2)
    ]
    store.record_result(CollectionResult(source="opire_bounties", opportunities=opportunities))
    return store


def _patch_client(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    transport = httpx.MockTransport(handler)

    class _Client(httpx.Client):
        def __init__(self, **kwargs):
            super().__init__(transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "Client", _Client)


def test_github_token_is_sent_when_available(tmp_path, monkeypatch) -> None:
    _seed_issue_rows(tmp_path, monkeypatch)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(200, json={"state": "open", "labels": []})

    _patch_client(monkeypatch, handler)
    result = CliRunner().invoke(app, ["verify-github-issues"])
    assert result.exit_code == 0
    assert seen == ["Bearer test-token", "Bearer test-token"]


def test_no_authorization_header_without_token(tmp_path, monkeypatch) -> None:
    _seed_issue_rows(tmp_path, monkeypatch)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    seen: list[bool] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append("Authorization" in request.headers)
        return httpx.Response(200, json={"state": "open", "labels": []})

    _patch_client(monkeypatch, handler)
    result = CliRunner().invoke(app, ["verify-github-issues"])
    assert result.exit_code == 0
    assert seen == [False, False]


@pytest.mark.parametrize("status", [403, 429])
def test_rate_limit_stops_batch_immediately(tmp_path, monkeypatch, status) -> None:
    store = _seed_issue_rows(tmp_path, monkeypatch)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(
            status,
            headers={"X-RateLimit-Reset": "4102444800"},
            json={"message": "API rate limit exceeded"},
        )

    _patch_client(monkeypatch, handler)
    result = CliRunner().invoke(app, ["verify-github-issues"])
    assert result.exit_code == 0
    # Two rows exist, but the batch stops at the first rate-limit response.
    assert calls["count"] == 1
    output = result.output.lower()
    assert "rate limit" in output
    assert "resets at" in output
    # Nothing was discarded by the interrupted run.
    assert len(store.list_opportunities()) == 2
