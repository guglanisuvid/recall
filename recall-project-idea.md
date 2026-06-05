# Recall — Window Position Memory for Windows

> The thing macOS has done since 2011 that Windows still hasn't figured out.

---

## The Idea

Every developer, designer, or office worker with a laptop and an external monitor lives this pain daily. You unplug your laptop, Windows throws every window into a pile on the small screen. You plug back in. Windows does nothing. You drag everything back. Repeat forever.

macOS solved this a decade ago. Windows never bothered. The APIs to fix it have existed since Windows 95. Nobody built a good free tool. So this is that.

**Recall** is a lightweight system tray app that remembers your window layout per monitor configuration and restores it automatically when monitors change.

---

## The Problem in Numbers

- Average time to rearrange windows after reconnecting a monitor: **2–4 minutes**
- Times a developer does this per day: **2–5** (morning dock, coffee shop, meeting room, home)
- Working days per year: **~230**
- Time lost per year: **~15–45 hours**

That's a full work week, every year, just dragging windows around.

---

## Why Windows Doesn't Fix This

The Win32 API has had everything needed since the 90s:

| API | What it does |
|---|---|
| `WM_DISPLAYCHANGE` | Fires when monitors connect/disconnect |
| `EnumWindows` | List all open windows |
| `GetWindowRect` | Get exact position of a window |
| `SetWindowPos` | Move a window to an exact position |
| `GetWindowPlacement` | Get maximized/normal/minimized state |
| `SetWindowPlacement` | Restore window state |
| `SetWinEventHook` | Hook into window move/resize events |

Microsoft has all the tools. They just never shipped the feature. The closest they came was a vague "improve multi-monitor support" item in Windows 11 — which did almost nothing.

Third-party solutions: DisplayFusion ($30, bloated), WindowsLayoutSnapshot (abandoned 2015), various AutoHotkey scripts (fragile, no UI). Nothing clean, free, and modern.

---

## The Insight That Makes It Work

The naive implementation fails on one critical edge case: **snapped windows**.

When you snap a window to the left half of your screen, Windows internally stores two positions:
- The **snapped** position (what you see) — from `GetWindowRect`
- The **pre-snap** position (where it was before snapping) — stored in `GetWindowPlacement.rcNormalPosition`

If you restore using `SetWindowPlacement`, Windows restores to the pre-snap position — completely wrong. The window flies to wherever it was before you snapped it.

