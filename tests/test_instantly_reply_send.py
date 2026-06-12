"""Unit tests for Instantly-approved reply send helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from modules.outreach.instantly_reply_send import (
    _re_subject,
    _reply_uuid_from_lead,
    resolve_instantly_reply_context,
    send_approved_reply_via_instantly,
)


def _lead(**enrichment: object) -> SimpleNamespace:
    return SimpleNamespace(
        id="lead-1",
        email="client@example.com",
        enrichment_data=enrichment,
    )


def test_reply_uuid_from_lead_uses_stored_id() -> None:
    lead = _lead(last_reply={"instantly_email_id": "abc-123-def"})
    assert _reply_uuid_from_lead(lead) == "abc-123-def"


def test_reply_uuid_from_lead_ignores_webhook_placeholder() -> None:
    lead = _lead(last_reply={"instantly_email_id": "webhook"})
    assert _reply_uuid_from_lead(lead) == ""


def test_re_subject_prefixes_re() -> None:
    assert _re_subject("Hello there") == "Re: Hello there"
    assert _re_subject("Re: Already") == "Re: Already"


@pytest.mark.asyncio
async def test_resolve_context_fetches_sent_when_no_received() -> None:
    lead = _lead(outbound_mailbox="gaurav@gauravxd.dev")
    settings = SimpleNamespace(
        has_instantly=True,
        instantly_api_key="key",
        instantly_campaign_id="camp",
    )
    mock_client = AsyncMock()
    mock_client.is_configured = True
    mock_client.list_emails = AsyncMock(
        side_effect=[
            ([], None),
            (
                [
                    {
                        "id": "sent-uuid-1",
                        "eaccount": "gaurav@gauravxd.dev",
                        "ue_type": 1,
                        "from_address_email": "gaurav@gauravxd.dev",
                    }
                ],
                None,
            ),
        ]
    )

    ctx = await resolve_instantly_reply_context(settings, lead, client=mock_client)
    assert ctx["reply_to_uuid"] == "sent-uuid-1"
    assert ctx["eaccount"] == "gaurav@gauravxd.dev"


@pytest.mark.asyncio
async def test_resolve_context_from_locked_mailbox_and_last_reply() -> None:
    lead = _lead(
        outbound_mailbox="gaurav@gauravxd.dev",
        last_reply={"instantly_email_id": "uuid-999"},
    )
    settings = SimpleNamespace(
        has_instantly=True,
        instantly_api_key="key",
        instantly_campaign_id="camp",
    )

    ctx = await resolve_instantly_reply_context(settings, lead)
    assert ctx["reply_to_uuid"] == "uuid-999"
    assert ctx["eaccount"] == "gaurav@gauravxd.dev"


@pytest.mark.asyncio
async def test_send_approved_reply_calls_instantly_client() -> None:
    lead = _lead(
        outbound_mailbox="gaurav@gauravxd.dev",
        last_reply={"instantly_email_id": "uuid-999", "subject": "Pricing?"},
        send_channel="instantly",
    )
    settings = SimpleNamespace(
        has_instantly=True,
        instantly_api_key="key",
        instantly_campaign_id="camp",
        outreach_domains_file="data/outreach_domains.json",
    )

    mock_client = AsyncMock()
    mock_client.is_configured = True
    mock_client.send_reply = AsyncMock(return_value={"ok": True, "email_id": "sent-1"})

    with patch(
        "modules.outreach.instantly_reply_send.InstantlyClient",
        return_value=mock_client,
    ):
        result = await send_approved_reply_via_instantly(
            settings,
            lead,
            subject="Thanks",
            body="Here is the info",
            client=mock_client,
        )

    assert result["ok"] is True
    assert result["channel"] == "instantly"
    mock_client.send_reply.assert_awaited_once()
    call_kw = mock_client.send_reply.await_args.kwargs
    assert call_kw["eaccount"] == "gaurav@gauravxd.dev"
    assert call_kw["reply_to_uuid"] == "uuid-999"
    assert call_kw["subject"] == "Re: Thanks"
