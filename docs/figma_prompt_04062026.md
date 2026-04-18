# Figma Prompt — BioFlow Scheduler Wireframes

> Use this prompt with Figma's AI features (Figma Make, Figma AI, or any Figma-compatible mockup generator). Copy the entire prompt below into Figma. The prompt is structured to produce a complete set of wireframes covering all key user flows.

---

## CONTEXT SECTION (paste this first)

I need you to design wireframes for **BioFlow Scheduler**, an AI-driven manufacturing scheduling tool for autologous CAR-T cell therapy. This is an enterprise SaaS product used by pharmaceutical manufacturing teams to schedule patient batches across cleanroom suites.

### Product summary

BioFlow uses reinforcement learning to recommend optimal batch-to-suite assignments. It does not replace humans — it sits next to manufacturing coordinators and recommends actions they approve, override, or flag. The tool integrates with existing platforms (Vineti, TrakCel, MES, LIMS) and presents a unified view.

### Design principles

1. **Glanceable status, deep on demand.** Coordinators are juggling many things — they need to absorb the current state in 3 seconds, then drill down only when something needs attention.
2. **Action-oriented, not browse-oriented.** Every screen should make the next action obvious. No "explore the dashboard" patterns.
3. **Trust through transparency.** Every AI recommendation must show *why* — confidence score, top contributing factors, alternative options.
4. **Pharma-appropriate aesthetic.** Clinical, calm, professional. Not consumer-app playful. Think Epic, Veeva, or Benchling — not Notion or Linear.
5. **Compliance-visible.** Audit trail entries, e-signature prompts, and version indicators should be present but not dominant.

### Visual style

- **Color palette:** Primarily neutral (whites, light grays, deep navy for primary actions). Use color sparingly and semantically — green for healthy/approved, amber for attention needed, red for critical/blocked, blue for informational.
- **Typography:** Sans-serif (Inter or similar). Generous line height. Clear hierarchy with 3-4 sizes max.
- **Density:** Medium-to-high information density. These are professional users, not first-timers. Tables and Gantt charts should fit lots of data without feeling cramped.
- **No icons-as-decoration.** Every icon must convey meaning. No dashboard fluff.
- **Card-based layout.** Group related information in subtle cards with thin borders (not heavy shadows).
- **Status colors:** Success #10b981, Warning #f59e0b, Danger #ef4444, Info #3b82f6, Neutral grays #f3f4f6 / #6b7280 / #1f2937.

### Brand colors

- Primary: Deep navy #1e2761 (used sparingly, for primary CTAs and brand accents)
- Secondary: Soft blue #cadcfc (backgrounds, hover states)
- Accent: Teal #0f6e56 (for healthy metrics and confirmations)

---

## USERS & INTERACTION MOMENTS

Design for two primary personas. Each persona has multiple interaction "moments" that require different screens.

### Persona 1: Maya — Manufacturing Coordinator

Maya runs daily scheduling for a CAR-T manufacturing site with 6 cleanroom suites. She works 8-hour shifts and is responsible for assigning incoming patient batches to suites, handling disruptions (QC failures, equipment downtime, urgent patients), and coordinating handoffs with the next shift. She is technically literate but not a data scientist. Her current tools are Excel, email, and a Vineti dashboard. She is skeptical of AI but open if it makes her job easier.

**Maya's interaction moments to design:**

1. **Start of shift (morning login)** — Maya needs to absorb the current state: which suites are running, which batches are in progress, what changed overnight, and what needs her attention first.

2. **New patient assignment** — A new patient order arrives. Maya needs to see the recommendation, understand why, and approve or override.

3. **QC failure response** — A batch fails quality control. Maya needs to see the cascade impact and the recommended re-scheduling plan.

4. **Urgent patient escalation** — A clinical site flags a deteriorating patient. Maya needs to evaluate whether to preempt a current batch and what the trade-offs are.

5. **End of shift handoff** — Maya needs to generate a structured handoff summary for the incoming coordinator.

### Persona 2: David — Manufacturing Director

David runs the entire site. He has 4 coordinators reporting to him, manages a $30M annual P&L, and reports to the VP of Operations. He cares about throughput, vein-to-vein time, batch failure rates, and capacity utilization. He checks in 2-3 times per day and runs a weekly capacity review.

**David's interaction moments to design:**

1. **Morning KPI review** — David opens the app first thing. He wants yesterday's performance, today's outlook, and any incidents.

