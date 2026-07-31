#!/usr/bin/env python3
"""
instantly.py — trellis-ae ↔ Instantly connector (PROTOTYPE / spike)

Purpose: push Claude-written, RoE-cleared, AE-approved emails into an Instantly
campaign so Instantly does the sending + threading, while Claude/HubSpot stays
the brain (writes the copy, gates who gets a touch).

Auth: reads the Instantly v2 API key from ~/.instantly-key (one line). The key is
NEVER passed on the command line or printed. Create it yourself:
    (in Instantly → Settings → Integrations → API → new key)
    printf '%s' 'YOUR_KEY' > ~/.instantly-key && chmod 600 ~/.instantly-key

Threading model (why this shape):
- Instantly keeps follow-ups in the SAME email thread as long as the SAME sending
  mailbox is used — it owns the thread because it sent E1. So E2 can be written
  AFTER E1 already went out and still land as a reply, AS LONG AS E2 is Step 2 of
  the same lead's sequence (not a brand-new send).
- So: the campaign holds the sequence SKELETON (Step 1 body = {{e1_body}},
  Step 2 body = {{e2_body}}, ...). Each lead carries its own copy in
  custom_variables. We late-fill {{e2_body}} via `fill` once Claude has written +
  RoE-checked it, before Step 2 is due. To NOT send a touch (they got called /
  replied / booked), we pull the lead (`stop`) before that step fires.

GOTCHA (confirmed in docs): updating a lead's custom_variables REPLACES the whole
object, it does not merge. `fill` below reads current vars first, merges, writes back.

Endpoints marked (VERIFY) are best-guess paths to confirm on first live run by
reading the API's error/response — create-lead + campaigns list are confirmed.
"""
import json, os, sys, urllib.request, urllib.error

BASE = "https://api.instantly.ai/api/v2"
KEY_FILE = os.path.expanduser("~/.instantly-key")


def _key():
    try:
        with open(KEY_FILE) as f:
            k = f.read().strip()
    except FileNotFoundError:
        sys.exit(f"No API key at {KEY_FILE}. Create it (see header) — I never handle the raw key.")
    if not k:
        sys.exit(f"{KEY_FILE} is empty.")
    return k


def api(method, path, body=None, query=None):
    url = BASE + path
    if query:
        from urllib.parse import urlencode
        url += "?" + urlencode(query)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + _key())
    req.add_header("Content-Type", "application/json")
    # Instantly sits behind Cloudflare, which 403s (error 1010) the default
    # Python-urllib user-agent. Present a normal browser UA.
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {method} {path}\n{e.read().decode()}")


# ---- commands ---------------------------------------------------------------

def cmd_campaigns(_):
    """List campaigns so we can grab the target campaign id. (confirmed: GET /campaigns)"""
    out = api("GET", "/campaigns", query={"limit": "50"})
    items = out.get("items", out if isinstance(out, list) else [])
    for c in items:
        print(f"{c.get('id')}  [{c.get('status')}]  {c.get('name')}")
    if not items:
        print("(no campaigns — create one in the Instantly UI first)")


def cmd_push(a):
    """Create a lead in a campaign with E1 copy in custom_variables. (confirmed: POST /leads)
       usage: push <campaign_id> <email> <first> <last> <company> <e1_subject> <e1_body>"""
    campaign, email, first, last, company, subj, body = a[0], a[1], a[2], a[3], a[4], a[5], a[6]
    payload = {
        "campaign": campaign,
        "email": email,
        "first_name": first,
        "last_name": last,
        "company_name": company,
        "custom_variables": {"e1_subject": subj, "e1_body": body},
    }
    res = api("POST", "/leads", body=payload)
    print(json.dumps(res, indent=2))


def cmd_push_batch(a):
    """Push a whole approved batch into a campaign from a JSON file (avoids shell-quoting long bodies).
       usage: push-batch <campaign_id> <leads.json>
       leads.json = [{"email","first","last","company","e1_subject","e1_body"}, ...]
       Creates each as a lead (paused campaign) with E1 in custom_variables. Prints per-lead result."""
    campaign, path = a[0], a[1]
    with open(path) as f:
        leads = json.load(f)
    results = []
    for L in leads:
        payload = {"campaign": campaign, "email": L["email"],
                   "first_name": L.get("first", ""), "last_name": L.get("last", ""),
                   "company_name": L.get("company", ""),
                   "custom_variables": {"e1_subject": L["e1_subject"], "e1_body": L["e1_body"]}}
        try:
            r = api("POST", "/leads", body=payload)
            results.append({"email": L["email"], "lead_id": r.get("id"), "ok": True})
        except SystemExit as e:
            results.append({"email": L["email"], "ok": False, "error": str(e)})
    print(json.dumps(results, indent=1))


def cmd_fill(a):
    """Late-fill a later touch's body on an existing lead (replace-all safe: read→merge→write).
       usage: fill <lead_id> <var_name> <value>   e.g. fill <id> e2_body "Following up ..."
       (VERIFY endpoint: GET /leads/{id}, PATCH /leads/{id})"""
    lead_id, var, val = a[0], a[1], a[2]
    cur = api("GET", f"/leads/{lead_id}")               # VERIFY path
    vars_ = dict(cur.get("custom_variables") or {})
    vars_[var] = val
    res = api("PATCH", f"/leads/{lead_id}", body={"custom_variables": vars_})  # VERIFY method/path
    print(json.dumps(res, indent=2))


def cmd_get(a):
    """Fetch a lead by id (to inspect what Instantly stored). (VERIFY: GET /leads/{id})
       usage: get <lead_id>"""
    print(json.dumps(api("GET", f"/leads/{a[0]}"), indent=2))


def cmd_leads(a):
    """List a campaign's leads with reply/open counts (for the sync job's reply-poll + stop-guard).
       usage: leads <campaign_id>   → prints JSON [{id,email,email_reply_count,email_open_count,status}]"""
    campaign = a[0]
    # POST /leads/list is the paged list endpoint; page via starting_after.
    out, after = [], None
    while True:
        body = {"campaign": campaign, "limit": 100}
        if after:
            body["starting_after"] = after
        r = api("POST", "/leads/list", body=body)
        items = r.get("items", [])
        for L in items:
            out.append({"id": L.get("id"), "email": L.get("email"),
                        "email_reply_count": L.get("email_reply_count"),
                        "email_open_count": L.get("email_open_count"),
                        "status": L.get("status")})
        after = r.get("next_starting_after")
        if not after or not items:
            break
    print(json.dumps(out, indent=1))


def cmd_stop(a):
    """Stop a lead's sequence by setting a non-default interest status (Instantly's own method:
       any status other than the default 'Lead' halts the sequence; keeps the record, reversible).
       usage: stop <lead_id> [interest_status]   default interest_status = 3 (a non-default 'paused' value)
       VERIFY on a test lead before the scheduled job mutates anything — field is lt_interest_status."""
    lead_id = a[0]
    status = int(a[1]) if len(a) > 1 else 3
    res = api("PATCH", f"/leads/{lead_id}", body={"lt_interest_status": status})
    print(json.dumps({"stopped": lead_id, "lt_interest_status": status, "ok": bool(res)}, indent=1))


CMDS = {"campaigns": cmd_campaigns, "push": cmd_push, "push-batch": cmd_push_batch,
        "fill": cmd_fill, "get": cmd_get, "leads": cmd_leads, "stop": cmd_stop}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        sys.exit("usage: instantly.py {campaigns|push|fill|get|stop} [args]")
    CMDS[sys.argv[1]](sys.argv[2:])
