"""
Targeted Unfollower Script for Category 5 (Bots & Trackers),
Category 9 (Non-Mutual Sports & Celebrities), and Requested Prune Candidates.
"""

import json
import os
import random
import sys
import time
import requests

# Reconfigure stdout for UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "").strip() or "51c752155f1489e7a36ed3595bb4a68ded7bf42d"
CT0_CSRF   = os.getenv("CT0_CSRF", "").strip() or "a21abe5bf24a95c8a2f9d2483a8c7001eafbbaf152226c3effa1f61a56d53c51633b820ef80398ba8b122645dcc20d5946cfaa626f28f083e0f23d9cc18ad229fb2024360280a4194ae7172e3a62fa42"

UNFOLLOW_API_URL = "https://x.com/i/api/1.1/friendships/destroy.json"
HISTORY_LOG_FILE = "unfollowed_history.log"
PROGRESS_JSON    = "unfollowed_history.json"

HEADERS = {
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "x-csrf-token": CT0_CSRF,
    "cookie": f"auth_token={AUTH_TOKEN}; ct0={CT0_CSRF};",
    "content-type": "application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

# Target list: Category 5 Bots + Category 9 Non-Mutuals + Requested Prune Targets
TARGET_HANDLES = [
    # Category 5: Bots & Trackers (21)
    "33StrategiesBot",
    "TrackerFink",
    "TeslaAIBot",
    "WhaleReceipts",
    "HuangTracker",
    "AltmanTracker",
    "TrumpsPortfolio",
    "pelositracker",
    "insiderwave",
    "MoneyQuotesX",
    "quotesdaily100",
    "BookOfPook",
    "thehealthb0t",
    "UnmodernmanBot",
    "thematrixb0t",
    "conspiracyb0t",
    "iluminatibot",
    "0ccultbot",
    "redpillb0t",
    "48_quotes",
    "IllimitableBot",

    # Category 9: Non-Mutual Sports & Celebrities (11)
    "Cristiano",
    "Erling",
    "KMbappe",
    "HKane",
    "ManCity",
    "FCReplays",
    "Cr7Godbrand",
    "GothamChess",
    "chesscom",
    "VictorManjul",
    "Debbiektcha_",

    # Additional user requested prune targets (4)
    "Iyanuoluwa_io",
    "DeletedAcc3573",
    "osca_hq",
    "dment37"
]

def load_history():
    if os.path.exists(PROGRESS_JSON):
        try:
            with open(PROGRESS_JSON, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def record_success(screen_name):
    history = load_history()
    history.add(screen_name.lower())
    try:
        with open(PROGRESS_JSON, "w", encoding="utf-8") as f:
            json.dump(list(history), f, indent=2)
    except Exception:
        pass
    try:
        with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{screen_name}\n")
    except Exception:
        pass

def unfollow_user(screen_name):
    data = {"screen_name": screen_name}
    try:
        r = session.post(UNFOLLOW_API_URL, data=data, timeout=15)
        if r.status_code == 200:
            return "success", ""
        elif r.status_code == 429:
            return "rate_limited", "Rate limit hit"
        elif r.status_code == 404:
            return "not_found", "User not found / already unfollowed"
        elif r.status_code == 403:
            return "forbidden", f"HTTP 403 Forbidden"
        else:
            return "failed", f"HTTP {r.status_code}"
    except Exception as e:
        return "error", str(e)

def run():
    print("=" * 65)
    print("   🎯 Targeted Unfollow Execution: Bots, Trackers & Celebrities   ")
    print("=" * 65)

    # Filter out duplicates while preserving order
    seen = set()
    targets = []
    for h in TARGET_HANDLES:
        if h.lower() not in seen:
            seen.add(h.lower())
            targets.append(h)

    history = load_history()
    pending = [h for h in targets if h.lower() not in history]

    print(f"[+] Total Targets Configured: {len(targets)}")
    print(f"[+] Already Processed:        {len(targets) - len(pending)}")
    print(f"[+] Remaining to Unfollow:    {len(pending)}\n")

    if not pending:
        print("[+] All targeted accounts have already been unfollowed!")
        return

    success = 0
    for i, handle in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] Unfollowing @{handle}...", end="", flush=True)

        status, msg = unfollow_user(handle)

        if status in ("success", "not_found"):
            success += 1
            record_success(handle)
            print(f" ✅ [OK] ({status})")
        elif status == "rate_limited":
            print(f" ⚠️ [429 Rate Limit] Pausing for 60s...")
            time.sleep(60)
            retry_status, _ = unfollow_user(handle)
            if retry_status in ("success", "not_found"):
                success += 1
                record_success(handle)
                print(f"    ↳ Retry successful ✅")
        elif status == "forbidden":
            print(f" ❌ [403 Forbidden] {msg}")
            print("[!] Halting execution.")
            break
        else:
            print(f" ❌ [{status}] {msg}")

        if i < len(pending):
            sleep_sec = random.uniform(5.0, 9.0)
            print(f"    ⏳ Jitter sleep: {sleep_sec:.1f}s...")
            time.sleep(sleep_sec)

    print("\n" + "=" * 65)
    print(f"🎉 COMPLETED! Successfully unfollowed {success} / {len(pending)} accounts.")
    print("=" * 65)

if __name__ == "__main__":
    run()
