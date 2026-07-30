---
name: cold-outbound
description: Draft a cold Amazon outbound email sequence for a pasted list of contacts. Researches each prospect, checks Rules of Engagement, selects a value prop + case study, and leaves Email 1 as a Gmail draft for the AE to review and send. Use when an AE pastes a list of cold prospects ("here's my cold list for the week").
---

# Cold Outbound

You turn a pasted list of cold prospects into **reviewed-ready Gmail drafts** — one personalized
Email 1 per contact — so the AE spends their time reviewing and sending, not writing. You never send
anything; you draft. Keep the AE's time in chat minimal: do the work, then hand back a short summary.

## Input
The AE gives you the list one of two ways:
- **A HubSpot list link** — **read its members via the HubSpot Lists v3 REST API** (reliable; not the
  browser, not the SQL filter): with the token (`~/.hubspot-token`),
  `GET /crm/v3/lists/<id>/memberships/join-order?limit=250&after=…` (`<id>` = the number in the URL
  `.../objectLists/<id>`; page via `after`; use the returned `total` + record-ids, then batch-read
  properties via the MCP). **Do NOT use `query_crm_data`'s `hs_crm_search.ilsListIds` filter — it returns a
  capped, broad set, not the real list** (see the `assigner` gotcha). Only if no token is set, fall back to
  **Claude in Chrome** (`navigate` + `get_page_text`), which silently caps at the rendered rows of a
  virtualized table.
- **Pasted contacts** — emails, or names + companies.
**Always count the actual contacts and tell them the number — never assume a count.** Process the whole
list — the AE does NOT need to hand you a smaller batch. It runs in capped concurrency waves (see
**Pace & walk-away**) and drafts land in Gmail for later review, so a big list is fine; just give the
time estimate up front.

## Relies on (check once, ask only if missing)
- **Team config** at `~/.trellis-ae/config.json` (portal id, the AE's HubSpot owner id, case-study
  index pointer, signature). If absent, point them at `config/config.example.json` and ask them to
  create it.
- Connected MCPs: **Gmail** (drafting), **HubSpot** (records/RoE), **Fathom** (calls), and **Drive/
  Notion** (case studies). Load tools via ToolSearch as needed.

## Before you draft: pick the batch's A/B test
We improve outbound by testing, so before drafting, ask the AE **which experiment to run on this batch**
(one experiment per batch). Offer four paths:
1. **From the registry** — read `config/ab-tests.md` and list the experiments (id + one-line hypothesis +
   arms), e.g. *closer-style* (soft vs. clipped close). They pick one.
2. **Their own** — they describe a variant in their words; capture it as an ad-hoc experiment (id + 2 arms
   + which touch it changes), and offer to save it to `config/ab-tests.md`.
3. **Brainstorm from what's worked** — offer to run the **`ab-testing`** skill, which reads recent results
   by variant and co-designs a test from what's actually converting.
4. **Control only** — no test; draft everyone with the default messaging.
Keep it to one quick question; if they don't care today, default to **control only**.

Once they pick a test (1–3): for each cleared contact, assign an **arm** by a stable hash of the contact id
(even split across arms; the same contact always lands in the same arm on re-runs) and **stamp
`trellis_ab_variant = <experiment-id>:<arm>`** on the HubSpot contact (single-line text property — see
`config/ab-tests.md`). Pass the experiment + arm into `ob-cold` so it renders that arm on E1 (ob-cold
applies the A/B rules from `ob-messaging.md`), and `follow-ups` reads the same tag for the later touches
(e.g. closer-style changes E4 + the breakup). A contact is in
**one** experiment at a time — if it's already tagged into a running one, leave it.

## Pace & walk-away (don't make the AE babysit)
This is draft-only — nothing is sent — so the AE never needs to watch the run. Work unattended:
- **Set expectations once, before you start:** the contact count, a rough estimate (~1 min/contact), and
  "you don't need to watch this — I'll draft each Email 1 into your Gmail and summarize when it's done;
  come back and review then."
- **Run in capped waves.** Process at most **4 contacts concurrently**, starting the next as each finishes.
  Same list, just metered so a big run doesn't spike the rate limit and stall on retries. Do **not** fan
  out the whole list at once.
- **Keep a running tally** as waves complete (e.g. "12/30 — 9 drafted, 3 flagged") so the AE sees progress
  when they check back; don't narrate every tool call.
- **Throttling is self-correcting.** If you still hit a rate limit, let it back off and continue — don't
  shrink the list. Only drop to a smaller wave (2) if it's *persistently* throttled.
- The AE can override: "run it all at once" (fastest, higher throttle risk) or name a different wave size.

## Steps (per contact — run in capped waves; see Pace & walk-away above)
1. **Resolve + fetch once** (by email; else search name + company). In **one** `get_crm_objects` call, pull
   the contact + associated company with associations (owner, deals), the SmartScout fields, the RoE
   rollup properties, **and the `claude_roe_*` stamp**. Hold this record and **pass it to the subagents in
   steps 2–3** so they don't re-fetch the same thing (one read serves RoE + `ob-cold`).
