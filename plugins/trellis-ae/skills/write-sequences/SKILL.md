---
name: write-sequences
description: CENTRAL pre-write of full cold email sequences. Given a verified/assigned list, it researches each contact and writes all five cold touches (E1–E5) onto the contact's trellis_email_* properties, so AEs can later pull + review + push them with almost no token cost. Token-HEAVY by design — meant to run on the admin machine at off-peak. If you just want to work a cold list today, use /trellis-ae:cold-outbound instead. Use when someone says "pre-write sequences," "bake the emails," "write-sequences," or is prepping lists for the team.
---

# Write Sequences (central pre-write)

You research every contact on a list and write the **full 5-touch cold sequence** onto each contact in
HubSpot, so the expensive generation happens **once, centrally**, and AEs just pull + review + push (near
zero cost on their side). You never send and never push to Instantly — you write the emails onto the
`trellis_email_*` properties for later review.

## ⚠️ FIRST — confirm this is the run they want (it's the expensive one)
Before generating anything, say this plainly and get an explicit **yes**:

> "This is the **token-heavy** central pre-write: I research every contact and write all five emails each.
> It's meant to run on the admin machine at off-peak, not on an AE's. **If you're an AE just trying to
> work today's cold list, stop and run `/trellis-ae:cold-outbound` instead** — it pulls these pre-written
> emails and costs almost nothing. This will write full sequences for **N** contacts. Proceed?"

Fill in **N** (the real, counted list size). Only proceed on an explicit yes. If they hesitate or it sounds
like they wanted to send today, point them to `cold-outbound` and stop. (This is the whole guardrail — the
cost lives here, so don't let it run by accident.)

## Intake
A **HubSpot list link** (the verified / assigned pool) or **pasted contacts**. Read a list link via the
HubSpot Lists v3 REST API (token at `~/.hubspot-token`): `GET /crm/v3/lists/<id>/memberships/join-order?limit=250&after=…`,
then batch-read properties via the MCP. **Count the real members and report N** (used in the gate above).
Not gated on `assigner` — point it at any list; it just needs contacts.

## A/B variant (chosen here — this is where the copy is written)
If an experiment is running (`config/ab-tests.md`), assign each contact an **arm** by a stable hash of the
contact id (even split; same contact → same arm on re-runs), **stamp `trellis_ab_variant = <experiment>:<arm>`**,
and pass the arm to `ob-cold` so it writes that arm's copy. Default = **control** (no tag). `cold-outbound`
pushes whatever was written and carries the tag; `ab-testing` groups results by it. One experiment per contact.

## Relies on
- **Team config** `~/.trellis-ae/config.json`. Connected **HubSpot** MCP (records + the `trellis_email_*`
  properties). Spawns **`ob-cold`** (the full-sequence writer). Case studies from the baked
  `config/case-studies.md`. Load tools via ToolSearch as needed.

## Per contact (capped waves — see Pace; it's a big off-peak run)
1. **Fetch once** (by email; else name + company): contact + associated company with associations + SmartScout
   + the `claude_roe_*` stamp + existing `trellis_email_*` (for idempotency). Hold it, pass to `ob-cold`.
2. **Skip the ones we shouldn't write** (don't burn generation on them):
   - **RoE stamp says blocked** (`claude_roe_status == blocked`), opted out / do-not-contact, or a **dead
     lifecycle** (Disqualified / Wrong Info / Churned / customer) → **skip**, don't generate. (Reads the
     stamp; does not re-run RoE — that's `assigner`/`ob-verification`'s job.)
   - **Already written + fresh** (`trellis_email_1_body` set and `trellis_sequence_written_date` recent) →
     **skip** unless the user asked to rewrite. Idempotent.
3. **Generate** — spawn **`ob-cold`** (Task tool, `subagent_type: ob-cold`; it's Sonnet/low-effort),
   passing the step-1 record. It researches + writes the **full E1–E5** (per `ob-messaging` rules) and
   returns the five emails + `outreach_summary` + a give/CTA note per touch + any `risks`.
4. **Stamp the emails onto the contact** (`manage_crm_objects`, ≤10/batch — see [[hubspot-write-mechanics]]):
   - `trellis_email_1_subject` ← e1_subject · `trellis_email_1_body` ← e1_body
   - `trellis_email_2_body` ← e2_body
   - `trellis_email_3_subject` ← e3_subject · `trellis_email_3_body` ← e3_body
   - `trellis_email_4_body` ← e4_body · `trellis_email_5_body` ← breakup_body
   - `trellis_sequence_written_date` ← today (`YYYY-MM-DD`)
   - also `trellis_value_prop` and the compact plan/trigger in `trellis_outreach_context` (context for
     `cold-outbound` + reporting).
   - **If `ob-cold` returned an uncleared `risk`** (e.g. couldn't confirm the contact is a real person) →
     **do NOT stamp**; add to a **Held** list with the reason (feeds contact-finder / your review).
   > **Property guard:** if HubSpot errors that any `trellis_email_*` property is unknown, **stop and tell
   > the user** — they need creating (see the plugin's property setup); don't improvise onto other fields.
5. **Verify the writes** — after a fanned-out batch write, **re-query** a sample (agents can silently miss
   one yet report 100%; see [[verify-bulk-subagent-writes]]).

## Pace & walk-away
Set expectations once: N contacts, ~1–2 min each, "you don't need to watch this — kick it off and come
back; I'll write each sequence onto the contact and summarize." Run **≤4 concurrent**, metered so a big
off-peak run doesn't spike the rate limit. Keep a running tally. This is the run to schedule at off-peak
on the admin machine.

## Hand back (short)
- "Wrote full 5-touch sequences onto **W** contacts. Skipped **S** (blocked/dead/opted-out or already
  written). **H** held (unconfirmed contact / risk) — listed below."
- Held contacts (ids + reason). Any property-guard or write-verify issues.
- Reminder: "AEs now run `/trellis-ae:cold-outbound` on this list — it pulls these, they approve in the
  Doc/chat, and it pushes to Instantly. Near-zero cost on their end."

## Rules
- **The intent gate is not optional** — always confirm before generating; steer casual/AE runs to `cold-outbound`.
- **Never send; never push to Instantly.** You only write the `trellis_email_*` properties (drafts for review).
- **Respect the RoE stamp** (skip blocked/opted-out/dead); don't re-run RoE here.
- **Idempotent** — skip already-written-and-fresh contacts unless asked to rewrite; never re-stamp the date
  when nothing changed.
- **Never fabricate** — copy comes from `ob-cold` (following `ob-messaging`); case-study metrics verbatim;
  an unconfirmed contact is held, not written.
- No fixed cap — report the real count; offer to batch a very large list.
