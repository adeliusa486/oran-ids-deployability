# Generation prompts for Figure 1 and Figure 2

**Date:** 2026-09-20
**Why these exist:** both figures currently assert things the measurements
contradict. Figure 2 states "32 total, 24 shared" features (it is 15 shared
concepts / 18 columns) and "5 architectures, 5 seeds" (it is 8 and 20), and both
figures show a **live RIC measurement that was never executed** (Track C is
BLOCKED — `reports/EXP-031_real_ric_blocked.md`).

These prompts are self-contained. Hand either one to an illustrator, an AI image
tool, or use it as the specification for a TikZ rewrite.

**Non-negotiable across both figures:** nothing may be drawn in a way that
implies a measurement we did not take. Anything not executed is drawn in a
visually distinct, obviously-inactive style and labelled as such.

---

## FIGURE 1 — Reference deployment and measurement points

### Purpose

Establish where an intrusion-detection xApp sits in an O-RAN deployment, what it
observes, and — critically — **which of the paper's three deployment criteria are
measured in that setting and which are not.**

### Format

- **Full page width** (IEEE `figure*`, two-column span), approximately 7.16 in
  wide by 2.6 in tall.
- Vector output (PDF or SVG). No raster.
- Serif font matching the body text (Times/Nimbus), 7–8 pt for node labels,
  6 pt for sub-labels.
- Print-safe: must be legible in greyscale and at 100% zoom on paper.

### Layout — left to right, three zones

**Zone A (left, ~0–28% of width): the access side.**

A horizontal chain of four boxes, equal vertical centre:

```
[ IoT devices ] --Uu--> [ O-RU ] --> [ O-DU ] --> [ O-CU ]
```

- "IoT devices" is wider than the others and carries a two-line sub-label in
  smaller type: *sensors, meters, cameras*.
- The `Uu` label sits above the first arrow.
- O-RU, O-DU and O-CU are uniform small boxes.

**Zone B (right, ~35–100%): the edge data centre.**

Enclose this zone in a **dashed rounded rectangle with a very light grey fill**,
labelled in the bottom-left corner in small bold grey: **Edge data centre**.

Inside it, two rows.

*Lower row — the platform:*

```
[ E2 termination                     ] <--> [ Near-RT RIC platform                                  ]
  E2AP / E2SM-KPM / E2SM-RC                   message router · shared data layer · subscription mgr
```

*Upper row — three xApps sitting on the platform, each connected down to the
platform box by a short vertical bidirectional arrow:*

```
[ KPIMON xApp ]   [ IoT intrusion detection xApp (this work) ]   [ Traffic steering xApp ]
```

The **centre xApp is the subject of the paper** and must be visually dominant:
thicker border, a warm accent colour (red family), bold label, and noticeably
larger than its two neighbours. The flanking xApps are muted (green family, thin
border) — they exist only to show the xApp is one tenant among several.

*Above the enclosure:*

```
[ Non-RT RIC / SMO  —  rApps, model lifecycle, policy ]
```

connected down to the detection xApp by a single arrow labelled **A1**.

**Zone C: the connection between A and B.**

A bidirectional arrow from O-CU to E2 termination, labelled **E2**, crossing the
enclosure boundary.

**The mitigation path.** A **dashed red arrow** leaving the top-left of the
detection xApp, routing up and around the outside of the enclosure, down the left
side, and back into the bottom of O-CU. Label it below the O-CU in small red
type: *mitigation action (E2SM-RC)*. Drawing it as a long way round is
deliberate — it visually conveys that the control loop is closed through the RAN,
not inside the RIC.

### The measurement points — this is the part that must change

Three small circled numerals placed on the diagram. **They must be styled in two
distinct ways**, and the caption must explain the distinction.

| Marker | Placement | Style | Meaning |
|---|---|---|---|
| **1** | On the detection xApp, upper right | **Solid yellow fill, black border** | MEASURED |
| **2** | On the link between the xApp column and the platform | **Solid yellow fill, black border** | MEASURED |
| **3** | On the E2 path, between O-CU and E2 termination | **Hollow / white fill, dashed grey border** | **EMULATED — not measured in this setting** |

Add a small two-entry legend in the lower-right of the enclosure:

```
(●) measured on this path      (○) emulated off-platform; see Limitations
```

This distinction is the entire reason the figure is being redrawn. Marker 3 sits
on the E2 path because that is where decision latency *would* be measured, and it
must be visually obvious that it was not measured there.

### Caption

> Reference deployment. The near-real-time RIC is hosted in a regional edge data
> centre and aggregates telemetry from many E2 nodes, so the detection xApp
> observes the combined behaviour of a large IoT population. Circled markers show
> where this paper takes measurements: (1) cross-deployment generalisation of the
> classifier and (2) the alert burden imposed on the operator per unit time are
> measured; (3) decision latency against the near-real-time budget is **emulated
> off-platform**, with no RIC in the path, and supports relative ordering only.

