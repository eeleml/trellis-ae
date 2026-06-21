# A/B tests — outbound messaging experiment registry

The `/trellis-ae:ab-testing` skill reads this file to know what's being tested and proposes updates to
it (human-approved). One experiment per section. Nothing here changes messaging on its own — the motion
skills + `ob-messaging` carry out whatever is marked **rolled out**, and only after a human says so.

## How variants are recorded
Each enrolled contact gets a **`trellis_ab_variant`** value on its HubSpot record = `<experiment-id>:<arm>`
(e.g., `cs-format:pdf`). Sends/replies are read from Gmail and grouped by that tag. A contact is in at
most one running experiment at a time.

## Status legend
`draft` = defined, not yet live (the send-path wiring may not exist) · `running` = arms being assigned +
measured · `concluded` = winner picked / rolled out.

---

## cs-format — does the case study help, and in what format?
- **Status:** `draft` — NOT yet live. Needs the send-path to (a) split contacts across arms + stamp
  `trellis_ab_variant`, and (b) actually **attach a case-study PDF** / **insert a HubSpot preview link**
  in the Gmail draft. That capability isn't built yet (phase 2).
- **Hypothesis:** including the case study lifts reply + meeting rate, and the **format** (PDF vs link) matters.
- **Arms (≈1/3 each):**
  - `cs-format:none` — control: no case study attached (today's behavior — the metric is still cited in the body).
  - `cs-format:pdf` — case study attached as a **PDF** (pulled from the Drive case-study index).
  - `cs-format:link` — case study as a **HubSpot preview link** in the body.
- **Metric:** reply rate (primary), meeting-booked rate (secondary). No open rate (manual sends untracked).
- **Minimum sample:** ≥ ~100 sends per arm before calling a winner. *(Placeholder — tune with Ethan; reply
  rates are low, so anything smaller is only directional.)*
- **Assignment:** at `cold-outbound` time, once the phase-2 wiring exists.
- **Results so far:** —
