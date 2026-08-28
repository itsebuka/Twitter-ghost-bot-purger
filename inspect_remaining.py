import csv
import json
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

with open("following_categorized.csv", mode="r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

with open("unfollowed_history.json", "r", encoding="utf-8") as f:
    unfollowed = set(json.load(f))

remaining = [r for r in rows if r["screen_name"].lower() not in unfollowed and r["followed_by"] != "YES (Mutual)"]

cats = {}
for r in remaining:
    c = r["category"]
    cats.setdefault(c, []).append(r)

print("=== REMAINING NON-MUTUAL ACCOUNTS BY CATEGORY ===")
for c, items in sorted(cats.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{c} ({len(items)} accounts):")
    for item in items[:6]:
        print(f"  - @{item['screen_name']} ({item['name']}): {item['bio'][:70]}...")
