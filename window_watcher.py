import ctypes
import ctypes.wintypes
import win32gui
import win32process
import os
from datetime import datetime

EVENT_SYSTEM_MOVESIZEEND    = 0x000B
EVENT_SYSTEM_MINIMIZESTART  = 0x0016
EVENT_SYSTEM_MINIMIZEEND    = 0x0017
WINEVENT_OUTOFCONTEXT       = 0x0000

SW_SHOWMAXIMIZED = 3

WinEventProc = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)

_EVENT_LABELS = {
    EVENT_SYSTEM_MOVESIZEEND:   "MOVED   ",
    EVENT_SYSTEM_MINIMIZESTART: "MINIMIZE",
    EVENT_SYSTEM_MINIMIZEEND:   "RESTORE ",
}


def _get_exe(hwnd: int) -> str:
    try:
        import win32api, win32con
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False, pid,
        )
        path = win32process.GetModuleFileNameEx(handle, 0)
        win32api.CloseHandle(handle)
        return os.path.basename(path)
    except Exception:
        return "unknown"


def _make_callback():
    def callback(hook, event, hwnd, id_object, id_child, thread, time_ms):
        if not hwnd:
            return
        try:
            title  = win32gui.GetWindowText(hwnd) or "<no title>"
            rect   = win32gui.GetWindowRect(hwnd)
            exe    = _get_exe(hwnd)
            label  = _EVENT_LABELS.get(event, "EVENT   ")
            ts     = datetime.now().strftime("%H:%M:%S")

            # Detect maximized state on move/resize events
            if event == EVENT_SYSTEM_MOVESIZEEND:
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == SW_SHOWMAXIMIZED:
                    label = "MAXIMIZE"

            print(
                f"[{ts}] {label}  "
                f"{exe:<22} "
                f"{title!r:<40} "
                f"rect={list(rect)}"
            )
        except Exception:
            pass
    return callback


def start() -> tuple:
    cb   = _make_callback()
    proc = WinEventProc(cb)

    # Hook all three events with a single proc
    hooks = []
    for event_id in (
        EVENT_SYSTEM_MOVESIZEEND,
        EVENT_SYSTEM_MINIMIZESTART,
        EVENT_SYSTEM_MINIMIZEEND,
    ):
        h = ctypes.windll.user32.SetWinEventHook(
            event_id, event_id,
            0, proc,
            0, 0,
            WINEVENT_OUTOFCONTEXT,
        )
        hooks.append(h)

    return hooks, proc  # keep proc alive — GC will break the hook otherwise
