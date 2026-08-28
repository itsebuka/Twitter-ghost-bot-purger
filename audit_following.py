"""
X (Twitter) Following Profile Auditor & Whitelist Evaluator
Reads enriched following profile metadata (following_profiles.json),
applies deterministic whitelist rules, and generates following_cleanup_audit.csv for review.
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone

# Reconfigure stdout for UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WHITELIST_FILE    = "whitelist.txt"
PROFILES_JSON     = "following_profiles.json"
AUDIT_CSV_FILE    = "following_cleanup_audit.csv"

# 2-Month Inactivity Threshold (60 Days)
INACTIVITY_DAYS_THRESHOLD = 60

# Core Designated Handles
CORE_PROTECTED_HANDLES = {
    "pau_nigeria",
    "ikejaelectric",
    "vireontech",
}

# Niche Engineering & AI Keywords for Biography Matching
ENGINEERING_KEYWORDS = [
    "hardware", "pcb", "electronics", "embedded", "firmware",
    "robotics", "cad", "defense", "founder", "engineer",
    "aerospace", "ai", "c++", "python", "deep learning"
]

def load_whitelist():
    """Loads user whitelist from whitelist.txt."""
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

def evaluate_profile(profile, custom_whitelist):
    """
    Evaluates a profile against Whitelist and Purge criteria.
    Returns: (verdict, reason, is_bot, days_inactive, last_post_str)
    """
    screen_name = str(profile.get("screen_name", "")).strip().lstrip("@").lower()
    rest_id = str(profile.get("rest_id", "") or profile.get("id_str", "")).strip()
    bio = str(profile.get("description", "")).lower()
    name = str(profile.get("name", "")).strip()
    followers_count = profile.get("followers_count", 0)
    friends_count = profile.get("friends_count", 0)
    statuses_count = profile.get("statuses_count", None)
    profile_image_url = profile.get("profile_image_url_https", "")

    # Check Inactivity if last_post timestamp available
    last_post_date = profile.get("last_post_date")
    days_inactive = "N/A"
    last_post_str = "Unknown"
    is_inactive_2mo = False

    if last_post_date:
        try:
            if isinstance(last_post_date, str):
                try:
                    dt = datetime.strptime(last_post_date, "%a %b %d %H:%M:%S %z %Y")
                except ValueError:
                    dt = datetime.fromisoformat(last_post_date)
            else:
                dt = last_post_date

            days = (datetime.now(timezone.utc) - dt).days
            days_inactive = days
            last_post_str = dt.strftime("%Y-%m-%d")
            if days > INACTIVITY_DAYS_THRESHOLD:
                is_inactive_2mo = True
        except Exception:
            pass

    # Bot Profile Detection
    is_default_avatar = "default_profile_normal" in profile_image_url or "default_profile_images" in profile_image_url
    is_ratio_bot = (friends_count > 1000 and followers_count < 5 and statuses_count == 0)
    is_bot_suspect = is_default_avatar or is_ratio_bot

    # -------------------------------------------------------------
    # 1. IMMUTABLE SAFETY WHITELIST (Never Unfollow)
    # -------------------------------------------------------------
    if screen_name in CORE_PROTECTED_HANDLES or rest_id in CORE_PROTECTED_HANDLES:
        return "PROTECTED_WHITELIST", "Hardcoded Designated Handle", is_bot_suspect, days_inactive, last_post_str

    if screen_name in custom_whitelist or rest_id in custom_whitelist:
        return "PROTECTED_WHITELIST", "Custom User Whitelist", is_bot_suspect, days_inactive, last_post_str

    if profile.get("followed_by") is True:
        return "PROTECTED_WHITELIST", "Mutual Connection (Follows You Back)", is_bot_suspect, days_inactive, last_post_str

    if profile.get("is_verified") or profile.get("is_blue_verified") or profile.get("verified"):
        return "PROTECTED_WHITELIST", "Verified Authority / Institution", is_bot_suspect, days_inactive, last_post_str

    matched_kws = [kw for kw in ENGINEERING_KEYWORDS if kw in bio]
    if matched_kws:
        return "PROTECTED_WHITELIST", f"Bio Keyword Match ({', '.join(matched_kws[:3])})", is_bot_suspect, days_inactive, last_post_str

    # -------------------------------------------------------------
    # 2. PURGE & TARGETING CRITERIA
    # -------------------------------------------------------------
    if is_bot_suspect:
        bot_reason = "Default Avatar" if is_default_avatar else "Follow Ratio Anomaly"
        return "UNFOLLOW_BOT", f"Suspected Bot/Spam ({bot_reason})", True, days_inactive, last_post_str

    if is_inactive_2mo:
        return "UNFOLLOW_GHOST", f"Ghost Account (Inactive for {days_inactive} days > 2mo)", False, days_inactive, last_post_str

    if statuses_count == 0:
        return "UNFOLLOW_GHOST", "Ghost Account (0 Total Posts)", False, days_inactive, last_post_str

    return "UNFOLLOW_IRRELEVANT", "Non-Mutual & Non-Engineering Profile", False, days_inactive, last_post_str

def run_audit():
    print("=" * 65)
    print("       X (Twitter) Following Profile Auditor & Reviewer       ")
    print("=" * 65)

    if not os.path.exists(PROFILES_JSON):
        print(f"\n[!] Missing '{PROFILES_JSON}' file.")
        print("    Please run the browser harvester script on x.com/following to generate it.")
        return

    with open(PROFILES_JSON, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    print(f"[+] Loaded {len(profiles)} rich user profiles from '{PROFILES_JSON}'.")

    custom_whitelist = load_whitelist()
    print(f"[+] Loaded {len(custom_whitelist)} custom whitelist entries from '{WHITELIST_FILE}'.")

    audited = []
    protected = []
    candidates = []

    for p in profiles:
        verdict, reason, is_bot, days_inactive, last_post_str = evaluate_profile(p, custom_whitelist)
        record = {
            "screen_name": p.get("screen_name", ""),
            "name": p.get("name", ""),
            "user_id": p.get("rest_id", "") or p.get("id_str", ""),
            "followed_by": p.get("followed_by", False),
            "is_verified": p.get("is_verified", False) or p.get("is_blue_verified", False) or p.get("verified", False),
            "bio": p.get("description", "").replace("\n", " "),
            "last_post_date": last_post_str,
            "days_inactive": days_inactive,
            "is_bot_suspect": is_bot,
            "verdict": verdict,
            "reason": reason
        }

        if verdict == "PROTECTED_WHITELIST":
            protected.append(record)
        else:
            candidates.append(record)

        audited.append(record)

    # Export CSV
    fieldnames = [
        "screen_name",
        "name",
        "user_id",
        "followed_by",
        "is_verified",
        "bio",
        "last_post_date",
        "days_inactive",
        "is_bot_suspect",
        "verdict",
        "reason"
    ]
    with open(AUDIT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in audited:
            writer.writerow(r)

    print(f"\n[+] Audit CSV successfully written to: {AUDIT_CSV_FILE}")
    print("\n" + "-" * 55)
    print("📊 COMPLETE AUDIT RESULTS:")
    print(f"   • Total Accounts Audited:     {len(profiles)}")
    print(f"   • 🛡️ PROTECTED BY WHITELIST:  {len(protected)}")
    print(f"   • 🎯 CANDIDATES FOR UNFOLLOW: {len(candidates)}")
    print("-" * 55)
    print(f"\n👉 You can now open '{AUDIT_CSV_FILE}' to inspect every single account!")

if __name__ == "__main__":
    run_audit()
