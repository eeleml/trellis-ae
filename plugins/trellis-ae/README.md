# trellis-ae

AE-facing outbound toolkit for Trellis, distributed as a Claude Code plugin. Paste a list of
contacts; it researches each, respects Rules of Engagement, and **drafts motion-appropriate outreach
into your Gmail for review** — nothing is sent automatically. Built so AEs spend their time on calls
and meetings, not writing email.

## What's inside
| Skill / agent | What it does |
|---|---|
| `/trellis-ae:setup` | **Run once after install** — checks connectors, finds your HubSpot owner ID, saves your signature, takes the Clay webhook, writes your config |
| `/trellis-ae:cold-outbound` | Paste ~25 cold contacts → research + RoE → Email 1 drafted in Gmail (+ follow-up plan) |
| `/trellis-ae:closed-lost` | Re-engagement: deal-history + Fathom-first → Gmail draft; owner-aware, job-change & lost-reason driven |
| `/trellis-ae:follow-ups` | Finds your sent Email 1's and drafts the next in-thread touch on cadence; skips anyone who replied |
| `/trellis-ae:accountability` | Checks Email 1's are sent, follow-ups + calls are happening, replies handled → flags gaps per AE |
| `/trellis-ae:local-visits` *(coming)* | Door-knock prep: text-message drafts + one lunch-invite email + talking points + visit task |
| `contact-finder` (agent) | "Help me find this person" → Clay enrichment → HubSpot (reads `clay_mobile`) |
| `ob-verification`, `ob-internal-research`, `ob-external-research`, `ob-messaging` (agents) | Shared RoE, research, and copywriting the motion skills spawn |

**Each AE keeps 3 chats — one per motion** (cold / closed-lost / local) — and runs the matching skill there.

## Install
```
/plugin marketplace add eeleml/trellis-ae
/plugin install trellis-ae@trellis-ae
```

## One-time setup (per AE)
1. **Install** (the two commands above).
2. **Connect these connectors** in Claude → Settings → Connectors:
   - **HubSpot · Gmail · Fathom · Google Drive** — all required.
   - **Slack** — only if you'll run `accountability` or want reply alerts.
3. **Run `/trellis-ae:setup`** — it verifies your connectors, finds your HubSpot owner ID, saves your signature, has you paste the team **Clay webhook** (get it from your admin), locates the case-study index in Drive, and writes `~/.trellis-ae/config.json`.
4. **Schedule** via `/schedule`: follow-ups at 6 AM weekdays (and `accountability` weekly if you run it).

*(Optional: set `APOLLO_API_KEY` only if you use the Apollo enrichment fallback.)*

## How email works here
- Everything is a **Gmail draft** — you review and send. The chat is for kicking off the list; the review surface is your inbox.
- **Follow-ups are in-thread replies.** Email 1 drafts first; Email 2/3/breakup can only thread off a *sent* message, so `follow-ups` drafts them as replies after you send, on a T+2/4/6 cadence, and **skips anyone who already replied.**

## Scheduling (set up after install — plugins can't ship cron)
Use `/schedule` to run `follow-ups` and `accountability` on a cadence (e.g., follow-ups each weekday
morning, accountability Friday). Each AE sets this up once.

## Data hygiene
This repo can be **public**: it holds no secrets and no customer data. Secrets live locally (Clay
webhook in `~/.clay-webhook`, Apollo key in env). Internal identifiers (owner ids, portal) live in
`~/.trellis-ae/config.json`. Case-study customer names/metrics live in **Google Drive**, read live at
messaging time — never committed.

## Updating the team
Edit the skill/agent, bump `version` in both `plugins/trellis-ae/.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`, commit, and push. Installers pick up the new version on next session.

## Status
Built: `setup`, `cold-outbound`, `closed-lost`, `follow-ups`, `accountability` + `contact-finder` + the
4 shared agents. Coming: `local-visits`, and the `reporting` + `ab-testing` analytics agents.