The fix: use `GetWindowRect` to capture the actual screen position, and use `SetWindowPos` to restore it for normal windows. Only use `SetWindowPlacement` for maximized windows (where it's needed to restore the maximized state correctly).

This is the bug that every naive implementation gets wrong. Getting it right is what makes the restore feel seamless.

---

## Monitor Fingerprinting

Each unique monitor configuration is identified by the set of monitor rectangles:

```python
monitors = win32api.EnumDisplayMonitors()
sig_parts = []
for monitor in monitors:
    info = win32api.GetMonitorInfo(monitor[0])
    sig_parts.append(str(info["Monitor"]))
signature = "|".join(sorted(sig_parts))
```

Example signatures:
- Laptop only: `(0, 0, 1536, 864)`
- Laptop + external 1080p left: `(-1920, 0, 0, 1080)|(0, 0, 1536, 864)`
- Laptop + external 1080p right: `(0, 0, 1536, 864)|(1536, 0, 3456, 1080)`

Each signature maps to its own saved layout. You can have 10 different monitor setups and each one has its own layout independently.

---

## Window Matching Strategy

When restoring, you need to match saved window entries to currently open windows. Title alone is fragile — Chrome's title changes with every tab, VS Code's title changes with every file.

**Primary key:** `(exe_name, window_class)` — e.g. `(chrome.exe, Chrome_WidgetWin_1)`
**Fallback:** window title

This means Chrome stays Chrome regardless of which tab is active. VS Code stays VS Code regardless of which project is open. The match is stable across sessions.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Fast to iterate, excellent Win32 bindings |
| Windows API | `pywin32` | Full access to Win32 — EnumWindows, SetWindowPos, WM_DISPLAYCHANGE, SetWinEventHook |
| System tray | `pystray` | Clean cross-version tray icon with menu |
| Icon generation | `Pillow` | Generate tray icon in code — no asset files needed |
| Packaging | `PyInstaller` | Single .exe, no Python install required |
| Storage | JSON (`~/.window_memory.json`) | Zero dependencies, human-readable, easy to inspect |
| Auto-start | Windows Registry (`HKCU\...\Run`) | Standard approach, same as Spotify/Discord/Steam |

---

## Architecture

```
main.py
  ├── monitor_manager.py     Hidden message-only window listens for WM_DISPLAYCHANGE
  │     └── on_change()      Auto-save old layout, auto-restore new layout
  ├── window_watcher.py      SetWinEventHook on EVENT_SYSTEM_MOVESIZEEND/MINIMIZE/RESTORE
  │     └── callback()       Logs every window event to CLI in real time  
  ├── window_manager.py      capture() → GetWindowRect per window
  │     └── restore()        SetWindowPos (normal) / SetWindowPlacement (maximized)
  ├── storage.py             JSON read/write keyed by monitor signature
  └── tray.py                pystray icon + menu (Save, Restore, Toggle Autostart, Quit)
```

**Threading model:**
- Main thread runs `PeekMessage` loop — required for `SetWinEventHook` to fire
- Tray icon runs on a background daemon thread
- Monitor listener runs on a background daemon thread

---

## Step-by-Step Build Plan

### Day 1 — Core pipeline

**Hour 1-2: Setup + basic window capture**
```bash
mkdir recall && cd recall
pip install pywin32 pystray Pillow pyinstaller
```
```python
# window_manager.py — prove you can read window positions
import win32gui
def capture():
    windows = []
    win32gui.EnumWindows(lambda hwnd, _: windows.append({
        "title": win32gui.GetWindowText(hwnd),
        "rect": list(win32gui.GetWindowRect(hwnd))
    }), None)
    return windows
```

**Hour 3-4: Restore + verify it works**
```python
def restore(snapshot):
    # SetWindowPos each window back to saved rect
    # Test: capture, move Calculator manually, restore, verify position
```

**Hour 5-6: Monitor change detection**
```python
# monitor_manager.py — hidden window + WM_DISPLAYCHANGE
# Fires callback when monitors connect/disconnect
```

**Hour 7-8: System tray + storage**
```python
# tray.py — pystray icon with Save/Restore/Quit menu
# storage.py — JSON keyed by monitor signature
```

### Day 2 — Polish + ship

**Hour 1-2: Fix the snapped window bug**
- Switch normal windows from `SetWindowPlacement` to `SetWindowPos`
- Test with snapped Chrome, snapped terminal, verify positions are exact

**Hour 3-4: Real-time event logging**
```python
# window_watcher.py — SetWinEventHook for live MOVED/MAXIMIZE/MINIMIZE logs
```

**Hour 5-6: Auto-start on boot**
```python
# Write to HKCU\Software\Microsoft\Windows\CurrentVersion\Run
# Only when running as compiled exe (sys.frozen)
# Toggle from tray menu
```

**Hour 7-8: Build + test**
```bash
pyinstaller --onefile --windowed --name "Recall" main.py
# Double-click Recall.exe, verify tray appears, verify auto-start registered
```

---

## Features

### Shipped (v1.0)
- [x] Auto-save layout on monitor disconnect
- [x] Auto-restore layout on monitor reconnect
- [x] Manual save/restore via tray menu
- [x] Correct snapped window restore (the hard part)
- [x] Correct maximized window restore
- [x] Multi-monitor configuration fingerprinting
- [x] Smart window matching by exe + class (not just title)
- [x] Auto-start on Windows boot (registry)
- [x] Toggle auto-start from tray
- [x] Real-time move/maximize/minimize event logging in CLI
- [x] Zero-dependency .exe (PyInstaller)
- [x] Excludes system windows (explorer tray, shell UI)

### Potential V2
- [ ] Per-app ignore list (skip certain apps from save/restore)
- [ ] Named layout profiles ("work", "presentation", "home")
- [ ] Hotkey to save/restore without opening tray
- [ ] Restore only specific windows (not all)
- [ ] Taskbar position included in layout
- [ ] Tray icon shows current profile name

---

## Known Edge Cases

| Situation | Behavior |
|---|---|
| Two Chrome windows open | First match wins (by exe+class) |
| Window title changes between save and restore | Falls back to exe+class match — usually fine |
| App was closed between save and restore | Skipped — `[NO MATCH]` logged |
| Minimized windows | Skipped during save — restore them first |
| DPI scaling differences between monitors | Works correctly — uses screen coordinates throughout |
| UWP apps (Calculator, Settings) | Handled via `ApplicationFrameHost.exe` as the exe |

---

## Monetization Options (If You Wanted To)

| Model | Approach |
|---|---|
| Free forever | Open source, build reputation |
| Freemium | Free for 1 monitor config, paid for multiple |
| One-time purchase | $5–10, simple Gumroad or Paddle |
| Sponsorware | Free after X GitHub sponsors |

Realistically: this is the kind of tool that builds an audience. Ship it free, get stars, get known.

---

## Competitive Landscape

| Tool | Price | Issues |
|---|---|---|
| DisplayFusion | $30 | Expensive, bloated with features |
| WindowsLayoutSnapshot | Free | Abandoned ~2015, no installer |
| AutoHotkey scripts | Free | Fragile, requires AHK installed, no UI |
| Microsoft PowerToys | Free | Has FancyZones but no monitor-change restore |
| **Recall** | Free | Lightweight, modern, just works |

---

## Resources Used

- [Win32 Window Management docs](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-management)
- [SetWinEventHook reference](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook)
- [pywin32 documentation](https://mhammond.github.io/pywin32/)
- [pystray documentation](https://pystray.readthedocs.io/)
- [PyInstaller docs](https://pyinstaller.org/en/stable/)

---

## GitHub

[https://github.com/guglanisuvid/recall](https://github.com/guglanisuvid/recall)

---

*Built: June 2026 | Time taken: Under 1 hour | Time Microsoft had: 30 years*
