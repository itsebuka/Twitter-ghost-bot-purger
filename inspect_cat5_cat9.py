import csv
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

with open("following_categorized.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

cat5 = [r for r in rows if "Bots" in r["category"]]
cat9 = [r for r in rows if "Football" in r["category"]]

print(f"=== Category 5: Bots & Trackers ({len(cat5)} accounts) ===")
for r in cat5:
    print(f"  @{r['screen_name']} - {r['name']}")

print(f"\n=== Category 9: Football, Sports & Celebrities ({len(cat9)} accounts) ===")
for r in cat9:
    print(f"  @{r['screen_name']} - {r['name']} [Mutual: {r['followed_by']}]")
