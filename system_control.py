import os
import pyautogui
import re
from voice import speak
import psutil
import time
import requests
try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS
from io import BytesIO
from PIL import Image
import subprocess
from pycaw.pycaw import AudioUtilities
from gemini_client import client as gemini_client

# Local session tracking (replaces legacy memory.py)
current_active_app = None
last_found_file_path = None

def set_app(app_name):
    global current_active_app
    current_active_app = app_name

def get_app():
    return current_active_app

def set_last_file(file_path):
    global last_found_file_path
    last_found_file_path = file_path

def get_last_file():
    return last_found_file_path

# ---------------------------------------------
# HARDWARE & SYSTEM AUTOMATION
# ---------------------------------------------
def _get_volume_endpoint():
    """Retrieves the default Windows CoreAudio endpoint volume interface."""
    speakers = AudioUtilities.GetSpeakers()
    if speakers is None:
        raise RuntimeError("No active audio output device found.")
    return speakers.EndpointVolume

def get_volume() -> str:
    """
    Reads and returns the current system master volume percentage and mute status.
    """
    try:
        endpoint = _get_volume_endpoint()
        percent = round(endpoint.GetMasterVolumeLevelScalar() * 100)
        is_muted = bool(endpoint.GetMute())
        if is_muted:
            return f"Current system volume is {percent} percent and muted."
        return f"Current system volume is {percent} percent."
    except Exception as e:
        print(f"[IRIS Error] Failed to get volume: {e}")
        return "I could not retrieve the current system volume."

def set_volume(command: str):
    """
    Adjusts system master volume using Windows CoreAudio.
    Supports volume up/down, setting exact percentages, and explicit mute/unmute.
    """
    try:
        command = command.lower()
        endpoint = _get_volume_endpoint()

        # Handle explicit mute/unmute (check 'unmute' before 'mute')
        if "unmute" in command:
            endpoint.SetMute(0, None)
            speak("Volume unmuted")
            return
        elif "mute" in command:
            endpoint.SetMute(1, None)
            speak("Volume muted")
            return

        current_scalar = endpoint.GetMasterVolumeLevelScalar()
        current_percent = round(current_scalar * 100)
        numbers = re.findall(r'\d+', command)

        if numbers:
            value = int(numbers[0])
            if "up" in command or "increase" in command:
                target_percent = min(100, current_percent + value)
                endpoint.SetMasterVolumeLevelScalar(target_percent / 100.0, None)
                speak(f"Volume increased by {value} percent")
            elif "down" in command or "decrease" in command:
                target_percent = max(0, current_percent - value)
                endpoint.SetMasterVolumeLevelScalar(target_percent / 100.0, None)
                speak(f"Volume decreased by {value} percent")
            else:
                target_percent = max(0, min(100, value))
                endpoint.SetMasterVolumeLevelScalar(target_percent / 100.0, None)
                speak(f"Volume set to {target_percent} percent")
        else:
            # Relative adjustment without explicit numbers (default 10% step)
            if "up" in command or "increase" in command:
                target_percent = min(100, current_percent + 10)
                endpoint.SetMasterVolumeLevelScalar(target_percent / 100.0, None)
                speak("Volume increased")
            elif "down" in command or "decrease" in command:
                target_percent = max(0, current_percent - 10)
                endpoint.SetMasterVolumeLevelScalar(target_percent / 100.0, None)
                speak("Volume decreased")
            else:
                speak("Please specify how you would like me to adjust the volume.")

    except Exception as e:
        print(f"[IRIS Error] Failed to set volume: {e}")
        speak("I encountered an issue adjusting the volume.")


def open_app(command: str):
    """
    Opens a local application on the computer using the Windows Start Menu.
    """
    command = command.lower()
    
    saved_file = get_last_file()
    if saved_file and os.path.exists(saved_file):
        if "it" in command or "that" in command or "file" in command:
            print(f"[IRIS Action] Opening saved file: {saved_file}")
            speak("Opening your file.")
            os.startfile(saved_file)
            set_last_file(None) 
            return
            
    app_name = command.replace("open", "").replace("launch", "").replace("start", "").strip()
    
    if not app_name:
        speak("What application would you like me to open?")
        return
        
    print(f"[IRIS Action] Using Start Menu to launch: {app_name}")
    speak(f"Opening {app_name}")
    
    pyautogui.press('win')          
    time.sleep(0.5)                 
    pyautogui.write(app_name, interval=0.05) 
    
    time.sleep(1.0)                 
    pyautogui.press('enter')        
    
    set_app(app_name)


