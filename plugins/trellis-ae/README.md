# trellis-ae

AE-facing outbound toolkit for Trellis, distributed as a Claude Code plugin. Paste a list of
contacts; it researches each, respects Rules of Engagement, and **drafts motion-appropriate outreach
into your Gmail for review** — nothing is sent automatically. Built so AEs spend their time on calls
and meetings, not writing email.

## What's inside
| Skill / agent | What it does |
|---|---|
| `/trellis-ae:setup` | **Run once after install** — checks connectors, finds your HubSpot owner ID, saves your signature, takes the Clay webhook, writes your config |
| `/trellis-ae:qualify` | Vet a list before assigning/working it → checks email/right-person/employment/deliverability/sequence, stamps each **contact's** `icp_lead_stage` (verified / failed) + buckets revisits. The Verify stage after `icp-sourcing`. Standalone, or a pre-gate inside cold-outbound |
| `/trellis-ae:cold-outbound` | Paste your cold list → research + RoE → Email 1 delivered for review (+ follow-up plan). If Instantly is set up, the batch is approved in a Google Doc / chat then pushed to your **paused Instantly campaign**; otherwise it's a **Gmail draft** |
| `/trellis-ae:closed-lost` | Re-engagement: deal-history + Fathom-first → Gmail draft; owner-aware, job-change & lost-reason driven. Reads the **full** lost reason + cross-references **`config/whats-new.md`** (releases since you last spoke); previews the angle + E1 in chat before drafting |
| `/trellis-ae:follow-ups` | Finds your sent Email 1's and drafts the next in-thread touch on cadence; skips anyone who replied |
| `/trellis-ae:accountability` | Checks Email 1's are sent, follow-ups + calls are happening, replies handled → flags gaps per AE |
| `/trellis-ae:reporting` | **Your morning briefing** — replies waiting, yesterday's emails/calls + outcomes, cadence health, what worked, and how many call tasks to line up today (read-only) |
| `/trellis-ae:create-tasks` | Creates the day's **call tasks** off the email cadence (the call analog of follow-ups) — deduped, due today, calling note attached. Calls only; never sends email |
| `/trellis-ae:ab-testing` | Consult on what's working by variant + co-design the next messaging test; proposes `ob-messaging` changes for your approval (never auto-applies). Experiments live in `config/ab-tests.md` |
| `/trellis-ae:local-visits` *(beta)* | Door-knock prep: text-message drafts (for your phone) + one lunch-invite email (Gmail draft) + walk-in talking points + a HubSpot visit task on your committed date |
| `/trellis-ae:sanity-check` | Audits the plugin's own skills/agents for sound process + outputs (structure, invariants, cross-agent consistency); read-only, proposes fixes. Run before a release |
| `contact-finder` (agent) | "Help me find this person" → Clay enrichment → HubSpot (reads `clay_mobile`) |
| `ob-cold` (agent) | **The single cold-motion agent** — research + value-prop/case-study pick + Email 1 + follow-up plan in one pass (Sonnet, low effort). Cold-outbound spawns just this per contact instead of the research+messaging trio, so a cold list drafts at ~a third the cost. Copy rules still live in `ob-messaging` |
| `ob-verification`, `ob-internal-research`, `ob-external-research`, `ob-messaging` (agents) | Shared RoE, research, and copywriting; used by closed-lost / local / qualify (and `ob-messaging` writes the later follow-up touches) |

**Each AE keeps 3 chats — one per motion** (cold / closed-lost / local) — and runs the matching skill there.

