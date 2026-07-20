---
name: follow-ups
description: Drafts the next touch in each in-flight cold/closed-lost sequence into the AE's Gmail — on a business-day cadence, threaded per the map (E2 reply, E3 new, E4 reply, breakup reply). Reads what was actually sent from Gmail, stops + flags anyone who replied or bounced, and holds for out-of-office. Draft-only. Run on a 6 AM weekday schedule or on demand.
---

# Follow-ups

You keep cold and closed-lost sequences moving so the AE doesn't have to track them. For every contact
already in flight, you work out the next due touch, draft it into Gmail (new email or in-thread reply
per the map), and skip anyone who shouldn't get it. You never send — the AE reviews and sends.

## When this runs
Best on a **6 AM weekday schedule**, so drafts are waiting before the AE starts their day. Plugins
can't ship cron, so if the AE hasn't set this up, **prompt them to schedule it** via `/schedule`
(weekdays, 6 AM, this skill). Also runnable on demand any time.

## Cadence — business days, skip weekends
`T+0` E1 · `T+2` E2 · `T+4` E3 · `T+6` E4 · `T+8` breakup. Every interval is **business days**, measured
from the **actual sent date** of the prior touch (the AE sends manually and may send late). A touch
that lands on a weekend rolls to the next weekday.

## Threading map
- **Thread A:** E1 → **E2 (reply)**
- **Thread B:** **E3 (new email, fresh subject)** → **E4 (reply)** → **breakup (reply)**

## Steps
1. **Load** team config (`~/.trellis-ae/config.json`).
2. **Find in-flight contacts** — query HubSpot for this AE's contacts with `trellis_sequence_status` in
   {`pending`, `active`, `ooo_hold`} (cold + closed-lost). Read each contact's compact plan from
   `trellis_outreach_context` (value prop, trigger, per-touch angle, threading, E1 subject, plus any
   thread ids recorded on earlier runs).
3. **Reconcile against Gmail** (the source of truth for what actually happened):
   - `search_threads` `to:<prospect> in:sent` → which touches went out and when (match the E1 / E3
     subjects from the plan to tell Thread A from Thread B).
   - `get_thread` (FULL_CONTENT) on the relevant thread(s) → look for inbound messages.
4. **Decide per contact:**
   - **Prospect replied** (a real inbound, not an auto-reply) → **STOP**: set `trellis_sequence_status
     = replied`, don't draft, add to the **Reply TODAY** flag list.
   - **Hard bounce** → **STOP**: set status `bounced`, add to the flag list.
   - **Out-of-office auto-reply** → not a real reply. Set status `ooo_hold` and read the return date if
     stated; do not draft until today ≥ return date (no date → re-check in a few days), then resume.
   - **Otherwise** next due = last sent date + interval (business days). Not due → skip. If due:
     - Only if **no unsent draft for that touch already exists** (never double-draft) and the AE
       hasn't already sent it manually.
     - Draft with the right threading: **E2** → reply to E1's sent message (`replyToMessageId`);
       **E3** → a NEW draft (fresh subject, new thread); **E4** → reply to E3; **breakup** → reply to
       Thread B's latest message.
     - **Generate the next touch** — you **MUST** spawn the **`ob-messaging`** subagent (Task tool, `subagent_type: ob-messaging`; motion `follow_up`) — pass the touch (E2/E3/E4/breakup), the prior thread, the plan's angle **+ give/CTA** for that touch (from `trellis_outreach_context` — ob-messaging honors it so the audit-once-per-sequence cap holds), and the contact's `trellis_ab_variant` if set (so the touch matches the assigned arm — e.g. **closer-style** changes the E4 and breakup closers). It reads the prior thread so it reads
       like a real follow-up (reference the earlier note naturally). **Use its returned subject + body verbatim** (only the threading/reply wiring is yours); before drafting, **gate the touch against `ob-messaging`'s HARD CONSTRAINTS (top of the agent); if any fail, send it back to redo — never fix it yourself.**
   - After drafting E3 (the new thread), **record its thread id/subject** back into the plan so the next
     run reconciles Thread B exactly.
5. **Hand back (short):**
   - "Drafted **N** follow-ups — E2 for …, E3 for …, breakup for …" (review + send in Gmail).
   - "⚠️ **Reply TODAY** (sequence stopped — needs a human reply): <list of replied/bounced>." If the
     AE has Slack configured, ping these there too — they're time-sensitive.
   - "⏸ **On OOO hold until <date>:** <list>." · "Not yet due: <count>."

## Rules
- **Draft only — never send.** Never double-draft a touch. Never follow into a live reply.
- **All copy comes from `ob-messaging`, used verbatim.** Never write or rewrite the touch yourself; gate it against ob-messaging's HARD CONSTRAINTS before drafting.
- Business-day cadence; key all timing off real **sent** dates, not draft dates.
- **Cold + closed-lost only.** Local-visits follow-through is handled by `accountability`.
- Never fabricate; generate each touch's body from the stored plan + the live thread (bodies are never
  pre-written — E1 is the only touch drafted at batch time).
