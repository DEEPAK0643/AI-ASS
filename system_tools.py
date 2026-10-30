"""
JARVIS System Automation Tools
Handles local Windows controls, application launching, screen capture,
media/volume controls, and telemetry diagnostics.
"""

import os
import subprocess
import webbrowser
import datetime
import psutil
import pyautogui
import ctypes
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Common Windows App Path mappings
KNOWN_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "chrome",
    "edge": "msedge",
    "explorer": "explorer.exe",
    "files": "explorer.exe",
    "file explorer": "explorer.exe",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
    "spotify": "spotify",
    "code": "code",
    "vs code": "code",
    "paint": "mspaint.exe",
    "whatsapp": "whatsapp:",
    "whats app": "whatsapp:"
}

def get_system_telemetry() -> dict:
    """Returns current real-time system performance telemetry."""
    battery = psutil.sensors_battery()
    battery_info = {
        "percent": battery.percent if battery else 100,
        "plugged": battery.power_plugged if battery else True
    }
    
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": mem.percent,
        "ram_used_gb": round((mem.total - mem.available) / (1024**3), 2),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "battery": battery_info,
        "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    }

def open_whatsapp() -> str:
    """Opens WhatsApp desktop application or WhatsApp Web."""
    try:
        os.system("start whatsapp:")
        return "Opening WhatsApp."
    except Exception:
        webbrowser.open("https://web.whatsapp.com")
        return "Opening WhatsApp Web."

def launch_application(app_name: str) -> str:
    """Launches an application or program by name."""
    clean_name = app_name.strip().lower()
    
    if clean_name in ["whatsapp", "whats app"]:
        return open_whatsapp()

    target = KNOWN_APPS.get(clean_name, None)
    try:
        if target:
            if target.startswith("ms-") or target.endswith(":"):
                os.system(f"start {target}")
            else:
                subprocess.Popen(target, shell=True)
            return f"Opening {app_name}."
        else:
            subprocess.Popen(clean_name, shell=True)
            return f"Attempting to launch {app_name}."
    except Exception as e:
        return f"Unable to launch {app_name}: {str(e)}"

def search_web(query: str) -> str:
    """Searches Google for the given query."""
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching the web for '{query}'."

def open_youtube(query: str = "") -> str:
    """Opens YouTube or searches for a video."""
    if query:
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching YouTube for '{query}'."
    else:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."

def open_url(url: str) -> str:
    """Opens any specified website URL."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}."

def take_screenshot(filename: str = "") -> str:
    """Captures a screenshot of the primary display."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"screenshot_{timestamp}.png" if not filename else f"{filename}.png"
    file_path = SCREENSHOTS_DIR / name
    
    screenshot = pyautogui.screenshot()
    screenshot.save(str(file_path))
    return f"Screenshot saved successfully as {file_path.name}."

def adjust_volume(action: str) -> str:
    """Adjusts Windows system volume: 'up', 'down', or 'mute'."""
    action = action.lower().strip()
    if action in ["up", "increase", "louder"]:
        for _ in range(5):
            pyautogui.press("volumeup")
        return "Volume increased."
    elif action in ["down", "decrease", "softer", "lower"]:
        for _ in range(5):
            pyautogui.press("volumedown")
        return "Volume decreased."
    elif action in ["mute", "unmute", "toggle"]:
        pyautogui.press("volumemute")
        return "Audio toggled."
    else:
        return f"Unknown volume action '{action}'."

def control_media(action: str) -> str:
    """Controls media playback: 'play_pause', 'next', 'previous'."""
    action = action.lower().strip()
    if action in ["play", "pause", "play_pause", "toggle"]:
        pyautogui.press("playpause")
        return "Media playback toggled."
    elif action in ["next", "skip"]:
        pyautogui.press("nexttrack")
        return "Skipped to next track."
    elif action in ["prev", "previous", "back"]:
        pyautogui.press("prevtrack")
        return "Returned to previous track."
    else:
        return f"Unknown media action '{action}'."

def lock_workstation() -> str:
    """Locks the Windows computer."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked."
    except Exception as e:
        return f"Could not lock workstation: {str(e)}"

def get_current_datetime() -> str:
    """Returns the current date and time."""
    now = datetime.datetime.now()
    return now.strftime("Current time is %I:%M %p on %A, %B %d, %Y.")

def list_running_processes(limit: int = 6) -> list:
    """Returns top resource consuming processes."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            if info['name'] and info['cpu_percent'] is not None:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda x: (x['cpu_percent'] or 0, x['memory_percent'] or 0), reverse=True)
    return processes[:limit]