2. **Weekly capacity planning** — David runs a what-if analysis to plan the next 30/60/90 days based on the known patient pipeline.

3. **Monthly board prep** — David generates an exportable report showing throughput trends, attribution, and forward-looking capacity.

---

## SCREENS TO DESIGN

Generate the following screens. Each screen should be a separate frame in the Figma file, labeled clearly. Design at desktop resolution (1440x900). Where mobile is mentioned, also produce a mobile companion frame (375x812).

### Screen 1: Login & shift selection

**User:** Maya (and any user)
**Moment:** Start of session

A clean login screen with SSO (SAML / OIDC) as the primary path. After login, if the user is a coordinator, prompt them to select which shift they're starting (morning, afternoon, night). Show the current site name and date prominently.

**Key elements:**
- Company logo top-left
- "Sign in with SSO" as the primary button (deep navy)
- "Sign in with email" as a secondary text link below
- After login: shift selector card with three large buttons (Morning 7am-3pm, Afternoon 3pm-11pm, Night 11pm-7am)
- Current site indicator: "Rockville Site A" with a small site selector dropdown
- Compliance footer: "21 CFR Part 11 compliant · v2.1.4 · Audit logging enabled"

---

### Screen 2: Coordinator home — start of shift

**User:** Maya
**Moment:** First screen after shift selection

This is the most important screen in the entire product. Maya needs to absorb the state of the facility in 3 seconds, see what changed overnight, and know what needs her attention first.

**Layout:** Three-column dashboard.

**Left column (30% width): "Needs your attention"**
A vertical stack of 3-5 action cards, ordered by urgency. Each card shows:
- A status icon (urgent / attention / info)
- A one-line description ("Patient PT-2401 cells expiring in 18 hours")
- Time since flagged
- A primary action button ("Review")

Examples to include in the mockup:
- "QC failure overnight: Batch B-1042 — review re-scheduling plan" (urgent, red)
- "New urgent patient PT-2487 from Memorial Sloan Kettering" (attention, amber)
- "Suite 4 cleaning cycle complete, ready for next batch" (info, blue)
- "Shift handoff note from Sarah (night shift)" (info, gray)

**Center column (45% width): "Today's schedule"**
A Gantt chart showing the next 24 hours across all 6 suites. Each suite is a horizontal lane. Each batch is a colored bar showing patient ID, current phase, and estimated completion. Color-code by status (in progress = teal, scheduled = light blue, at risk = amber, blocked = red). Time axis along the top with current time indicator (vertical line).

Above the Gantt: a small toolbar with view toggles (24h / 48h / 7d), a filter dropdown (all suites / specific suite), and a "Refresh" button with last-updated timestamp.

**Right column (25% width): "At a glance"**
Four KPI tiles stacked vertically:
- Suite utilization: 78% (with mini sparkline showing 7-day trend)
- Patients in queue: 12 (with breakdown: 3 urgent, 7 standard, 2 scheduled)
- Avg wait time: 11.4 days (with delta vs last week: -0.6 days, green)
- This week's throughput: 18 batches (with target: 22, amber indicator)

Below the KPIs: a small "system status" indicator showing model version, last training date, and confidence ("Model v2.3.1 · trained 2 weeks ago · avg confidence 87%")

**Top bar (across all columns):**
- Logo + product name on the left
- Site / shift indicator: "Rockville Site A · Morning shift · Maya R."
- Notification bell with red dot
- User avatar with dropdown

---

### Screen 3: New patient assignment — recommendation view

**User:** Maya
**Moment:** A new patient order arrives via Vineti

Maya clicked on a notification ("New patient assignment needed: PT-2487"). She lands on this screen.

**Layout:** Two-panel layout. Left panel = recommendation. Right panel = patient context.

**Left panel (60% width): "Recommended assignment"**

A large card with the recommendation:
- Header: "Recommended: Assign to Suite 3, start in 4 hours"
- Confidence indicator: large pill saying "92% confidence" in green
- Three sub-cards showing alternatives:
  - "Alternative 1: Suite 5, start tomorrow 8am — 84% confidence — adds 0.8 days wait"
  - "Alternative 2: Suite 2, start in 6 hours — 78% confidence — minor resource conflict"
- Below the alternatives: "Why this recommendation?" expandable section showing the top 3 SHAP factors:
  - Suite 3 has the earliest open slot matching this indication's typical duration
  - Patient acuity score (0.72) prioritizes earlier start
  - Suite 3 expansion success rate for this indication is 94% historically
