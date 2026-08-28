# 👻 X (Twitter) 24/7 Ghost, Bot & Inactivity Purger

Automated, rate-limit-aware Python engine that audits and un-follows ghost accounts (inactive for >2 months / 60 days), bot/spam profiles, and low-signal non-mutuals on X (Twitter) while strictly preserving mutuals, designated handles, verified accounts, and engineering connections.

Runs locally or 24/7 in the cloud via GitHub Actions.

---

## 🛡️ Immutable Safety Whitelist (Never Unfollowed)
* **Mutual Connections**: Anyone where `followed_by == True` is automatically protected.
* **Designated Handles**: `@pau_nigeria`, `@IkejaElectric`, `@vireontech`, and handles in `whitelist.txt`.
* **Verified Accounts**: Any account with Blue, Gold, or Gray verification badges.
* **Niche Engineering & AI Keywords**: Profiles containing `hardware`, `pcb`, `electronics`, `embedded`, `firmware`, `robotics`, `cad`, `defense`, `founder`, `engineer`, `aerospace`, `ai`, `c++`, `python`, `deep learning`.

---

## 🎯 Purge & Targeting Criteria
* **Ghost Accounts**: Inactive for >60 days (2 months) or 0 total posts.
* **Bot / Spam Profiles**: Default avatar templates or follow-ratio anomalies.
* **Low-Signal Non-Mutuals**: Non-mutual accounts with no engineering/tech relevance.

---

## 🚀 Cloud Runner Setup (GitHub Actions 24/7)

1. Create a **Public** repository on GitHub (e.g. `Twitter-ghost-bot-purger`) for **unlimited free minutes**.
2. Go to **Settings** → **Secrets and variables** → **Actions** → Add:
   * `AUTH_TOKEN`: Your Twitter session `auth_token`
   * `CT0_CSRF`: Your Twitter `ct0` CSRF token
3. Go to **Settings** → **Actions** → **General** → **Workflow permissions** → Select **Read and write permissions** → Save.
4. Under the **Actions** tab, click **"Twitter 24/7 Ghost & Bot Purger"** → **Run workflow**.

---

## 💻 Local CLI Usage

```bash
# Dry-run audit preview (zero API mutations)
python x_ghost_bot_purger.py --dry-run --limit 20

# Live execution with safety throttle (60 accounts per session)
python x_ghost_bot_purger.py --live-run --limit 60
```
