---
name: setup
description: One-time onboarding for the trellis-ae plugin — run once after installing. Checks your connectors (HubSpot, Gmail, Fathom, Google Drive), finds your HubSpot owner ID, saves your email signature, takes the team Clay webhook, locates the case-study index in Drive, and writes ~/.trellis-ae/config.json. Use when an AE first installs trellis-ae or says "set up trellis."
---

# Setup (run once)

Walk a new AE through trellis-ae onboarding: collect what's needed, verify it, write their config, and
tell them how to run their first list. Friendly and quick — a few prompts, not an interrogation. Never
print secrets back, and resolve IDs at runtime (don't hardcode portal/owner ids).

## 1. Check connectors
Confirm each by making one tiny read (load tools via ToolSearch). Report ✅ / ❌ and, for anything
missing, tell them to enable it in Claude → Settings → Connectors — **you can't connect it for them.**
- **HubSpot** (required) — `get_user_details` or `get_organization_details`.
- **Gmail** (required) — `list_labels` or `list_drafts`.
- **Fathom** (required) — `get_identity` or `list_meetings`.
- **Google Drive** (required, for case studies) — `list_recent_files`.
- **Claude in Chrome** (optional — only a fallback for reading a HubSpot list link if the token below isn't set) — `list_connected_browsers`.
- **Slack** (only if they'll run `accountability` or want reply alerts) — `slack_search_channels`.
If a required one is missing, gather what you can, tell them to connect it, and have them re-run setup.

**Then trim the rest — this is a real credit saver, not housekeeping.** Every connected MCP server's tool
definitions are re-loaded into context on **every subagent spawn**, and the outbound skills spawn several
agents per contact — so an unused connector's cost is paid dozens of times per list. trellis-ae uses **only
the six above** (HubSpot, Gmail, Fathom, Drive, Chrome-if-needed, Slack). **List every _other_ connector
that's currently connected and tell them to disconnect it** — especially heavy ones like **Shopify, Notion,
Google Calendar, Claude Preview, and the MCP registry**, which the plugin never touches. On a lower-credit
plan this is the single biggest reduction, with zero loss of function. (You can't disconnect for them —
point them to Settings → Connectors.)

## 2. Identify the AE
Ask their **full name** and **work email**, then:
- Resolve their **HubSpot owner ID** with `search_owners` (match on email/name) — confirm the match.
- Resolve the **portal ID** with `get_organization_details` (don't hardcode it).

## 3. Email signature
Ask how they sign emails (name + title). Keep it short.

## 4. Case-study index (Drive)
Search Drive (`search_files`) for the shared case-study index (a doc/sheet named like "Trellis Case
Studies" / "Case Study Index"). Confirm the right file and capture its file ID. If they can't find it,
note it and tell them to get the link from the admin.

## 5. Team Clay webhook (for contact-finder)
Ask them to paste the team Clay webhook (pinned in Slack / from the admin). Save it WITHOUT echoing it:
`printf '%s' "PASTED_URL" > ~/.clay-webhook`. Never print it back.

## 6. HubSpot list token (reads list links)
The read-skills read HubSpot list links via the Lists v3 REST API, which needs a private-app token (the
MCP can't read list membership reliably). Ask them to paste the **read-only list token their admin shares**
(pinned in Slack / a password manager — NOT one they create themselves). Save it WITHOUT echoing it:
`printf '%s' "PASTED_TOKEN" > ~/.hubspot-token`. Then confirm it authenticates, without printing it:
`curl -s -o /dev/null -w '%{http_code}' -X POST https://api.hubapi.com/crm/v3/lists/search -H "Authorization: Bearer $(cat ~/.hubspot-token)" -H 'Content-Type: application/json' -d '{"count":1}'`
— **200** = good · **401** = wrong/expired token · **403** = missing the `crm.lists.read` scope. Report
✅/❌, never the token. *(If `~/.hubspot-token` isn't set, the skills fall back to Claude in Chrome, which
caps at the rendered rows — so the token is strongly preferred. Admins who run `assigner` use a read+write token.)*

## 7. Write the config
Create `~/.trellis-ae/` if needed and write `~/.trellis-ae/config.json`:
```json
{
  "hubspot_portal_id": "<resolved>",
  "ae_owner_id": "<their resolved owner id>",
  "ae_name": "<name>",
  "outbound_signature": "<signature>",
  "case_study_index": { "type": "drive_file", "file_id": "<resolved>" },
  "alerts_channel": "<slack channel, or blank>"
}
```

## 8. Schedule + first run
- Have them set the recurring jobs via `/schedule`: **follow-ups at 6 AM weekdays** (and **accountability**
  weekly if they run it).
- Confirm they're ready and suggest a first run: "`/trellis-ae:cold-outbound`, then paste ~25 contacts."

## Rules
- Never print the Clay webhook, the HubSpot token, or any secret. Resolve portal/owner IDs at runtime — never hardcode them.
- If a required connector is missing, guide them to enable it; you can't do it for them.
- Confirm each resolved value with the AE before writing the config.
