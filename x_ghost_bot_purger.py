"""
X (Twitter) Ghost & Bot Account Purger
Audits and un-follows ghost accounts, bot/spam profiles, and low-signal non-mutuals
while strictly preserving mutuals, designated handles, verified accounts, and engineering connections.
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
import requests

# Reconfigure stdout for UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Optional dotenv support
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ================= CONFIGURATION & CONSTANTS =================
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "").strip() or "51c752155f1489e7a36ed3595bb4a68ded7bf42d"
CT0_CSRF   = os.getenv("CT0_CSRF", "").strip() or "a21abe5bf24a95c8a2f9d2483a8c7001eafbbaf152226c3effa1f61a56d53c51633b820ef80398ba8b122645dcc20d5946cfaa626f28f083e0f23d9cc18ad229fb2024360280a4194ae7172e3a62fa42"

PROFILES_JSON_FILE = os.getenv("PROFILES_JSON", "following_profiles.json")
WHITELIST_FILE     = os.getenv("WHITELIST_FILE", "whitelist.txt")
AUDIT_CSV_FILE     = os.getenv("AUDIT_CSV_FILE", "following_cleanup_audit.csv")
HISTORY_LOG_FILE   = os.getenv("HISTORY_LOG_FILE", "unfollowed_history.log")
PROGRESS_JSON_FILE = os.getenv("PROGRESS_JSON_FILE", "unfollowed_history.json")

UNFOLLOW_API_URL   = "https://x.com/i/api/1.1/friendships/destroy.json"

# Core designated handles permanently protected
CORE_PROTECTED_HANDLES = {
    "pau_nigeria",
    "ikejaelectric",
    "vireontech",
}

# Niche engineering & tech keywords for bio matching
ENGINEERING_KEYWORDS = [
    "hardware", "pcb", "electronics", "embedded", "firmware",
    "robotics", "cad", "defense", "founder", "engineer",
    "aerospace", "ai", "c++", "python", "deep learning"
]

HEADERS = {
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "x-csrf-token": CT0_CSRF,
    "cookie": f"auth_token={AUTH_TOKEN}; ct0={CT0_CSRF};",
    "content-type": "application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)
# =============================================================

def load_whitelist():
    """Loads custom whitelisted handles from whitelist.txt."""
    whitelist = set()
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    clean = line.strip().lstrip("@").lower()
                    if clean and not clean.startswith("#"):
                        whitelist.add(clean)
        except Exception as e:
            print(f"[!] Warning reading whitelist file: {e}")
    return whitelist

def load_unfollowed_history():
    """Loads set of user handles / IDs already unfollowed in past runs."""
    history = set()
    if os.path.exists(PROGRESS_JSON_FILE):
        try:
            with open(PROGRESS_JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                history.update(str(x).lower() for x in data)
        except Exception:
            pass
    if os.path.exists(HISTORY_LOG_FILE):
        try:
            with open(HISTORY_LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if parts and parts[0]:
                        history.add(parts[0].strip().lower())
        except Exception:
            pass
    return history

def record_unfollow_success(handle_or_id, screen_name=""):
    """Persists unfollowed user to history log and JSON."""
    key = str(handle_or_id).lower()
    history = load_unfollowed_history()
    history.add(key)
    if screen_name:
        history.add(screen_name.lower())

    try:
        with open(PROGRESS_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(list(history), f, indent=2)
    except Exception as e:
        print(f"[!] Warning updating JSON progress: {e}")

    try:
        with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now(timezone.utc).isoformat()
            f.write(f"{handle_or_id},{screen_name},{timestamp}\n")
    except Exception as e:
        print(f"[!] Warning appending to history log: {e}")

def load_profiles_dataset():
    """Loads rich profile dataset from following_profiles.json."""
    if not os.path.exists(PROFILES_JSON_FILE):
        print(f"[!] Missing rich profiles file '{PROFILES_JSON_FILE}'.")
        return []

    with open(PROFILES_JSON_FILE, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    return profiles

def evaluate_profile(profile, custom_whitelist):
    """
    Evaluates account against Whitelist rules and Purge criteria.
    Returns: (verdict, reason)
    """
    screen_name = str(profile.get("screen_name", "")).strip().lstrip("@").lower()
    rest_id = str(profile.get("rest_id", "") or profile.get("id_str", "")).strip()
    bio = str(profile.get("description", "")).lower()

    # Rule 1: Core Designated Handles or Custom Whitelist
    if screen_name in CORE_PROTECTED_HANDLES or rest_id in CORE_PROTECTED_HANDLES:
        return "PROTECTED_WHITELIST", "Hardcoded Core Designated Handle"

    if screen_name in custom_whitelist or rest_id in custom_whitelist:
        return "PROTECTED_WHITELIST", "User Custom Whitelist File"

    # Rule 2: Mutual Connection (Follows You Back)
    if profile.get("followed_by") is True:
        return "PROTECTED_WHITELIST", "Mutual Connection (Follows Back)"

    # Rule 3: Verified Accounts
    if profile.get("is_verified") or profile.get("is_blue_verified") or profile.get("verified"):
        return "PROTECTED_WHITELIST", "Verified Authority / Institution"

    # Rule 4: Niche Engineering & AI Keywords in Bio
    matched_kws = [kw for kw in ENGINEERING_KEYWORDS if kw in bio]
    if matched_kws:
        return "PROTECTED_WHITELIST", f"Bio Keyword Match ({', '.join(matched_kws[:3])})"

    return "CANDIDATE_UNFOLLOW", "Non-Mutual & Non-Engineering Profile"

def execute_unfollow(screen_name, user_id=None):
    """Sends authenticated unfollow request using screen_name or user_id."""
    data = {}
    if screen_name:
        data["screen_name"] = str(screen_name)
    if user_id and str(user_id).isdigit():
        data["user_id"] = str(user_id)

    try:
        response = session.post(UNFOLLOW_API_URL, data=data, timeout=20)
    except requests.RequestException as e:
        return "network_error", str(e), 10

    if response.status_code == 200:
        return "success", "", 0
    elif response.status_code == 429:
        reset_epoch = response.headers.get("x-rate-limit-reset")
        if reset_epoch:
            wait_seconds = max(int(float(reset_epoch) - time.time()) + 5, 30)
        else:
            wait_seconds = 900
        return "rate_limited", f"Rate limit reset in {wait_seconds}s", wait_seconds
    elif response.status_code == 403:
        return "forbidden", "HTTP 403 Forbidden (Session token expired or blocked)", 0
    elif response.status_code == 404:
        return "not_found", "User already deactivated or unfollowed", 0
    else:
        return "failed", f"HTTP {response.status_code}: {response.text[:100]}", 0

def run():
    parser = argparse.ArgumentParser(description="X (Twitter) Ghost & Bot Purger")
    parser.add_argument("--dry-run", action="store_true", help="Preview candidate accounts without unfollowing")
    parser.add_argument("--live-run", action="store_true", help="Execute live throttled unfollow loop")
    parser.add_argument("--auto", action="store_true", help="Non-interactive mode for CI/CD runners (GitHub Actions)")
    parser.add_argument("--limit", type=int, default=60, help="Maximum unfollows per run (default: 60)")
    parser.add_argument("--min-sleep", type=float, default=25.0, help="Minimum jittered sleep (default: 25s)")
    parser.add_argument("--max-sleep", type=float, default=55.0, help="Maximum jittered sleep (default: 55s)")
    args = parser.parse_args()

    auto_mode = args.auto or os.getenv("CI") == "true" or "--auto" in sys.argv

    print("=" * 65)
    print("      X (Twitter) Ghost, Bot & Inactivity Pruning Engine      ")
    print("=" * 65)

    profiles = load_profiles_dataset()
    if not profiles:
        print("[!] No profile data found. Exiting.")
        return

    print(f"[+] Loaded {len(profiles)} rich user profiles from '{PROFILES_JSON_FILE}'.")
    custom_whitelist = load_whitelist()
    print(f"[+] Loaded {len(custom_whitelist)} Custom Whitelist Handles from '{WHITELIST_FILE}'.")
    unfollowed_history = load_unfollowed_history()
    print(f"[+] Loaded {len(unfollowed_history)} Previously Unfollowed Accounts from History.")

    audited = []
    protected = []
    candidates = []
    already_done = 0

    for p in profiles:
        s_name = p.get("screen_name", "").strip().lower()
        r_id = str(p.get("rest_id", "") or p.get("id_str", "")).strip().lower()

        if s_name in unfollowed_history or r_id in unfollowed_history:
            already_done += 1
            continue

        verdict, reason = evaluate_profile(p, custom_whitelist)
        record = {
            "screen_name": p.get("screen_name", ""),
            "name": p.get("name", ""),
            "user_id": p.get("rest_id", "") or p.get("id_str", ""),
            "followed_by": p.get("followed_by", False),
            "is_verified": p.get("is_verified", False) or p.get("is_blue_verified", False) or p.get("verified", False),
            "bio": p.get("description", "").replace("\n", " "),
            "verdict": verdict,
            "reason": reason
        }

        if verdict == "PROTECTED_WHITELIST":
            protected.append(record)
        else:
            candidates.append(record)

        audited.append(record)

    # Export Audit CSV
    fieldnames = ["screen_name", "name", "user_id", "followed_by", "is_verified", "bio", "verdict", "reason"]
    with open(AUDIT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in audited:
            writer.writerow(r)

    print(f"[+] Full audit report exported to: {AUDIT_CSV_FILE}")
    print("\n" + "-" * 55)
    print("AUDIT SUMMARY STATS:")
    print(f"   * Total Profiles Evaluated:    {len(profiles)}")
    print(f"   * Already Unfollowed:          {already_done}")
    print(f"   * PROTECTED BY WHITELIST:      {len(protected)}")
    print(f"   * CANDIDATES FOR UNFOLLOW:     {len(candidates)}")
    print("-" * 55)

    if not candidates:
        print("\n[+] All candidate accounts have been pruned! Following list is 100% clean.")
        return

    batch = candidates[:args.limit]
    print(f"\n[*] Processing Batch Size: {len(batch)} (Safety Cap: {args.limit})")

    # Dry-run
    if args.dry_run:
        print("\n[!] === DRY-RUN PREVIEW (No API requests made) ===")
        for i, target in enumerate(batch, 1):
            print(f"  [{i}/{len(batch)}] Would Unfollow: @{target['screen_name']} ({target['name']})")
            print(f"      Reason: {target['reason']}")
        print(f"\n[+] Dry-run finished. Run with '--live-run' to execute live.")
        return

    # Live run
    if not (args.live_run or auto_mode):
        confirm = input("\nType 'UNFOLLOW' to confirm live execution (or Ctrl+C to abort): ")
        if confirm.strip() != "UNFOLLOW":
            print("[!] Aborted by user.")
            return

    print("\n[*] Starting live throttled unfollow loop...")
    success_count = 0

    for i, target in enumerate(batch, 1):
        s_name = target["screen_name"]
        u_id = target["user_id"]

        print(f"[{i}/{len(batch)}] Unfollowing @{s_name} ({target['name']})...", end="", flush=True)

        status, msg, wait_sec = execute_unfollow(s_name, u_id)

        if status in ("success", "not_found"):
            success_count += 1
            record_unfollow_success(s_name, u_id)
            print(f" [OK] ({status})")
        elif status == "rate_limited":
            print(f" [429 Rate Limited] Waiting {wait_sec}s...")
            time.sleep(wait_sec)
            retry_status, _, _ = execute_unfollow(s_name, u_id)
            if retry_status == "success":
                success_count += 1
                record_unfollow_success(s_name, u_id)
                print("    ↳ Retry Successful [OK]")
        elif status == "forbidden":
            print(f" [403 Forbidden] {msg}")
            print("[!] Halting execution to protect account safety.")
            break
        else:
            print(f" [Failed] {msg}")

        if i < len(batch):
            sleep_time = random.uniform(args.min_sleep, args.max_sleep)
            print(f"    Sleeping {sleep_time:.1f}s (anti-ban safety throttle)...")
            time.sleep(sleep_time)

    print(f"\n[+] Session complete! Successfully unfollowed {success_count} accounts.")

if __name__ == "__main__":
    run()
