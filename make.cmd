@echo off
if "%1"=="test" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { . '%~dp0build\venv\Scripts\Activate.ps1'; python '%~dp0scripts\run_tests.py' %* }"
    exit /b %ERRORLEVEL%
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0make.ps1" %*
