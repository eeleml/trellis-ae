---
name: local-visits
description: Prep in-person visits for a list of nearby Amazon-seller accounts — door-knock + lunch outreach. Researches each, checks Rules of Engagement, then produces text-message drafts for your phone, ONE lunch-invite email drafted in Gmail, walk-in talking points, and a HubSpot visit task dated to when you commit to go. Use when an AE pastes a local/territory list or says "I'm visiting accounts in <city>," "door-knock prep," or "set up some lunches."
---

# Local Visits

You turn a list of nearby accounts into **in-person-ready prep** so the AE can walk in or grab lunch
without writing anything first. Per account you produce: **text-message drafts** (copy for the AE's
phone), **one lunch-invite email** (a Gmail draft), **walk-in talking points**, and a **HubSpot visit
task** dated to when the AE commits to going. You never send — texts are copy the AE sends from their
own phone, the lunch invite is a Gmail draft to review. Route and day planning live in the AE's
separate route planner; you prep each stop and capture the date.

## First, ask the plan
Before processing, get two things so the lunch invite and the task dates are concrete:
- **Where** — which city / area / territory these accounts are in (if it isn't obvious from the list).
- **When** — specific dates, a rough week ("week of the 14th"), or "sometime." If "sometime," keep the
  lunch invite open-ended and set a soft task date ~2 weeks out that the AE can move.

## Input
The AE gives the list one of two ways:
- **A HubSpot list link** — **read its members via the HubSpot Lists v3 REST API** (reliable; not the
  browser, not SQL): with the token (`~/.hubspot-token`),
  `GET /crm/v3/lists/<id>/memberships/join-order?limit=250&after=…` (`<id>` = the number in the URL
  `.../objectLists/<id>`; page via `after`, then batch-read properties via the MCP). **Don't use the
  `hs_crm_search.ilsListIds` SQL filter — it returns a capped, broad set** (see the `assigner` gotcha).
  Only if no token is set, fall back to **Claude in Chrome** (`navigate` + `get_page_text`), which caps at
  a virtualized table's rendered rows.
- **Pasted contacts** — names + companies (+ city if they have it).
**Count the actual contacts and report the number.** In-person is lower-volume than email, but you still
don't need a smaller batch — process the whole list in capped waves (see **Pace & walk-away**); outputs
(texts, the lunch-invite draft, visit tasks) are all for later review. For a large list, give the estimate up front.

## Relies on (check once, ask only if missing)
- **Team config** at `~/.trellis-ae/config.json` (the AE's HubSpot owner id, signature, case-study index
  pointer). If absent, point them at `config/config.example.json` and ask them to create it.
- Connected MCPs: **HubSpot** (records / RoE / the visit task), **Gmail** (the lunch-invite draft),
  **Fathom** (any prior call), and **Drive/Notion** (case studies). Load tools via ToolSearch as needed.

## Pace & walk-away (don't make the AE babysit)
Nothing is sent — texts, the lunch invite, and visit tasks are all drafts/tasks for later — so the AE
needn't watch the run. Tell them up front: the count, a rough estimate, and "you don't need to watch this
— I'll prep everything and summarize when done." Then run **at most 4 contacts concurrently**, starting
the next as each finishes, so a big list doesn't spike the rate limit and stall on retries. Keep a running
tally; if throttled, let it back off and continue rather than shrinking the list. The AE can override the wave size.

## Per-contact pipeline (run in capped waves; see Pace & walk-away above)
1. **Resolve + fetch once** the contact + company in HubSpot. In one fetch pull the SmartScout fields, any
   location / HQ, the RoE rollup properties, **and the `claude_roe_*` stamp**, and hold the record to
   **pass to the subagents** (steps 2–3) so they don't re-fetch.
2. **Rules of Engagement — a fresh `cleared` stamp is the ONLY thing that skips the live check.** A stamp
   is fresh + matching only if `claude_roe_cleared_for` == this AE's owner id AND `claude_roe_motion ==
   local` AND `claude_roe_checked_date` is within 7 days. Fresh + matching **`cleared`** → use it (don't
   spawn `ob-verification`). Fresh + matching **`blocked`/`flagged`** → **HOLD + surface the
   `claude_roe_note`** (held unless the AE explicitly clears it or runs RoE live). Otherwise (no/stale/other
   stamp) → spawn the `ob-verification` subagent (motion `local`, requesting AE from config, **passing the
   step-1 record**). `local` blocks on the same conditions as cold: ownership by another AE, an open deal,
   lifecycle Meeting Booked / SQL / Opportunity / customer, a prior reply / booked meeting / recent
   connected call, or opt-out. If not affirmatively clear, DO NOT prep — surface + hold with the reason.
   *(Assigner pre-clears only `cold` today, so local usually checks live.)*
3. **Research** — spawn `ob-internal-research` (motion `local`, **reusing the step-1 record**) and `ob-external-research` in parallel.
   Lean on **local presence** (storefront, HQ city, regional events / shows) plus the trigger and the
   SmartScout footprint.
4. **Message** — choose the value prop (`config/value-props.md` affinity + the research) and ONE case
   study from the **local baked index `config/case-studies.md`** (metric **verbatim**; if the vertical isn't
   covered, use the strongest in-value-prop metric as generic proof; the Drive index is the source of
   truth for updating the baked file — fall back to it only if the baked index is missing). Then you **MUST** spawn the **`ob-messaging`** subagent (Task tool, `subagent_type: ob-messaging`; motion `local`) with the research + value prop + case study. It returns the
   **text-message drafts**, the **lunch-invite email**, and the **walk-in talking points**, all in
   Trellis voice. *(Voice + structure live in `ob-messaging`, so the team tunes messaging in one place.)*
5. **Lunch invite → Gmail draft** — use ob-messaging's lunch-invite subject + body **verbatim** (append only the signature); `create_draft` (to: the prospect). **Never send.** Capture the draft id. (Texts are NOT drafted into Gmail — see step 7.) **Before using ANY of ob-messaging's output (texts, lunch email, talking points), gate it against `ob-messaging`'s HARD CONSTRAINTS (top of the agent) for the `local` motion — especially texts ≤320 chars, no signature, no em dashes; if any fail, send it back to redo, don't fix it yourself.**
6. **HubSpot writes:**
   - **Visit task** (HubSpot TASK, on the contact / company) — **due on the date the AE committed to**
     (or the soft date if "sometime"), titled like `In-person visit: <Company> (<city>)`, with the
     **walk-in talking points** in the task body. This is how the AE commits to *when* they'll go.
   - **Visit note** (contact-level, exactly **3 bullets**, glanceable): two **pain points**, then one
     **context** bullet (e.g. "local — HQ in Austin, no prior contact", "store in SoHo", "met at Prosper
     Show"). One short line each, no preamble.
   - Set `trellis_value_prop` and `trellis_batch_date` for reporting. **Do NOT set
     `trellis_sequence_status = pending`** — local isn't the 5-touch email cadence, so `follow-ups`
     should leave it alone. The next action is the visit (the task), not an email sequence.
7. **Hand the texts back as copy** — present each contact's text drafts as a clearly labeled
   copy-paste block in the chat (and in the visit note), since the AE sends these from their own phone.

## Hand back (keep it short)
- "Prepped **N** visits for **<area>**." Per contact: **Company — city — visit date** (committed or
  suggested).
- For each: ✅ texts ready to copy · ✅ lunch invite drafted in Gmail · ✅ talking points + visit task created.
- "**M** flagged, not prepped:" each with the one-line RoE reason (owner / active deal / replied / opted out).
- Reminder: "Nothing sent — **texts are copy for your phone**, the **lunch invite is a Gmail draft** to
  review and send. Your visit task is on **<date>**." Then offer: "Want a post-visit thank-you email
  drafted after you go? Just say so." *(Post-visit follow-up is an open design choice — opt-in for now.)*

## Rules
- **Prep only — never send.** Texts are copy for the AE's phone; the lunch invite is a Gmail draft.
- **All copy (texts, lunch email, talking points) comes from `ob-messaging`, used verbatim** — never write or rewrite it yourself; gate it against ob-messaging's HARD CONSTRAINTS first.
- Respect RoE (step 2 is not optional). Cap **15 visits per run** — in-person is a short list, not a blast.
- **Don't plan the route or the day** — that's the AE's separate route / timing planner. Capture the
  committed date and create the task; never invent a route or a driving order.
- Never fabricate a storefront, location, event, or metric. Case-study numbers are used verbatim from
  the index. No em dashes in the texts or the email; texts carry no signature.
