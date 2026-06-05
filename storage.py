import json
import os

STORAGE_FILE = os.path.join(os.path.expanduser("~"), ".window_memory.json")


def load() -> dict:
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r") as f:
        return json.load(f)


def save(data: dict):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_snapshot(monitor_sig: str, snapshot: list):
    data = load()
    data[monitor_sig] = snapshot
    save(data)


def load_snapshot(monitor_sig: str) -> list | None:
    data = load()
    return data.get(monitor_sig)
