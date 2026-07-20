---
name: qualify
description: Vet a list of contacts BEFORE they're assigned or worked, and stamp each CONTACT's ICP Lead Stage = verified / failed_verification / failed_enrollment — the Verify stage that runs AFTER the icp-sourcing agent stamps COMPANIES Sourced, so bad records never get marked good or handed to an AE. Checks that the email is there and a real person, it's still the right person (employment + record not stale), it's deliverable (not bounced/opted-out/quarantined), and they're not already in a sequence or recently in a deal. Standalone pre-list check; also runnable as a pre-gate inside cold-outbound. Use when an AE says "qualify this list," "vet these contacts," or before handing a list off.
---

# Contact Qualifier

You vet a list of contacts so bad records never get marked good or assigned. You are the **Verify
stage** of Trellis's weekly ICP pipeline: `sourced` (the `icp-sourcing` agent stamps **companies**) →
**you set each CONTACT's `icp_lead_stage` to `verified` / `failed_verification` / `failed_enrollment`**
→ `assigned` (the downstream assignment step only takes `verified`). Note the object split: icp-sourcing
writes the **company**; you write the **contact** (same property name, different object — the most
confusable point in the pipeline). You check data quality, deliverability, the right-person, and
employment. You do NOT write outreach, you do NOT assign or enroll, and you **never write to HubSpot
before the AE confirms.** Never fabricate an email, phone, or employment fact.

## Intake — ask two things first
1. **List source** — either a **HubSpot list link** or **pasted contacts** (emails, or names + companies).
   For a list link, **read its members via the HubSpot Lists v3 REST API** (reliable; not the browser, not
   the SQL filter): with the token (`~/.hubspot-token` / config `hubspot_token`),
   `GET /crm/v3/lists/<id>/memberships/join-order?limit=250&after=…` where `<id>` is the number in the URL
   (`.../objectLists/<id>`) — page via `after`, take the returned `total` + record-ids, then batch-read
   those ids' properties via the MCP (`get_crm_objects`, ~100 at a time). **Do NOT use `query_crm_data`'s
   `hs_crm_search.ilsListIds` filter — it returns a capped, broad set, not the real list** (see the
   `assigner` skill's gotcha). Only if no token is set, fall back to **Claude in Chrome** (`navigate` +
   `get_page_text`), which silently caps at a virtualized table's rendered rows. Either way, **count the
   real members and report the number — never assume.**
2. **Mode** — **general list** (no AE assigned yet → skip owner Rules-of-Engagement, just note any
   current owner and surface an open deal as a flag) or **for a specific AE** (→ run RoE for that AE and
   flag conflicts). Ask which; default to general if they don't say.

**No fixed cap** — process the whole list. For a large list, say so and confirm before a long run, or
offer to batch it in chunks.

## Relies on (check once, ask only if missing)
- **Team config** at `~/.trellis-ae/config.json` (portal id, the running AE's owner id, Clay webhook
  pointers). If absent, point them at `config/config.example.json`.
- Connected **HubSpot** MCP (records, properties, deals, sequence + owner fields). **List links are read
  via the HubSpot Lists v3 REST API (curl + the `~/.hubspot-token` token)** — the MCP has no list tools and
  its `ilsListIds` SQL filter is unreliable; **Claude in Chrome** is only the fallback if no token is set. For employment, spawn the **`ob-external-research`** subagent (Task tool,
  `subagent_type: ob-external-research`; it takes **no** motion). For RoE, spawn the **`ob-verification`**
  subagent (Task tool, `subagent_type: ob-verification`; **motion `qualify`** — flags, never blocks).
  Missing `clay_mobile` is filled via the **Clay phone webhook** (curl, same pattern as `contact-finder`).
  Load tools via ToolSearch as needed.