- Bottom of card: two large buttons side-by-side
  - Primary (deep navy): "Approve recommendation"
  - Secondary (outline): "Override and choose differently"
- Below buttons: a small "Flag for supervisor review" link

**Right panel (40% width): "Patient context"**

A scrollable card showing:
- Patient header: "PT-2487 · DLBCL · Female, 64"
- Acuity score: 0.72 (medium-high) with explanation tooltip
- Key dates:
  - Apheresis scheduled: April 8, 2026
  - Cells expected: April 9, 2026
  - Target infusion window: April 22-26, 2026
- Treatment center: "Memorial Sloan Kettering, NYC"
- Bridging therapy status: "On bridging therapy until infusion"
- Clinical notes: "Patient has had two prior lines of therapy. Disease progression noted on last imaging. Treating physician requests earliest possible slot."
- Linked Vineti record: button "Open in Vineti ↗"

**Top bar:** breadcrumb showing "Home > Patient queue > PT-2487 assignment"

---

### Screen 4: QC failure response

**User:** Maya
**Moment:** A batch fails QC release testing

Maya clicked on the urgent notification "QC failure: Batch B-1042". She lands on this screen.

**Layout:** Top alert banner + impact view + recommended plan.

**Top banner:**
A red alert banner spanning the top: "QC Failure · Batch B-1042 · Patient PT-2401 · Failed sterility test at 11:42pm" with a "View QC report ↗" link.

**Middle section: Cascade impact**
A horizontal timeline showing the next 7 days. Above the timeline, a label: "Schedule cascade impact (without re-optimization)". Show:
- The original schedule for affected suites as faded bars
- The disruption point marked with a red vertical line
- Affected downstream batches highlighted with red borders
- A summary line: "4 patients affected, average wait increase 2.3 days"

**Bottom section: Recommended re-scheduling plan**
A card with the title "Recommended re-scheduling plan" and a green checkmark. Inside:
- A second timeline showing the proposed new schedule with re-arranged batches
- A summary comparing old vs new: "Re-scheduled to minimize patient impact: 2 patients affected, average wait increase 0.6 days"
- An expandable "What changed?" section listing the moves:
  - "Batch B-1043 moved from Suite 2 to Suite 5"
  - "Batch B-1045 delayed by 8 hours"
  - "Patient PT-2401 will need re-collection — clinical site notified"
- Action buttons:
  - Primary: "Apply re-scheduling plan"
  - Secondary: "Modify plan"
  - Tertiary text link: "Reject and handle manually"

**Right side panel:** "Notify stakeholders" checklist
- ☑ Treating physician for PT-2401
- ☑ Clinical site coordinator
- ☑ QA team
- ☐ VP of Operations (only if requested)
- "Send notifications" button at bottom

---

### Screen 5: Urgent patient escalation

**User:** Maya
**Moment:** A clinical site escalates a deteriorating patient

Maya receives a notification: "Urgent: Patient PT-2493 deteriorating, treating physician requesting expedited slot." She lands on this screen.

**Layout:** Decision-support view with side-by-side options.

**Top header:**
A prominent header: "Urgent escalation · PT-2493" with patient acuity now showing as 0.94 (red, increased from 0.71 yesterday).
Subtitle: "Treating physician request received 12 minutes ago"

**Body: Decision options**

Three side-by-side option cards. Each card shows the same structure:

**Option A: "Schedule normally"**
- Estimated start: April 12 (6 days from now)
- Patient impact: "High — patient may not survive wait window"
- Operational impact: "Minimal — no schedule changes"
- Confidence: 88%
- Recommendation badge: gray (no recommendation)

**Option B: "Expedite to next available slot" (RECOMMENDED)**
- Estimated start: April 8 (2 days from now)
- Patient impact: "Medium — within survival window"
- Operational impact: "Low — minor delays for 2 other patients (avg 0.4 days)"
- Confidence: 91%
- Recommendation badge: green "Recommended"

**Option C: "Preempt current batch in Suite 4"**
- Estimated start: 6 hours from now
- Patient impact: "Low — earliest possible"
- Operational impact: "High — current batch B-1051 must be discarded, patient PT-2456 will need re-collection"
- Confidence: 76%
- Recommendation badge: red "High disruption"

Each card has a "Select this option" button. The recommended option (B) has its button styled as primary.