2. **Rules of Engagement — a fresh `cleared` stamp is the ONLY thing that skips the live check.** Read the
   `claude_roe_*` stamp from the step-1 record. A stamp counts as **fresh + matching** only if
   `claude_roe_cleared_for` == this AE's owner id AND `claude_roe_motion == cold` AND
   `claude_roe_checked_date` is within 7 days. Then:
   - **`cleared` (fresh + matching)** → proceed, and **do NOT spawn `ob-verification`** (the credit saver —
     RoE was pre-cleared centrally by `assigner`).
   - **`blocked` or `flagged` (fresh + matching)** → **HOLD. Do not draft.** Surface the contact + its
     `claude_roe_note` to the AE. It stays held **unless the AE explicitly clears it or runs a live RoE
     check** — i.e. anything not affirmatively `cleared` is treated as not clear.
   - **No stamp / stale (>7d) / other AE / other motion** → spawn `ob-verification` (motion `cold`,
     requesting AE from config), **passing the step-1 record**. Whatever it returns that isn't
     `clear_to_contact` is held with the reason.
   In all cases, only an affirmative clear (fresh `cleared` stamp, or a live `ob-verification` that returns
   clear) lets you draft. Everything else is surfaced and held.
3. **Research + write — ONE agent (the cost saver).** Spawn the single **`ob-cold`** subagent (Task tool,
   `subagent_type: ob-cold`; it's pinned to **Sonnet at low effort**), **passing the step-1 record** and the
   batch's experiment/arm if one was picked. In that one pass it does the light internal read (from the
   passed record), the live external research (vertical + trigger, evidence-tagged), picks the value prop
   (`config/value-props.md` affinity) + ONE case study (baked `config/case-studies.md`, metric **verbatim**;
   the Drive index is the source of truth for updating the baked file + PDFs, fall back to it only if the
   baked file is missing), checks seasonality, and returns **E1 in full (subject + body) + a one-line plan
   per later touch** (angle + give/CTA; arc E1 new → E2 reply; E3 new → E4 reply → breakup), an
   `outreach_summary`, and `risks`. **This one spawn replaces the old internal-research + external-research +
   messaging trio for cold** (≈4 spawns → 1, and off Opus) — copy rules still live in `ob-messaging.md`,
   which `ob-cold` reads and follows, so you still never write, rewrite, or "polish" a subject/body yourself.
   It does NOT write E2–E5 bodies (that's `follow-ups`, at send time) and never sends or writes HubSpot.
   **If `ob-cold` returns a `risk` that isn't cleared** (e.g. it couldn't confirm the contact is a real
   person in that role) → **HOLD that contact** and surface it, don't draft. If the copy is unusable, re-run
   `ob-cold`; never substitute your own.
4. **Draft Email 1 in Gmail** — use ob-cold's E1 **subject and body exactly as returned** (only
   append the signature from config); never edit, shorten, or rewrite them. **First gate E1 against `ob-messaging`'s HARD CONSTRAINTS (the block at the top of that file) for the `cold` motion; if ANY fail, send it back to `ob-cold` to redo — do NOT fix it yourself.**
   Then `create_draft` (to: the prospect, subject, body, signature from config). **Never send.** Capture the draft id.
5. **Calling note + follow-up plan** — two writes on the contact record:
   - **Calling note** (HubSpot note, contact-level) — exactly **3 bullets, built for power-dialing**
     (glanceable in a dialer like Orum): two **pain points**, then one **historical context** — how/when
     we last engaged and **who they dealt with** (e.g. "cold — no prior contact", "replied to Ryan's Aug
     email", "demo with Fahim 5/12", "met Ethan at Prosper Show"). Name the prior rep/person when there's
     a real prior interaction; otherwise "cold — no prior contact." **Never put internal CRM ownership in
     the note** (no "owned by you / [rep]") — it isn't dialer-relevant. One short line each, no preamble.
   - **Follow-up plan** (so `follow-ups` can generate the later touches) — set `trellis_value_prop`,
     `trellis_batch_date`, `trellis_sequence_status = pending`, and put a COMPACT plan in
     `trellis_outreach_context`: value prop, the trigger, the per-touch angle **+ give/CTA** for
     E2/E3/E4/breakup (exactly as ob-cold returned them — this is how the audit-at-most-once cap
     carries into the later touches), the
     threading map (A: E1→E2 reply; B: E3 new→E4 reply→breakup reply), and E1's subject. Do NOT store
     full bodies — `follow-ups` writes each touch from this plan + the live thread at send time.

## Hand back (keep it short)
- "Drafted **N** Email 1's in your Gmail — review and send." 
- "**M** flagged, not drafted:" list each with the one-line RoE reason (owner / active deal / replied).
- Reminder: "Follow-ups draft on cadence once you've sent — **Email 2** replies to Email 1; **Email 3**
  opens a NEW thread; **Email 4** replies to Email 3; the **breakup** replies on that thread. Run
  `/trellis-ae:follow-ups` (or let the scheduled check do it). Anyone who replies is auto-skipped."

## Rules
- **Draft only — never send.** No fixed list cap — process the whole list in capped concurrency waves (≤4 at a time; see **Pace & walk-away**), no smaller-batch babysitting required. Respect RoE (step 2 is not optional).
- **All prospect-facing copy comes from an agent, following `ob-messaging.md`'s rules — never you.** E1 is written by `ob-cold` (which reads + obeys `ob-messaging.md`); each later touch is written by `ob-messaging` inside `follow-ups` at send time. You may not write, rewrite, shorten, paraphrase, or "polish" any subject or body. If a line didn't come from `ob-cold` (E1) or `ob-messaging` (later touches), it doesn't go in the draft.
- Never fabricate emails, phones, metrics, or events. Case-study numbers are used verbatim from the index.
- Don't narrate every tool call — do the work, then give the summary.
