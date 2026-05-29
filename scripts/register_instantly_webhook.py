"""
Register Instantly workspace webhook → Railway (or any public URL).

  python scripts/register_instantly_webhook.py
  python scripts/register_instantly_webhook.py --url https://service-1-webhooks-production.up.railway.app/webhooks/instantly
  python scripts/register_instantly_webhook.py --list
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

V2 = "https://api.instantly.ai/api/v2"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }


async def list_webhooks(client: httpx.AsyncClient, api_key: str) -> list[dict[str, Any]]:
    resp = await client.get(f"{V2}/webhooks", headers=_headers(api_key))
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    return list(data.get("items") or data.get("webhooks") or [])


async def delete_webhook(
    client: httpx.AsyncClient, api_key: str, webhook_id: str
) -> bool:
    resp = await client.delete(
        f"{V2}/webhooks/{webhook_id}", headers=_headers(api_key)
    )
    return resp.status_code < 400


async def create_webhook(
    client: httpx.AsyncClient,
    api_key: str,
    *,
    target_url: str,
    campaign_id: str | None,
    name: str,
    secret: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "target_hook_url": target_url,
        "event_type": "reply_received",
    }
    if campaign_id:
        body["campaign"] = campaign_id
    if secret.strip():
        body["headers"] = {"X-Webhook-Secret": secret.strip()}

    resp = await client.post(
        f"{V2}/webhooks",
        headers=_headers(api_key),
        json=body,
    )
    if resp.status_code >= 400:
        return {"ok": False, "status": resp.status_code, "body": resp.text}
    return {"ok": True, "data": resp.json() if resp.content else {}}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default=os.environ.get(
            "INSTANTLY_WEBHOOK_URL",
            "https://service-1-webhooks-production.up.railway.app/webhooks/instantly",
        ),
    )
    parser.add_argument("--list", action="store_true", help="List existing webhooks only")
    parser.add_argument("--all-campaigns", action="store_true", help="Do not filter by campaign")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing webhooks for this URL, then re-create (fixes disabled/no-header)",
    )
    args = parser.parse_args()

    api_key = (os.environ.get("INSTANTLY_API_KEY") or "").strip()
    if not api_key:
        print("Missing INSTANTLY_API_KEY in .env")
        sys.exit(1)

    campaign_id = (os.environ.get("INSTANTLY_CAMPAIGN_ID") or "").strip()
    if args.all_campaigns:
        campaign_id = ""
    secret = (os.environ.get("INSTANTLY_WEBHOOK_SECRET") or "").strip()

    async with httpx.AsyncClient(timeout=60.0) as client:
        existing = await list_webhooks(client, api_key)
        if args.list:
            for wh in existing:
                print(
                    f"- {wh.get('name')!r} | {wh.get('event_type')} | "
                    f"{wh.get('target_hook_url')} | status={wh.get('status')}"
                )
            return

        target = args.url.strip()
        matching = [
            wh
            for wh in existing
            if str(wh.get("target_hook_url") or "").rstrip("/") == target.rstrip("/")
        ]

        if args.replace:
            for wh in matching:
                wid = str(wh.get("id") or "")
                if wid and await delete_webhook(client, api_key, wid):
                    print(f"Deleted old webhook {wid} (status was {wh.get('status')})")
        else:
            for wh in matching:
                if wh.get("event_type") == "reply_received":
                    print(
                        f"Already registered: {wh.get('id')} "
                        f"(status={wh.get('status')}). Use --replace to recreate with header."
                    )
                    return

        name = "Atlas Railway - reply_received"
        result = await create_webhook(
            client,
            api_key,
            target_url=target,
            campaign_id=campaign_id or None,
            name=name,
            secret=secret,
        )
        if not result.get("ok"):
            print(f"Failed ({result.get('status')}): {result.get('body')}")
            sys.exit(1)
        data = result.get("data") or {}
        print(f"Created webhook id={data.get('id')} name={data.get('name')!r}")
        print(f"  URL: {target}")
        print(f"  Event: reply_received")
        if campaign_id:
            print(f"  Campaign: {campaign_id}")
        if secret:
            print("  Header: X-Webhook-Secret (set in Railway INSTANTLY_WEBHOOK_SECRET)")


if __name__ == "__main__":
    asyncio.run(main())
