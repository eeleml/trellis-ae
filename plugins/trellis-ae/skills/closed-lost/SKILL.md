---
name: closed-lost
description: Re-engage closed-lost contacts — people who already know Trellis and previously said no. Pulls deal history + the original objection (Fathom) first, tailors the angle to why they passed, respects a 3-month cool-off and Rules of Engagement, and drafts a 5-touch re-engagement sequence into Gmail for review. Use when an AE pastes a closed-lost list or asks "get me closed-lost accounts."
---

# Closed-Lost Re-Engagement

You re-open conversations with people who already know Trellis and previously passed. The hook is
**"what's changed since you said no"** — so you lead from the prior conversation and the original
objection, never a cold pitch. Everything is drafted into Gmail for the AE to review and send; you
never send.

## Intake — two modes
- **Curated list** (Ethan handed the AE a list, or the AE pastes specific contacts): targeting and
  assignment are already decided — **trust it**. Still run the RoE checks, but **don't block on
  existing ownership**.
- **Self-serve** ("get me closed-lost accounts in <segment>"): query HubSpot for **Closed Lost** deals
  matching the ask, apply the eligibility filter, then follow RoE — **flag the existing owner**, but
  it's fair game as long as RoE is otherwise clear. Report owners so routing can be confirmed.

When the list comes as a **HubSpot list link**, open it with **Claude in Chrome** (`navigate` + `get_page_text`, paging through) to read the members. **Count the actual contacts and report the number — never assume 25.** Process the whole list; for large lists (40+), confirm before a long run or offer to batch.

## Eligibility (who's in-bounds)
- **≥ 3-month cool-off** since the deal closed lost — an RoE/ownership rule; don't re-poke a fresh
  loss. In the **3–6-month+** window they're an opportunity again — reach out.
- **Hard-exclude** (never re-engage): out of business, explicit do-not-contact / opt-out. (Read
  `closed_lost_reason` + the opt-out flag.)
- **Signed with a competitor is NOT an exclusion** → route to a **check-in track** (see Messaging). If
  the timing of their signing is knowable (notes / Fathom / research), time the outreach toward their
  likely renewal.

## Per-contact pipeline
1. **Resolve** the contact + company + the **Closed Lost deal**. Pull `closed_lost_reason`, the stage
   reached, the close date, and the original owner.
2. **RoE** — spawn `ob-verification` (motion `closed_lost`): it surfaces the owner (flag, don't block),
   and **does block** on a new open deal, recent reply/meeting/call, customer/won, or opt-out. Then
   apply the eligibility filter; drop hard-excludes and anything still in the 3-month cool-off.
3. **Research** — spawn `ob-internal-research` (motion `closed_lost`: deal history + **Fathom objection
   calls first**) and `ob-external-research` (what's changed on their side) in parallel.
4. **Message** — read the **lost reason** (`closed_lost_reason`) and whether they signed with a
   competitor, pick the value prop + a verified case study (live from Drive/Notion, metric verbatim),
   then spawn the **`ob-messaging`** shared agent (motion `closed_lost`) with all of that. It tailors the
   re-engagement angle to why they passed (price → new ROI; missing feature → "we built it"; timing →
   "is now better?"; no bandwidth → fully-managed; **competitor-signed → a check-in tone, not a pitch**),
   leads from the prior conversation, and writes the same **5-touch sequence sent as the most recent deal owner** (the rep who actually met with them — not necessarily the contact owner; if that owner is an inactive user, flag for reassignment to a live rep).
   *(The angle logic + voice live in `ob-messaging` — one place to tune.)*
5. **Draft Email 1 in Gmail** (`create_draft`, to the prospect; never send). Capture the draft id.
6. **Calling note + follow-up plan** (same mechanism as cold):
   - **Calling note** (contact-level, 3 bullets, power-dialing): two pain points, then one historical
     bullet = **the lost reason + when** (e.g. "lost on price, demo 11/24" or "signed w/ <competitor>
     Q1'25 — checking in").
   - **Follow-up plan** in `trellis_outreach_context` + set `trellis_value_prop`, `trellis_batch_date`,
     `trellis_sequence_status = pending`. `follow-ups` runs the cadence from here.

## Hand back (short)
- "Drafted **N** re-engagement Email 1's — review + send."
- "**M** excluded:" hard-nos (out of business / do-not-contact) and anything still in the 3-month
  cool-off, with reasons.
- "**Owned (FYI):** <list + owner>" — for self-serve runs, so you can confirm routing.
- "**How it ended (your go/no-go):**" per contact, the lost reason + how it ended — and if they **signed with a competitor**, name it + the **contract length/renewal timing** so you can decide pursue-now (worth a check-in) vs. wait-for-renewal.
- "**Cleanup flags:**" any **duplicate records to merge**, and any **inactive deal owner to reassign** to a live rep before sending.
- Reminder that `follow-ups` drafts the rest on cadence once E1 is sent.

## Rules
- **Draft only — never send.** Lead from the prior conversation + what's changed, never a cold pitch.
- Respect the 3-month cool-off and hard-excludes. Competitor-signed → check-in, not a pitch.
- Never fabricate the prior conversation — pull it from HubSpot/Fathom; if there's no record, say so
  and keep it light ("wanted to reconnect").
- Cap 25; respect RoE (flag owner, block on active motion / opt-out).
