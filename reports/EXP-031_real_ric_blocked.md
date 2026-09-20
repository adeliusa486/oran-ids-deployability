# EXP-031 — Real Near-RT RIC runtime track

**Date:** 2026-09-20
**Phase:** 31
**Gate:** **BLOCKED**, not attempted and not partially attempted
**Decision affected:** D-005 (Track C at Level 2)

---

## 1. Verdict in one line

Track C cannot run on this host. The blocker is now **command-verified and
specific**, which it was not before: it is not "needs dedicated hardware", it is
a single uninstalled Windows feature that prevents any Linux kernel from starting
at all.

## 2. What was actually checked

D-005 recorded the blocker as "the development host is Windows 11, while the
runtime methodology requires `isolcpus`, `nohz_full`, `cpupower` and `pidstat`".
That was an inference from the operating system, not a measurement. Since the
brief argues that a FlexRIC-based environment is now a realistic benchmark rather
than a hypothetical, the host was re-probed properly.

The findings were better than D-005 assumed, and then worse.

| Prerequisite | Present? | Evidence |
|---|---|---|
| Docker CLI | **yes** | `Docker version 29.6.2, build dfc4efb` |
| kubectl | **yes** | `v1.36.1`, Kustomize `v5.8.1` |
| WSL2 registered, Ubuntu default | **yes** | `Default Distribution: Ubuntu`, `Default Version: 2` |
| **WSL2 able to start** | **NO** | see below |
| **Docker Linux engine** | **NO** | see below |
| CPU isolation (`isolcpus`, `nohz_full`) | **NO** | unreachable — no Linux kernel to configure |

### The blocker

```
$ wsl -d Ubuntu -- bash -lc 'uname -a'
The operation could not be started because a required feature is not installed.
Error code: Wsl/Service/CreateInstance/CreateVm/HCS/HCS_E_SERVICE_NOT_AVAILABLE
```

```
$ docker info
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine;
check if the path is correct and if the daemon is running
```

The Windows **Virtual Machine Platform** / Hyper-V feature is not installed. WSL2
is registered but cannot instantiate a VM, and Docker Desktop's Linux engine runs
*on* WSL2, so both routes fail for the same single reason.

Installing that feature requires **local administrator rights and a reboot**.
Neither is available to this session, and neither is something an experiment
script may do on a user's machine unasked.

## 3. What a Level-2 run would still have failed to deliver

Worth stating, because it changes how much this blocker costs.

Even with WSL2 running, the measurement would have been made on a **virtualised
Linux kernel inside a Windows laptop with no isolated cores**. D-005 lists CPU
isolation, a `performance` governor and disabled turbo as prerequisites, and they
are prerequisites for a reason: tail latency is exactly what a noisy scheduler
destroys, and p99/p99.9 are the numbers the whole track exists to produce.

So the realistic outcome of forcing this route was **a third emulated
measurement wearing the word "real"**, which is worse than an honest gap. That is
the thing D-005's "required labelling" section was written to prevent, and it is
the thing the previous README accidentally did anyway.

## 4. What the literature now supplies instead

`reports/literature_audit_v2.md`, finding 2:

**Obiuwevwi et al. (2026)**, *Enabling Real-Time AI in O-RAN: Deploying and
Measuring AI Inside a Near-RT RIC xApp*, arXiv:2607.01583 — an AI xApp on a real
**OpenAirInterface + FlexRIC** testbed:

| Quantity | Reported |
|---|---|
| Logistic regression inference | 1–5 µs |
| Shallow MLP inference | 10–25 µs |
| End-to-end service latency | < 4 ms |
| 10 ms near-RT budget | met for > 95% of projected loop executions |

This is the measurement Track C was for, done properly, by people with the
hardware. The right response is to cite it, not to approximate it badly.

## 5. What their numbers do to our latency finding

This is the substantive scientific content of this phase, and it is a negative
result about our own method.

| Model | Ours — emulated, Python/sklearn, p50 | Theirs — embedded, real RIC |
|---|---:|---:|
| logistic regression | 2.45 ms | 1–5 **µs** |
| MLP | 2.25 ms | 10–25 **µs** |

Roughly **three orders of magnitude**, for the same model families. A gap that
size is not hardware and not CPU isolation. It is the difference between a
compiled model embedded in a service and a Python object graph calling into
scikit-learn per request.

The consequence for our Finding 4:

> The near-RT conformance verdict is not a property of the model architecture.
> It is a property of the implementation. Our emulated measurement places four of
> six architectures inside a 10 ms budget and two outside it, and orders them by
> architecture. A real embedded implementation places the two *slowest-ranked-by-us*
> families three orders of magnitude inside the same budget. Any recommendation
> of an architecture on the basis of prototype latency is a statement about the
> prototype's toolchain, not about the architecture.

That is more useful than the finding it replaces. It also means our own **C9**
verdict — "only XGBoost meets p99", already contradicted by our measurement — is
now contradicted a second time, from outside.

And it sharpens Finding 5. Our extraction/inference ratios (7x–39x for the light
architectures) were computed against Python inference times of 0.18–0.96 ms. If
deployed inference is microseconds, then **feature extraction does not merely
dominate — it is essentially the entire budget**, and the pure-Python exporter
caveat in `results/EXP-005` becomes the most important open question in the
latency story. That is what Phase 30 measures.

## 6. Required manuscript consequences

| Item | Action |
|---|---|
| Every latency figure | labelled **EMULATED**; measurement class stated in the caption |
| "Near-RT conformance" | **removed as a claim.** Budget crossing points reported as a sensitivity analysis, not a verdict |
| Track C | reported as **BLOCKED / not executed**, with the reason in §2 |
| C9 | remains **CONTRADICTED** |
| Finding 4 | rewritten around implementation, per §5 |
| Obiuwevwi et al. 2026 | cited in Related Work and at every latency claim |
| `final_validation` | `RIC INTEGRATION .... BLOCKED` — correct, unchanged |

## 7. What would unblock it

In order of cost:

1. Install the Windows Virtual Machine Platform feature and reboot. Gets WSL2 and
   Docker back, but **still no CPU isolation** — good enough for E2 message-path
   and throughput work, not for tail latency.
2. A bare-metal Linux host with root: `isolcpus`, `nohz_full`, `rcu_nocbs`,
   `performance` governor, turbo disabled, `OMP_NUM_THREADS=1`. This is what
   D-005 specified and it remains the requirement for any p99 claim.
3. FlexRIC plus a synthetic E2 load generator with a **recorded** arrival process.
   A Poisson and a periodic generator produce different tails, so the arrival
   distribution is a reported parameter, not an implementation detail.
4. The floor experiment (D-007) before any model is timed.

Nothing in the design changes. Only the hardware is missing, and it is missing
for a reason that is one administrator action away from being fixed — which is
worth recording, because it means this gap is cheap to close later and should not
be designed around permanently.
