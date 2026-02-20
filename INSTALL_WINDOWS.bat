@echo off
echo ==========================================
echo   Vacation Deal Finder - Installation
echo ==========================================
echo.
echo 1. Creating Virtual Environment...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from python.org
    pause
    exit /b
)

echo.
echo 2. Installing Dependencies (this may take a minute)...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo 3. Installing Browsers for Airbnb Scraper...
venv\Scripts\python.exe -m patchright install

echo.
echo ==========================================
echo   DONE! You can now use START_APP.bat
echo ==========================================
pause
