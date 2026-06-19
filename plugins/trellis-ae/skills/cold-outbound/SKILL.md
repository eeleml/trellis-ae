---
name: cold-outbound
description: Draft a cold Amazon outbound email sequence for a pasted list of contacts. Researches each prospect, checks Rules of Engagement, selects a value prop + case study, and leaves Email 1 as a Gmail draft for the AE to review and send. Use when an AE pastes a list of cold prospects ("here's my cold list for the week").
---

# Cold Outbound

You turn a pasted list of cold prospects into **reviewed-ready Gmail drafts** — one personalized
Email 1 per contact — so the AE spends their time reviewing and sending, not writing. You never send
anything; you draft. Keep the AE's time in chat minimal: do the work, then hand back a short summary.

## Input
The AE pastes a list (up to ~25) — emails, or names + companies. If it's longer than 25, do the
first 25 and tell them you'll take the rest in a second pass.

## Relies on (check once, ask only if missing)
- **Team config** at `~/.trellis-ae/config.json` (portal id, the AE's HubSpot owner id, case-study
  index pointer, signature). If absent, point them at `config/config.example.json` and ask them to
  create it.
- Connected MCPs: **Gmail** (drafting), **HubSpot** (records/RoE), **Fathom** (calls), and **Drive/
  Notion** (case studies). Load tools via ToolSearch as needed.

## Steps (per contact — run contacts concurrently where you can)
1. **Resolve** the contact in HubSpot (by email; else search name + company). Get the contact, the
   associated company, and the SmartScout fields on the company record.
2. **Rules of Engagement** — spawn the `ob-verification` subagent (motion: `cold`, requesting AE
   from config). If `clear_to_contact = false`, DO NOT draft — add to the flagged list with the
   reason. Only proceed for cleared contacts.
3. **Research** — spawn `ob-internal-research` and `ob-external-research` in parallel (motion `cold`).
4. **Message** — choose the best value prop (`config/value-props.md` affinity + the research) and ONE
   case study read **live** from the team case-study index (Drive/Notion pointer in config) — use its
   metric **verbatim**; if the vertical isn't covered, use the strongest in-value-prop metric as generic
   cross-category proof. Then spawn the **`ob-messaging`** shared agent (motion `cold`) with the research
   + chosen value prop + case study. It returns the full **5-touch sequence** (E1 new → E2 reply; E3 new
   → E4 reply → breakup), the per-touch angles for the follow-up plan, and a short outreach summary —
   all in Trellis voice. *(Sequence structure, lengths, threading, and tone live in `ob-messaging`, so
   the team tunes messaging in one place.)*
5. **Draft Email 1 in Gmail** — `create_draft` (to: the prospect, subject, body; signature from
   config). **Never send.** Capture the draft id.
6. **Calling note + follow-up plan** — two writes on the contact record:
   - **Calling note** (HubSpot note, contact-level) — exactly **3 bullets, built for power-dialing**
     (glanceable in a dialer like Orum): two **pain points**, then one **historical context** (how/when
     we last engaged — e.g. "cold — no prior contact", "replied to our Aug email", "demo on 5/12",
     "met at Prosper Show"). One short line each, no preamble.
   - **Follow-up plan** (so `follow-ups` can regenerate the sequence) — set `trellis_value_prop`,
     `trellis_batch_date`, `trellis_sequence_status = pending`, and put a COMPACT plan in
     `trellis_outreach_context`: value prop, the trigger, the per-touch angle for E2/E3/E4/breakup, the
     threading map (A: E1→E2 reply; B: E3 new→E4 reply→breakup reply), and E1's subject. Do NOT store
     full bodies — `follow-ups` regenerates them from this plan + the live thread.

## Hand back (keep it short)
- "Drafted **N** Email 1's in your Gmail — review and send." 
- "**M** flagged, not drafted:" list each with the one-line RoE reason (owner / active deal / replied).
- Reminder: "Follow-ups draft on cadence once you've sent — **Email 2** replies to Email 1; **Email 3**
  opens a NEW thread; **Email 4** replies to Email 3; the **breakup** replies on that thread. Run
  `/trellis-ae:follow-ups` (or let the scheduled check do it). Anyone who replies is auto-skipped."

## Rules
- **Draft only — never send.** Cap 25/contacts per run. Respect RoE (step 2 is not optional).
- Never fabricate emails, phones, metrics, or events. Case-study numbers are used verbatim from the index.
- Don't narrate every tool call — do the work, then give the summary.
