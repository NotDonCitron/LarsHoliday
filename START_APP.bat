@echo off
echo ==========================================
echo   Starting Vacation Deal Finder...
echo ==========================================
echo.

if not exist venv (
    echo [!] Error: Virtual environment not found.
    echo Please run INSTALL_WINDOWS.bat first!
    echo.
    pause
    exit /b
)

:: Run the GUI app
venv\Scripts\python.exe gui_app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] The application closed with an error.
    echo.
    pause
)
