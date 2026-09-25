# Round-2 revision: launch the three long experiments as detached processes, so
# they survive the end of an interactive session. EXP-054 and EXP-055 resume from
# their raw CSV; EXP-056 restarts. Logs go to results/EXP-05x/logs/.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File scripts/round2_launch.ps1
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = (Get-Command python).Source
$jobs = @(
  @{ log = "results/EXP-056/logs/transfer.log";
     args = "experiments/run_transfer_v2.py --exp EXP-056 --direction a_to_b --sweeps --group-counts --seeds 10" },
  @{ log = "results/EXP-055/logs/run.log";
     args = "experiments/run_published_pipeline.py --repeats 2" },
  @{ log = "results/EXP-054/logs/run.log";
     args = "experiments/run_target_reference.py --seeds 3 --native-seeds 2" }
)
foreach ($j in $jobs) {
  $err = $j.log -replace '\.log$', '.err.log'
  Start-Process -FilePath $py -ArgumentList $j.args -WorkingDirectory $root `
    -RedirectStandardOutput $j.log -RedirectStandardError $err -WindowStyle Hidden
  "started: $($j.args)"
}
