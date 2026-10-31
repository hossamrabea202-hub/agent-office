@echo off
rem #302 Join the live Castle Defender session (adjustedfilm, 2026-10-31). Run on every OTHER editor seat.
rem   join_session.bat "D:\CastleDefender\CastleDefender.uproject" SeatName
rem   join_session.bat "D:\CastleDefender\CastleDefender.uproject" SeatName 100.a.b.c 100.x.y.z
rem        (Tailscale: this PC's Tailscale IP, then the server PC's Tailscale IP)
rem The project copy must be the SAME revision as the server's (same files, same UE 5.3.2), or joining is refused.
set UE=C:\Program Files\Epic Games\UE_5.3
set ED=%UE%\Engine\Binaries\Win64\UnrealEditor.exe
if not exist "%ED%" (echo UnrealEditor.exe not found under %UE% - fix the UE line in this file & pause & exit /b 1)
if "%~2"=="" (echo usage: join_session.bat "path\to\CastleDefender.uproject" SeatName [myTailscaleIP serverTailscaleIP] & pause & exit /b 1)
set NET=
if not "%~4"=="" set NET=-UDPMESSAGING_TRANSPORT_UNICAST=%~3:0 -UDPMESSAGING_TRANSPORT_STATIC=%~4:9030
"%ED%" "%~1" -CONCERTAUTOCONNECT -CONCERTSERVER=CastleServer -CONCERTSESSION=CastleDefender -CONCERTDISPLAYNAME=%~2 %NET%
