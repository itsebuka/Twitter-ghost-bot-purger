"""
X (Twitter) Comprehensive Following Classifier
Categorizes all 965 followed accounts into clean, distinct thematic categories
and exports following_categorized.csv for easy filtering and decision making.
"""

import csv
import json
import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

INPUT_FILE = "following_profiles.json"
OUTPUT_CSV = "following_categorized.csv"

def classify_account(profile):
    """
    Classifies a profile into a single distinct category.
    Returns: (category, subcategory_reason)
    """
    handle = profile.get("screen_name", "").lower()
    name = profile.get("name", "").lower()
    bio = profile.get("description", "").lower()
    followed_by = profile.get("followed_by", False)
    is_verified = profile.get("is_verified", False)

    text = f"{handle} {name} {bio}"

    # 1. CORE INSTITUTIONS & UNIVERSITY
    if handle in ["pau_nigeria", "ikejaelectric", "vireontech"] or "pan-atlantic" in text:
        return "🏛️ Core Network & Institutions", "Core Designated Connection"

    # 2. BOTS, SCRAPERS & TRACKERS (High priority check for non-mutuals)
    bot_triggers = ["bot", "tracker", "quotes", "archive", "daily", "facts", "automatic", "aggregator", "retard", "porn"]
    if not followed_by and any(b in handle or b in name for b in ["bot", "tracker", "quotes", "receipts"]):
        return "🤖 Bots, Trackers & AI Reposters", "Automated / Bot Account"

    if not followed_by and any(t in handle for t in ["pelositracker", "altmantracker", "huangtracker", "trackerfink", "trumpsportfolio", "insiderwave"]):
        return "🤖 Bots, Trackers & AI Reposters", "Stock / Politician Tracker Bot"

    if not followed_by and any(t in handle for t in ["48_quotes", "33strategiesbot", "illimitablebot", "unmodernmanbot", "bookofpook", "thehealthb0t", "thematrixb0t", "conspiracyb0t", "0ccultbot", "redpillb0t", "teslaaibot"]):
        return "🤖 Bots, Trackers & AI Reposters", "Automated Quote / Topic Bot"

    # 3. HARDWARE, ROBOTICS, AEROSPACE & DEFENSE TECH
    hardware_kws = ["hardware", "pcb", "electronics", "embedded", "firmware", "robotics", "cad", "defense", "aerospace", "solidworks", "drone", "turbine", "rocket", "satellite", "uav", "manufacturing", "semiconductor", "kicad"]
    if any(k in text for k in hardware_kws) or handle in ["nasa", "spacex", "nasajpl", "rocketlab", "anduriltech", "bostondynamics", "figure_robot", "unitreerobotics", "nvdiarobotics", "openroboticsorg", "etched", "droneforge", "terraindustries", "nextpcb"]:
        return "⚙️ Hardware, Robotics, Aerospace & Defense", "Engineering & Hardware Niche"

    # 4. SOFTWARE, AI/ML, DATA SCIENCE & CODING
    software_kws = ["software", "ai/ml", "machine learning", "deep learning", "developer", "frontend", "backend", "python", "c++", "golang", "react", "devops", "cloud", "data scientist", "data analyst", "full stack"]
    if any(k in text for k in software_kws) or handle in ["googledeepmind", "karpathy", "freecodecamp", "threejs", "nvidia", "mit", "satyanadella", "jomatech"]:
        return "💻 Software, AI/ML, Coding & Data", "Software & Computing Niche"

    # 5. STOCKS, TRADING, CRYPTO & FINANCE
    finance_kws = ["stock", "ngx", "investor", "investing", "forex", "trader", "crypto", "bitcoin", "solana", "equity", "finance", "dividend", "financial analyst", "market", "bamboo", "wealth", "portfolio"]
    if any(k in text for k in finance_kws) or handle in ["investbamboo", "stockyvest", "nairametrics", "unusual_whales", "kalshi", "stockbubblesng"]:
        return "📈 Stocks, Crypto, Trading & Finance", "Financial & Investment Niche"

    # 6. DATING, REDPILL, MASCULINITY & MINDSET
    dating_kws = ["red pill", "redpill", "masculinity", "intersexual", "seduction", "dating coach", "testosterone", "simp", "hypergamy", "alpha", "patriarchy", "anti-feminist", "feminism", "men's health", "semen retention", "biohack"]
    if any(k in text for k in dating_kws) or handle in ["rationalmale", "myrongainesx", "wadedatings", "stirlingwisdom", "scrowder", "simppolice911", "freshandfit", "andrewtate", "lukebelmar", "gadzhiman", "shubhvanii"]:
        return "🥊 Dating, Masculinity, RedPill & Mindset", "Dating & Self-Improvement Influencer"

    # 7. MEMES, CLIPS, ENTERTAINMENT & SHITPOSTS
    meme_kws = ["meme", "memes", "clips", "funny", "humor", "shitpost", "aesthetic", "cinema", "wallpaper", "edits", "nostalgia", "cringe"]
    if any(k in text for k in meme_kws) or handle in ["picturesfoider", "humansnocontext", "historyinmemes", "fightwithmemes", "geekedmemes", "memesupmyass", "darkoddcon", "cartoonvidio", "nostalgiaa", "uberfacts", "creepydotorg", "fact"]:
        return "😂 Memes, Clips, Nostalgia & Entertainment", "Meme / Viral Content Page"

    # 8. FOOTBALL / SPORTS & CELEBRITIES
    sports_kws = ["chelsea", "arsenal", "manchester united", "man city", "real madrid", "barcelona", "football", "soccer", "cr7", "ronaldo", "messi", "haaland", "mbappe"]
    if any(k in text for k in sports_kws) or handle in ["cristiano", "kmbappe", "erling", "mancity", "gothamchess", "chesscom"]:
        return "⚽ Football, Sports & Celebrities", "Sports & Athletes"

    # 9. NEWS, POLITICS & CURRENT AFFAIRS
    politics_kws = ["politics", "governance", "president", "senator", "army", "navy", "police", "dss", "efcc", "news", "journalist", "sahara reporters", "channels tv", "brics", "military"]
    if any(k in text for k in politics_kws) or handle in ["officialefcc", "ngrpresident", "nigeriannavy", "hqnigerianarmy", "channelstv", "saharareporters", "officialdssng", "peterobi", "sowore", "arisetv", "usafricacommand"]:
        return "📰 News, Politics & Public Figures", "Political / Media Account"

    # 10. MUTUAL CONNECTIONS (Personal Friends / Classmates / Peers)
    if followed_by:
        return "🤝 Mutual Friends & Peers (Follows You Back)", "Personal Mutual Connection"

    # 11. GENERAL NON-MUTUAL ACCOUNTS
    return "🌐 Other Non-Mutual Accounts", "General / Miscellaneous Account"

