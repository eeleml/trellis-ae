# trellis-ae — Roadmap / To-Do

Living build plan for the AE outbound plugin. (Safe to ship — no secrets or customer data.)

## ✅ Done
- Plugin spine: manifests, `contact-finder`, shared subagents (`ob-verification`, `ob-internal-research`, `ob-external-research`), `value-props`, `config.example`, README.
- **`cold-outbound`** skill (flagship): RoE check → research → value prop + case study → **Email 1 drafted in Gmail**.
- **Email threading locked:** Thread A = E1 → E2 (reply); Thread B = E3 (new) → E4 (reply) → breakup (reply). E1 & E3 are new sends; E2, E4, breakup are in-thread replies.
- **`follow-ups` skill built** — business-day cadence T+0/2/4/6/8 (skip weekends), Gmail-as-truth, reply/bounce → stop + flag TODAY, OOO → hold until back, no double-drafts, regenerates from the stored plan. Scheduled 6 AM weekdays (prompts AE to set it up).
- **Calling note spec decided + built into `cold-outbound`:** contact-level HubSpot note, **3 bullets** = 2 pain points + 1 historical context, glanceable for power-dialing. Follow-up plan lives in `trellis_outreach_context` + the `trellis_*` properties.
- **`ob-messaging` shared agent built** — messaging extracted out of the skills into one tunable copywriter (cold / closed_lost / follow_up / local). `cold-outbound`, `closed-lost`, and `follow-ups` now delegate copy to it, so the team tunes voice in one place + pushes one update.
- **`closed-lost` skill built** — re-engagement, deal-history + Fathom-first, lost-reason-driven angle, **same 5-touch**. Two intake modes (curated = trust assignment; self-serve = query HubSpot Closed Lost + flag owner, fair game if RoE clear). **≥3-month cool-off**; hard-exclude out-of-business / do-not-contact; **competitor-signed → check-in track** (timed near renewal). Added a universal opt-out / do-not-contact stop to `ob-verification`.
- **`reporting` skill built (v1 — pending a live test)** — AE-facing **morning briefing**, read-only. Run `/trellis-ae:reporting`: replies waiting, yesterday's emails sent + cadence health, calls + dispositions, what worked (with the value prop/subject behind it), review/flags, then tees up how many call tasks for today (hand-off to the future `create-tasks` step). Self-scoped to the running AE by default; manager all-AE rollup. Sources: Gmail sent/replies + HubSpot calls/dispositions/lifecycle/deals (shares the metric layer with `accountability`). No open rate unless a tracker is added.
- **`create-tasks` skill built** — the call analog of `follow-ups`: reads who's due for a call off the email cadence, confirms the count with the AE, and creates **deduped** HubSpot call tasks due today with the 3-bullet calling note attached. **Calls only** — never sends email (those stay Gmail drafts) or auto-dials. Pairs with `reporting`'s "how many calls today?" hand-off.
- **`ab-testing` skill built (phase 1)** — consultative experimentation brain: reads outbound results **by `trellis_ab_variant`**, judges with honest sample-size caveats, co-designs the next test with the AE, and drafts proposed variants via `ob-messaging` — **proposes, never auto-applies**. Registry at `config/ab-tests.md`; first experiment `cs-format` (none / PDF / link). Phase 2 (variant assignment + attach-PDF/link in the send path) pending.
- **`sanity-check` skill built** — read-only QA audit of the plugin itself: structure (manifests/versions/frontmatter), per-agent consistency + valid cross-references, the system invariants, cross-agent contradictions, and an optional live-output spot-check. Severity-ranked findings + proposed fixes; never edits or sends.
- **`qualify` skill built** — the **Verify stage** of the weekly ICP pipeline (`sourced` → **`verified` / `failed_verification` / `failed_enrollment`** → `assigned`), run at the **contact** level. Vets a list before assignment/work: email present + a real person (role-based/stale flags), still-employed (via `ob-external-research`), deliverable (optout / hard-bounce / quarantine / invalid → `failed_enrollment`; ignores `hs_marketable_status`), and not already in a sequence or a recent deal (in-sequence or closed-deal &lt;2mo → Revisit; closed 2–6mo → flag). Two modes (general vs for-a-specific-AE, RoE via a new `qualify` motion on `ob-verification` that flags-not-blocks). Confirm-before-write; idempotent (won't flip `assigned`). Standalone or a pre-gate inside `cold-outbound`. *(Adversarially reviewed: all HubSpot property names verified live in portal 6658395.)*

## 🚧 In progress / not fully built out yet
- **`local-visits` skill — NOT fully built out yet.** v1 drafted (the skill `SKILL.md` + the `local` mode in `ob-messaging` exist): in-person motion — RoE (`local`) → research → **text-message drafts** (copy for the AE's phone) + **one lunch-invite email** (Gmail draft) + **walk-in talking points** + a **HubSpot visit task** dated to when the AE commits to go. Cap 15/run; does NOT enter the 5-touch `follow-ups` cadence (next action is the visit, not an email sequence); route/day planning stays in Ethan's separate planner; post-visit thank-you is opt-in. **Still needs:** testing + sign-off before it's production-ready.

## 🔨 Claude's build tasks (next, in order)
1. ✅ **`follow-ups`** — built (see Done).
2. ✅ **`closed-lost`** — built (see Done).
3. 🚧 **`local-visits`** — v1 drafted but **NOT fully built out yet** (needs testing + sign-off; see In progress).
4. ✅ **`accountability`** — built. Checks Email 1 sent + follow-ups on cadence + ~2 calls in 4 business days + replies handled (skips converted); flags gaps per AE to Slack + a HubSpot note. Shares the metric layer with `reporting`. Run on a weekday `/schedule`.
5. ✅ **`reporting`** — built as a skill (v1, pending a live test; see Done).
6. 🟡 **`ab-testing`** — **phase 1 built** as a skill (`/trellis-ae:ab-testing`) + registry `config/ab-tests.md`: consultative readout — reads results by `trellis_ab_variant`, judges with honest sample-size caveats, co-designs the next test, drafts variants via `ob-messaging` (proposes, never auto-applies). **Phase 2 (pending):** wire variant assignment into `cold-outbound` + the attach-PDF / insert-HubSpot-link capability so experiments can run. First experiment defined: `cs-format` (none / PDF / link).
7. ✅ **`create-tasks`** — built as a skill (`/trellis-ae:create-tasks`): the call analog of `follow-ups` — reads who's due for a call off the email cadence, confirms the count, creates **deduped** call tasks due today with the calling note attached. Calls only; never sends email or auto-dials.
8. ✅ **`sanity-check`** — built as a skill (`/trellis-ae:sanity-check`): read-only audit of the plugin's own skills/agents — structure (manifests/versions/frontmatter), per-agent consistency, the system invariants, cross-agent contradictions, optional output spot-check. Severity-ranked findings + proposed fixes; never edits.

## 🔭 Later / future
- **`linkedin` agent** — a LinkedIn outbound motion (connection requests + follow-up DMs / InMail), RoE-aware, **drafted for AE review — never auto-sends**. Pairs with the email + call motions toward a multi-channel cadence.
- **LinkedIn copywriter** — LinkedIn-specific copy (short, native LinkedIn voice, no email formality), analogous to `ob-messaging` for email — likely a `linkedin` mode in `ob-messaging` or a sibling agent.

## 🧩 Ethan's decisions / setup
- ~~Calling notes~~ **DECIDED & built:** contact-level note, 3 bullets (2 pain points + 1 historical context), glanceable for power-dialing.
- **Local motion:** v1 drafted (texts + lunch-invite email + talking points + a dated visit task) but **not fully built out yet** — needs testing/sign-off. Route / timing planning stays in Ethan's separate planner. Scope can still expand (multi-stop batching, post-visit follow-up).
- **Repo:** public GitHub repo live at `eeleml/trellis-ae`; marketplace + plugin published. Update flow: bump `version` in **both** manifests, commit, push (see README "Updating the team").
- **`~/.trellis-ae/config.json`:** fill portal id, AE owner ids, case-study index pointer, signature.
- **Case-study index → Drive/Notion** (so messaging reads verified metrics live; nothing customer-specific in the repo).
- **Per-AE one-time setup:** connect Gmail / HubSpot / Fathom / Drive / Notion MCPs; paste Clay webhook (`~/.clay-webhook`); optional `APOLLO_API_KEY`.
- **Scheduling:** each AE sets `follow-ups` + `accountability` (+ `reporting` if desired) cadence via `/schedule` (plugins can't ship cron).

## ❓ Open questions
- **Cadence days** for the 5 touches (currently placeholder T+0/2/4/6/8) — confirm.
- Draft-only now; **auto-send** later? (currently always draft, AE sends.)
- Does the local-visits motion also need a post-visit follow-up email? (v1: opt-in — the AE can ask for one after the visit.)
- **Call/email orchestration (for `create-tasks`) — DECIDED:** call tasks only (no email steps); **emails stay in Gmail** (drafted by cold-outbound / follow-ups; AE sends), and the AE marks the matching call task complete. **Never send from HubSpot.** Still open: formal HubSpot **Sequences** vs. plain dated **call tasks** as the call scaffold (leaning plain tasks).
