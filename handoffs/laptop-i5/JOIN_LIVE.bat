@echo off
rem JOIN_LIVE.bat - open Castle Defender on this laptop and join the Master's live Multi-User session.
rem Put this file next to CastleDefender.uproject, then double-click it.
rem   JOIN_LIVE.bat              -> Master over Tailscale (ZBook = 100.87.149.123)
rem   JOIN_LIVE.bat 192.168.137.1 -> Master on the ZBook Mobile Hotspot instead
setlocal
set MASTER=%~1
if "%MASTER%"=="" set MASTER=100.87.149.123
set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe
set PROJ=%~dp0CastleDefender.uproject
if not exist "%UE%" (echo Unreal Engine 5.8 not found at "%UE%" & pause & exit /b 1)
if not exist "%PROJ%" (echo Put this file next to CastleDefender.uproject & pause & exit /b 1)
rem Multi-User needs the same plugin list as the Master: add MultiUserClient once.
powershell -NoProfile -Command "$p=$env:PROJ; $j=Get-Content -Raw $p | ConvertFrom-Json; if (-not ($j.Plugins | Where-Object Name -eq 'MultiUserClient')) { $j.Plugins += [pscustomobject]@{Name='MultiUserClient';Enabled=$true}; $j | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $p; 'Multi-User plugin enabled' }"
echo Joining session CastleDefender on %MASTER%:9030 ...
echo If Windows Firewall asks: tick Private AND Public, then Allow.
rem 2026-11-02: start on the empty Entry map, NOT ThirdPersonMap: opening the map from disk before the join loads ~110 BPs
rem that the join then hot-reloads in one frame, which crashed i5 (05:10, 05:18, 08:13, 08:38). Open the map after the join.
start "" "%UE%" "%PROJ%" /Engine/Maps/Entry -CONCERTAUTOCONNECT -CONCERTSERVER=CastleDefenderServer -CONCERTSESSION=CastleDefender6 -CONCERTDISPLAYNAME=Laptop-i5 -LocalLogTimes -ExecCmds="r.Streaming.PoolSize 400, py C:/Users/hossam.rabea/agent-office/handoffs/laptop-i5/ue_inbox_watcher.py" -UDPMESSAGING_TRANSPORT_UNICAST=0.0.0.0:9031 -UDPMESSAGING_TRANSPORT_STATIC=%MASTER%:9030