**Right side panel: Patient timeline**
A vertical timeline showing key clinical events:
- April 1: Patient enrolled
- April 3: Apheresis completed
- April 5: Acuity score 0.71
- April 6 (today): Acuity score 0.94, physician escalation
- "Required infusion by": April 14 (highlighted)

**Bottom bar:**
"Decision will be logged with e-signature. You will be required to provide justification for your selection."

---

### Screen 6: End of shift handoff

**User:** Maya
**Moment:** End of her shift, before logging out

A focused screen with one job: produce a clean handoff document for the next coordinator.

**Layout:** Left panel = auto-generated content. Right panel = preview.

**Left panel: "Handoff content (auto-generated)"**

A series of expandable sections, each pre-populated by the system:

1. **Shift summary** — auto-generated paragraph: "During this shift, 4 batches progressed normally, 1 QC failure was handled with re-scheduling, 2 new patients were assigned, and 1 urgent escalation was approved with expedited scheduling."

2. **Open issues for next shift** — checklist:
   - "Suite 6 ventilation maintenance scheduled for 4pm — confirm completed"
   - "PT-2487 transducation results expected at 8pm — verify before assigning next batch to Suite 3"
   - "Patient PT-2493 expedited start requires 6am verification call to MSKCC"

3. **Decisions made (with rationale)** — auto-list of all approve/override actions taken during the shift.

4. **Optional notes** — a free-text area for Maya to add personal observations.

**Right panel: "Preview"**
A formatted version of the handoff document as it will appear to the next coordinator. Updates live as Maya edits the left panel.

**Bottom bar:**
- "Save and sign" button (primary)
- "Save as draft" link (secondary)
- The handoff is signed with the coordinator's e-signature and timestamped.

---

### Screen 7: Director home — morning KPI review

**User:** David
**Moment:** First check-in of the day

David opens the app. He needs yesterday's performance, today's outlook, and any incidents — in 60 seconds.

**Layout:** A dashboard optimized for executive-level glanceability. Larger numbers, more whitespace, fewer interactive elements than Maya's view.

**Top section: "Yesterday at a glance"**
A row of 5 large KPI cards:
- Throughput: 4 successful infusions (target: 3, green)
- Avg vein-to-vein time: 14.2 days (target: <15, green)
- Suite utilization: 81% (target: 75-85%, green)
- Batch failure rate: 11% (target: <12%, green)
- Open incidents: 1 (red)

Each card has a tiny sparkline showing the 14-day trend.

**Middle section: "Today's outlook"**

Two side-by-side cards:

**Left card: "Capacity forecast (next 7 days)"**
A line chart showing daily projected utilization. Yesterday and today are solid, future days are dashed. A horizontal target band shows the 75-85% optimal range. Days projecting outside the band are highlighted.

**Right card: "Patient pipeline"**
A horizontal stacked bar showing the patient queue composition:
- 3 in process (teal)
- 2 awaiting cells (blue)
- 7 in queue (gray)
- 2 urgent (amber)

Below the bar: small text "12 total patients, 18% urgent share"

**Bottom section: "Incidents & alerts"**
A list of any open incidents, each with:
- Severity icon
- Description
- Owner
- Time elapsed
- "View details" link

For the mockup, show one incident: "QC failure on Batch B-1042 — handled by Maya R. — re-scheduling plan applied — closed at 7:14am"

**Top right: Shortcuts**
Three buttons:
- "Run capacity forecast"
- "Generate weekly report"
- "Export to PDF"

---

### Screen 8: Capacity planning — what-if analysis

**User:** David
**Moment:** Weekly capacity planning meeting

David is exploring "what if we add a 7th suite" or "what if patient demand grows 20%".

**Layout:** Controls on the left, simulation results on the right.

**Left panel (30% width): "Scenario controls"**

A form with adjustable parameters:
- Number of suites: slider from 4 to 12 (default 6)
- Average daily patient arrival rate: slider from 0.5 to 5 (default 1.8)
- QC failure rate: slider from 5% to 25% (default 12%)
- Average expansion duration: slider from 10 to 20 days (default 14)
- Time horizon: dropdown (30 / 60 / 90 / 180 days)

A "Run simulation" button at the bottom (primary). Above it: "Simulation will run 1000 trajectories. Estimated time: 12 seconds."

**Right panel (70% width): "Simulation results"**

Three stacked sections:

