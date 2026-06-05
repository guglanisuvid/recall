import os
import win32gui
import win32con
import win32process
import win32api

SW_SHOWNORMAL    = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3

IGNORED_TITLES  = {"", "Program Manager", "Windows Input Experience"}
IGNORED_CLASSES = {"Shell_TrayWnd", "DV2ControlHost", "MsgrIMEWindowClass"}
IGNORED_EXES    = {"explorer.exe", "shellexperiencehost.exe", "startmenuexperiencehost.exe", "searchhost.exe"}


def _get_exe(hwnd: int) -> str:
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False, pid,
        )
        path = win32process.GetModuleFileNameEx(handle, 0)
        win32api.CloseHandle(handle)
        return os.path.basename(path).lower()
    except Exception:
        return ""


def _is_valid_window(hwnd: int) -> bool:
    if not win32gui.IsWindowVisible(hwnd):
        return False
    title = win32gui.GetWindowText(hwnd)
    if title in IGNORED_TITLES:
        return False
    cls = win32gui.GetClassName(hwnd)
    if cls in IGNORED_CLASSES:
        return False
    exe = _get_exe(hwnd).lower()
    if exe in IGNORED_EXES:
        return False
    placement = win32gui.GetWindowPlacement(hwnd)
    if placement[1] == SW_SHOWMINIMIZED:
        return False
    return True


def _serialize_placement(p) -> dict:
    return {
        "flags":       p[0],
        "show_cmd":    p[1],
        "min_pos":     list(p[2]),
        "max_pos":     list(p[3]),
        "normal_rect": list(p[4]),
    }


def _deserialize_placement(d: dict) -> tuple:
    return (
        d["flags"],
        d["show_cmd"],
        tuple(d["min_pos"]),
        tuple(d["max_pos"]),
        tuple(d["normal_rect"]),
    )


def capture() -> list[dict]:
    snapshot = []

    def callback(hwnd, _):
        if not _is_valid_window(hwnd):
            return
        placement = win32gui.GetWindowPlacement(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        state = {
            SW_SHOWNORMAL:    "normal",
            SW_SHOWMAXIMIZED: "maximized",
        }.get(placement[1], "normal")

        snapshot.append({
            "title":     win32gui.GetWindowText(hwnd),
            "cls":       win32gui.GetClassName(hwnd),
            "exe":       _get_exe(hwnd),
            "state":     state,
            "placement": _serialize_placement(placement),
            "rect":      list(rect),
        })

    win32gui.EnumWindows(callback, None)
    return snapshot


def restore(snapshot: list[dict]) -> int:
    # Build lookup: primary key = (exe, cls), secondary = title
    current_by_exe_cls: dict[tuple, int] = {}
    current_by_title:   dict[str, int]   = {}

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        cls   = win32gui.GetClassName(hwnd)
        exe   = _get_exe(hwnd)
        key   = (exe, cls)
        if key not in current_by_exe_cls:
            current_by_exe_cls[key] = hwnd
        if title and title not in current_by_title:
            current_by_title[title] = hwnd

    win32gui.EnumWindows(callback, None)

    restored = 0
    for entry in snapshot:
        key  = (entry.get("exe", ""), entry["cls"])
        hwnd = current_by_exe_cls.get(key) or current_by_title.get(entry["title"])
        if not hwnd:
            title = entry['title'].encode('ascii', errors='replace').decode('ascii')
            print(f"  [NO MATCH] {entry.get('exe',''):<25} {title!r}")
            continue

        title = entry['title'].encode('ascii', errors='replace').decode('ascii')
        try:
            if entry["state"] == "maximized":
                # SetWindowPlacement correctly restores maximized state
                win32gui.SetWindowPlacement(hwnd, _deserialize_placement(entry["placement"]))
            else:
                # SetWindowPos restores the exact pixel position (works for snapped windows too)
                left, top, right, bottom = entry["rect"]
                win32gui.ShowWindow(hwnd, SW_SHOWNORMAL)  # un-maximize if needed first
                win32gui.SetWindowPos(
                    hwnd, win32con.HWND_TOP,
                    left, top, right - left, bottom - top,
                    win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE,
                )

            actual = win32gui.GetWindowRect(hwnd)
            print(f"  [OK] {entry.get('exe',''):<25} {title!r:<35} -> {list(actual)}")
            restored += 1
        except Exception as e:
            print(f"  [ERR] {entry.get('exe',''):<25} {title!r}: {e}")

    return restored
