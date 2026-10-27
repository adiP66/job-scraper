#!/usr/bin/env python3
"""
revert_to_aditya.py — Instantly restores the project back to Aditya Parkhe's exact state.
"""
import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, "aditya_backup")

FILES_TO_RESTORE = [
    "run_scrape_and_fit.py",
    "track_applications.py",
    "applied_jobs.csv",
    "master_applied_jobs.csv",
    "README.md",
    "HOW_TO_USE.md"
]

def revert():
    if not os.path.exists(BACKUP_DIR):
        print(f"❌ Error: Backup directory '{BACKUP_DIR}' not found!")
        sys.exit(1)
    
    for f in FILES_TO_RESTORE:
        src = os.path.join(BACKUP_DIR, f)
        dst = os.path.join(BASE_DIR, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ Restored: {f}")
        else:
            print(f"⚠️ Warning: {f} not found in backup.")
    
    print("\n🎉 Revert complete! Project restored to Aditya Parkhe's exact state.")

if __name__ == "__main__":
    revert()
