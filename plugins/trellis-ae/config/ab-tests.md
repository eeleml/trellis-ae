# A/B tests — outbound messaging experiment registry

The `/trellis-ae:ab-testing` skill reads this file to know what's being tested and proposes updates to
it (human-approved). One experiment per section. Nothing here changes messaging on its own — the motion
skills + `ob-messaging` carry out whatever is marked **rolled out**, and only after a human says so.
`/trellis-ae:cold-outbound` reads this file at draft time to offer the AE a test to run on the batch (pick
one from here, define their own, or brainstorm via `ab-testing`).

## How variants are recorded
Each enrolled contact gets a **`trellis_ab_variant`** value on its HubSpot contact record =
`<experiment-id>:<arm>` (e.g., `cs-format:pdf`, `closer:soft`). Sends/replies are read from Gmail and
grouped by that tag. A contact is in at most one running experiment at a time.

**Property type: single-line text.** It must be free text so it can hold any `experiment:arm` string and
scale to new experiments/arms with no schema edits. Do NOT make it an enumeration — a fixed option list
(or a bare A/B) can't namespace experiments or carry 3-arm tests (e.g. `cs-format` = none/pdf/link).

> ⚠ **Migration needed (as of 2026-06-22):** the live property in portal 6658395 is currently an
> *enumeration* with options `A`/`B`, and **0 contacts are tagged**. Convert it to single-line text (keep
> the internal name `trellis_ab_variant` and label "Trellis A/B Variant") before enrolling anyone. Nothing
> is tagged yet, so the conversion is safe.

## Status legend
`draft` = defined, not yet live (the send-path wiring may not exist) · `running` = arms being assigned +
measured · `concluded` = winner picked / rolled out.

---

## cs-format — does the case study help, and in what format?
- **Status:** `draft` — NOT yet live. (a) Splitting contacts across arms + stamping `trellis_ab_variant`
  now exists (the `cold-outbound` picker). (b) Still needs the send-path to actually **attach a case-study
  PDF** / **insert a HubSpot preview link** in the Gmail draft — that capability isn't built yet (phase 2).
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

---

## closer-style — does a soft close beat a clipped tag-CTA?
- **Status:** `ready` — the variant-assignment wiring now exists (the `cold-outbound` picker assigns arms +
  stamps the tag, `ob-messaging` renders the arm, `follow-ups` applies it to E4/breakup). Only prerequisite:
  `trellis_ab_variant` must be single-line text (or use the A/B-enum stopgap for this single 2-arm test).
  **Ethan wants this run first.**
- **Hypothesis:** on the softer touches (E4, the breakup, any "I can send X" line), a low-pressure,
  forward-looking close earns more replies than a clipped tag-CTA. `ob-messaging` already **defaults to the
  soft close** (clipped tags like "Want it?" / "I'm one reply away" are banned there); this test checks
  whether that default is actually the reply-winner or whether a direct micro-ask pulls more.
- **Arms (≈1/2 each):**
  - `closer:soft` — control / current default: forward-looking, door left open ("let me know if that
    changes," "if [priority] shifts this season, I'm around").
  - `closer:ask` — a clipped direct micro-ask, re-introduced for this arm only ("Want it?", "Want a quick
    teardown?", "I'm one reply away").
  - *(optional 3rd arm `closer:none` — drop the closing line entirely, let the prior sentence stand.)*
- **Scope:** ONLY the closing line of E4 / breakup / "I can send X" touches. The early give-first audit ask
  and the meeting ask ("Open to 15 minutes?", "Want me to pull a teardown?") are identical across arms.
- **Metric:** reply rate (primary), meeting-booked rate (secondary).
- **Minimum sample:** ≥ ~100 sends per arm before calling a winner (placeholder — reply rates are low, so
  anything smaller is directional only).
- **Assignment:** at draft time (`cold-outbound` / `follow-ups`), stamp `trellis_ab_variant = closer:<arm>`
  by stable hash of contact id. Once the `cs-format` phase-2 wiring exists, this needs only the
  arm-appropriate closer from `ob-messaging` — nothing new to build.
- **Results so far:** —