def close_app(command: str):
    """
    Closes an open application on the computer.
    """
    command = command.lower()
    app_to_close = None

    if "it" in command or "that" in command:
        app_to_close = get_app()
    else:
        app_to_close = command.replace("close", "").replace("quit", "").replace("exit", "").replace("app", "").strip()

    if not app_to_close:
        speak("What application would you like me to close?")
        return

    print(f"[IRIS Action] Attempting to close: {app_to_close}")
    speak(f"Closing {app_to_close}")

    # Special safety check for File Explorer to protect the Windows Taskbar
    if "explorer" in app_to_close or "file" in app_to_close or "folder" in app_to_close:
        ps_command = "(New-Object -ComObject Shell.Application).Windows() | ForEach-Object { if ($_.FullName -like '*explorer.exe*') { $_.Quit() } }"
        subprocess.run(["powershell", "-Command", ps_command], creationflags=subprocess.CREATE_NO_WINDOW)
        return

    app_mapping = {
        "edge": "msedge.exe",
        "visual studio code": "Code.exe",
        "vs code": "Code.exe",
        "command prompt": "cmd.exe",
        "cmd": "cmd.exe",
        "powerpoint": "powerpnt.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "settings": "SystemSettings.exe",
        "store": "WinStore.App.exe",
        "photos": "PhotosApp.exe",
        "chatgpt": "chatgpt.exe", 
        "notepad": "notepad.exe",
        "chrome": "chrome.exe",
        "calculator": "calculator.exe",
        "spotify": "spotify.exe"
    }

    exe_name = f"{app_to_close.replace(' ', '')}.exe" 
    
    for spoken_name, real_exe in app_mapping.items():
        if spoken_name in app_to_close:
            exe_name = real_exe
            break

    # Silent command line executions
    subprocess.run(["taskkill", "/f", "/im", exe_name], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.run(["taskkill", "/f", "/fi", f"WINDOWTITLE eq *{app_to_close}*"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    
    if "calculat" in app_to_close:
        subprocess.run(["taskkill", "/f", "/fi", "windowtitle eq Calculator*"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

    if get_app() == app_to_close:
        set_app(None)


def get_system_status() -> str:
    battery = psutil.sensors_battery()
    if battery is not None:
        plugged = "plugged in" if battery.power_plugged else "on battery power"
        battery_percent = battery.percent
        battery_info = f"The system is currently {plugged} at {battery_percent}% battery."
    else:
        battery_info = "The system is running on desktop/AC power (no battery detected)."

    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_percent = ram.percent

    return (f"{battery_info} "
            f"CPU usage is at {cpu_usage}%, and RAM usage is at {ram_percent}%.")

def take_screenshot() -> str:
    current_folder = os.getcwd()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"Iris_Screenshot_{timestamp}.png"
    file_path = os.path.join(current_folder, filename)
    
    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)
    
    return f"Screenshot successfully captured and saved in your project folder as {filename}."

def search_local_file(filename: str) -> str:
    home_dir = os.path.expanduser("~")
    search_dirs = [
        os.path.join(home_dir, "Desktop"), 
        os.path.join(home_dir, "Documents"),
        os.path.join(home_dir, "OneDrive", "Desktop"),
        os.path.join(home_dir, "OneDrive", "Documents")
    ]
    
    found_paths = []
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for item in dirs + files:
                    if filename.lower() in item.lower():
                        found_paths.append(os.path.join(root, item))
                        if len(found_paths) >= 3:
                            break
                if len(found_paths) >= 3:
                    break
            if len(found_paths) >= 3:
                break
                
    if found_paths:
        set_last_file(found_paths[0])
        results = "\n".join(found_paths)
        return f"I found the following matches:\n{results}"
    return f"I could not find any files or folders matching '{filename}'."

def search_the_web(query: str) -> str:
    print(f"[IRIS Action] Searching the live web for: {query}")
    try:
        results = DDGS().text(query, max_results=3, backend="lite")
        if not results: return f"I searched the web for '{query}' but could not find any relevant results."
            
        formatted_results = f"Here are the top web search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No Title')
            body = result.get('body', 'No Description')
            formatted_results += f"Result {i} - {title}:\n{body}\n\n"
            
        return formatted_results
    except Exception as e:
        return f"An error occurred while trying to search the web: {str(e)}"

# ---------------------------------------------
#  IMAGE QUEUE & PREVIEW STATE
# ---------------------------------------------
IMAGE_QUEUE = []
CURRENT_IMAGE_INDEX = 0
CURRENT_PREVIEW_PATH = os.path.join(os.path.expanduser("~"), "temp_iris_preview.png")

def find_image(query: str) -> str:
    global IMAGE_QUEUE, CURRENT_IMAGE_INDEX
    print(f"[IRIS Action] Searching images for: {query}")
    try:
        results = list(DDGS().images(query, max_results=5))
        if not results: return f"I could not find any images for '{query}'."
        
        IMAGE_QUEUE = results
        CURRENT_IMAGE_INDEX = 0
        
        success = _load_current_preview()
        if success:
            title = IMAGE_QUEUE[CURRENT_IMAGE_INDEX].get('title', 'Image')
            return f"I am displaying an image titled '{title}' on your screen. Ask the user if they want to download it or see the next one."
        return "Failed to load the image preview."
            
    except Exception as e:
        return f"Error searching for images: {str(e)}"

def show_next_image() -> str:
    global IMAGE_QUEUE, CURRENT_IMAGE_INDEX
    if not IMAGE_QUEUE: return "No image search is currently active."
        
    CURRENT_IMAGE_INDEX = (CURRENT_IMAGE_INDEX + 1) % len(IMAGE_QUEUE)
    success = _load_current_preview()
    
    if success:
        title = IMAGE_QUEUE[CURRENT_IMAGE_INDEX].get('title', 'Image')
        return f"Now showing image {CURRENT_IMAGE_INDEX + 1} of {len(IMAGE_QUEUE)}: '{title}'."
    return "Could not load the next image."

def download_current_image() -> str:
    global IMAGE_QUEUE, CURRENT_IMAGE_INDEX
    if not IMAGE_QUEUE: return "There is no image on screen to download."
        
    try:
        img_data = IMAGE_QUEUE[CURRENT_IMAGE_INDEX]
        url = img_data.get('image')
        title = img_data.get('title', 'downloaded_image')
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip().replace(' ', '_')
            filename = f"{safe_title[:25]}.jpg"
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
            
            with open(save_path, 'wb') as f:
                f.write(resp.content)
                
            return f"Successfully saved the image to your Downloads folder as '{filename}'."
        return "Failed to download the high-resolution image."
    except Exception as e:
        return f"Download error: {str(e)}"

def _load_current_preview() -> bool:
    try:
        url = IMAGE_QUEUE[CURRENT_IMAGE_INDEX].get('image')
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            img.thumbnail((380, 200))
            img.save(CURRENT_PREVIEW_PATH, "PNG")
            return True
    except Exception as e:
        print(f"[IRIS Error] Preview load failed: {e}")
    return False

def analyze_screen(query: str) -> str:
    print(f"[IRIS Action] Capturing screen and performing vision analysis for: {query}")
    try:
        screenshot = pyautogui.screenshot()
        
        prompt = (
            f"You are Iris, an intelligent AI co-pilot looking at the user's computer screen. "
            f"Answer their specific request based on what you see in the screenshot: '{query}'. "
            f"Keep your spoken response concise, clear, direct, and actionable."
        )
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[screenshot, prompt]
        )
        
        if response.text: return response.text
        return "I analyzed your screen, but could not extract a definitive answer."

    except Exception as e:
        print(f"[IRIS Error] Vision analysis failed: {e}")
        return f"An error occurred while analyzing your screen: {str(e)}"
    
