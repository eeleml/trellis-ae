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

When the list comes as a **HubSpot list link**, **read its members via the HubSpot Lists v3 REST API** (reliable; not the browser, not the SQL filter): with the token (`~/.hubspot-token`), `GET /crm/v3/lists/<id>/memberships/join-order?limit=250&after=…` (`<id>` = the number in the URL `.../objectLists/<id>`; page via `after`; use the returned `total` + record-ids, then batch-read properties via the MCP). **Do NOT use `query_crm_data`'s `hs_crm_search.ilsListIds` filter — it returns a capped, broad set, not the real list** (see the `assigner` gotcha). Only if no token is set, fall back to **Claude in Chrome** (`navigate` + `get_page_text`), which silently caps at the rendered rows of a virtualized table. **Count the actual contacts and report the number — never assume 25.** Process the whole list — no smaller batch needed; it runs in capped waves (see **Pace & walk-away**) and drafts land in Gmail for later review. For a large list, just give the time estimate up front.

## Eligibility (who's in-bounds)
- **≥ 3-month cool-off** since the deal closed lost — an RoE/ownership rule; don't re-poke a fresh
  loss. In the **3–6-month+** window they're an opportunity again — reach out.
- **Hard-exclude** (never re-engage): out of business, explicit do-not-contact / opt-out. (Read
  `closed_lost_reason` + the opt-out flag.)
- **Signed with a competitor is NOT an exclusion** → route to a **check-in track** (see Messaging). If
  the timing of their signing is knowable (notes / Fathom / research), time the outreach toward their
  likely renewal.

## Pace & walk-away (don't make the AE babysit)
Draft-only — nothing is sent — so the AE never needs to watch the run. Tell them up front: the count, a
rough estimate, and "you don't need to watch this — I'll draft into your Gmail and summarize when done."
Then run **at most 4 contacts concurrently**, starting the next as each finishes — same list, just metered
so a big run doesn't spike the rate limit and stall on retries. Keep a running tally as waves complete; if
throttled, let it back off and continue rather than shrinking the list. The AE can override the wave size.

## Per-contact pipeline (run in capped waves; see Pace & walk-away above)
1. **Resolve** the contact + company + the **Closed Lost deal**. Pull the **full lost-reason picture**,
   not just the category: `closed_lost_category` + `closed_lost_reason_1`/`_2` (the structured reason),
   `closed_lost_reason` (the free-text *"Closed Lost Reason Comment"*), `closed_lost_reason_comment_product`
   (the product/feature gap that lost it), and `closed_lost_reason_comment_competitor` + `who_we_lost_to`
   (if they went elsewhere). Also pull the **close date** — this is **when we last spoke**, the anchor for
   the "what's new since" cross-reference — plus the stage reached and the most-recent deal owner.
2. **RoE** — spawn `ob-verification` (motion `closed_lost`): it surfaces the owner (flag, don't block),
   and **does block** on a new open deal, recent reply/meeting/call, customer/won, or opt-out. Then
   apply the eligibility filter; drop hard-excludes and anything still in the 3-month cool-off.
3. **Research** — spawn `ob-internal-research` (motion `closed_lost`: deal history + **Fathom objection
   calls first**) and `ob-external-research` (what's changed on their side) in parallel.
4. **What's new since they passed** — read **`config/whats-new.md`** and pick the Trellis release(s)
   **dated after the deal's close date** (when we last spoke), preferring the one that answers their lost
   reason (especially the product/feature gap in `closed_lost_reason_comment_product`). If nothing
   postdates the close date, there's no "new since" angle — fall back to what's changed on their side +
   "how did it go." Never use a release that isn't in `whats-new.md` or that predates the conversation.
5. **Message** — hand `ob-messaging` the full angle inputs: the **full lost reason** (category +
   reason_1/2 + the free-text comment + product/competitor comments), whether they signed with a
   competitor, the **"what's new since" release** (or none) from step 4, plus the value prop + a verified
   case study (live from Drive/Notion, metric verbatim). You **MUST** spawn the **`ob-messaging`**
   subagent (Task tool, `subagent_type: ob-messaging`; motion `closed_lost`). It tailors the re-engagement
   angle to why they passed (price → new ROI; **missing feature → name the actual release from
   `whats-new.md` that closes that gap**; timing → "is now better?"; no bandwidth → fully-managed;
   **competitor-signed → a check-in tone, not a pitch**), leads from the prior conversation, and writes the
   same **5-touch sequence sent as the most recent deal owner** (the rep who met them; if that owner is an
   inactive user, flag for reassignment to a live rep). *(Angle logic + voice live in `ob-messaging`.)*
6. **Preview, then draft Email 1 in Gmail.** First **show the AE, in chat, the chosen angle + E1
   (subject + body)** — including which lost reason and which "what's new" release it leans on — so they
   can sign off **before anything lands in Gmail**. (For a large batch, preview a representative sample +
   the angle logic rather than making them approve all 25 one by one.) On the AE's OK: use ob-messaging's
   E1 **verbatim** (append only the signature); **first gate it against `ob-messaging`'s HARD CONSTRAINTS
   for the `closed_lost` motion — if any fail, send it back to redo, don't fix it yourself.** Then
   `create_draft` (to the prospect; never send). Capture the draft id.
7. **Calling note + follow-up plan** (same mechanism as cold):
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
- **All prospect-facing copy comes from `ob-messaging`, used verbatim** — never write or rewrite it yourself; gate every draft against ob-messaging's HARD CONSTRAINTS first.
- Respect the 3-month cool-off and hard-excludes. Competitor-signed → check-in, not a pitch.
- Never fabricate the prior conversation — pull it from HubSpot/Fathom; if there's no record, say so
  and keep it light ("wanted to reconnect"). **Same for "what's new": cite a Trellis release only if it's
  in `config/whats-new.md` AND postdates the last contact — never invent "we shipped X."**
- Cap 25; respect RoE (flag owner, block on active motion / opt-out).
