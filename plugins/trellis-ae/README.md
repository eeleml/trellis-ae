# trellis-ae

AE-facing outbound toolkit for Trellis, distributed as a Claude Code plugin. Paste a list of
contacts; it researches each, respects Rules of Engagement, and **drafts motion-appropriate outreach
into your Gmail for review** — nothing is sent automatically. Built so AEs spend their time on calls
and meetings, not writing email.

## What's inside
| Skill / agent | What it does |
|---|---|
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
/plugin marketplace add <owner>/trellis-ae
/plugin install trellis-ae@trellis-ae
```
(Use a **public** repo — private marketplace auth is unreliable on the macOS desktop app.)

## One-time setup
1. **Connect MCPs:** Gmail (drafting), HubSpot (records/RoE), Fathom (calls), Google Drive + Notion (case studies). Slack optional (accountability alerts).
2. **Team config:** copy `config/config.example.json` → `~/.trellis-ae/config.json` and fill in your HubSpot portal id, owner ids, case-study index pointer, and signature. **This file stays local — never committed.**
3. **contact-finder:** paste the team Clay webhook once (it saves to `~/.clay-webhook`).
4. **Optional:** set `APOLLO_API_KEY` if you use Apollo enrichment anywhere.

## How email works here
- Everything is a **Gmail draft** — you review and send. The chat is for kicking off the list; the review surface is your inbox.
- **Follow-ups are in-thread replies.** Email 1 drafts first; Email 2/3/breakup can only thread off a *sent* message, so `follow-ups` drafts them as replies after you send, on a T+2/4/6 cadence, and **skips anyone who already replied.**

## Scheduling (set up after install — plugins can't ship cron)
Use `/schedule` to run `follow-ups` and `accountability` on a cadence (e.g., follow-ups each weekday
morning, accountability Friday). Each AE sets this up once.

## Data hygiene
This repo can be **public**: it holds no secrets and no customer data. Secrets live locally (Clay
webhook in `~/.clay-webhook`, Apollo key in env). Internal identifiers (owner ids, portal) live in
`~/.trellis-ae/config.json`. Case-study customer names/metrics live in **Drive/Notion**, read live at
messaging time — never committed.

## Updating the team
Edit the skill/agent, bump `version` in both `plugins/trellis-ae/.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`, commit, and push. Installers pick up the new version on next session.

## Status
`cold-outbound` + shared agents + `contact-finder` are built. `closed-lost`, `local-visits`,
`follow-ups`, and `accountability` follow the same pattern — coming next.
