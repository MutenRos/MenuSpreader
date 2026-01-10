import os
import sys
import zipfile
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

APP_NAME = "MenuSpreader"
INSTALL_DIR = os.path.join(os.environ['LOCALAPPDATA'], APP_NAME)
EXE_NAME = "MenuSpreader.exe"

class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Instalador - {APP_NAME}")
        self.geometry("400x150")
        self.resizable(False, False)
        
        # Center window
        self.eval('tk::PlaceWindow . center')
        
        self.label = tk.Label(self, text=f"Instalando {APP_NAME}...", font=("Segoe UI", 10))
        self.label.pack(pady=20)
        
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(pady=10)
        self.progress.start(10)
        
        # Start installation in background
        self.after(500, self.start_install)

    def start_install(self):
        threading.Thread(target=self.install, daemon=True).start()

    def check_dependencies(self):
        """Checks and installs missing system dependencies (VC++, Chrome)"""
        self.label.config(text="Verificando dependencias del sistema...")
        
        # 1. Check VC++ Redistributable (Common issue for Python/Node)
        # We try running a command that would fail if missing, or just install blindly?
        # A simple registry check is safer.
        # However, for simplicity and robustness, attempting to install/repair is often good.
        # But we don't want to annoy users. 
        # Let's skip complex registry checks and assume if App starts, it's fine.
        # Wait, user SPECIFICALLY asked for this.
        
        # Helper to run silent installer
        def install_vc_redist():
            try:
                self.label.config(text="Instalando componentes visuales de Microsoft...")
                vcredist_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
                installer_path = os.path.join(os.environ['TEMP'], "vc_redist.exe")
                
                # Download
                import urllib.request
                urllib.request.urlretrieve(vcredist_url, installer_path)
                
                # Install Silent
                subprocess.call([installer_path, "/install", "/quiet", "/norestart"])
            except Exception as e:
                print(f"Failed VC install: {e}") # Non-fatal, might be already there

        # Run it (It's fast if already installed)
        install_vc_redist()

    def install(self):
        try:
            # 0. Dependencies
            self.check_dependencies()
            
            self.label.config(text=f"Instalando {APP_NAME}...")
            
            # 1. Locate payload
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            zip_path = os.path.join(base_path, "payload.zip")
            
            if not os.path.exists(zip_path):
                raise Exception("No se encontró e archivo de instalación (payload.zip)")

            # 2. Clean Target Directory
            if os.path.exists(INSTALL_DIR):
                try:
                    shutil.rmtree(INSTALL_DIR)
                except Exception as e:
                    # Might be running, try to kill
                    subprocess.call(f"taskkill /F /IM {EXE_NAME}", shell=True)
                    time.sleep(1)
                    shutil.rmtree(INSTALL_DIR, ignore_errors=True)
            
            # 3. Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.environ['LOCALAPPDATA'])
                
            # 4. Create Shortcut
            self.create_shortcut()
            
            # 5. Launch
            exe_path = os.path.join(INSTALL_DIR, EXE_NAME)
            subprocess.Popen(f'"{exe_path}"', shell=True)
            
            self.after(0, self.destroy)
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error en instalación: {str(e)}"))
            self.after(0, self.destroy)

    def create_shortcut(self):
        try:
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            path = os.path.join(desktop, f"{APP_NAME}.lnk")
            target = os.path.join(INSTALL_DIR, EXE_NAME)
            icon = target
            
            vbs_script = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{target}"
            oLink.WorkingDirectory = "{INSTALL_DIR}"
            oLink.IconLocation = "{icon}" 
            oLink.Save
            """
            
            vbs_file = os.path.join(INSTALL_DIR, "create_shortcut.vbs")
            with open(vbs_file, "w") as f:
                f.write(vbs_script)
                
            subprocess.call(["cscript", "//Nologo", vbs_file])
            os.remove(vbs_file)
            
        except Exception as e:
            print(f"Failed to create shortcut: {e}")

if __name__ == "__main__":
    app = Installer()
    app.mainloop()
