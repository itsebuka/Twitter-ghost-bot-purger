import csv

with open("following_cleanup_audit.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    candidates = [r for r in reader if r["verdict"] != "PROTECTED_WHITELIST"]

print(f"Total Accounts Slated for Unfollow: {len(candidates)}\n")
for i, c in enumerate(candidates, 1):
    print(f"{i}. @{c['screen_name']} ({c['name']})")
    print(f"   Reason: {c['reason']}")
    print(f"   Bio: {c['bio'][:85]}...")
    print("-" * 50)