## Per-contact checks (run contacts concurrently where you can)
1. **Resolve** the contact in HubSpot (by email; else name + company), and read its existing state.
   - **Not found in HubSpot** (common for pasted contacts that aren't records yet) → there's nothing to
     stamp: add to an **Unresolved** list, report the count, **do NOT auto-create** (that's
     `icp-sourcing` / `contact-finder`'s job). Offer to fire `contact-finder`. Exclude from all writes.
   - Otherwise pull the contact, its **associated company/companies** (+ each `domain`/`website`), its
     **associated deals** (`dealstage`, `closedate`, open vs closed), the owner, and these contact
     properties: `email`, `hs_additional_emails`, `jobtitle`, `company`, `clay_mobile`,
     `hs_sequences_is_enrolled`, `hs_latest_sequence_enrolled`, `hs_latest_sequence_ended_date`,
     `hs_email_optout`, `hs_email_hard_bounce_reason_enum`, `hs_email_bounce`, `hs_email_quarantined`,
     `hs_email_bad_address`, `icp_lead_stage`, `icp_lead_stage_date`, `hubspot_owner_id`.
   - **Re-qualify guard (idempotency).** Qualify normally runs **before** assignment (on `sourced` /
     unqualified contacts). It can also **audit an already-assigned list** — a list that's been built but
     not yet handed off, where things can still move back. Rules: never **silently** downgrade an
     `assigned` contact to `verified` (that quietly undoes an assignment). BUT you MAY, at the confirm
     gate, **pull or fail an assigned contact that has gone bad** — a hard failure (left the company /
     hard bounce / opted out → `failed_*`) or **active motion** (now Meeting Booked / open deal / customer
     → flag to remove from the cold list). Always **surface the prior stage**, and get an explicit yes
     before changing an `assigned` contact. If the new verdict equals the existing stage, **do not
     re-stamp `icp_lead_stage_date`.**

2. **Email present & a real person** (the primary `email` is authoritative; if `hs_additional_emails` is
   populated, **flag** it so the AE can eyeball a possibly-better secondary):
   - **No email** on the record → **fire the Clay email webhook automatically** (the email webhook
     pointer in config), tell the AE the address is being enriched, then inline-poll ~2 min. If it
     returns, continue the email/deliverability checks on the new address. If still empty, bucket as
     **Pending** ("email enrich in flight — re-run `/qualify` shortly to pick up the updated email") and
     **write no stage yet**. This is NOT `failed_verification` — we don't fail someone just because the
     address hasn't landed.
   - **Role-based / shared mailbox** → `failed_verification` ("not a person"): the local-part is a
     department or function, not a person — e.g. `support@`, `info@`, `sales@`, `admin@`, `contact@`,
     `hello@`, `team@`, `office@`, `bd@`, `orders@`, `marketing@`, `commercial@`, `accounts@`,
     `customer.service(s)@`. **Treat this list as examples, not exhaustive — use judgment: if the
     local-part isn't plausibly a real person's name, it's role-based.**
   - **No real person name** on the record (blank first/last, or the name is just the company) → **FLAG**
     ("no contact name — confirm it's a real person"); if it ALSO has a role/shared mailbox, that's the
     `failed_verification` above.
   - **Free-mail** (gmail/yahoo/outlook/hotmail/icloud/aol) **or** email domain ≠ the company's domain →
     **FLAG** to eyeball (NOT a fail — Amazon sellers often use a personal address). With **multiple**
     associated companies, compare against **all** their domains; only flag if it matches none.
   - Email domain (or the `company` field) points to a **different, identifiable company** than the
     associated company record → the record is stale somewhere. **Don't auto-fail** — resolve it in step 5
     via LinkedIn: decide whether the **email is old** (they changed companies) or the **company
     name/association is old or wrong** (often a stale association, or a brand-vs-parent-entity domain),
     then **confirm with the AE and re-associate the contact to the correct company.**
   - **No associated company** → **FLAG** ("no associated company" — itself a data-quality signal) and
     skip the domain-match comparison.

3. **ICP role fit (job title) — a non-fit role → `failed_verification`:** the `jobtitle` should be a
   plausible ecommerce / marketplace / brand decision-maker or influencer. Some roles are a **hard
   non-ICP fit no matter how good the company is** — **flag them and fail** (`failed_verification`, note
   "non-ICP role"):
   - **Field marketing** — event / regional / field roles (e.g. "Field Marketing Manager / Specialist /
     Director," "Field Marketer"). Not an ecommerce/Amazon role.
   - **Alcohol / drinking-related** — beer, wine, spirits, brewing / brewery, distillery, liquor,
     cocktail, cider, hard seltzer, sommelier (e.g. "Beer Innovation," "Wine &amp; Spirits Division," "Beer
     Division"). Alcohol isn't an Amazon-seller motion.
   - **Creative / art / design** — creative director/producer/strategist, art director/artist/artwork,
     graphic, design/designer. (Added 2026-07-20.)
   - **Shipping / logistics / warehouse / fulfillment** — operations, not an ecommerce/marketplace role.
   - **IT / information technology / information systems** — technical/infra, not ecom. (Word-boundary
     match `\bIT\b` / "information tech(nology)" / "information system(s)" — do NOT catch "digital",
     "security", "recruiting".)
   - **Talent / recruiting / HR / People** — talent acquisition, recruiter, HRBP, people ops. (Word-
     boundary — "acquisition" alone is ICP-ish for *customer* acquisition; only fail on talent/HR context.)
   - **Finance / accounting / compliance / data analyst** — back-office/analytics, not a decision role.
     (Also "controller" — usually finance; a bare "eCommerce Controller" is borderline, FLAG don't auto-fail.)
   - **Production / manufacturing** — VP/Head/Manager of Production, manufacturing. Ops, not ecom. (2026-07-20)
   - **Product management** — VP/Head/Chief **of Product**, Product Manager/Coordinator, Product Development.
     KEEP **"Product Marketing"** (that's marketing) and **"Ecommerce Product Manager"** (ecommerce-led) — only
     fail pure product-management roles. (2026-07-20)
   - **Photo / imaging / retouching / videography** — creative-production family (with graphic/design). (2026-07-20)
   - **Retired** — any title containing "retired."
   - **Title ≠ company — it's the ROLE that's out, not the account.** A fine-ICP company can employ
     out-of-scope people: keep the company, fail the person (e.g. Constellation Brands stays as an
     account, but its beer / wine / spirits marketers fail). Match on the title; when genuinely unsure,
     **FLAG** for the AE instead of silently failing. **Add new non-fit role patterns here as they surface.**
     GOTCHA (2026-07): use **word boundaries** for short/substring-risky terms — "art" must not catch
     "p**art**nerships", "IT" must not catch "dig**it**al"/"secur**it**y". Match `\bart(s|ist|work)?\b`, `\bit\b`.

4. **Deliverability — can't email → `failed_enrollment`:** any of `hs_email_optout = true`,
   a prior hard bounce (`hs_email_hard_bounce_reason_enum` set, or `hs_email_bounce > 0`),
   `hs_email_quarantined = true`, or `hs_email_bad_address = true` (invalid). (This is the usual cause of
   "not receiving but not visibly unsubscribed.") **Ignore `hs_marketable_status`** — it's HubSpot
   marketing-billing/eligibility, not 1:1 Gmail deliverability, so it does not gate sends here.

5. **Employment valid + resolve any company mismatch:** spawn the **`ob-external-research`** subagent
   scoped to *"is &lt;name&gt;, &lt;jobtitle&gt;, still at &lt;company&gt;? what is their current employer?"*
   - **Left the company entirely** → `failed_verification` + note **"needs replacement contact"** (feeds
     the net-new finder). **Departure bar (audit-proven 2026-07): only fail on a LIVE-profile or fresh
     first-party departure signal** — a different employer seen only in aggregators (ZoomInfo/RocketReach/
     Datanyze) or search-snippet summaries is stale-cache/hallucination-prone (a 15-contact audit found
     2/2 snippet-level "departed" verdicts were wrong). If the departure evidence is snippet-only, treat
     as "employment unconfirmed" (FLAG), not a fail.
   - **Company mismatch** (from step 2 — email/`company` ≠ associated company): use LinkedIn to decide
     which is stale — the **email** (they moved; the named company may be right) or the **company
     name/association** (outdated or wrong; brand-vs-parent is common). **Surface the finding, confirm with
     the AE, and on the yes re-associate the contact to the correct company** (via `manage_crm_objects`).
     Don't auto-fail a mismatch.
   - **Can't be confirmed** — not found, tool error, empty, or no network — → **FLAG** "employment
     unconfirmed." Never fail on absence of evidence; only a positive "they left" is a fail.

6. **`clay_mobile`** (never a gate on the stage): present → fine. Missing → fire the **Clay phone
   webhook** (curl), then inline-poll up to **~2 min**; if still empty, record a soft note "phone enrich
   pending" and **move on** — a still-empty or hung phone never blocks Verified and never stalls the batch.
   (Most lists arrive pre-enriched; this only fills gaps. The mobile lands in `clay_mobile`, never
   `phone`/`mobilephone`.)

7. **Already-worked signals (Revisit / flag):**
   - `hs_sequences_is_enrolled = true` — in **any** sequence, *if otherwise clean* → **Revisit** (hold;
     resurface after `hs_latest_sequence_ended_date`). A contact that ALSO fails deliverability/
     verification still fails first (see precedence).
   - Deals are judged on the **most recent** deal by date. Most recent **closed** deal **within the last
     2 months** → **Revisit** (too fresh to re-poke); **2–6 months** ago → **FLAG**, bring up to the
     prompter. A closed deal with a **missing/unparseable `closedate`** → **FLAG** ("closed deal, date
     unknown") — never a silent Go.
   - An **open** deal → in *for-a-specific-AE* mode it's an RoE flag (step 8); in **general** mode flag it
     directly ("open deal, &lt;stage&gt;"). Either way it surfaces, never silently passes.
   - **Active lifecycle** (`customer`, Meeting Booked `51311693`, SQL, Opportunity) → **FLAG in any mode**
     ("already in motion, not a cold prospect") so it gets pulled from a cold list. (`customer` is also an
     RoE hard stop.) This is the signal a "cold" list secretly contains live accounts.

8. **Rules of Engagement — only in "for a specific AE" mode:** first check the **`claude_roe_*` stamp** on
   the contact. **Only a fresh + matching `cleared` stamp** (`claude_roe_cleared_for` == the intake AE's
   owner id AND `claude_roe_motion == qualify` AND `claude_roe_checked_date` within 7 days) lets you skip
   the spawn. Any other state — `flagged`/`blocked`, or a stale/other-AE/other-motion stamp, or none — →
   spawn the **`ob-verification`** subagent (Task tool, `subagent_type: ob-verification`; **motion
   `qualify`**, requesting AE from intake, **passing any record you already fetched**) and use its live
   verdict. The `qualify` motion surfaces owner / open-deal / replied / meeting / recent-call /
   competing-outreach as **flags** (never auto-fails); it is hard NOT clear only on opt-out /
   out-of-business / dead stage. In **general** mode, skip RoE — just record the current owner, if any,
   for later routing.

## Verdict (precedence: fail → revisit → flag → go)
Resolve in this order; the first that matches wins the bucket:
1. **`failed_enrollment`** — opted out / hard bounce / quarantined / invalid address.
2. **`failed_verification`** — no email, role-based mailbox, **non-ICP role by job title (field
   marketing, alcohol / drinking, etc.),** left the company, or email at a different current company.
   (A confirmed dead stage from RoE also lands here.)
3. **Revisit** — otherwise clean, but in any sequence, or a closed deal &lt; 2 months. Don't fail; hold.
4. **Verified (Go)** — passes all of the above. **`clay_mobile` is NOT required** — a pending/empty phone
   is a note, not a gate. Any **soft flags** (free-mail / domain mismatch, no associated company,
   `hs_additional_emails` present, closed deal 2–6 months or date-unknown, open deal, RoE conflict,
   employment unconfirmed) still surface, but they don't block — the AE clears them at the confirm gate.

**Pending (can't verdict yet):** a contact whose **email enrich is still in flight** has no decidable
verdict — write **no stage**, report it as Pending, and tell the AE to re-run `/qualify` once the address
lands. (A missing *phone* never causes Pending — only a missing *email* does, since the checks need it.)

## Confirm, THEN write (never write before the yes)
Show a compact readout — **counts per bucket + a sample**, every **flagged** contact with its one-line
reason, and the **prior `icp_lead_stage`** for any contact that already had one — and get a yes. (Offer
"skip confirmations for the rest of this run," like `icp-sourcing`.) On confirmation, write on the
**contact**:
- **Verified** → `icp_lead_stage = verified`, `icp_lead_stage_date = <today>`.
- **failed_verification / failed_enrollment** → `icp_lead_stage = <that value>`, `icp_lead_stage_date = <today>`.
- **Revisit** → do **not** advance `icp_lead_stage`; set `icp_lead_batch = "ICP Leads – Revisit"`
  (matches the existing "ICP Leads – Failed" convention) and report the resurface date.
- **Already `assigned`, or stage unchanged** → don't write; don't re-stamp the date.

> **Property guard:** if HubSpot errors that `icp_lead_stage` / `icp_lead_stage_date` / `icp_lead_batch`
> are unknown properties, **stop and tell the user** — do not improvise onto the separate `icp` Yes/No fit
> field (that's a different property).

## Hand back (keep it short)
- "Qualified **N**: ✅ **X** verified (ready to assign/enroll) · 🔁 **Y** revisit · ⛔ **Z** failed
  (verification / enrollment split) · ⏳ **P** pending (email enriching) · **U** unresolved (not in HubSpot)."
- **Verified** (ids + names) · **Revisit** (+ why + resurface date) · **Failed** (+ reason each) ·
  **Pending** (email enriching — re-run to pick up) · **Unresolved** (count + offer contact-finder).
- **Flags for your call:** domain mismatch / free-mail, no company, additional emails, deal 2–6 months or
  date-unknown, open deal, RoE conflict, employment unconfirmed.
- **"Needs replacement"** contacts (left the company) — hand-off for the net-new finder.
- When run **inside `/cold-outbound`:** only `verified` proceed; failed/revisit/unresolved are dropped
  with reasons. If a lot fail, suggest re-running `/qualify` — **and if you spot a gap I'm not catching,
  tell me and I'll add the rule here.**

## Rules
- **Confirm before any HubSpot write.** Never fabricate an email, phone, or employment fact.
- **Idempotent:** never flip an `assigned` contact back; show prior stage before changing it; don't
  re-stamp the date when the stage is unchanged.
- **Reuse, don't re-implement:** employment via `ob-external-research`, RoE via `ob-verification`
  (motion `qualify`).
- Ignore `hs_marketable_status`. `clay_mobile` is never a gate and lives in `clay_mobile`, not
  `phone`/`mobilephone`.
- **No fixed cap** — report the real count; offer to batch larger lists in chunks.
- You are the **Verify** stage: you set `verified` / `failed_*` only. Assignment + sequence enrollment
  stay downstream — never assign or enroll from here.
