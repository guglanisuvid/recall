"""
Simulates a WM_DISPLAYCHANGE event to test the auto-save/restore flow
without a real monitor connect/disconnect.
"""
import time
import win32api
import win32con
import win32gui
import monitor_manager
import storage

WM_DISPLAYCHANGE = 0x007E

def find_watcher_hwnd():
    result = []
    def callback(hwnd, _):
        if win32gui.GetClassName(hwnd) == "WindowMemoryMonitorWatcher":
            result.append(hwnd)
    win32gui.EnumWindows(callback, None)
    return result[0] if result else None

if __name__ == "__main__":
    sig = monitor_manager.get_signature()
    print(f"Current monitor signature: {sig}")
    print(f"Saved layouts: {list(storage.load().keys())}")

    hwnd = find_watcher_hwnd()
    if hwnd:
        print(f"Found watcher window: {hwnd}")
        win32api.PostMessage(hwnd, WM_DISPLAYCHANGE, 32, 0)
        print("WM_DISPLAYCHANGE sent.")
    else:
        print("Watcher window not found — make sure main.py is running first.")
