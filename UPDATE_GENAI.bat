@echo off
title Update SmartClip AI - Google GenAI Migration
color 0C

echo ========================================================
echo        SMARTCLIP AI - UPDATE GOOGLE GENAI
echo ========================================================
echo.

echo [!] Google GenerativeAI package has been deprecated.
echo     Updating to new google-genai package...
echo.

if not exist .venv (
    echo [!] Virtual environment tidak ditemukan.
    echo     Silakan jalankan "INSTALL_SMARTCLIP.bat" terlebih dahulu.
    pause
    exit /b
)

echo [+] Activating virtual environment...
call .venv\Scripts\activate

echo [+] Uninstalling old google-generativeai package...
pip uninstall google-generativeai -y

echo [+] Installing new google-genai package...
pip install google-genai

echo [+] Updating other dependencies...
pip install --upgrade customtkinter opencv-python numpy mediapipe

echo.
echo ========================================================
echo        UPDATE COMPLETED SUCCESSFULLY!
echo ========================================================
echo.
echo Sekarang Anda bisa menjalankan SmartClip AI tanpa warning.
echo Gunakan "START_SMARTCLIP.bat" untuk membuka aplikasi.
echo.
pause