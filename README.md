# Window Memory

> Because Windows keeps forgetting where you put your stuff.

---

## The Problem Nobody Talks About (But Everyone Feels)

You've got a setup. Chrome on the left, your IDE on the right, terminal in the corner, calculator somewhere sensible. It took you 30 seconds to arrange. You're in the zone.

Then you unplug your monitor.

Windows panics. Every window collapses onto your laptop screen in a pile of chaos. You reconnect the monitor. Windows shrugs. Nothing moves back. You spend the next 3 minutes dragging everything back to where it was — for the 400th time this year.

**macOS has solved this since 2011.** Unplug a Mac from its monitor, use it standalone, plug back in — everything snaps back to exactly where it was. No clicks. No dragging. It just works.

Windows? Still nothing. After 30 years of development.

---

## Why Hasn't Microsoft Fixed This?

Genuinely unclear. The APIs to do it have existed for decades:

- `WM_DISPLAYCHANGE` — Windows fires this event every time monitors change
- `GetWindowRect` / `SetWindowPos` — read and set exact window positions
- `GetWindowPlacement` / `SetWindowPlacement` — handle maximized state

Everything needed to replicate macOS behavior has been in the Win32 API since Windows 95. Microsoft just never wired it together into a product feature.

Third-party tools exist — DisplayFusion does it for $30, and costs more than most people want to pay for something that should ship in the OS. The free alternatives are either abandoned or clunky.

So this is that, but free, lightweight, and open source.

---

## What Window Memory Does

- Runs silently in your system tray — no windows, no UI, just a small icon
- Watches for monitor connect/disconnect events in real time
- **Auto-saves** your window layout when a monitor is disconnected
- **Auto-restores** your window layout when that monitor configuration comes back
- Handles snapped windows, maximized windows, and normal windows correctly
- Remembers multiple monitor configurations independently

---

## How It Works (The Technical Bit)

```
Windows fires WM_DISPLAYCHANGE
       ↓
App detects monitor config changed
       ↓
Saves layout for old config (GetWindowRect per window)
       ↓
Looks up saved layout for new config
       ↓
Restores each window (SetWindowPos for normal, SetWindowPlacement for maximized)
       ↓
You didn't have to do anything
```

**Window matching** uses `(exe name, window class)` as the primary key — so Chrome stays Chrome even when your tab title changes. Title matching is a fallback.

**Snapped windows** are a special case. Windows internally stores the pre-snap position in `GetWindowPlacement`, which means naive placement restore sends your snapped windows back to wherever they were *before* snapping — completely wrong. This app uses `GetWindowRect` (the actual screen coordinates) for normal windows, and only uses `SetWindowPlacement` for maximized windows where it's actually needed.

**Monitor fingerprinting** uses the set of monitor rectangles as a signature. If you have a 1080p monitor on the left and a 1440p monitor on the right, that's a unique config. Unplug the 1440p and reconnect it — the signature matches and your layout comes back.

---

## Getting Started

### Option 1 — Just Download the .exe (Easiest)

1. Go to the [Releases](../../releases) page
2. Download `WindowMemory.exe`
3. Double-click it

That's it. No Python. No install. No setup. The app adds itself to Windows startup automatically on first run so you never have to think about it again. Look for the icon in your system tray (bottom-right near the clock — you may need to click the `^` arrow to find it).

---

### Option 2 — Run from Source

**Requirements:** Python 3.11+, Windows 10/11, Google Chrome (for the best experience)

```bash
# Clone the repo
git clone https://github.com/yourusername/window-memory.git
cd window-memory

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

**Build your own exe:**

```bash
build.bat
```

The exe appears in `dist/WindowMemory.exe`. No Python required on the target machine.

---

## Usage

Once running, the app lives in your system tray. Right-click the icon for the menu:

| Option | What It Does |
|---|---|
| **Save Layout** | Snapshot all window positions for your current monitor setup |
| **Restore Layout** | Move all windows back to the last saved positions |
| **Toggle Auto-start** | Enable or disable launching at Windows startup |
| **Quit** | Exit the app |

**Auto-save / Auto-restore** happens automatically on monitor change — you don't need to use the menu unless you want manual control.

**First-time setup:**
1. Connect your monitor(s)
2. Arrange your windows exactly how you want them
3. Click **Save Layout** once
4. From now on, layouts restore automatically

---

## Running in the CLI (Development)

```bash
python main.py
```

You'll see live logs for every window event:

```
[INIT]  Window Memory started.
[INIT]  Monitor signature: (0, 0, 1920, 1080)
[INIT]  Watching for window moves...

[10:32:14] MOVED     chrome.exe             'GitHub - Google Chrome'    rect=[0, 0, 960, 1080]
[10:32:19] MAXIMIZE  windsurf.exe           'project - Windsurf'        rect=[-7, -7, 1927, 1087]
[10:32:25] MINIMIZE  calculator.exe         'Calculator'                rect=[914, 138, 1248, 678]
[10:32:30] RESTORE   calculator.exe         'Calculator'                rect=[914, 138, 1248, 678]

[SAVE]  Saved 5 windows:
         chrome.exe        'GitHub - Google Chrome'    normal   rect=[0, 0, 960, 1080]
         windsurf.exe      'project - Windsurf'        maximized rect=[-7, -7, 1927, 1087]
         ...

[RESTORE] Done — matched and moved 5/5 windows.
  [OK] chrome.exe    'GitHub - Google Chrome'  -> [0, 0, 960, 1080]
  [OK] windsurf.exe  'project - Windsurf'      -> [-7, -7, 1927, 1087]
```

Press `Ctrl+C` to quit.

---

## Project Structure

```
window-memory/
├── main.py              # Entry point — wires everything together
├── window_manager.py    # Capture and restore window positions
├── monitor_manager.py   # WM_DISPLAYCHANGE listener
├── window_watcher.py    # Real-time move/minimize/maximize event hook
├── storage.py           # JSON persistence (~/.window_memory.json)
├── tray.py              # System tray icon and menu
├── requirements.txt     # Python dependencies
├── build.bat            # One-click PyInstaller build
└── test_auto.py         # Automated save/restore test
```

---

## Known Limitations

- **Windows only** — by design. macOS doesn't have this problem.
- **Chrome browser** works best. Firefox and some Electron apps occasionally resist being moved by external processes.
- **Windows with changing titles** (like a browser with many tabs) are matched by exe + class. If two windows from the same app are open, the first match wins.
- **Minimized windows** are skipped during save/restore — restore them manually first.

---

## Why Build This?

This started as a "what would I build in a weekend" thought experiment. The gap was obvious: macOS has had this for over a decade, Windows still doesn't, and the best existing solution costs $30.

Built in Python because it's fast to iterate, `pywin32` gives full access to the Win32 API, and PyInstaller packages it into a zero-dependency exe. The entire core logic — monitor detection, window capture, restore — is under 150 lines of Python.

---

## License

MIT — do whatever you want with it.
