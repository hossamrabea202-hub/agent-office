param([string]$Script, [int]$Timeout = 180)
$me = Split-Path -Parent $MyInvocation.MyCommand.Path
$c = 'C:\Users\hossa\AppData\Local\Temp\claude\C--Users-hossa-OneDrive-Documents-Unreal-Projects-ChatGPT2\24d8ba66-0bcb-4231-aec1-6e53088d09d5\scratchpad\cmd'
$r = "$c\result.txt"; Remove-Item $r -EA 0
$out = "$me\$([IO.Path]::GetFileNameWithoutExtension($Script)).txt"; Remove-Item $out -EA 0
Copy-Item "$me\$Script" "$c\go.tmp"; Move-Item "$c\go.tmp" "$c\go.py" -Force
$t = 0; while (-not (Test-Path $r) -and $t -lt $Timeout*4) { Start-Sleep -Milliseconds 250; $t++ }
if (Test-Path $r) { Get-Content $r | Select-Object -Skip 1 } else { 'TIMEOUT' }
if (Test-Path $out) { Get-Content $out }
