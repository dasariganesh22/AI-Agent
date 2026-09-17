import subprocess
import sys
import time

def launch_system():
    print("[SYSTEM] Booting Iris Neural Interface...")
    
    python_exe = sys.executable
    
    # 1. Launch the backend AI and Websocket server
    server_process = subprocess.Popen([python_exe, "server.py"])
    
    time.sleep(1.5) # Give the server a moment to open the socket port
    
    # 2. Launch the frontend Hologram UI
    ui_process = subprocess.Popen([python_exe, "hologram.py"])
    
    try:
        # 3. Monitor both processes. If one closes (like saying "Exit"), kill the other.
        while True:
            if server_process.poll() is not None: 
                ui_process.terminate()
                break
            if ui_process.poll() is not None:
                server_process.terminate()
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting down completely...")
        server_process.terminate()
        ui_process.terminate()

if __name__ == "__main__":
    launch_system()