"""
First-time setup wizard.
Run: python scripts/setup.py
"""

import os
import shutil
import sys


def main():
    print("\n" + "="*55)
    print("  Agent-Earns | Atlas — First-Time Setup")
    print("="*55)

    # 1. Create .env from example
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
        print("\n[OK] Created .env from .env.example")
        print("     >>> EDIT .env AND ADD YOUR API KEYS <<<")
    else:
        print("\n[OK] .env already exists")

    # 2. Create all output/log directories
    dirs = [
        "logs", "outputs/websites", "outputs/chatbots",
        "outputs/designs", "outputs/content", "outputs/reports", "outputs/invoices"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("[OK] Output directories created")

    # 3. Create empty .gitkeep files
    for d in ["logs", "outputs/websites", "outputs/chatbots"]:
        gitkeep = os.path.join(d, ".gitkeep")
        open(gitkeep, "a").close()

    # 4. Initialize database
    print("\n[..] Initializing database...")
    try:
        import asyncio
        from database.connection import init_db
        asyncio.run(init_db())
        print("[OK] Database initialized (agent.db created)")
    except Exception as e:
        print(f"[WARN] Database init failed: {e}")
        print("       Run 'python scripts/init_db.py' after installing dependencies")

    print("\n" + "="*55)
    print("  NEXT STEPS:")
    print("="*55)
    print("  1. Open .env and add your API keys")
    print("  2. Run: python scripts/test_all_apis.py")
    print("  3. Run: python main.py --test --verbose")
    print("  4. When ready: python main.py")
    print("="*55 + "\n")


if __name__ == "__main__":
    main()
