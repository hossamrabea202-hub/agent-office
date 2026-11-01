@echo off
rem Chat Bubble: puts a "Studio Chat" shortcut on the desktop and in Startup (starts with Windows), then starts it.
rem   INSTALL_CHAT_BUBBLE.bat            counts every new chat line
rem   INSTALL_CHAT_BUBBLE.bat Alien      counts only lines NOT from Alien (use your chat name)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %1
