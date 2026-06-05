"""Step 2: Run this after dragging windows — they should snap back."""
import json
import window_manager

with open("snapshot_test.json") as f:
    snapshot = json.load(f)

count = window_manager.restore(snapshot)
print(f"Restored {count} windows.")
