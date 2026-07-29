---
name: assigner
description: Assign a VERIFIED ICP list of contacts across a set of AEs and stamp each CONTACT's ICP Lead Stage = assigned — the Assign stage that runs AFTER /qualify marks contacts verified. Routes by company ownership first (the AE who owns the account gets the contact), keeps every contact at the same account with the same AE, then distributes the leftover (unowned + orphans of deactivated owners) evenly across the AEs to even out overall workload. Builds one static "ICP Leads for [NAME] - [DATE]" list per AE and stamps icp_lead_stage / icp_lead_stage_date / icp_lead_batch. Never poaches accounts owned by an active rep outside the set. Use when someone says "assign this verified list," "assigner," "split these leads across the team / Ryan, Liam, Hamza," or right after /qualify.
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
0. **Segment — AGENCY or BRAND? ASK FIRST if the user hasn't said, before running fully.** Trellis runs
   **two parallel ICP tracks with separate lists**: **brands** (Amazon *sellers* → the general
   `ICP Leads for [AE] - [date]` lists) and **agencies** (Amazon *service providers* → the separate
   `Agency ICP Leads for [AE] - [date]` lists). The standing `verified` pool is **agency-dominated**, so a
   general/brand run that doesn't filter will silently fill the brand lists with agencies. **Do not guess —
   if the requester didn't specify agency vs brand, ASK before assigning anything.** Then filter the pool to
   that segment: classify each company as brand vs agency via **SmartScout `seller_id`** (has one → seller =
   brand), **agency-track list membership**, **company industry** (Marketing/Advertising Services = agency),
   and **agency-name/domain signals** (agency, media, digital, marketing, consulting, PPC, SEO, commerce,
   sellers, growth, etc.). Exclude the other segment entirely, and never mix an agency into a brand batch or
   vice-versa. (Added 2026-07-27 after a general run mistakenly assigned ~135 agencies into the brand lists —
   no double-assignment resulted, but they belonged in the agency track.)
1. **Source list** — a HubSpot list link or ID (this should be the *verified* pool, e.g. "ICP Leads
   Verified"). Pull the **real membership** (see Gotchas — do NOT trust the SQL `ilsListIds` filter).
   **Count the actual members and report the number.**
2. **AEs** — the names to assign across (e.g. Ryan, Liam, Hamza — **Alex left the company 2026-07**; see the
   departed-rep note in Gotchas). Resolve each to an **owner id**
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

**Hard rule — never poach:** if the governing owner is a **confirmed-active rep who is NOT in the AE set**
(resolved via `search_owners` with `isActive=true`), do **not** assign that contact (hold it out entirely).
Surface these as "held — owned by &lt;rep&gt;." **An empty, shared, deactivated, or unresolvable owner is
NOT a poach block** — only a confirmed-active outsider is (see the archived-owner gotcha below).

Because company owner is a property of the **company**, every contact at the same account shares the same
company owner, so accounts never split in Phase A.

### Phase B — distribute the leftover evenly (accounts stay whole)
The leftover = contacts not claimed in Phase A. **Scope** (default): include contacts with **no company
owner** *and* contacts whose company owner is a **deactivated/removed** user (orphans — check
`isActive=false` via `search_owners`; **an owner id that won't resolve is a departed rep — treat it as an
orphan, not as territory**, see the archived-owner gotcha); **exclude** contacts at companies owned by a
**confirmed-active** rep outside the set (those are live territory). Offer the stricter "only truly
unowned" or looser "all leftover" if they prefer.

Then distribute, **keeping every contact at the same account with the same AE**:
1. Group leftover contacts by **primary company** (the account).
2. Seed each AE's running total with its **Phase A count** (so balancing evens the *final* totals — unless
   they chose "split leftover evenly," in which case seed all at 0).
