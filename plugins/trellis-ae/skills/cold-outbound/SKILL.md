---
name: cold-outbound
description: Draft a cold Amazon outbound email sequence for a pasted list of contacts. Researches each prospect, checks Rules of Engagement, selects a value prop + case study, and delivers Email 1 for the AE to review and send — pushed into their Instantly campaign (after a Google-Doc/chat approval) if Instantly is set up, otherwise left as a Gmail draft. Use when an AE pastes a list of cold prospects ("here's my cold list for the week").
---

# Cold Outbound

You turn a cold list into sent-ready outreach with **almost no generation on your side** — the five emails
were **pre-written centrally** by `/trellis-ae:write-sequences` and stored on each contact. You **pull**
them, get them **approved** (Google Doc or chat), and **push the approved ones into the AE's paused Instantly
campaign** if Instantly is configured (`config.instantly.campaign_id`), otherwise drop E1 as a **Gmail
draft**. You **never send** — the AE reviews and sends (in Instantly or Gmail). If a contact isn't
pre-written, you **flag it** rather than silently run the expensive generation. Keep the AE's time in chat
minimal: do the work, hand back a short summary.

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
**Pace & walk-away**) and outputs land for later review (Gmail drafts, or — on the Instantly path — an
approval doc, then a push into the paused campaign), so a big list is fine; just give the time estimate up front.

## Relies on (check once, ask only if missing)
- **Team config** at `~/.trellis-ae/config.json` (portal id, the AE's HubSpot owner id, case-study
  index pointer, signature). If absent, point them at `config/config.example.json` and ask them to
  create it.
- Connected MCPs: **Gmail** (drafting), **HubSpot** (records/RoE), **Fathom** (calls), and **Drive/
  Notion** (case studies). Load tools via ToolSearch as needed.

## A/B variant (set at WRITE time, not here)
The messaging variant is chosen when the sequence is **written** (`/trellis-ae:write-sequences`), because
that's where the copy is produced — write-sequences assigns the arm and stamps
`trellis_ab_variant = <experiment>:<arm>` on the contact. Cold-outbound just **pushes whatever variant was
written** and carries that tag through, so results still group by arm. A contact with no tag is control.
(Registry: `config/ab-tests.md`.)

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
   steps 2–3** so they don't re-fetch the same thing (one read serves RoE + the pre-written-sequence pull).
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
3. **Pull the pre-written sequence — do NOT generate (this is the cost saver).** From the step-1 record,
   read `trellis_email_1_subject`/`_1_body`, `_2_body`, `_3_subject`/`_3_body`, `_4_body`, `_5_body`, plus
   `trellis_value_prop` + `trellis_outreach_context` (trigger + per-touch give plan). These were written
   centrally by **`/trellis-ae:write-sequences`**, so the expensive research + copywriting already happened
   once on the admin machine — your machine spends almost nothing here.
   - **Present** → use them **as-is**. Don't regenerate, don't "polish."
   - **Missing** (`trellis_email_1_body` empty — not pre-written) → **flag it, don't silently generate**
     (generation is the expensive path). List the not-pre-written contacts and offer: have the admin run
     `/write-sequences` on this list, **or** — only with the AE's explicit OK and a note that it costs more —
     spawn `ob-cold` to write that one now. Default is **flag + skip**.
