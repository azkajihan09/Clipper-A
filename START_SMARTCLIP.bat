@echo off
title SmartClip AI Launcher
color 0B

if not exist .venv (
    echo [!] Virtual environment tidak ditemukan.
    echo     Silakan jalankan "INSTALL_SMARTCLIP.bat" terlebih dahulu.
    pause
    exit /b
)

echo [+] Membuka SmartClip AI...
@REM Clear Python cache silently
@if exist __pycache__ rmdir /s /q __pycache__ >nul 2>&1
@for /d /r %%i in (__pycache__) do @if exist "%%i" rmdir /s /q "%%i" >nul 2>&1
@del /s /q *.pyc >nul 2>&1

call .venv\Scripts\activate
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Aplikasi tertutup karena error.
    pause
)
