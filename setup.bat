@echo off
REM Minimal first-time setup for the will system.
REM Installs only what is needed to run Claude Code, then exits.
REM Claude handles everything else.
REM
REM Usage: Double-click or run from Command Prompt in the will folder.

setlocal enabledelayedexpansion
title will — system setup

echo.
echo   will - system setup
echo   Installing prerequisites for Claude Code...
echo.

REM ---------------------------------------------------------------------------
REM Check winget
REM ---------------------------------------------------------------------------
where winget >nul 2>&1
if errorlevel 1 (
    echo ERROR: winget not found.
    echo Install "App Installer" from the Microsoft Store, then re-run.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------------------
REM git
REM ---------------------------------------------------------------------------
echo =^> git
where git >nul 2>&1
if not errorlevel 1 (
    echo     -- git already installed
) else (
    winget install --id Git.Git --silent --accept-package-agreements --accept-source-agreements
    echo     ok: git installed
)

REM ---------------------------------------------------------------------------
REM Node.js
REM ---------------------------------------------------------------------------
echo =^> Node.js
where node >nul 2>&1
if not errorlevel 1 (
    echo     -- node already installed
) else (
    winget install --id OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    echo     ok: node installed
)

REM ---------------------------------------------------------------------------
REM uv
REM ---------------------------------------------------------------------------
echo =^> uv
where uv >nul 2>&1
if not errorlevel 1 (
    echo     -- uv already installed
) else (
    powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression"
    echo     ok: uv installed
)

REM ---------------------------------------------------------------------------
REM Claude Code
REM ---------------------------------------------------------------------------
echo =^> Claude Code
where claude >nul 2>&1
if not errorlevel 1 (
    echo     -- claude already installed
) else (
    call npm install -g @anthropic-ai/claude-code
    echo     ok: Claude Code installed
)

REM ---------------------------------------------------------------------------
REM Done — hand off to Claude
REM ---------------------------------------------------------------------------
echo.
echo ==============================================================
echo.
echo   Prerequisites installed.
echo.
echo   You may need to open a NEW terminal window so PATH updates
echo   take effect.
echo.
echo   From this folder, run:
echo.
echo       claude
echo.
echo   Claude will read SETUP.md and walk you through the rest.
echo.
echo ==============================================================
echo.
pause
