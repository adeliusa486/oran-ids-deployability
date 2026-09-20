# EXP-025 — Target corpus acquisition and verification

**Date:** 2026-09-20
**Phase:** 25
**Gate:** A1-target — **CLOSED**
**Verdict:** an independent target corpus was obtained from an open, citable,
author-associated repository under CC BY 4.0. **RQ1 is no longer blocked.**

---

## 1. Why this was the highest-priority phase

The previous campaign ended with one sentence that mattered more than the rest of
the report:

> RQ1 has no result because no target corpus could be obtained.

Cross-deployment generalisation is what the paper's title promises. Without a
second corpus there is no transfer experiment, and the paper measures evaluation
protocol and alert burden — both real, neither the headline.

Decision D-011 had recorded the blocker honestly and let Phase 2 proceed without
it. This phase closes it.

## 2. What was rejected, and why

The corpus was already chosen: 5G-NIDD, fixed as `D_B` by D-002. The problem was
never identification, it was **access**.

| Route | Outcome |
|---|---|
| IEEE DataPort (`10.21227/xtep-hv36`) | **Paywalled.** The canonical DOI requires a paid subscription for the data behind it |
| Third-party mirrors (Kaggle re-uploads, GitHub copies) | **Rejected.** Unattributable: no checksum, no licence statement, no way to show the bytes match what the authors published |

The rejection of mirrors is not fastidiousness. A corpus whose provenance cannot
be established cannot support a generalisation claim, because a reader has no way
to tell whether the target was the published corpus or a re-processed derivative
of it. The previous campaign had already set this standard and it is kept here.

## 3. The route that worked

**Etsin / Fairdata — the Finnish national research data repository.**

```
Landing page  https://etsin.fairdata.fi/dataset/9d13ef28-2ca7-44b0-9950-225359afac65
Repository DOI  10.23729/e80ac9df-d9fb-47e7-8d0d-01384a415361
Licence         CC BY 4.0
Access          open, no account, no request
```

This is an institutional repository operated by CSC for the Finnish Ministry of
Education and Culture. It is the authors' own national deposit of the same
corpus, not a re-upload, and it carries its own citable DOI. It satisfies the
brief's access order at the "legitimate institutional source" tier while ranking
above it on openness: no access request was needed at all.

The IEEE DataPort DOI and the IEEE Data Descriptions article
(`10.1109/IEEEDATA.2025.3592888`) remain the citations of record in
`configs/corpora/d_b.yaml`. The Etsin deposit is recorded as the route by which
the bytes were obtained. Both are in the paper.

## 4. Integrity

All four published artefacts were hashed on download and **re-verified for this
report**:

| File | Bytes | SHA-256 (first 16) | Status |
|---|---:|---|---|
| `Combined.zip` | 28,028,224 | `07531b251f3f35be` | verified |
| `Encoded.zip` | 30,635,901 | `62de4b513e1f294d` | verified |
| `Combined.csv` | 275,265,610 | `fa36f80859585f47` | verified |
| `Encoded.csv` | 489,226,785 | `7c238e2d5dabbc1a` | verified |

Full hashes: `data/provenance/d_b_files.json`.

The compressed sizes matched the repository's own published record **to the byte
before anything was extracted**, which is the check that distinguishes the
authors' artefact from a re-processed copy.

## 5. Schema and label verification

Performed on the artefact, not on the landing page.

| Property | Value |
|---|---|
| Rows | 1,215,890 |
| Columns | 52 |
| Exporter | **Argus** flow records, GTP layer removed, both base stations concatenated |
| Attack prevalence | 60.71% |
| Exact duplicate rows | 1 |
| Binary label | `Label` ∈ {Benign, Malicious} |
| Category label | `Attack Type`, 8 attack classes + Benign |
| Tool label | `Attack Tool` — Hping3, Goldeneye, Torshammer, Nmap, Slowloris |
| **Identifier columns** | **NONE.** No IP addresses, no ports |
| Time columns | none usable as a wall clock |

