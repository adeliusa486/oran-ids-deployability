# Track C: runtime measurement

## Before any measurement

1. Boot with `isolcpus=`, `nohz_full=`, `rcu_nocbs=` on the measurement cores.
2. `cpupower frequency-set -g performance`; disable turbo.
3. `export OMP_NUM_THREADS=1` (ONNX and BLAS oversubscription inflates the tail).
4. Verify no co-tenants: `pidstat 1 10`.

## Run the floor experiment FIRST

An xApp whose model is `lambda x: 0.0`. Its latency distribution is the platform
floor. Every model result is interpreted against it. If the floor p99 is already
near the 10 ms budget, the latency finding is about the platform, not the models,
and Section VI-E must say so.

## Fallback levels (state which was used, in both paper and README)

1. Real RIC + real gNB + real E2.
2. Real RIC + synthetic E2 load, no gNB.
3. xApp container only, E2 encode/decode included, no RIC.

Level 3 still supports the "feature extraction dominates" claim. It does not
support the p99-against-budget claim as strongly.
