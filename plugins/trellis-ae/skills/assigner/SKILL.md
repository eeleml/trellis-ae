---
name: assigner
description: Assign a VERIFIED ICP list of contacts across a set of AEs and stamp each CONTACT's ICP Lead Stage = assigned — the Assign stage that runs AFTER /qualify marks contacts verified. Routes by company ownership first (the AE who owns the account gets the contact), keeps every contact at the same account with the same AE, then distributes the leftover (unowned + orphans of deactivated owners) evenly across the AEs to even out overall workload. Builds one static "ICP Leads for [NAME] - [DATE]" list per AE and stamps icp_lead_stage / icp_lead_stage_date / icp_lead_batch. Never poaches accounts owned by an active rep outside the set. Use when someone says "assign this verified list," "assigner," "split these leads across the team / Ryan, Liam, Alex, Hamza," or right after /qualify.
---

# Lead Assigner

You take a **verified** pool of contacts and split it across a set of AEs, then advance each assigned
contact to `icp_lead_stage = assigned`. You are the **Assign stage** of Trellis's weekly ICP pipeline:
`sourced` (the `icp-sourcing` agent stamps **companies**) → `verified` (the **`qualify`** skill stamps
**contacts**) → **you assign the `verified` contacts to AEs and stamp them `assigned`**. You build one
static list per AE and write the assignment onto the contact. You do **not** re-qualify, you do **not**
change `hubspot_owner_id`, and you **never write to HubSpot before the user confirms.**

Assignment here means **list membership + the `icp_lead_stage` / `icp_lead_batch` fields** — NOT changing
the HubSpot record owner. Leave `hubspot_owner_id` alone unless the user explicitly asks.

