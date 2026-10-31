# #302 Can this PC be a Multi-User editor seat for Castle Defender (UE 5.3.2)?  (adjustedfilm, 2026-10-31)
#   powershell -ExecutionPolicy Bypass -File check_pc.ps1        (reads only; changes nothing)
# Prints GPU / VRAM, CPU, RAM, free disk, installed UE versions and Tailscale, then a verdict. Paste the output on card #302.
$gpu = Get-CimInstance Win32_VideoController | ForEach-Object {
    $vram = 0
    # AdapterRAM caps at 4 GB; the registry has the real size for most drivers
    foreach ($k in (Get-ItemProperty 'HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0*' -ErrorAction SilentlyContinue)) {
        if ($k.DriverDesc -eq $_.Name -and $k.'HardwareInformation.qwMemorySize') { $vram = [int64]$k.'HardwareInformation.qwMemorySize' }
    }
    if (-not $vram) { $vram = [int64]$_.AdapterRAM }
    [pscustomobject]@{ Name = $_.Name; VRAM_GB = [math]::Round($vram / 1GB, 1) }
}
$cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
$ram = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
$disks = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null } | ForEach-Object { [pscustomobject]@{ Drive = $_.Name; FreeGB = [math]::Round($_.Free / 1GB) } }
$ue = @()
$dat = 'C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat'
if (Test-Path $dat) { $ue = (Get-Content $dat -Raw | ConvertFrom-Json).InstallationList | Where-Object { $_.AppName -like 'UE_*' } | ForEach-Object { "$($_.AppName) at $($_.InstallLocation)" } }
$ts = [bool](Get-Command tailscale -ErrorAction SilentlyContinue) -or (Test-Path 'C:\Program Files\Tailscale\tailscale.exe')

"== Castle Defender seat check ($env:COMPUTERNAME)"
$gpu | Format-Table -AutoSize | Out-String
"CPU: $cpu"
"RAM: $ram GB"
$disks | Format-Table -AutoSize | Out-String
"Unreal installed: " + ($(if ($ue) { $ue -join '; ' } else { 'none' }))
"Tailscale: " + ($(if ($ts) { 'installed' } else { 'not installed' }))

$best = ($gpu | Measure-Object VRAM_GB -Maximum).Maximum
$free = ($disks | Measure-Object FreeGB -Maximum).Maximum
$why = @()
if ($best -lt 6) { $why += "GPU has $best GB VRAM (needs 6+, 8+ recommended)" }
if ($ram -lt 32) { $why += "RAM $ram GB (32 recommended; 16 works for light editing only)" }
if ($free -lt 200) { $why += "largest free disk $free GB (needs ~200: engine ~45 + project + DDC)" }
if ($best -ge 6 -and $free -ge 200) { "VERDICT: can be an editor seat" + ($(if ($why) { ' (note: ' + ($why -join '; ') + ')' } else { '' })) }
else { "VERDICT: not an editor seat: " + ($why -join '; ') + ". It can still run an agent (background work, no editor)." }
