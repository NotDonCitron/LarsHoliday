import os
import shutil

SOURCE_DIR = "."
DEST_DIR = "VacationDealFinder_Source"

FILES_TO_COPY = [
    "main.py",
    "gui_app.py",
    "holland_agent.py",
    "airbnb_scraper.py",
    "airbnb_scraper_enhanced.py",
    "booking_scraper.py",
    "patchright_airbnb_scraper.py", # Required by enhanced scraper
    "rate_limit_bypass.py",
    "favorites_manager.py",
    "report_generator.py",
    "html_report_generator.py",
    "scraper_health.py",
    "weather_integration.py",
    "deal_ranker.py", # Forgot this one!
    "requirements.txt",
    "INSTALL_WINDOWS.bat",
    "START_APP.bat",
    ".env.example",
    "README_FRIEND.md",
    "vacation_finder.spec",
    "build_windows.bat"
]

def main():
    if os.path.exists(DEST_DIR):
        print(f"Cleaning existing release folder: {DEST_DIR}")
        shutil.rmtree(DEST_DIR)
    
    os.makedirs(DEST_DIR)
    print(f"Created release folder: {DEST_DIR}")

    for file_name in FILES_TO_COPY:
        src = os.path.join(SOURCE_DIR, file_name)
        dst = os.path.join(DEST_DIR, file_name)
        
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied: {file_name}")
        else:
            print(f"WARNING: File not found: {file_name}")

    # Rename README for friend
    if os.path.exists(os.path.join(DEST_DIR, "README_FRIEND.md")):
        shutil.move(
            os.path.join(DEST_DIR, "README_FRIEND.md"),
            os.path.join(DEST_DIR, "README.txt") # Rename to .txt so it opens easily on Windows
        )
        print("Renamed README_FRIEND.md to README.txt")

    print(f"\nSUCCESS! Package ready in '{DEST_DIR}'")
    print("You can now zip this folder and send it to your friend.")

if __name__ == "__main__":
    main()
