"""
Window Memory — saves and restores window positions per monitor configuration.
Runs as a system tray app. Auto-saves on monitor disconnect, auto-restores on reconnect.
Logs every window move/resize to the CLI in real time.
"""

import sys
import signal
import time
import threading
import ctypes
import winreg
import monitor_manager
import window_manager
import window_watcher
import storage
import tray

REGISTRY_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
REGISTRY_NAME = "WindowMemory"


def _register_autostart():
    exe_path = sys.executable if not getattr(sys, "frozen", False) else sys.executable
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, REGISTRY_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        print(f"[AUTOSTART] Registered: {exe_path}")
    except Exception as e:
        print(f"[AUTOSTART] Failed to register: {e}")


def _unregister_autostart():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, REGISTRY_NAME)
        print("[AUTOSTART] Removed from startup.")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[AUTOSTART] Failed to remove: {e}")

_last_sig: str = ""
_icon = None


def _notify(message: str):
    if _icon:
        _icon.notify(message, "Window Memory")


def save_layout():
    sig = monitor_manager.get_signature()
    snapshot = window_manager.capture()
    storage.save_snapshot(sig, snapshot)
    print(f"[SAVE]  Saved {len(snapshot)} windows:")
    for w in snapshot:
        title = w['title'].encode('ascii', errors='replace').decode('ascii')
        print(f"         {w['exe']:<25} {title!r:<35} state={w['state']} rect={w['rect']}")
    _notify(f"Saved {len(snapshot)} windows for this monitor layout.")


def restore_layout():
    sig = monitor_manager.get_signature()
    snapshot = storage.load_snapshot(sig)
    if not snapshot:
        print("[RESTORE] No saved layout for current monitor config.")
        _notify("No saved layout for the current monitor configuration.")
        return
    print(f"[RESTORE] Restoring {len(snapshot)} windows:")
    for w in snapshot:
        title = w['title'].encode('ascii', errors='replace').decode('ascii')
        print(f"          {w['exe']:<25} {title!r:<35} → rect={w['rect']}")
    count = window_manager.restore(snapshot)
    print(f"[RESTORE] Done — matched and moved {count}/{len(snapshot)} windows.")
    _notify(f"Restored {count} windows.")


def on_monitor_change():
    global _last_sig
    new_sig = monitor_manager.get_signature()

    if new_sig == _last_sig:
        return

    prev_sig = _last_sig
    _last_sig = new_sig

    print(f"[MONITOR] Config changed.")
    print(f"  prev → {prev_sig}")
    print(f"  new  → {new_sig}")

    if prev_sig:
        snapshot = window_manager.capture()
        storage.save_snapshot(prev_sig, snapshot)
        print(f"[MONITOR] Auto-saved {len(snapshot)} windows for previous config.")

    snapshot = storage.load_snapshot(new_sig)
    if snapshot:
        count = window_manager.restore(snapshot)
        print(f"[MONITOR] Auto-restored {count} windows for new config.")
        _notify(f"Monitor config changed — restored {count} windows.")
    else:
        print("[MONITOR] No saved layout for new config. Arrange windows and click Save Layout.")
        _notify("New monitor config detected. Arrange your windows and click Save Layout.")


def _is_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY) as key:
            winreg.QueryValueEx(key, REGISTRY_NAME)
            return True
    except FileNotFoundError:
        return False


def toggle_autostart():
    if _is_autostart_enabled():
        _unregister_autostart()
        _notify("Window Memory removed from startup.")
    else:
        _register_autostart()
        _notify("Window Memory will now start with Windows.")


def quit_app():
    if _icon:
        _icon.stop()
    sys.exit(0)


def main():
    global _icon, _last_sig

    _last_sig = monitor_manager.get_signature()
    print(f"[INIT]  Window Memory started.")
    print(f"[INIT]  Monitor signature: {_last_sig}")
    print(f"[INIT]  Watching for window moves...\n")

    # Monitor change listener (background thread)
    monitor_manager.start_listener(on_monitor_change)

    # Auto-register on first run (only when running as compiled exe)
    if getattr(sys, "frozen", False) and not _is_autostart_enabled():
        _register_autostart()

    # Tray icon (background thread — main thread is needed for the event hook message loop)
    _icon = tray.create_tray(
        on_save=save_layout,
        on_restore=restore_layout,
        on_toggle_autostart=toggle_autostart,
        on_quit=quit_app,
    )
    tray_thread = threading.Thread(target=_icon.run, daemon=True)
    tray_thread.start()

    # Install window move/resize/minimize hooks
    hooks, proc = window_watcher.start()

    # Ctrl+C handler — sets a flag, main loop checks it
    _quit = threading.Event()

    def _handle_sigint(sig, frame):
        print("\n[EXIT]  Ctrl+C received. Quitting...")
        _quit.set()

    signal.signal(signal.SIGINT, _handle_sigint)

    # PeekMessage loop — non-blocking so Python signals fire between ticks
    PM_REMOVE = 0x0001
    WM_QUIT   = 0x0012
    msg = ctypes.wintypes.MSG()
    while not _quit.is_set():
        if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, PM_REMOVE):
            if msg.message == WM_QUIT:
                break
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        else:
            time.sleep(0.05)  # yield to Python so Ctrl+C can fire


if __name__ == "__main__":
    main()
