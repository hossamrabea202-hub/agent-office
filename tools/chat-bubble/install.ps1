# Installs the Chat Bubble: desktop + Startup shortcuts, then starts it.  install.ps1 [ChatName]
param([string]$Me = '')
$ps1 = Join-Path $PSScriptRoot 'ChatBubble.ps1'
$args1 = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ps1`"" + $(if ($Me) { " -Me $Me" } else { '' })
$ws = New-Object -ComObject WScript.Shell
foreach ($d in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Startup'))) {
    $s = $ws.CreateShortcut((Join-Path $d 'Studio Chat.lnk'))
    $s.TargetPath = 'powershell.exe'; $s.Arguments = $args1
    $s.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"; $s.Description = 'Studio chat bubble'; $s.Save()
}
Start-Process powershell.exe -ArgumentList $args1 -WindowStyle Hidden
Write-Host 'Chat Bubble installed (desktop + Startup) and started.'
