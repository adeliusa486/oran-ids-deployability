# EXP-058: transfer from D_A and from D_B to the third corpus D_C, detached.
# Usage (repo root): powershell -ExecutionPolicy Bypass -File scripts/exp058_launch.ps1
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = (Get-Command python).Source
# a_to_c: 20 split seeds (as EXP-041); b_to_c: 10 (the D_B source takes ~10 min per seed)
foreach ($d in @("a_to_c", "b_to_c")) {
  $seeds = if ($d -eq "b_to_c") { " --seeds 10" } else { "" }
  $log = "results/EXP-058/logs/$d.log"
  Start-Process -FilePath $py -WorkingDirectory $root -WindowStyle Hidden `
    -ArgumentList ("experiments/run_transfer_v2.py --exp EXP-058 --direction $d --sweeps --group-counts" + $seeds) `
    -RedirectStandardOutput $log -RedirectStandardError ($log -replace '\.log$', '.err.log')
  "started $d"
}