### Do not draw

- Any indication that the xApp was deployed, containerised or executed on a RIC.
- Any throughput, load or saturation annotation — no load sweep was performed.
- Any "real-time" or "conformance" wording.

---

## FIGURE 2 — Experimental pipeline

### Purpose

Show that **one trained model is evaluated under four protocols of increasing
realism**, and that each step away from the convenient protocol costs
performance. The old version showed three evaluation arms, one of which never
ran. This version's argument is the *ladder*.

### Format

- **Single column** (IEEE `figure`), approximately 3.5 in wide by 3.2 in tall.
- Vector output. Serif font, 6.5–7 pt labels, 5.5 pt sub-labels.
- Must survive greyscale printing: distinguish arms by border style and fill
  density, not by hue alone.

### Layout — a left spine, a right ladder

**Left column (the training spine), four boxes stacked top to bottom, joined by
downward arrows.** Blue family, light fill.

```
┌──────────────────────────────────┐
│ D_A : O-RAN testbed              │
│   Zeek flow records + radio KPIs │
└──────────────────────────────────┘
                ↓
┌──────────────────────────────────┐
│ Shared feature space             │
│   15 concepts / 18 columns       │
└──────────────────────────────────┘
                ↓
┌──────────────────────────────────┐
│ Group-disjoint split (src_ip)    │
│   20 split seeds                 │
└──────────────────────────────────┘
                ↓
┌──────────────────────────────────┐
│ Train                            │
│   8 architectures incl. 2 floors │
└──────────────────────────────────┘
```

**Every number in those boxes is load-bearing and must be exactly as written.**
The previous version said "32 total, 24 shared" and "5 architectures, 5 seeds";
both were wrong. The phrase **"incl. 2 floors"** must appear — the trivial
baselines are what make every downstream number readable.

**Right column (the evaluation ladder), four boxes stacked top to bottom,
ordered by increasing realism.** Each receives an arrow from the "Train" box.

Render them with **progressively heavier borders and darker fill going down**, so
the ladder reads as increasing difficulty at a glance:

```
① Held-out D_A, group-disjoint      lightest
   in-distribution reference

② Time-disjoint D_A                 ↓
   train early runs, test late

③ D_B : 5G-NIDD                     ↓
   independent deployment, once

④ Operational / calibration         darkest
   base-rate sweep, threshold, burden
```

Annotate each arrow from "Train" to its evaluation box with the measured cost, in
small type beside the arrow:

- to ①: *reference*
- to ②: *−0.27 F1*
- to ③: *to the trivial floor*
- to ④: *PPV 0.93 → 0.006*

**The blocked arm.** Below the ladder, a fifth box drawn in an obviously inactive
style — **grey hatched or heavily stippled fill, dashed grey border, grey text**:

```
┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
╎ Live Near-RT RIC                  ╎
╎   NOT EXECUTED — see Limitations  ╎
└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
```

Its incoming arrow is **dashed grey**, not solid. Including this box rather than
deleting it is deliberate: it shows the reader what the design intended and what
was not achieved, which is more honest than silently omitting the arm.

**A one-way gate.** Draw a small vertical barrier or a distinct marker on the
arrow into box ③, annotated in small type:

> *evaluated once; every access logged*

This encodes protocol A11 visually.

### Caption

> Experimental pipeline. One trained model is evaluated under four protocols of
> increasing realism, and each step away from the conventional protocol costs
> performance: a group-disjoint held-out split, a time-disjoint split of the same
> corpus, an independently collected corpus evaluated once, and an operational
> analysis over a swept attack base rate. The live-RIC arm was not executed.
> Numbers on the arrows are measured degradations relative to the in-distribution
> reference.

### Do not draw

- "ONNX", "container image" or any packaging step — no model was packaged.
- Any arrow suggesting target data flows back into training, harmonisation,
  threshold selection or model selection. The pipeline is strictly left-to-right
  into box ③.
- A fine-tuning or adaptation arm. None was run.

---

## Verification checklist before either figure ships

- [ ] No number in Figure 2 disagrees with `configs/features/shared_space.yaml`
      or `results/EXP-026/statistics/provenance__a_to_b.json`
- [ ] Marker 3 in Figure 1 is visually distinct and captioned as emulated
- [ ] The word "conformance" appears in neither figure nor caption
- [ ] The blocked RIC arm is visible and unmistakably inactive in Figure 2
- [ ] Both figures legible in greyscale at print size
- [ ] Trivial baselines are mentioned in Figure 2's training box
