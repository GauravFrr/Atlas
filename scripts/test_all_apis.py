"""
Test all API connections.
Run: python scripts/test_all_apis.py

Verifies every configured API key works before starting the agent.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from utils.health_checker import HealthChecker


async def main():
    settings = get_settings()

    print("\n" + "="*55)
    print("  Agent-Earns | API Connection Tests")
    print("="*55)

    features = settings.get_enabled_features()
    enabled_count = sum(features.values())

    if enabled_count == 0:
        print("\n[ERROR] No API keys configured!")
        print("        Edit .env and add your API keys first.")
        return

    print(f"\nTesting {enabled_count} configured services...\n")

    checker = HealthChecker(settings)
    results = await checker.check_all()

    passed = 0
    failed = 0

    for service, status in results.items():
        if status["healthy"]:
            extra = ""
            if "bot_name" in status:
                extra = f" (@{status['bot_name']})"
            if "sender" in status:
                extra = f" ({status['sender']})"
            print(f"  [PASS] {service}{extra}")
            passed += 1
        else:
            error = status.get("error", "Unknown error")
            print(f"  [FAIL] {service}: {error}")
            failed += 1

    print(f"\n{'='*55}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*55}")

    if failed == 0:
        print("  All APIs healthy! Run: python main.py --test")
    else:
        print("  Fix failing APIs before starting the agent.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
