# trellis-ae — Roadmap / To-Do

Living build plan for the AE outbound plugin. (Safe to ship — no secrets or customer data.)

## ✅ Done
- Plugin spine: manifests, `contact-finder`, shared subagents (`ob-verification`, `ob-internal-research`, `ob-external-research`), `value-props`, `config.example`, README.
- **`cold-outbound`** skill (flagship): RoE check → research → value prop + case study → **Email 1 drafted in Gmail**.
- **Email threading locked:** Thread A = E1 → E2 (reply); Thread B = E3 (new) → E4 (reply) → breakup (reply). E1 & E3 are new sends; E2, E4, breakup are in-thread replies.
- **`follow-ups` skill built** — business-day cadence T+0/2/4/6/8 (skip weekends), Gmail-as-truth, reply/bounce → stop + flag TODAY, OOO → hold until back, no double-drafts, regenerates from the stored plan. Scheduled 6 AM weekdays (prompts AE to set it up).
- **Calling note spec decided + built into `cold-outbound`:** contact-level HubSpot note, **3 bullets** = 2 pain points + 1 historical context, glanceable for power-dialing. Follow-up plan lives in `trellis_outreach_context` + the `trellis_*` properties.
- **`ob-messaging` shared agent built** — messaging extracted out of the skills into one tunable copywriter (cold / closed_lost / follow_up). `cold-outbound`, `closed-lost`, and `follow-ups` now delegate copy to it, so the team tunes voice in one place + pushes one update.
- **`closed-lost` skill built** — re-engagement, deal-history + Fathom-first, lost-reason-driven angle, **same 5-touch**. Two intake modes (curated = trust assignment; self-serve = query HubSpot Closed Lost + flag owner, fair game if RoE clear). **≥3-month cool-off**; hard-exclude out-of-business / do-not-contact; **competitor-signed → check-in track** (timed near renewal). Added a universal opt-out / do-not-contact stop to `ob-verification`.

## 🔨 Claude's build tasks (next, in order)
1. **`follow-ups`** skill — implement the threading map: find the sent Email 1 (Gmail `search_threads` `to:<email> in:sent`) → draft E2 as a reply; open E3 as a NEW thread; E4 reply to E3; breakup reply. Cadence-driven; **skip anyone who replied**.
2. ✅ **`closed-lost`** — built (see Done).
3. **`local-visits`** skill — **text-message drafts** (copy for the AE's phone) + **one lunch-invite email** (prompt AE: specific dates vs "sometime") + walk-in talking points + a HubSpot visit task.
4. ✅ **`accountability`** — built. Checks Email 1 sent + follow-ups on cadence + ~2 calls in 4 business days + replies handled (skips converted); flags gaps per AE to Slack + a HubSpot note. Shares the metric layer with `reporting`. Run on a weekday `/schedule`.
5. **`reporting` agent** — rates: conversion, reply, meeting, call-connect, call-booking, wrong-number, not-interested (+ open rate ONLY if a tracker is added — see open Q). Sources: HubSpot CALL `hs_call_disposition` (Nooks) + lifecycle/deals + Gmail replies/sends. Segments by motion / value prop / variant / AE. Weekly. Shares the metric layer with `accountability`.
6. **`ab-testing` agent** — reads the report and tunes messaging toward what works by **proposing** edits to `ob-messaging` / an A/B config (human-approved, not auto). DEPENDS ON: `ob-messaging` emitting A **and** B variants + a `trellis_ab_variant` tag, and a minimum sample before calling a winner.
5. **Calling notes** (DEFERRED — needs Ethan's input, see below) — create a HubSpot note for call prep.

## 🧩 Ethan's decisions / setup
- ~~Calling notes~~ **DECIDED & built:** contact-level note, 3 bullets (2 pain points + 1 historical context), glanceable for power-dialing.
- **Local motion (evolving):** Ethan is building the route/timing planner separately; `local-visits` should also get the AE to commit to *when* they'll visit. Local will include text-message drafts + some emails — scope to be expanded.
- **Repo plan:** create the public GitHub repo, push the marketplace, write the AE install + setup steps. (gh isn't installed locally — push via `git` + GitHub web, or install `gh`.)
- **`~/.trellis-ae/config.json`:** fill portal id, AE owner ids, case-study index pointer, signature.
- **Case-study index → Drive/Notion** (so messaging reads verified metrics live; nothing customer-specific in the repo).
- **Per-AE one-time setup:** connect Gmail / HubSpot / Fathom / Drive / Notion MCPs; paste Clay webhook (`~/.clay-webhook`); optional `APOLLO_API_KEY`.
- **Scheduling:** each AE sets `follow-ups` + `accountability` cadence via `/schedule` (plugins can't ship cron).

## ❓ Open questions
- **Cadence days** for the 5 touches (currently placeholder T+0/2/4/6/8) — confirm.
- Draft-only now; **auto-send** later? (currently always draft, AE sends.)
- Does the local-visits motion also need a post-visit follow-up email?
