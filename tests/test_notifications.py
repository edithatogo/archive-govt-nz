"""Unit tests for automated webhook notifications."""

import asyncio
from typing import Any

import httpx

from archive_govt_nz.notifications import (
    HarvestNotificationPayload,
    dispatch_webhook,
    format_discord_payload,
    format_slack_payload,
)


def test_format_slack_payload() -> None:
    """Validate Slack BlockKit structure."""
    payload = HarvestNotificationPayload(
        status="success",
        discovered_datasets=100,
        evaluated_resources=250,
        successful_captures=200,
        broken_urls_count=5,
        parquet_derivatives_count=180,
        hf_repo_url="https://huggingface.co/datasets/edithatogo/archive-govt-nz-global",
        completed_at="2026-08-16T12:00:00Z",
        duration_seconds=42.5,
    )
    slack = format_slack_payload(payload)
    assert "blocks" in slack
    assert len(slack["blocks"]) == 3
    assert "100" in slack["blocks"][1]["fields"][0]["text"]
    assert "Hugging Face" in slack["blocks"][1]["fields"][5]["text"]


def test_format_slack_payload_without_hf_url() -> None:
    """Validate Slack BlockKit fallback when HF repo is omitted."""
    payload = HarvestNotificationPayload(
        status="warning",
        discovered_datasets=0,
        evaluated_resources=0,
        successful_captures=0,
        broken_urls_count=0,
        parquet_derivatives_count=0,
        hf_repo_url=None,
        completed_at="2026-08-16T12:00:00Z",
    )
    slack = format_slack_payload(payload)
    assert "N/A" in slack["blocks"][1]["fields"][5]["text"]


def test_format_discord_payload() -> None:
    """Validate Discord embed structure."""
    payload = HarvestNotificationPayload(
        status="warning",
        discovered_datasets=50,
        evaluated_resources=100,
        successful_captures=80,
        broken_urls_count=12,
        parquet_derivatives_count=70,
        hf_repo_url="https://huggingface.co/datasets/edithatogo/archive-govt-nz-global",
        completed_at="2026-08-16T12:00:00Z",
        duration_seconds=15.0,
    )
    discord = format_discord_payload(payload)
    assert "embeds" in discord
    assert discord["embeds"][0]["color"] == 0xE67E22
    assert len(discord["embeds"][0]["fields"]) == 6


def test_dispatch_webhook_slack_endpoint() -> None:
    """Validate webhook dispatch to Slack URL."""
    payload = HarvestNotificationPayload(
        status="success",
        discovered_datasets=10,
        evaluated_resources=20,
        successful_captures=18,
        broken_urls_count=1,
        parquet_derivatives_count=15,
        hf_repo_url="https://huggingface.co/datasets/edithatogo/archive-govt-nz-global",
        completed_at="2026-08-16T12:00:00Z",
        duration_seconds=5.0,
    )

    observed: list[dict[str, Any]] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        observed.append({"url": str(request.url), "body": request.read()})
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(mock_handler)
    success = asyncio.run(
        dispatch_webhook(
            "https://hooks.slack.com/services/test",
            payload,
            transport=transport,
        )
    )
    assert success is True
    assert len(observed) == 1
    assert "hooks.slack.com" in observed[0]["url"]


def test_dispatch_webhook_discord_and_generic() -> None:
    """Validate webhook dispatch to Discord and generic HTTP webhooks."""
    payload = HarvestNotificationPayload(
        status="success",
        discovered_datasets=10,
        evaluated_resources=20,
        successful_captures=18,
        broken_urls_count=1,
        parquet_derivatives_count=15,
        hf_repo_url=None,
        completed_at="2026-08-16T12:00:00Z",
        duration_seconds=5.0,
    )

    observed: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        observed.append(str(request.url))
        return httpx.Response(204)

    transport = httpx.MockTransport(mock_handler)

    success_discord = asyncio.run(
        dispatch_webhook(
            "https://discord.com/api/webhooks/123/abc",
            payload,
            service="discord",
            transport=transport,
        )
    )
    assert success_discord is True

    success_generic = asyncio.run(
        dispatch_webhook(
            "https://api.example.com/harvest-webhook",
            payload,
            service="generic",
            transport=transport,
        )
    )
    assert success_generic is True
    assert len(observed) == 2
