#!/bin/bash
echo "=========================================="
echo "  Vacation Deal Finder - Linux Build"
echo "=========================================="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed."
    exit 1
fi

# Install PyInstaller
echo "[1/5] Installing PyInstaller..."
pip install pyinstaller --quiet

# Install project dependencies
echo "[2/5] Installing project dependencies..."
pip install -r requirements.txt --quiet

# Clean previous builds
echo "[3/5] Cleaning previous builds..."
rm -rf build dist

# Build executable
echo "[4/5] Building executable (this may take a few minutes)..."
pyinstaller vacation_finder.spec --clean

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Build failed!"
    exit 1
fi

echo
echo "[5/5] Creating distribution package..."

# Create distribution folder
rm -rf VacationDealFinder_Package
mkdir -p VacationDealFinder_Package

# Copy executable
# Copy executable and dependencies (onedir mode)
cp -r dist/VacationDealFinder/* VacationDealFinder_Package/

# Copy README
cp USER_README.md VacationDealFinder_Package/README.md

# Copy .env.example
cp .env.example VacationDealFinder_Package/.env.example

echo
echo "=========================================="
echo "  BUILD SUCCESSFUL!"
echo "=========================================="
echo
echo "  Package:    VacationDealFinder_Package/"
echo "  Executable: VacationDealFinder_Package/VacationDealFinder"
echo
echo "  You can now test the executable:"
echo "  ./VacationDealFinder_Package/VacationDealFinder"
echo "=========================================="
