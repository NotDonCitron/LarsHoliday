@echo off
echo ==========================================
echo   Vacation Deal Finder - Windows EXE Build
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

:: Install PyInstaller
echo [1/5] Installing PyInstaller...
pip install pyinstaller --quiet

:: Install project dependencies
echo [2/5] Installing project dependencies...
pip install -r requirements.txt --quiet

:: Clean previous builds
echo [3/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: Build EXE
echo [4/5] Building executable (this may take a few minutes)...
pyinstaller vacation_finder.spec --clean

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Build failed!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [5/5] Creating distribution package...

:: Create distribution folder
if exist "VacationDealFinder_Package" rmdir /s /q "VacationDealFinder_Package"
mkdir "VacationDealFinder_Package"

:: Copy EXE
copy "dist\VacationDealFinder.exe" "VacationDealFinder_Package\" >nul

:: Copy README
copy "USER_README.md" "VacationDealFinder_Package\README.md" >nul

:: Copy .env.example
copy ".env.example" "VacationDealFinder_Package\.env.example" >nul

echo.
echo ==========================================
echo   BUILD SUCCESSFUL!
echo ==========================================
echo.
echo   EXE location: dist\VacationDealFinder.exe
echo   Package:      VacationDealFinder_Package\
echo.
echo   You can now zip 'VacationDealFinder_Package' folder
echo   and send it to your friend!
echo ==========================================
echo.
pause