4. **Approve, then push all five to Instantly (or Gmail fallback).** First **gate E1 against `ob-messaging`'s
   HARD CONSTRAINTS** (top of that file); if it fails, send that touch back to `ob-messaging` to rewrite —
   never hand-edit.
   - **Instantly configured** (config `instantly.campaign_id` is set) — the cold default. **Collect the batch,
     get approval BEFORE anything reaches Instantly** (you are the gate — Instantly only ever holds approved copy):
     1. Write the batch to a **Google Doc** (`create_file`): per contact — name · company · **E1 subject +
        body in full**, then E2–E5 listed below it (they're pre-written) — each contact with an `APPROVE:`
        line. Plus a compact chat summary.
     2. The AE approves **either way**: marks `yes` / `rewrite <touch>: <note>` / `no` on the Doc's APPROVE
        lines (re-read with `read_file_content`) **or** tells you in chat. For a **rewrite**, regenerate just
        that one touch via `ob-messaging` (motion `follow_up`, that touch), **update the matching
        `trellis_email_*` property**, and use the new body — never hand-edit copy.
     3. **Push the approved — all five touches** — into `instantly.campaign_id`, **paused**: write a temp JSON
        (`[{email,first,last,company,e1_subject,e1_body,e2_body,e3_subject,e3_body,e4_body,e5_body}]`) from the
        properties and run `python3 ~/.trellis-ae/instantly.py push-batch <instantly.campaign_id> <that.json>`.
        Each body rides as a custom variable; the campaign's 5 steps merge them (E1 + E3 open threads, E2/E4/
        breakup reply). **Never activate** — the AE reviews once more in Instantly and sends there. Report the
        campaign link + pushed/held counts.
   - **Instantly NOT configured** → Gmail fallback: `create_draft` the **E1** into Gmail (subject, body,
     signature); the later touches then run via the Gmail `follow-ups` cadence off the stored plan. **Never send.**
   *(Because all five bodies are pre-written and pushed up front, the Instantly campaign runs the full
   sequence natively — no late-fill.)*
5. **Calling note + follow-up plan** — two writes on the contact record:
   - **Calling note** (HubSpot note, contact-level) — exactly **3 bullets, built for power-dialing**
     (glanceable in a dialer like Orum): two **pain points**, then one **historical context** — how/when
     we last engaged and **who they dealt with** (e.g. "cold — no prior contact", "replied to Ryan's Aug
     email", "demo with Fahim 5/12", "met Ethan at Prosper Show"). Name the prior rep/person when there's
     a real prior interaction; otherwise "cold — no prior contact." **Never put internal CRM ownership in
     the note** (no "owned by you / [rep]") — it isn't dialer-relevant. One short line each, no preamble.
   - **Sequence status** — set `trellis_batch_date` and the status by delivery channel: **Instantly-pushed
     → `trellis_sequence_status = instantly`** (so the Gmail `follow-ups` skill skips them — their later
     touches run natively in the Instantly campaign); **Gmail-drafted → `pending`** (the Gmail `follow-ups`
     skill picks these up and drafts the later touches from the stored plan). The value prop, trigger, and
     per-touch plan are **already on the contact** from `write-sequences` (`trellis_value_prop`,
     `trellis_outreach_context`) — don't rewrite them. If you rewrote a touch at the approval gate, you
     already updated its `trellis_email_*` property in step 4.

## Hand back (keep it short)
- **Instantly path:** "Pushed **N** approved Email 1's into your Instantly campaign (**paused**) — do a final
  review in Instantly and send from there. **H** held (not approved / flagged). [campaign link]." Note:
  later touches run in Instantly; the automated E2–E5 late-fill isn't wired yet (next build), and reply
  handling + the "we already called them" stop-guard run in the central `instantly-sync` job.
- **Gmail path:** "Drafted **N** Email 1's in your Gmail — review and send." + the follow-ups reminder:
  "Follow-ups draft on cadence once you've sent — **E2** replies to E1; **E3** opens a NEW thread; **E4**
  replies to E3; the **breakup** replies on that thread. Run `/trellis-ae:follow-ups` (or the scheduled
  check). Anyone who replies is auto-skipped."
- Either path: "**M** flagged, not delivered:" list each with the one-line RoE / risk reason (owner /
  active deal / replied / unconfirmed contact).

## Rules
- **Deliver-for-review only — never send.** Instantly path = push into a **paused** campaign (never activate); Gmail path = an unsent draft. The AE reviews and sends. No fixed list cap — process the whole list in capped concurrency waves (≤4 at a time; see **Pace & walk-away**), no smaller-batch babysitting required. Respect RoE (step 2 is not optional).
- **All prospect-facing copy is pre-written by `write-sequences` (via `ob-cold`, following `ob-messaging.md`) — never you.** You pull it and use it as-is. The only regeneration here is an approval-gate **rewrite** of a single touch, done via `ob-messaging` — you still may not write, shorten, paraphrase, or "polish" copy yourself. If a line didn't come from the stored `trellis_email_*` values or an `ob-messaging` rewrite, it doesn't go out.
- Never fabricate emails, phones, metrics, or events. Case-study numbers are used verbatim from the index.
- Don't narrate every tool call — do the work, then give the summary.
