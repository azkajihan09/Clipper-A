@echo off
title Installer SmartClip AI
color 0A

echo ========================================================
echo        SMARTCLIP AI - AUTOMATIC INSTALLER
echo ========================================================
echo.

:: 1. Check Python
echo [+] Memeriksa instalasi Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python tidak ditemukan!
    echo     Silakan install Python 3.10 atau 3.11 dari python.org.
    echo     Pastikan centang "Add Python to PATH" saat install.
    echo.
    pause
    exit /b
)
echo     Python terdeteksi.

:: 2. Check FFmpeg (Simple check if in path, warning only)
echo.
echo [+] Memeriksa FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] FFmpeg tidak terdeteksi di PATH system.
    echo     Aplikasi memerlukan FFmpeg untuk pemrosesan video.
    echo     Pastikan anda telah mengunduh FFmpeg dan menambahkannya ke PATH,
    echo     ATAU letakkan file ffmpeg.exe di dalam folder ini.
    echo.
    echo     Tekan sembarang tombol untuk melanjutkan instalasi dependency...
    pause >nul
) else (
    echo     FFmpeg terdeteksi. (OK)
)

:: 3. Create Virtual Env
echo.
echo [+] Membuat Virtual Environment (.venv)...
if exist .venv (
    echo     Virtual environment sudah ada. Melewati langkah ini.
) else (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [!] Gagal membuat virtual environment.
        pause
        exit /b
    )
    echo     Berhasil dibuat.
)

:: 4. Install Dependencies
echo.
echo [+] Menginstall Library yang dibutuhkan...
echo     Proses ini membutuhkan internet. Mohon tunggu...
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [!] Terjadi kesalahan saat install library.
    echo     Cek koneksi internet anda atau pesan error di atas.
    pause
    exit /b
)

echo.
echo ========================================================
echo        INSTALASI BERHASIL! SIAP DIGUNAKAN.
echo ========================================================
echo.
echo Gunakan "START_SMARTCLIP.bat" untuk membuka aplikasi.
echo.
pause
