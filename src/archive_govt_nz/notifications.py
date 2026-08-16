"""Automated webhook notification engine for preservation harvest pipelines."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import httpx

_DISCORD_SUCCESS_COLOR = 0x2ECC71
_DISCORD_WARNING_COLOR = 0xE67E22


@dataclass(frozen=True, slots=True)
class HarvestNotificationPayload:
    """Structured metrics for a completed preservation harvest run."""

    status: str
    discovered_datasets: int
    evaluated_resources: int
    successful_captures: int
    broken_urls_count: int
    parquet_derivatives_count: int
    hf_repo_url: str | None
    completed_at: str
    duration_seconds: float = 0.0


def format_slack_payload(payload: HarvestNotificationPayload) -> dict[str, Any]:
    """Format rich Slack BlockKit payload."""
    status_emoji = "✅" if payload.status == "success" else "⚠️"
    header_text = (
        f"{status_emoji} NZ Government Preservation Harvest: {payload.status.upper()}"
    )

    hf_link = (
        f"<{payload.hf_repo_url}|Hugging Face Dataset>"
        if payload.hf_repo_url
        else "N/A"
    )

    return {
        "text": header_text,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header_text},
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*Datasets Discovered:*\n{payload.discovered_datasets}"
                        ),
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*Resources Evaluated:*\n{payload.evaluated_resources}"
                        ),
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*Captured into CAS:*\n{payload.successful_captures}"
                        ),
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*Parquet Derivatives:*\n"
                            f"{payload.parquet_derivatives_count}"
                        ),
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*Broken URLs Triangulated:*\n{payload.broken_urls_count}"
                        ),
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Hugging Face Repository:*\n{hf_link}",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"Completed at: `{payload.completed_at}` | "
                            f"Duration: `{payload.duration_seconds:.1f}s`"
                        ),
                    }
                ],
            },
        ],
    }


def format_discord_payload(payload: HarvestNotificationPayload) -> dict[str, Any]:
    """Format rich Discord embed payload."""
    color = (
        _DISCORD_SUCCESS_COLOR
        if payload.status == "success"
        else _DISCORD_WARNING_COLOR
    )

    fields = [
        {
            "name": "Datasets Discovered",
            "value": str(payload.discovered_datasets),
            "inline": True,
        },
        {
            "name": "Resources Evaluated",
            "value": str(payload.evaluated_resources),
            "inline": True,
        },
        {
            "name": "Captured into CAS",
            "value": str(payload.successful_captures),
            "inline": True,
        },
        {
            "name": "Parquet Tables",
            "value": str(payload.parquet_derivatives_count),
            "inline": True,
        },
        {
            "name": "Broken URLs",
            "value": str(payload.broken_urls_count),
            "inline": True,
        },
    ]
    if payload.hf_repo_url:
        fields.append(
            {
                "name": "Hugging Face Release",
                "value": f"[View Dataset]({payload.hf_repo_url})",
                "inline": True,
            }
        )

    return {
        "content": (
            f"**NZ Government Open Data Preservation Harvest Update** "
            f"({payload.status.upper()})"
        ),
        "embeds": [
            {
                "title": "🏛️ Preservation Harvest Summary",
                "color": color,
                "fields": fields,
                "footer": {"text": f"Completed: {payload.completed_at}"},
            }
        ],
    }


async def dispatch_webhook(
    webhook_url: str,
    payload: HarvestNotificationPayload,
    service: str = "auto",
    timeout_seconds: float = 15.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> bool:
    """Send structured payload to target webhook URL."""
    url_lower = webhook_url.lower()

    if service == "slack" or "hooks.slack.com" in url_lower:
        body = format_slack_payload(payload)
    elif service == "discord" or "discord.com/api/webhooks" in url_lower:
        body = format_discord_payload(payload)
    else:
        body = asdict(payload)

    async with httpx.AsyncClient(
        timeout=timeout_seconds, transport=transport
    ) as client:
        response = await client.post(webhook_url, json=body)
        return response.is_success
