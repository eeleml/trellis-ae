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

### Phase 2 — what to build to turn `cs-format` on (and why)

**Build decision: a file + edits to existing skills, NOT a new agent.** Variant assignment is a few lines
of logic and case studies are *data* — neither needs a subagent. (Agents here are for reusable *reasoning*
— research, copywriting, RoE checks. Looking up an asset and attaching a file is mechanical; it belongs in
the skill that drafts + a data file.)

**1. Case-study registry (data / file).** Extend the case-study index (in Drive/Notion, or add a
`config/case-studies.md` pointer list) so each study carries, next to its metric: a **PDF asset** (Drive
file id) for the `pdf` arm and a **HubSpot preview link** for the `link` arm. *Why:* the system already
reads case-study metrics live from the index; phase 2 just needs that same index to also know where each
study's PDF + link live. Customer specifics stay in Drive/HubSpot, never in the repo.

**2. Variant assignment + tag (edit `cold-outbound`).** At draft time, read the active `cs-format`
experiment from this file, assign the contact to an arm (≈1/3 each, by a **stable hash of the contact id**
so re-runs land in the same arm), and stamp `trellis_ab_variant = cs-format:<arm>`. *Why:* assignment has
to happen where outreach is created, and the tag is what `ab-testing` groups results by. Stable (not
random) keeps a contact consistent if the list is reprocessed.

**3. Attach / insert per arm (edit `cold-outbound`'s draft step).**
- `none` → today's behavior (metric cited in the body; nothing attached).
- `pdf` → attach the case-study **PDF** (Drive file id from the registry) to the Gmail draft.
- `link` → insert the **HubSpot preview link** in the body.
*Why:* the draft is built by `cold-outbound` via `create_draft`, so the attach/insert lives there. This is
the one genuinely new capability — nothing in the system attaches anything today.

**4. No change to `ab-testing`.** It already reads results by `trellis_ab_variant`; once contacts are
tagged and sends accumulate, it judges the arms.

**Confirm before building:** which case studies go in the registry; the minimum sample (≥~100/arm is a
placeholder); and whether to wire `cold-outbound` only first (vs. also `closed-lost` / `local-visits`,
which could reuse the registry later — extract a shared helper at that point if so).
