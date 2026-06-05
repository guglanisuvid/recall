"""
Manual test — no second monitor needed.
1. Opens Notepad + Calculator (or use any open windows)
2. Captures positions
3. Prompts you to manually drag windows somewhere else
4. Restores them back
"""
import os
import time
import subprocess
import window_manager

# Open two test windows
subprocess.Popen("notepad")
subprocess.Popen("calc")
time.sleep(1)

print("Step 1: Capturing window positions...")
snapshot = window_manager.capture()
for w in snapshot[:5]:  # show first 5
    title = w['title'].encode('ascii', errors='replace').decode('ascii')
    print(f"  {title!r:40} rect={w['rect']}")

input("\nStep 2: MANUALLY DRAG some windows to different positions, then press Enter...")

print("\nStep 3: Restoring positions...")
count = window_manager.restore(snapshot)
print(f"Restored {count} windows. Check if they moved back.")
