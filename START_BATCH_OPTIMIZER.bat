@echo off
title SmartClip AI - Batch Platform Optimizer
color 0B

if not exist .venv (
    echo [!] Virtual environment tidak ditemukan.
    echo     Silakan jalankan "INSTALL_SMARTCLIP.bat" terlebih dahulu.
    pause
    exit /b
)

echo [+] Membuka Batch Platform Optimizer...
call .venv\Scripts\activate
python batch_optimizer.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Aplikasi tertutup karena error.
    pause
)