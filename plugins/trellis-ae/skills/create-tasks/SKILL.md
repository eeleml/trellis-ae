---
name: create-tasks
description: Creates the day's HubSpot call tasks in line with the email cadence — the call analog of follow-ups. Reads who's due for a call (in-flight contacts, pegged to where they are in the email sequence), shows you replies waiting + the due list, confirms how many you want, then creates deduped call tasks dated for today with the calling note attached. Calls only — never sends email (those stay Gmail drafts), never auto-dials. Run each morning or right after /trellis-ae:reporting.
---

# Create Tasks

You set up the AE's **call tasks** for the day so their dialer queue matches where each contact sits in
the email cadence. You're the **call analog of `follow-ups`**: follow-ups drafts the emails that are due;
you create the **call tasks** that are due. You write HubSpot call tasks only — you **never send a
prospect email** (emails stay Gmail drafts) and you **never auto-dial**. The AE tells you how many calls
they have capacity for; you create that many, best-first.

## When this runs
**Each morning, on demand** — run `/trellis-ae:create-tasks` to set up the day's calls, or right after
`/trellis-ae:reporting` (which tells you how many are due). Can be scheduled via `/schedule`. **Idempotent:**
safe to re-run — it never double-creates a task for a contact that already has an open one.

## Relies on (check once, ask only if missing)
- **Team config** at `~/.trellis-ae/config.json` (the AE's HubSpot owner id + name). If absent, point them
  at `config/config.example.json`.
- **HubSpot MCP** — load via ToolSearch (search_crm_objects, query_crm_data, get_crm_objects,
  manage_crm_objects). Tasks are created in HubSpot; calls are logged there.

## The calling cadence (business days, from Email 1 *sent*)
Calls cluster early, alongside the email touches — the **~2 calls in the first ~4 business days** bar (the
same one `accountability` checks). A contact is **due for a call today** if it's at a point in that cadence
where a call should happen and one hasn't been logged or queued yet. Key all timing off **actual Gmail
send dates**, not draft dates.

## Steps
1. **Load** config (owner id, AE name); scope to the running AE.
2. **Find who's due for a call** — pull the AE's in-flight contacts (`trellis_sequence_status` in {active,
   pending} with `trellis_batch_date`); for each, decide if a call is due today per the cadence (Email 1
   sent? how many calls already logged? where in the window?). Use the same definitions as `reporting` /
   `accountability` (shared metric layer).
3. **Apply skips — don't task these:**
   - **Replied** → the AE should reply, not cold-call. Skip + surface under "replies waiting."
   - **Meeting booked / converted / customer** → skip (already advanced).
   - **Already has an open call task** (NOT_STARTED / IN_PROGRESS) → skip (no double-creating).
   - **Opted out / do-not-contact** → skip.
4. **Consult the AE** — show: "**X due for a call** today (+ N replies waiting — handle those first). **How
   many call tasks do you want?**" Capture the number (a count, or "all"). Calls are capacity-bound —
   respect their number; if it's large (30+), confirm before a big batch.
5. **Prioritize + create** — pick the top N best-first (most overdue on the call cadence first; a
   first-call-never-made before a second-call-due). For each, create a **HubSpot call task**:
   - type **CALL**, **due today**, owner = the AE, associated to the contact.
   - subject: `Call: <First> @ <Company>`.
   - body = the contact's existing **3-bullet calling note** (pain points + context) so it's glanceable in
     the dialer — **pull it from the contact; don't regenerate** — plus a one-line cadence note (e.g.
     "call 1 of 2 — Email 1 sent <date>").
6. **Hand back (short):**
   - "Created **N** call tasks for today: <First @ Company, …> — in your HubSpot task queue / dialer."
   - "**Handle first (don't cold-call):** replies waiting from <list>."
   - "Skipped **M**: already had a task / replied / booked."
   - "Run `/trellis-ae:follow-ups` for the matching email drafts." (the email half of the day)

## Rules
- **Create call tasks only — never send a prospect email** (emails are Gmail drafts via cold-outbound /
  follow-ups) and **never auto-dial.**
- **Never double-create** — always dedup against existing open call tasks first (idempotent re-runs).
- Respect the AE's requested count — calls are capacity-bound; create best-first.
- Skip anyone who replied (reply first), booked, converted, or opted out.
- Business-day cadence; key all timing off **actual Gmail send dates**.
- Never fabricate the calling note — use what's on the contact; if it's missing, build a minimal one from
  `trellis_outreach_context`, or note it's absent.
