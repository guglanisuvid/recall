"""Step 1: Run this, then drag your windows around, then run test_restore.py"""
import json
import window_manager

snapshot = window_manager.capture()

with open("snapshot_test.json", "w") as f:
    json.dump(snapshot, f, indent=2)

print(f"Captured {len(snapshot)} windows:")
for w in snapshot[:8]:
    title = w['title'].encode('ascii', errors='replace').decode('ascii')
    print(f"  {title!r:40} rect={w['rect']}")

print("\nNow drag some windows to different positions, then run test_restore.py")