1. **Headline metrics** — three large numbers comparing the scenario to current state:
   - "Projected throughput: 28 batches/week (+27%)"
   - "Projected avg wait: 9.1 days (-2.3 days)"
   - "Projected utilization: 72% (-9pp)"

2. **Throughput chart** — a line chart showing daily throughput over the time horizon, with a confidence band (5th-95th percentile across 1000 simulations). A second line shows current state for comparison.

3. **Bottleneck analysis** — a horizontal bar chart showing which constraint binds in the new scenario:
   - Suite capacity (40% of constraints)
   - QC throughput (30%)
   - Cell expansion variability (20%)
   - Patient arrival timing (10%)

**Bottom action bar:**
- "Save scenario" (saves the configuration for later reference)
- "Compare scenarios" (opens a modal to compare against another saved scenario)
- "Export to slides"

---

### Screen 9: Audit trail viewer (for QA persona)

**User:** QA reviewer
**Moment:** Periodic audit or incident investigation

A focused, table-driven screen for browsing the immutable audit log.

**Layout:** Filters on top, table dominant.

**Top filter bar:**
- Date range picker
- User filter (dropdown of coordinators)
- Action type filter (dropdown: all / approve / override / preempt / model_deploy / etc.)
- Patient ID search
- Batch ID search
- "Apply filters" button + "Clear" link

**Main table:**
Columns:
- Timestamp (sortable, default desc)
- User (with avatar)
- Action type (color-coded pill)
- Subject (patient or batch ID, clickable)
- Details (one-line summary)
- Justification (truncated, expandable)
- Model version
- Signature status (icon)

Each row is a single audit entry. Clicking a row expands it inline to show full details, including before/after state, related actions, and the cryptographic signature hash.

**Right side: "Quick stats"**
A small panel showing for the current filter:
- Total entries: 247
- Override rate: 14% (32 of 234 recommendations)
- Most active user: Maya R.
- Most overridden recommendation type: "preempt"

---

### Screen 10: Mobile companion — coordinator notifications

**User:** Maya
**Moment:** Off-shift, receives an urgent alert on her phone

Most coordinator work happens at a desktop, but urgent escalations need to reach Maya on her phone. Design a focused mobile screen for handling escalations on-the-go.

**Layout:** Single-column mobile (375x812). No login required if device is enrolled — biometric quick auth.

**Top:**
- App header: "BioFlow"
- Notification banner: "1 urgent action required"

**Body: Single action card**
- Patient ID + acuity badge
- One-line situation: "PT-2493 deteriorating — physician requests expedited slot"
- Recommendation: "Expedite to April 8 (2 days from now)"
- Confidence: 91%
- Two large buttons stacked vertically:
  - "Approve recommendation" (primary, full-width)
  - "Open full details" (secondary, full-width)
- Below: "Decline and call team" link

**Bottom:**
- All other notifications (collapsed, summary only)
- Status: "On call · Maya R. · 9:42pm"

---

## DELIVERABLES

Produce the following:
1. All 10 screens as separate, labeled frames in a single Figma file.
2. A simple component library showing reusable elements: KPI tile, action card, batch bar (Gantt segment), confidence pill, status badge, primary button, secondary button.
3. A title frame at the top of the file with the project name "BioFlow Scheduler — Wireframes v1" and a brief legend explaining the color-coding system (status colors, persona indicators).

## CONSTRAINTS

- Wireframes should be **medium fidelity**. Show real content (not Lorem Ipsum), real data values that look plausible, and proper hierarchy. Do not spend time on photographic imagery, micro-animations, or finished illustrations.
- Use **placeholder shapes for charts** (a clean line, a bar chart skeleton) — do not generate fake data visualizations with random points.
- **Do not invent features** beyond what is described above. If a screen needs an element not specified, use a labeled placeholder rectangle ("Stakeholder notification widget — TBD").
- **Annotate non-obvious interactions** with small numbered callouts and a legend on each frame (e.g., "1. Clicking the recommendation card opens the full SHAP explanation modal").

## STYLE REFERENCES

The visual language should feel like a cross between:
- **Linear** (clean information density, restrained color)
- **Veeva Vault** (pharma-appropriate, compliance-visible)
- **Datadog** (real-time ops dashboard patterns, status indicators)
- **Epic Hyperspace** (clinical workflow patterns, action-oriented)

It should NOT feel like:
- Notion (too playful, too consumer)
- Salesforce Lightning (too cluttered, too generic)
- Generic admin templates (too sterile, no personality)

---

**End of Figma prompt.**
