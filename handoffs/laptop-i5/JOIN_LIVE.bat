@echo off
rem JOIN_LIVE.bat - open Castle Defender on this laptop and join the Master's live Multi-User session.
rem Put this file next to CastleDefender.uproject, then double-click it.
rem   JOIN_LIVE.bat              -> Master on the ZBook's Mobile Hotspot (192.168.137.1)
rem   JOIN_LIVE.bat 100.x.y.z    -> Master's Tailscale IP (when not on the hotspot)
setlocal
set MASTER=%~1
if "%MASTER%"=="" set MASTER=192.168.137.1
set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe
set PROJ=%~dp0CastleDefender.uproject
if not exist "%UE%" (echo Unreal Engine 5.8 not found at "%UE%" & pause & exit /b 1)
if not exist "%PROJ%" (echo Put this file next to CastleDefender.uproject & pause & exit /b 1)
rem Multi-User needs the same plugin list as the Master: add MultiUserClient once.
powershell -NoProfile -Command "$p=$env:PROJ; $j=Get-Content -Raw $p | ConvertFrom-Json; if (-not ($j.Plugins | Where-Object Name -eq 'MultiUserClient')) { $j.Plugins += [pscustomobject]@{Name='MultiUserClient';Enabled=$true}; $j | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $p; 'Multi-User plugin enabled' }"
echo Joining session CastleDefender on %MASTER%:9030 ...
echo If Windows Firewall asks: tick Private AND Public, then Allow.
start "" "%UE%" "%PROJ%" -CONCERTAUTOCONNECT -CONCERTSERVER=CastleDefenderServer -CONCERTSESSION=CastleDefender -CONCERTDISPLAYNAME=Laptop-i5 -UDPMESSAGING_TRANSPORT_STATIC=%MASTER%:9030
