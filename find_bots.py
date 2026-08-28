import json
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

with open("following_profiles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

non_mutuals = [u for u in data if not u.get("followed_by")]

bot_keywords = ["bot", "tracker", "quotes", "memes", "clip", "archive", "daily", "facts", "porn", "retards", "curation", "aggregator"]

bot_accounts = []
for u in non_mutuals:
    handle = u.get("screen_name", "").lower()
    name = u.get("name", "").lower()
    bio = u.get("description", "").lower()
    if any(k in handle or k in name or k in bio for k in bot_keywords):
        bot_accounts.append(u)

print(f"Total Bot / Tracker / Meme / Aggregator Accounts found: {len(bot_accounts)}\n")
for i, b in enumerate(bot_accounts, 1):
    print(f"{i}. @{b.get('screen_name')} - {b.get('name')}")
    print(f"   Bio: {b.get('description')[:90]}...\n")
