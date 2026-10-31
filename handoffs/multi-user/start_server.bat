@echo off
rem #302 Multi-User server for Castle Defender (adjustedfilm, 2026-10-31). Run on the MASTER PC (always on during a session).
rem   start_server.bat                 -> LAN only (all machines in the house)
rem   start_server.bat 100.x.y.z       -> also over Tailscale: pass THIS PC's Tailscale IP (tailscale ip -4)
rem Edit UE if UE 5.3 is installed elsewhere.
set UE=C:\Program Files\Epic Games\UE_5.3
set SRV=%UE%\Engine\Binaries\Win64\UnrealMultiUserSlateServer.exe
if not exist "%SRV%" set SRV=%UE%\Engine\Binaries\Win64\UnrealMultiUserServer.exe
if not exist "%SRV%" (echo Multi-User server not found under %UE% - fix the UE line in this file & pause & exit /b 1)
if "%~1"=="" (
  "%SRV%" -CONCERTSERVER=CastleServer
) else (
  "%SRV%" -CONCERTSERVER=CastleServer -UDPMESSAGING_TRANSPORT_UNICAST=%~1:9030
)
