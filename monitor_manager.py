import threading
import win32api
import win32gui
import win32con

WM_DISPLAYCHANGE = 0x007E
_CLASS_NAME = "WindowMemoryMonitorWatcher"


def get_signature() -> str:
    """Fingerprint the current monitor layout by position + size of each monitor."""
    monitors = win32api.EnumDisplayMonitors()
    parts = []
    for monitor in monitors:
        info = win32api.GetMonitorInfo(monitor[0])
        parts.append(str(info["Monitor"]))
    return "|".join(sorted(parts))


def start_listener(on_change: callable):
    """Spin up a background thread with a hidden message-only window to catch WM_DISPLAYCHANGE."""
    thread = threading.Thread(target=_message_loop, args=(on_change,), daemon=True)
    thread.start()


def _message_loop(on_change: callable):
    def wnd_proc(hwnd, msg, wparam, lparam):
        if msg == WM_DISPLAYCHANGE:
            # Small delay so Windows finishes reconfiguring monitors before we act
            threading.Timer(2.0, on_change).start()
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    wc = win32gui.WNDCLASS()
    wc.lpszClassName = _CLASS_NAME
    wc.lpfnWndProc = wnd_proc

    try:
        win32gui.RegisterClass(wc)
    except Exception:
        pass  # Already registered from a previous run in same process

    hwnd = win32gui.CreateWindow(
        _CLASS_NAME, "", 0,
        0, 0, 0, 0,
        win32con.HWND_MESSAGE,  # message-only window, invisible
        0, 0, None,
    )

    win32gui.PumpMessages()  # blocks — runs on its own thread
