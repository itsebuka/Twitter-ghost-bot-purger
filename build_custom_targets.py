"""
Targeted Custom Purge Builder
Implements the exact whitelist and candidate selections requested:
1. Memes & Ragebait: Unfollow all EXCEPT HOUSEPORN___ and Auto_Porn
2. Dating & RedPill: Unfollow all EXCEPT seduction__king, WomenBeingAwful, IncelsCo, RationalMale
3. Politics: Unfollow all EXCEPT NickJFuentes, FuentesUpdates, DeleFarotimi, forbiddenmerch
4. Non-Mutual Baggage: Unfollow 150 non-mutual accounts (preserving all mutuals and engineering/tech)
"""

import csv
import json
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

with open("following_categorized.csv", mode="r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

with open("unfollowed_history.json", "r", encoding="utf-8") as f:
    unfollowed = set(json.load(f))

# Explicit Kept Handles from user prompt
EXPLICIT_KEPT_HANDLES = {
    # Memes kept
    "houseporn___",
    "auto_porn",

    # Dating/Redpill kept
    "seduction__king",
    "womenbeingawful",
    "incelsco",
    "rationalmale",

    # Politics kept
    "nickjfuentes",
    "fuentesupdates",
    "delefarotimi",
    "forbiddenmerch",

    # Core & Tech permanently kept
    "pau_nigeria",
    "ikejaelectric",
    "vireontech"
}

targets_to_unfollow = []

# 1. Process Memes Category
memes = [r for r in rows if "Memes" in r["category"] and r["followed_by"] != "YES (Mutual)" and r["screen_name"].lower() not in unfollowed]
for r in memes:
    h = r["screen_name"].lower()
    if h not in EXPLICIT_KEPT_HANDLES:
        targets_to_unfollow.append((r["screen_name"], r["name"], "Meme/Ragebait Aggregator"))

# 2. Process Dating / RedPill Category
dating = [r for r in rows if "Dating" in r["category"] and r["followed_by"] != "YES (Mutual)" and r["screen_name"].lower() not in unfollowed]
for r in dating:
    h = r["screen_name"].lower()
    if h not in EXPLICIT_KEPT_HANDLES:
        targets_to_unfollow.append((r["screen_name"], r["name"], "Dating/RedPill Coach"))

# 3. Process Politics Category
politics = [r for r in rows if "News" in r["category"] and r["followed_by"] != "YES (Mutual)" and r["screen_name"].lower() not in unfollowed]
for r in politics:
    h = r["screen_name"].lower()
    if h not in EXPLICIT_KEPT_HANDLES:
        targets_to_unfollow.append((r["screen_name"], r["name"], "Political Commentator / News"))

# 4. Process Non-Mutual Baggage (150 accounts)
baggage = [r for r in rows if "Other Non-Mutual" in r["category"] and r["followed_by"] != "YES (Mutual)" and r["screen_name"].lower() not in unfollowed]
baggage_targets = []
for r in baggage:
    h = r["screen_name"].lower()
    if h not in EXPLICIT_KEPT_HANDLES:
        baggage_targets.append((r["screen_name"], r["name"], "Non-Mutual Baggage"))

# Cap baggage at 150
targets_to_unfollow.extend(baggage_targets[:150])

print("=" * 65)
print("             🎯 CUSTOM PURGE SUMMARY & SELECTION             ")
print("=" * 65)
print(f"1. Memes slated for unfollow:       {len([t for t in targets_to_unfollow if t[2] == 'Meme/Ragebait Aggregator'])}")
print(f"2. Dating/RedPill slated:           {len([t for t in targets_to_unfollow if t[2] == 'Dating/RedPill Coach'])}")
print(f"3. Politics slated for unfollow:    {len([t for t in targets_to_unfollow if t[2] == 'Political Commentator / News'])}")
print(f"4. Non-Mutual Baggage slated:       {len([t for t in targets_to_unfollow if t[2] == 'Non-Mutual Baggage'])}")
print("-" * 65)
print(f"👉 TOTAL ACCOUNTS SLATED FOR UNFOLLOW: {len(targets_to_unfollow)}")
print("=" * 65)

# Save targets to JSON
with open("custom_purge_targets.json", "w", encoding="utf-8") as f:
    json.dump([{"screen_name": t[0], "name": t[1], "reason": t[2]} for t in targets_to_unfollow], f, indent=2)

print("\n📁 Targets saved to 'custom_purge_targets.json'")