### Class composition

| Class | Rows | Canonical |
|---|---:|---|
| Benign | 477,737 | benign |
| UDPFlood | 457,340 | dos |
| HTTPFlood | 140,812 | dos |
| SlowrateDoS | 73,124 | dos |
| TCPConnectScan | 20,052 | probe |
| SYNScan | 20,043 | probe |
| UDPScan | 15,906 | probe |
| SYNFlood | 9,721 | dos |
| ICMPFlood | 1,155 | dos |

Written into `configs/labels/canonical_map.yaml`, whose `corpus_d_b` block moves
from `not_yet_downloaded` to `verified`. An unmapped label raises rather than
becoming a silent `other` (B-008).

### One mapping worth stating explicitly

`HTTPFlood` maps to **`dos`, not `web`.** It is an HTTP-layer denial of service
produced by Goldeneye and Torshammer. D_A's `web` category is SQL injection, XSS
and directory brute force, which have no counterpart in D_B at all. Mapping
`HTTPFlood` onto `web` would invent a correspondence and make the transfer result
look better than it is.

### Category coverage against D_A

D_A has six canonical categories; D_B has three.

| Canonical | D_A | D_B |
|---|:--:|:--:|
| benign | yes | yes |
| dos | yes | yes |
| probe | yes | yes |
| ddos | yes | **no** |
| bruteforce | yes | **no** |
| web | yes | **no** |

`ddos`, `bruteforce` and `web` are **UNTESTABLE in transfer** and are reported as
such. They are not dropped quietly and not averaged into a macro score as if they
had been evaluated. The prediction recorded in the label map before download —
that coverage would be exactly {benign, dos, probe} — was correct.

## 6. Source/target overlap

| Check | Result |
|---|---|
| Shared flow records | None possible — different testbeds, different years, different operators |
| Shared identifiers | None — D_B publishes no IPs or ports |
| Shared column names | **Zero.** Zeek and Argus agree on nothing lexically |
| Shared measurable concepts | 15, mapped by meaning in `configs/features/shared_space.yaml` |

The absence of identifier columns in D_B is a benefit and is recorded as one: it
removes the route by which a model memorises which host attacks, and it means no
group key is needed, since D_B is evaluated whole and never split for training.

## 7. What was NOT used

`Encoded.csv` (489 MB) is present, hashed, and **deliberately unused**. It is
pre-encoded and one-hot expanded, and it discards the original Argus field names,
which makes it impossible to map onto D_A's Zeek columns by meaning. Using it
would mean accepting somebody else's undocumented feature construction as the
shared space. `Combined.csv` is the artefact of record.

## 8. Protocol discipline

The non-negotiable from the plan is kept and is now **enforced in code rather
than promised in prose**:

- `load_target_d_b()` appends every call to
  `results/EXP-026/logs/target_access.log` with a timestamp and a stated reason.
- The shared feature space was fixed, committed and unit-tested **before** any
  target metric was computed.
- No transform in that space is fitted, so none can carry target information.
- The decision threshold is fixed at 0.5 and is never tuned on D_B.

D-017 records the one relaxation made, and the reason: a reverse-direction
(D_B → D_A) run is needed to distinguish "detectors do not transfer" from "D_B is
simply harder". It is run and stored separately, after the primary direction.

## 9. Status

| Item | Before | After |
|---|---|---|
| Target corpus | none obtainable | **obtained, open, verified** |
| D-011 | blocking | **resolved** |
| `configs/corpora/d_b.yaml` | `status: unresolved` | `status: resolved` |
| Label map `corpus_d_b` | `not_yet_downloaded` | `verified` |
| RQ1 | no result possible | **experiment runnable** — EXP-026 |

`reports/RQ1_blocked.md` is **not** written. That branch of the decision tree does
not apply: the corpus was obtained legitimately, and the transfer experiment runs.