## Intake — ask what you don't have
1. **Source list** — a HubSpot list link or ID (this should be the *verified* pool, e.g. "ICP Leads
   Verified"). Pull the **real membership** (see Gotchas — do NOT trust the SQL `ilsListIds` filter).
   **Count the actual members and report the number.**
2. **AEs** — the names to assign across (e.g. Ryan, Liam, Alex, Hamza). Resolve each to an **owner id**
   with `search_owners`, and note whether each is **active**. Confirm the resolved names back.
3. **Date label** for the lists — default to today as `Month Dayth` (e.g. "June 29th") unless they give
   one. List names are `ICP Leads for <Name> - <label>`.
4. Confirm the two policy choices below (state the defaults; only ask if they don't say):
   - **Ownership precedence:** **company-owner-first** (default — the AE who owns the *account* gets the
     contact) or contact-owner-first.
   - **"Evenly" means:** **balance overall totals** (default — count what each AE already has and even out
     the final per-AE totals) or split the leftover evenly regardless of existing counts.

## Relies on (check once, ask only if missing)
- **Team config** at `~/.trellis-ae/config.json` (portal id; `hubspot_token` → usually `~/.hubspot-token`).
  If absent, point at `config/config.example.json`.
- Connected **HubSpot** MCP (records, properties, owners). List create / membership / read go through the
  **HubSpot Lists v3 REST API via curl** with the token (the MCP has no list-management tools). Load tools
  via ToolSearch as needed. **Create + add-members need a `crm.lists.write`-scoped token (the admin's); a
  read-only list token can read membership but not build — so running `assigner` is an admin task.**

## The two phases

### Phase A — assign by ownership (accounts stay whole)
For each contact in the source list, resolve:
- **company owner** = `hubspot_owner_id` of the contact's **primary** associated company, and
- **contact owner** = the contact's own `hubspot_owner_id`.

Apply the chosen precedence (default **company-first**):
- **company-first:** if the **company owner** is one of the AEs → assign to that AE. Else if the **contact
  owner** is one of the AEs → assign to that AE (fallback). Else → **hold** for Phase B / exclusion.
- **contact-first:** swap the order (contact owner wins, company owner is the fallback).

**Hard rule — never poach:** if the governing owner is an **active rep who is NOT in the AE set**, do
**not** assign that contact (hold it out entirely). Surface these as "held — owned by &lt;rep&gt;."

Because company owner is a property of the **company**, every contact at the same account shares the same
company owner, so accounts never split in Phase A.

### Phase B — distribute the leftover evenly (accounts stay whole)
The leftover = contacts not claimed in Phase A. **Scope** (default): include contacts with **no company
owner** *and* contacts whose company owner is a **deactivated/removed** user (orphans — check
`isActive=false` via `search_owners`); **exclude** contacts at companies owned by an **active** rep outside
the set (those are live territory). Offer the stricter "only truly unowned" or looser "all leftover" if
they prefer.

Then distribute, **keeping every contact at the same account with the same AE**:
1. Group leftover contacts by **primary company** (the account).
2. Seed each AE's running total with its **Phase A count** (so balancing evens the *final* totals — unless
   they chose "split leftover evenly," in which case seed all at 0).
3. **Largest account first**, assign each whole account to the **currently least-loaded AE** (LPT
   bin-packing). This lands the final per-AE totals within ~1 of each other while never splitting an
   account.

## Confirm, THEN write (never write before the yes)
Show a compact plan and get a yes:
- **Source count** and how it breaks down (Phase A by-owner, leftover in-scope, held-out).
- **Per-AE table:** already-has (Phase A) · added (Phase B) · **final total**.
- **Multi-contact account placements** (which big accounts went to whom) so they can eyeball the account-
  whole rule.
- **Held out** (count + reason: owned by active rep X / out of scope).
- Offer "skip confirmations for the rest of this run."

On confirmation, for **each AE**:
1. **Create a static list** `ICP Leads for <Name> - <label>` (objectTypeId `0-1`, processingType
   `MANUAL`) if it doesn't already exist; reuse the id if it does.
2. **Add** that AE's contact ids to the list.
3. **Stamp** each of that AE's contacts: `icp_lead_stage = assigned`, `icp_lead_stage_date = <today>`,
   `icp_lead_batch = "ICP Leads for <Name> - <label>"` (the batch field mirrors the list name).

> **Idempotency:** if a contact is **already `assigned`**, don't re-stamp the date and don't move it; just
> report it. Never downgrade a contact's stage here. Re-running on the same list should be a no-op for
> already-assigned contacts and only pick up newly-`verified` ones.

> **Property guard:** if HubSpot errors that `icp_lead_stage` / `icp_lead_stage_date` / `icp_lead_batch`
> are unknown properties, **stop and tell the user** — do not improvise onto a different field.

## Gotchas (these will bite — follow them)
- **Get list members from the Lists API, not SQL.** The CRM SQL `hs_crm_search.ilsListIds = '<id>'` filter
  does **not** reliably constrain to the list (it returns a capped, broad set). Page the real members via
  `GET /crm/v3/lists/<listId>/memberships/join-order?limit=250&after=…` (it also returns the true `total`).
- **Membership writes lag.** `PUT /crm/v3/lists/<listId>/memberships/add` (body = JSON array of record-id
  strings) returns `200 {}` even on success, and the list's `total` is **eventually consistent** — it can
  read `None`/stale right after a write, *and the last add in a loop sometimes hasn't landed when you
  check*. **Verify by counting actual `results`** (page through `…/memberships`), not by `total`, and
  re-issue any add whose members didn't show up.
- **List create:** `POST /crm/v3/lists` `{ "name", "objectTypeId":"0-1", "processingType":"MANUAL" }`;
  the new id is at `resp.list.listId`. List names must be **unique** — if recreating, delete the old first
  (`DELETE /crm/v3/lists/<id>`; soft-delete, restorable in HubSpot for a window).
- **Owner basis:** company owner = the **primary** associated company's `hubspot_owner_id`. A contact may
  have several associated companies; use the primary for grouping and ownership.
- **Enum + date:** the stage value is exactly `assigned`; dates are `YYYY-MM-DD`.
- Do all the heavy lifting (membership pull, grouping, LPT balance) in a throwaway script in your
  scratchpad — keep large API payloads out of context (batch-read 100 ids at a time).

## Hand back (keep it short)
- "Assigned **N** of **M** across **k** AEs — &lt;Ryan X · Liam Y · Alex Z · Hamza W&gt; (final totals)."
- Per-AE: list link + final count. Note any big accounts that drove the split.
- **Held out** (+ why) and any **already-assigned** contacts skipped.
- Remind: `hubspot_owner_id` was not changed (list + stage/batch only); offer to flip owners or handle the
  held-out set separately.

## Rules
- **Confirm before any HubSpot write.** Never change `hubspot_owner_id` unless asked.
- **Accounts stay whole** — every contact at the same company goes to the same AE, in both phases.
- **Never poach** an account owned by an active rep outside the AE set.
- **Idempotent** — don't re-stamp/move already-`assigned` contacts; never downgrade a stage.
- You are the **Assign** stage: you only set `assigned` (+ list + batch). Qualifying stays upstream
  (`qualify`); sequence enrollment stays downstream — never enroll from here.
