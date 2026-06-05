"""
Automated save/restore test — no tray interaction needed.
1. Captures current layout
2. Moves Calculator to a new position programmatically
3. Restores layout
4. Verifies Calculator is back
"""
import time
import win32gui
import win32con
import window_manager


def find_calculator():
    result = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and "Calculator" in win32gui.GetWindowText(hwnd):
            result.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return result[0] if result else None


hwnd = find_calculator()
if not hwnd:
    print("Calculator not open — please open Calculator first.")
    exit(1)

before = win32gui.GetWindowRect(hwnd)
print(f"[1] Calculator position before save: {list(before)}")

snapshot = window_manager.capture()
print(f"[2] Saved positions:")
for w in snapshot:
    t = w['title'].encode('ascii', errors='replace').decode('ascii')
    print(f"     {w['exe']:<30} {t!r:<40} {w['state']} {w['rect']}")

# Move Calculator to a clearly different position
win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 100, 100, 400, 500,
                      win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
time.sleep(0.3)
moved = win32gui.GetWindowRect(hwnd)
print(f"\n[3] Calculator moved to: {list(moved)}")

# Restore
print("\n[4] Restoring layout...")
count = window_manager.restore(snapshot)

time.sleep(0.3)
print(f"\n[5] Actual positions after restore:")
fails = []
for w in snapshot:
    t = w['title'].encode('ascii', errors='replace').decode('ascii')
    # find the hwnd and check actual position
    result = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h) == w['title']:
            result.append(h)
    win32gui.EnumWindows(cb, None)
    if result:
        actual = list(win32gui.GetWindowRect(result[0]))
        match = "OK  " if actual == w['rect'] else "FAIL"
        print(f"  [{match}] {w['exe']:<30} saved={w['rect']} actual={actual}")
        if match == "FAIL":
            fails.append(w['title'])

print(f"\n{'ALL PASS' if not fails else 'FAILED: ' + str(fails)}")