def run_classifier():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    categorized = []
    category_counts = {}

    for p in profiles:
        cat, reason = classify_account(p)
        record = {
            "screen_name": p.get("screen_name", ""),
            "name": p.get("name", ""),
            "category": cat,
            "followed_by": "YES (Mutual)" if p.get("followed_by") else "NO",
            "is_verified": "Verified" if p.get("is_verified") else "Regular",
            "bio": p.get("description", "").replace("\n", " "),
            "classification_reason": reason
        }
        categorized.append(record)
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Write CSV sorted by category
    categorized.sort(key=lambda x: (x["category"], x["followed_by"] != "YES (Mutual)"))

    fieldnames = ["category", "screen_name", "name", "followed_by", "is_verified", "classification_reason", "bio"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in categorized:
            writer.writerow(r)

    print("=" * 70)
    print("      📊 X (Twitter) FOLLOWING BREAKDOWN BY CATEGORY       ")
    print("=" * 70)
    print(f"Total Accounts Analyzed: {len(profiles)}\n")

    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    for cat, count in sorted_categories:
        pct = (count / len(profiles)) * 100
        print(f"  {cat:<48} : {count:>3} accounts ({pct:>4.1f}%)")

    print("=" * 70)
    print(f"📁 Detailed breakdown exported to: {OUTPUT_CSV}")

if __name__ == "__main__":
    run_classifier()
