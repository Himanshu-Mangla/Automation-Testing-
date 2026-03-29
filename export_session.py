"""
export_session.py
-----------------
Run this locally AFTER a successful login (so auth/auth_cookies.json exists).
It prints the SESSION_COOKIES value you need to paste into GitHub Secrets.

Usage:
    python export_session.py
"""

import json
from pathlib import Path

COOKIES_FILE = Path(__file__).parent / "auth" / "auth_cookies.json"


def main():
    if not COOKIES_FILE.exists():
        print("[ERROR] auth/auth_cookies.json not found.")
        print("        Run your tests locally first so a session is saved.")
        return

    raw = COOKIES_FILE.read_text(encoding="utf-8")

    # Validate it's valid JSON
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[ERROR] auth_cookies.json is not valid JSON: {e}")
        return

    print("=" * 70)
    print("  Copy everything between the dashes and paste it as the")
    print("  GitHub Secret named:  SESSION_COOKIES")
    print("  (Settings → Secrets and variables → Actions → New secret)")
    print("=" * 70)
    print()
    print(raw)
    print()
    print("=" * 70)
    print("  Done. Remember to update this secret whenever cookies expire.")
    print("=" * 70)


if __name__ == "__main__":
    main()
