"""
Health Checker — Verifies all external API connections on startup and hourly.
All checks run concurrently. Each check is fully self-contained with its own
try/except so one failure never blocks the others.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any
from loguru import logger

# Add project root to sys.path if run directly
sys.path.append(str(Path(__file__).parent.parent))

from config import Settings


class HealthChecker:
    """
    Pings all configured external APIs and returns a health status dict.
    Called on startup and every hour by the scheduler.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def check_all(self) -> dict[str, dict[str, Any]]:
        """Run all applicable health checks concurrently."""
        checks = []

        if self.settings.has_gemini:
            checks.append(self._check_gemini())
        if self.settings.has_groq:
            checks.append(self._check_groq())
        if self.settings.has_gmail:
            checks.append(self._check_gmail())
        if self.settings.has_razorpay:
            checks.append(self._check_razorpay())
        if self.settings.has_telegram:
            checks.append(self._check_telegram())

        # Database is always checked
        checks.append(self._check_database())

        results = await asyncio.gather(*checks, return_exceptions=True)

        health_report: dict[str, dict[str, Any]] = {}
        for result in results:
            if isinstance(result, dict):
                health_report.update(result)
            else:
                # Unexpected exception from gather — log it
                logger.warning(f"Health check raised unhandled exception: {result}")

        return health_report

    # ─────────────────────────────────────────────────────────────────────────
    # Individual checks
    # ─────────────────────────────────────────────────────────────────────────

    async def _check_gemini(self) -> dict[str, Any]:
        """Verify Gemini API with a minimal test call (new google-genai SDK)."""
        try:
            from google import genai  # type: ignore[import]
            from google.genai import types  # type: ignore[import]

            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents="Reply with the single word: OK",
                config=types.GenerateContentConfig(max_output_tokens=5),
            )
            try:
                text: str = response.text or ""
                healthy = bool(text)
            except (ValueError, AttributeError):
                healthy = True
                text = "(safety filtered — API is up)"
            return {"gemini": {"healthy": healthy, "response": text[:60]}}
        except ImportError:
            return {"gemini": {"healthy": False, "error": "google-genai not installed. Run: pip install google-genai"}}
        except Exception as exc:
            msg = str(exc).lower()
            if "quota" in msg or "429" in msg or "resource_exhausted" in msg:
                return {"gemini": {"healthy": False, "error": f"Quota exceeded — wait or check billing: {exc}"}}
            return {"gemini": {"healthy": False, "error": str(exc)}}

    async def _check_groq(self) -> dict[str, Any]:
        """Verify Groq API with a minimal test call."""
        try:
            from groq import AsyncGroq  # type: ignore[import]
            client = AsyncGroq(api_key=self.settings.groq_api_key, timeout=30.0)
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            healthy = bool(response.choices[0].message.content)
            return {"groq": {"healthy": healthy}}
        except ImportError:
            return {"groq": {"healthy": False, "error": "groq not installed"}}
        except Exception as exc:
            return {"groq": {"healthy": False, "error": str(exc)}}

    async def _check_gmail(self) -> dict[str, Any]:
        """
        Verify Gmail credentials are present.
        Full OAuth flow validation is done by the outreach module on first use.
        """
        healthy = bool(
            self.settings.gmail_client_id
            and self.settings.gmail_refresh_token
            and self.settings.gmail_sender_address
        )
        return {"gmail": {"healthy": healthy, "sender": self.settings.gmail_sender_address}}

    async def _check_razorpay(self) -> dict[str, Any]:
        """
        Verify Razorpay credentials.
        razorpay SDK is sync — run inside a thread executor to avoid blocking the event loop.
        """
        try:
            import razorpay  # type: ignore[import]

            loop = asyncio.get_running_loop()

            def _sync_verify() -> bool:
                """Blocking call — safe inside run_in_executor."""
                client = razorpay.Client(
                    auth=(self.settings.razorpay_key_id, self.settings.razorpay_key_secret)
                )
                client.order.all({"count": 1})  # type: ignore[attr-defined]
                return True

            await loop.run_in_executor(None, _sync_verify)
            return {"razorpay": {"healthy": True}}

        except ImportError:
            return {"razorpay": {"healthy": False, "error": "razorpay not installed"}}
        except Exception as exc:
            return {"razorpay": {"healthy": False, "error": str(exc)}}

    async def _check_telegram(self) -> dict[str, Any]:
        """
        Verify Telegram bot token.
        Uses direct HTTP request to avoid python-telegram-bot version conflicts.
        """
        try:
            import httpx  # type: ignore[import]

            url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/getMe"
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.get(url)

            if res.status_code == 200:
                data = res.json()
                if data.get("ok"):
                    bot_name = data["result"].get("username", "Bot")
                    return {"telegram": {"healthy": True, "bot_name": bot_name}}
                return {"telegram": {"healthy": False, "error": f"API error: {data}"}}

            return {"telegram": {"healthy": False, "error": f"HTTP {res.status_code}: {res.text}"}}

        except ImportError:
            return {"telegram": {"healthy": False, "error": "httpx not installed"}}
        except Exception as exc:
            return {"telegram": {"healthy": False, "error": str(exc)}}


    async def _check_database(self) -> dict[str, Any]:
        """Verify SQLite database — initializes it first if not yet created."""
        try:
            from database.connection import init_db, health_check
            # Auto-initialize on first check so the health script works standalone
            await init_db()
            healthy = await health_check()
            return {"database": {"healthy": healthy}}
        except Exception as exc:
            return {"database": {"healthy": False, "error": str(exc)}}