3. **Hamza-first, west-to-east (timezone priority).** Before the general even-out, **build Hamza's list
   first**: hand Hamza whole leftover accounts in **timezone order PST → MST → CST → EST** (west coast
   first — exhaust the higher-priority timezone before moving east), **capped at his balanced share** (his
   even portion of the run — normally the standard **50/AE** target; see the 50-per-AE goal below). The
   priority gives Hamza **first pick of western accounts within his fair share — it does NOT hand him extra
   beyond his share**; once he hits his share, remaining western accounts flow to the other AEs. Derive each
   account's
   timezone from the **primary company's geo — ZIP is the reliable key** (state/city are dirty, per the geo
   gotcha): map US ZIP → timezone (**PST** = CA/OR/WA/NV, group AK/HI here too; **MST** = AZ/CO/UT/NM/MT/ID/WY;
   **CST** = TX/IL/MN/MO/WI/LA/etc.; **EST** = NY/FL/GA/NC/OH/MA/etc.), falling back to `state` only when ZIP
   is missing, and treat **unknown-timezone accounts as last** (after EST). Respect account-whole, ≤5/brand,
   and never-poach throughout. (Added 2026-07-27 per Ethan — Hamza works west-coast hours, so give him the
   western pipeline first.)
4. **Then distribute the remaining leftover to the other AEs — east-to-west (conserve western inventory).**
   Fill the non-Hamza AEs (Ryan/Liam) preferring **EST → CST → MST → PST** accounts (east coast first — the
   mirror of Hamza's west-first). **When there's a large excess of accounts, give the others EST accounts
   FIRST and do not hand them western (PST/MST) accounts until eastern supply is exhausted** — western
   accounts are scarce and reserved for Hamza *this week and the following weeks* (we rebuild Hamza's
   west-coast list every run), so don't burn them on Ryan/Liam while eastern accounts are available. Within
   that ordering, use **largest account first → currently least-loaded of the non-Hamza AEs** (LPT
   bin-packing) so their final totals land within ~1 of each other, never splitting an account. (If supply is
   tight rather than in excess, just balance normally — the east-first preference only matters when there's
   enough excess that the choice is real.) (Added 2026-07-27 per Ethan.)

## Confirm, THEN write (never write before the yes)
Show a compact plan and get a yes:
- **Source count** and how it breaks down (Phase A by-owner, leftover in-scope, held-out).
- **Per-AE table:** already-has (Phase A) · added (Phase B) · **final total**.
- **Multi-contact account placements** (which big accounts went to whom) so they can eyeball the account-
  whole rule.
- **Held out** (count + reason: owned by active rep X / out of scope).
- **RoE pre-clear:** state that after assigning you'll pre-run RoE centrally and stamp `claude_roe_*`
  (motion `cold`) so AEs don't re-pay for it — and offer to **skip** it.
- **Mobile coverage (dialing readiness) — this is a HARD GATE, not just a flag (Ethan 2026-07-28):** a
  contact with no `clay_mobile` is **not assignable** — exclude it and top up from phone-having `verified`
  contacts so the per-AE target is hit with dialable records only (see the PHONE REQUIRED rule below). Per
  AE, report how many were **excluded for no mobile** and confirm the tops-up. Offer to stamp
  `clay_phone_status = needs_update` on the excluded ones to queue them into the
  standing **`Clay - Needs Mobile`** dynamic list (id 8351; as of 2026-07-28 the list gate is
  `clay_phone_status = needs_update` ALONE — the old `claude_employment_status = verified` AND-condition
  was removed, so a bare `needs_update` stamp queues ANY contact, not just build-list employment-verified
  ones → the mobile-waterfall table auto-writes `clay_mobile` back). Do **NOT** enrich mobiles from
  here — assigner only flags; the user runs it.
- Offer "skip confirmations for the rest of this run."

On confirmation, for **each AE**:
1. **Create a static list** `ICP Leads for <Name> - <label>` (objectTypeId `0-1`, processingType
   `MANUAL`) if it doesn't already exist; reuse the id if it does.
2. **Add** that AE's contact ids to the list.
3. **Stamp** each of that AE's contacts: `icp_lead_stage = assigned`, `icp_lead_stage_date = <today>`,
   `icp_lead_batch = "ICP Leads for <Name> - <label>"` (the batch field mirrors the list name).
4. **Pre-clear RoE and stamp `claude_roe_*`** (recommended — this is why it lives here). You run on the
   **admin account**, so do the expensive Rules-of-Engagement check **once, centrally**, and cache it on
   the record — then AEs' `cold-outbound` trusts the stamp instead of each re-spawning `ob-verification`
   (saving a subagent per contact on their lower-credit machines). For each of that AE's contacts, spawn
   the **`ob-verification`** subagent (`motion: cold` — assigned ICP leads are worked cold; requesting AE =
   **this AE's owner id**). Then **batch-write** the returned stamp onto each contact:
   `claude_roe_status`, `claude_roe_cleared_for` (= this AE's owner id), `claude_roe_motion = cold`,
   `claude_roe_note`, `claude_roe_checked_date = <today>`. Run the checks in **capped waves (≤4 concurrent)**
   like the outbound skills, and — per the membership-lag gotcha — **re-read a sample after writing** to
   confirm the stamps landed (fanned-out writes can silently drop a record). *Skippable:* if the user says
   "skip RoE" or the list isn't headed to cold outbound, omit this step; the AE skills will then run RoE
   live as before.

> **Idempotency:** if a contact is **already `assigned`**, don't re-stamp the date and don't move it; just
> report it. Never downgrade a contact's stage here. Re-running on the same list should be a no-op for
> already-assigned contacts and only pick up newly-`verified` ones.

> **Property guard:** if HubSpot errors that `icp_lead_stage` / `icp_lead_stage_date` / `icp_lead_batch`
> or the `claude_roe_*` properties are unknown, **stop and tell the user** — do not improvise onto a
> different field. (The `claude_roe_*` set is created once via the properties API; if they're missing,
> RoE pre-clear can't stamp — report it rather than silently skipping.)

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
- **Resolve owners INCLUDING archived — and fail safe to "inactive."** `search_owners` / `/crm/v3/owners`
  return only **active** owners by default, so a **deactivated rep** (someone who left, e.g. Kelly) won't
  appear and their owner id won't resolve. Three rules: (1) also fetch **archived** owners
  (`GET /crm/v3/owners?archived=true`, or `search_owners` by `ownerIds` — which returns archived) so every
  owner id resolves to a real `{name, isActive}`; (2) **default any unresolved owner id to _inactive_,
  never active** — `owners.get(id, {}).get("active", False)`, not `…, True)`; (3) the **never-poach guard
  must require a _confirmed-active_ outsider** — empty / shared (Genny·Ethan) / deactivated / unresolvable
  owners are all safe to reassign to the AE; only a resolved `isActive=true` rep outside the set is held.
  Defaulting unknown→active silently **protects a departed rep and drops their accounts from the run** — it
  bit a batch of Kelly-owned accounts (Sparkle Wellness, Biotics, Newton Baby, Orveon, Black Rifle) that
  were neither assigned nor flagged until a re-audit by owner id caught them. **Known departed reps: Kelly and
  Alex (Alex left 2026-07).** Treat their owned accounts as **orphans to redistribute**, never as active
  territory — fetch archived owners so their ids resolve to `isActive=false`, and never hold a contact just
  because Kelly or Alex owns the account.
- **Enum + date:** the stage value is exactly `assigned`; dates are `YYYY-MM-DD`.
- Do all the heavy lifting (membership pull, grouping, LPT balance) in a throwaway script in your
  scratchpad — keep large API payloads out of context (batch-read 100 ids at a time).

## Hand back (keep it short)
- "Assigned **N** of **M** across **k** AEs — &lt;Ryan X · Liam Y · Hamza Z&gt; (final totals)."
- Per-AE: list link + final count. Note any big accounts that drove the split.
- **RoE pre-clear (if run):** "Pre-cleared RoE for **N** contacts (cleared X · flagged Y · blocked Z),
  stamped `claude_roe_*` (motion cold) — AEs' cold-outbound will trust these for 7 days instead of
  re-checking." Note any **blocked** contacts so they're not worked.
- **Held out** (+ why) and any **already-assigned** contacts skipped.
- **Mobile coverage:** "**N** of **M** assigned have a `clay_mobile`; **K** missing." List the missing
  (or note they're queued in `Clay - Needs Mobile`) so the user enriches before working them — dialing
  without a number is dead time.
- Remind: `hubspot_owner_id` was not changed (list + stage/batch only); offer to flip owners or handle the
  held-out set separately.

## Rules
- **Confirm before any HubSpot write.** Never change `hubspot_owner_id` unless asked.
- **Accounts stay whole, but capped ≤5 best per brand.** A brand/company goes **entirely to ONE AE — never split a brand across AEs.** But assign at most **5 contacts per brand TOTAL** (not per AE); when a brand has >5, keep the **5 best titles** and defer the rest (leave them `verified`). Title priority for "best": **Ecommerce (higher seniority = better) > paid media > CMO > marketing director > CEO > head of brand > other ICP/growth (amazon/marketplace/acquisition/lifecycle/brand)**. Enforce ≤5/brand + no-split in both phases. (Added 2026-07-20 per Ethan — replaces pure accounts-whole, which over-indexed single brands like POP MART/HexArmor.)
- **Brand-covered ACROSS weeks (count prior assignments).** The ≤5/brand cap counts contacts **already `assigned`** to that brand in PRIOR runs, not just this run. Before assigning, look up each brand's existing `assigned` count + owning AE: (1) a brand already at 5 assigned → **skip entirely** (covered, assign none); (2) a brand with 1-4 already assigned → may top up to 5 **only on the SAME AE that already owns it** (never split to a 2nd AE); (3) never let a brand exceed **5 total assigned across all time**. This prevents re-assigning a covered account's leftover `verified` contacts week after week. (Added 2026-07-20 per Ethan: "exclude these now that we've assigned that brand already.")
- **Never poach** an account owned by an active rep outside the AE set.
- **Aim for 50 per AE each run (default target).** The standing goal is **50 contacts per AE** every run;
  top up toward 50 each (source/backfill as needed) rather than stopping short. Balance evens the *final*
  totals toward that target.
- **Hamza-first by timezone (Phase B leftover only).** When distributing unowned/orphan accounts, build
  **Hamza's list first** from **west-to-east timezones (PST → MST → CST → EST)**, deriving timezone from the
  company's **ZIP** (reliable) → `state` fallback, unknown last — **capped at his balanced share** (first
  pick within his fair portion, never extra beyond it). **Mirror for the other AEs: fill Ryan/Liam
  east-to-west (EST → CST → MST → PST); on a large excess, give them EST accounts FIRST and don't touch
  western (PST/MST) accounts until eastern is exhausted** — western inventory is reserved for Hamza this week
  and future weeks. Then even out the rest. Ownership (Phase A) still wins — this only governs the free
  leftover. (Ethan 2026-07-27.)
- **Knock out open deals + genuinely-in-motion; but lifecycle is a high-water mark — check dates.** In the RoE pre-clear: an **open deal** (any non-closed stage) → pull + backfill (never cold-outreach an active opportunity; Ethan 2026-07-24). `customer` → pull. **Disqualified** → pull. For **Meeting Booked / SQL / Opportunity**, do NOT blanket-pull — `lifecyclestage` is the furthest stage ever reached, often years stale; read the meeting / last-activity **date** and only pull if recent + active (Ethan 2026-07-27). **Churned** → keep (winback-eligible), do not pull. Pull anything owned/recently-met by an **active outside rep** (never-poach — check meeting history, not just current owner: a reassigned contact can still be another rep's relationship). Backfill pulls to hold the target count.
- **Idempotent** — don't re-stamp/move already-`assigned` contacts; never downgrade a stage.
- **PHONE REQUIRED — never assign a contact without a `clay_mobile` (Ethan 2026-07-28).** A contact with
  no `clay_mobile` is **not assignable** (the motion is cold-calling; no number = dead lead). **Gate on it:**
  exclude no-mobile contacts from the assign entirely and **top up from phone-having `verified` contacts** to
  hold the per-AE target — do NOT ship a list padded with un-dialable records. If a no-mobile contact was
  already assigned, **pull it and stamp `failed_verification`** (note "no clay_mobile — phone-required rule";
  it's recoverable to `verified` once the mobile enriches). Assigner still **never enriches** phones itself
  (mobile lives in `clay_mobile`, not `phone`/`mobilephone`) — queue the gaps via `clay_phone_status =
  needs_update` into list 8351 for the user's mobile-table run, then they re-enter a future run once dialable.
- You are the **Assign** stage: you only set `assigned` (+ list + batch). Qualifying stays upstream
  (`qualify`); sequence enrollment stays downstream — never enroll from here.
