"""
Automated Custom Purge Executor
Executes the approved 252-target purge with anti-ban jittered throttling,
rate-limit detection, and continuous progress persistence.
"""

import argparse
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
TARGETS_FILE     = "custom_purge_targets.json"
PROGRESS_JSON    = "unfollowed_history.json"
HISTORY_LOG_FILE = "unfollowed_history.log"

HEADERS = {
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "x-csrf-token": CT0_CSRF,
    "cookie": f"auth_token={AUTH_TOKEN}; ct0={CT0_CSRF};",
    "content-type": "application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

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
            return "success", "", 0
        elif r.status_code == 429:
            reset_epoch = r.headers.get("x-rate-limit-reset")
            wait_sec = max(int(float(reset_epoch) - time.time()) + 5, 60) if reset_epoch else 300
            return "rate_limited", f"Rate limited. Reset in {wait_sec}s", wait_sec
        elif r.status_code == 404:
            return "not_found", "User already deactivated or unfollowed", 0
        elif r.status_code == 403:
            return "forbidden", "HTTP 403 Forbidden", 0
        else:
            return "failed", f"HTTP {r.status_code}", 0
    except Exception as e:
        return "error", str(e), 5

def run():
    parser = argparse.ArgumentParser(description="Custom Targeted Unfollow Engine")
    parser.add_argument("--limit", type=int, default=252, help="Max accounts to process in this run (default: 252)")
    parser.add_argument("--auto", action="store_true", help="Non-interactive execution")
    args = parser.parse_args()

    if not os.path.exists(TARGETS_FILE):
        print(f"[!] Targets file '{TARGETS_FILE}' not found. Run 'build_custom_targets.py' first.")
        return

    with open(TARGETS_FILE, "r", encoding="utf-8") as f:
        all_targets = json.load(f)

    history = load_history()
    pending = [t for t in all_targets if t["screen_name"].lower() not in history]

    print("=" * 65)
    print("         🎯 CUSTOM TARGETED UNFOLLOW EXECUTION         ")
    print("=" * 65)
    print(f"• Total Targets Configured:  {len(all_targets)}")
    print(f"• Already Processed:         {len(all_targets) - len(pending)}")
    print(f"• Pending to Unfollow:       {len(pending)}")
    print(f"• Batch Cap for this Run:    {min(len(pending), args.limit)}")
    print("-" * 65)

    if not pending:
        print("\n[+] All configured targets have already been purged! Account is clean.")
        return

    batch = pending[:args.limit]

    if not args.auto:
        confirm = input("\nType 'UNFOLLOW' to start live execution (or Ctrl+C to abort): ")
        if confirm.strip() != "UNFOLLOW":
            print("[!] Operation cancelled by user.")
            return

    print("\n[*] Starting live throttled unfollow loop...\n")
    success_count = 0

    for i, t in enumerate(batch, 1):
        handle = t["screen_name"]
        name = t["name"]
        reason = t["reason"]

        print(f"[{i}/{len(batch)}] Unfollowing @{handle} ({name}) [{reason}]...", end="", flush=True)

        status, msg, wait_sec = unfollow_user(handle)

        if status in ("success", "not_found"):
            success_count += 1
            record_success(handle)
            print(f" ✅ [OK] ({status})")
        elif status == "rate_limited":
            print(f" ⚠️ [{msg}] Pausing execution...")
            time.sleep(wait_sec)
            retry_status, _, _ = unfollow_user(handle)
            if retry_status in ("success", "not_found"):
                success_count += 1
                record_success(handle)
                print(f"    ↳ Retry successful ✅")
        elif status == "forbidden":
            print(f" ❌ [403 Forbidden] Session expired or locked.")
            break
        else:
            print(f" ❌ [{status}] {msg}")

        # Throttled jitter sleep
        if i < len(batch):
            sleep_time = random.uniform(5.5, 9.5)
            print(f"    ⏳ Jitter sleep: {sleep_time:.1f}s...")
            time.sleep(sleep_time)

    print("\n" + "=" * 65)
    print(f"🎉 BATCH COMPLETE! Successfully unfollowed {success_count} / {len(batch)} accounts.")
    print("=" * 65)

if __name__ == "__main__":
    run()
