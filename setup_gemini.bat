@echo off
REM Quick Gemini Setup Script
REM Double-click this file to set up your Gemini API key

echo ======================================================================
echo GEMINI API KEY SETUP
echo ======================================================================
echo.
echo This script will help you add your Gemini API key to the .env file
echo.
echo Step 1: Get your free API key from:
echo   https://aistudio.google.com/apikey
echo.
echo Step 2: Copy your API key (looks like: AIzaSyXXX...)
echo.
set /p APIKEY="Step 3: Paste your API key here and press Enter: "

if "%APIKEY%"=="" (
    echo.
    echo ERROR: No API key entered!
    echo Please run this script again and paste your key.
    pause
    exit /b 1
)

echo.
echo Updating .env file...

REM Backup existing .env
if exist .env (
    copy .env .env.backup >nul
    echo Created backup: .env.backup
)

REM Update the API key in .env
powershell -Command "(gc .env) -replace 'GOOGLE_API_KEY=.*', 'GOOGLE_API_KEY=%APIKEY%' | Out-File -encoding ASCII .env"

echo.
echo ======================================================================
echo SUCCESS! Your Gemini API key has been configured.
echo ======================================================================
echo.
echo Testing the API connection...
echo.

REM Test the API
.venv\Scripts\python.exe test_gemini.py

echo.
echo ======================================================================
echo.
echo To run your first AI-powered astrological analysis:
echo.
echo   .venv\Scripts\python.exe main.py --date 2025-12-15 --time 12:00 --lat 28.6139 --lon 77.2090
echo.
echo See GEMINI_SETUP.md for more examples!
echo.
pause