## Install
```
/plugin marketplace add eeleml/trellis-ae
/plugin install trellis-ae@trellis-ae
```
Then **turn on auto-update** so you stay current automatically: `/plugin` → **Marketplaces** → select
`trellis-ae` → toggle auto-update on. (Without this you'd have to update manually — see *Updating the team*.)

## One-time setup (per AE)
1. **Install** (the two commands above).
2. **Connect these connectors** in Claude → Settings → Connectors:
   - **HubSpot · Gmail · Fathom · Google Drive** — required. **List links are read via the HubSpot Lists v3 REST API using a private-app token** saved at `~/.hubspot-token` — `/trellis-ae:setup` collects it. AEs get a **read-only** list token from their admin (scope `crm.lists.read`); the admin keeps a separate **read+write** token for building assignment lists with `assigner`. The token is how the skills get the *true* list membership (the MCP's `ilsListIds` SQL filter is unreliable, and a degraded browser caps at the rendered rows). **Claude in Chrome** is an optional fallback when no token is set.
   - **Slack** — only if you'll run `accountability` or want reply alerts.
3. **Run `/trellis-ae:setup`** — it verifies your connectors, finds your HubSpot owner ID, saves your signature, has you paste the team **Clay webhook** (get it from your admin), locates the case-study index in Drive, and writes `~/.trellis-ae/config.json`.
4. **Schedule** via `/schedule`: follow-ups at 6 AM weekdays (and `accountability` weekly if you run it).

*(Optional: set `APOLLO_API_KEY` only if you use the Apollo enrichment fallback.)*

## How email works here
- **Two delivery paths for cold, by setup:**
  - **Instantly** (if `config.instantly.campaign_id` is set — cold only): the batch is approved in a **Google Doc or chat**, then the approved Email 1's are pushed into your **paused Instantly campaign**. You do a final review in Instantly and send from there; Instantly runs the cadence + threading. Replies + the "we already called them" stop-guard are handled by the central `instantly-sync` job. *(Phase 1 pushes E1; automated E2–E5 late-fill is the next build.)*
  - **Gmail** (default when Instantly isn't set up, and always for **closed-lost / local**): everything is a **Gmail draft** — you review and send from your inbox.
- Nothing is ever sent automatically — Instantly campaigns are pushed **paused**, Gmail items are **drafts**.
- **Gmail follow-ups are in-thread replies.** Email 1 drafts first; E2/E3/breakup thread off a *sent* message, so `follow-ups` drafts them as replies on a T+2/4/6 cadence and **skips anyone who replied.** (Instantly-pushed cold is marked so `follow-ups` leaves it to Instantly.)
- **Instantly setup:** run `/trellis-ae:setup` — it installs the connector, takes your API key (`~/.instantly-key`, never committed), and records your campaign + mailbox.

## Scheduling (set up after install — plugins can't ship cron)
Use `/schedule` to run `follow-ups` and `accountability` on a cadence (e.g., follow-ups each weekday
morning, accountability Friday). Each AE sets this up once.

## Data hygiene
This repo can be **public**: it holds no secrets and no customer data. Secrets live locally (Clay
webhook in `~/.clay-webhook`, Apollo key in env). Internal identifiers (owner ids, portal) live in
`~/.trellis-ae/config.json`. Case-study customer names/metrics live in `config/case-studies.md`, which is
**gitignored — never committed to the public repo** and baked into the shareable zip instead; the **Google
Drive** index stays the source of truth for updating it.

## Updating the team
Edit the skill/agent, bump `version` in **both** `plugins/trellis-ae/.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json` (the value in `plugin.json` wins, so keep them in sync), commit, and push.
If you don't bump the `version` string, Claude Code keeps the cached copy and **ignores the new commits**.

**Pushing does not auto-update installed AEs.** Third-party marketplaces don't auto-update by default, so
each AE picks up a new version one of two ways:

- **Auto-update (recommended, set once):** `/plugin` → **Marketplaces** → select `trellis-ae` → enable
  auto-update. Claude Code then refreshes and updates at startup; the AE just runs `/reload-plugins` if prompted.
- **Manual (each release):**
  ```
  /plugin marketplace update trellis-ae
  /plugin update trellis-ae@trellis-ae
  ```

To check the installed version: `/plugin` → **Installed**.

## Status
Built: `setup`, `qualify`, `cold-outbound`, `closed-lost`, `follow-ups`, `accountability`, `reporting`,
`create-tasks`, `ab-testing`, `sanity-check` + `contact-finder` + the 4 shared agents. `local-visits`
is in **beta** (drafted, not fully built out). Coming: a LinkedIn agent + copywriter (see ROADMAP).
