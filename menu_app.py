import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import sqlite3
import subprocess
import threading
import time
import os
import sys
import qrcode
from PIL import Image, ImageTk
import io
import logging
import webbrowser # Added for donation link

import zipfile # Added for zip extraction

# Determine application path for robust file handling (Fixes PermissionError in protected folders)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure we write logs and DB to a writable location (The App Directory in AppData)
LOG_PATH = os.path.join(APP_DIR, 'app.log')
DB_PATH = os.path.join(APP_DIR, "bar_data.db")

# Setup logging
try:
    logging.basicConfig(filename=LOG_PATH, level=logging.DEBUG, 
                        format='%(asctime)s %(levelname)s:%(message)s')
except PermissionError:
    # Fallback to temp dir if App dir is not writable (e.g. Program Files)
    import tempfile
    LOG_PATH = os.path.join(tempfile.gettempdir(), 'MenuSpreader.log')
    logging.basicConfig(filename=LOG_PATH, level=logging.DEBUG, 
                        format='%(asctime)s %(levelname)s:%(message)s')

BOT_API_URL = "http://localhost:3001"
# DB_PATH is already defined above
CURRENT_VERSION = "v1.0.6"
REPO_OWNER = "MutenRos" # Cambiar si tu usuario de GitHub es diferente
REPO_NAME = "MenuSpreader"

class Colors:
    PRIMARY = "#3B82F6"   # Blue 500 (More vibrant)
    PRIMARY_HOVER = "#2563EB" # Blue 600
    SECONDARY = "#64748B" # Slate 500
    BG = "#F1F5F9"        # Slate 100 (Slightly darker for better contrast with white cards)
    CARD_BG = "#FFFFFF"   # White
    TEXT = "#0F172A"      # Slate 900 (High contrast)
    TEXT_LIGHT = "#64748B" # Slate 500
    BORDER = "#CBD5E1"    # Slate 300
    SUCCESS = "#10B981"   # Emerald 500
    DANGER = "#EF4444"    # Red 500
    WARNING = "#F59E0B"   # Amber 500

class MenuAppLocal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MenuSpreader Desktop - Pro")
        self.state('zoomed') # Start maximized
        self.configure(bg=Colors.BG)
        
        # Bot Server Process
        self.bot_process = None
        self.start_bot_server()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Check for updates in background
        threading.Thread(target=self.check_for_updates, daemon=True).start()
        
        # Configure Styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # General
        self.style.configure("TFrame", background=Colors.BG)
        
        # Modern Button Styling
        self.style.configure("TButton", 
            background=Colors.PRIMARY, 
            foreground="white", 
            font=("Segoe UI", 10, "bold"), 
            borderwidth=0, 
            padding=12,
            relief="flat"
        )
        self.style.map("TButton", 
            background=[("active", Colors.PRIMARY_HOVER)],
            relief=[("pressed", "sunken")]
        )
        
        # Tabs - Modern Flat Look
        self.style.configure("TNotebook", background=Colors.BG, borderwidth=0)
        self.style.configure("TNotebook.Tab", 
            background=Colors.BG, 
            foreground=Colors.TEXT_LIGHT, 
            padding=[20, 12], 
            font=("Segoe UI", 11, "bold"),
            borderwidth=0
        )
        self.style.map("TNotebook.Tab", 
            background=[("selected", Colors.CARD_BG)], 
            foreground=[("selected", Colors.PRIMARY)],
            expand=[("selected", [0, 0, 0, 0])] # Remove weird expansion
        )
        
        # Treeview (Table)
        self.style.configure("Treeview", 
            background="white",
            foreground=Colors.TEXT,
            fieldbackground="white",
            rowheight=35,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        self.style.configure("Treeview.Heading", 
            background="#F1F5F9", 
            foreground=Colors.TEXT, 
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        self.style.map("Treeview", background=[("selected", "#EFF6FF")], foreground=[("selected", Colors.PRIMARY)])

        # Initialize variables
        self.status_var = tk.StringVar(value="Iniciando sistema...")
        self.bar_name_var = tk.StringVar()
        self.selected_file_path = None
        self.has_shown_donation = False # Flag for donation popup

        # Initialize Data & UI
        self.load_bar_info()
        self.create_widgets()
        self.check_bot_connection()
        
    def check_for_updates(self):
        """Checks GitHub releases for a new version"""
        try:
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_tag = data.get("tag_name", "") # e.g. v1.0.0
                
                if self.is_newer(latest_tag, CURRENT_VERSION):
                    logging.info(f"New version found: {latest_tag}")
                    
                    # Find the asset url for ZIP
                    download_url = None
                    for asset in data.get("assets", []):
                        if asset.get("name").endswith(".zip"):
                            download_url = asset.get("browser_download_url")
                            break
                    
                    if download_url:
                        # Start silent update without asking
                        self.after(0, lambda: self.start_silent_update(download_url))
        except Exception as e:
            logging.error(f"Error Checking updates: {e}")

    def is_newer(self, remote_tag, current_tag):
        try:
            # Strip 'v' and split by '.' -> [1, 0, 1]
            r = [int(x) for x in remote_tag.lstrip('v').split('.')]
            c = [int(x) for x in current_tag.lstrip('v').split('.')]
            return r > c
        except:
            return False

    def start_silent_update(self, url):
        self.status_var.set("⚠️ Actualizando sistema... No cierre la ventana.")
        threading.Thread(target=self.perform_update, args=(url,), daemon=True).start()

    def perform_update(self, url):
        try:
            logging.info(f"Downloading update from {url}")
            
            # 1. Download ZIP
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                zip_name = "update.zip"
                with open(zip_name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logging.info("Download complete. Extracting...")
                
                # 2. Extract to temp folder
                extract_path = "update_temp"
                if os.path.exists(extract_path):
                   import shutil
                   shutil.rmtree(extract_path)
                
                with zipfile.ZipFile(zip_name, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # 3. Determine source folder (usually dist/MenuSpreader or similar inside zip)
                # We assume the zip contains a folder likely named "MenuSpreader"
                source_dir = os.path.join(extract_path, "MenuSpreader") 
                if not os.path.exists(source_dir):
                    # If not found, maybe files are at root of zip? -> use extract_path
                     source_dir = extract_path

                logging.info(f"Source dir for update: {source_dir}")
                
                # 4. Create updater batch script
                # Self-destruct logic included
                current_dir = os.getcwd()
                batch_script = f"""@echo off
timeout /t 3 /nobreak > NUL
echo Installing update...
xcopy "{os.path.abspath(source_dir)}\*" "{current_dir}" /E /H /Y /Q
rmdir "{os.path.abspath(extract_path)}" /S /Q
del "{os.path.abspath(zip_name)}"
start "" "{os.path.join(current_dir, 'MenuSpreader.exe')}"
del "%~f0"
"""
                with open("updater.bat", "w") as bat:
                    bat.write(batch_script)
                
                logging.info("Updater script created. Restarting...")
                
                # 5. Launch updater and exit
                self.after(0, lambda: subprocess.Popen("updater.bat", shell=True))
                self.after(1000, self.on_closing)
                
        except Exception as e:
            logging.error(f"Update failed: {e}")
            self.after(0, lambda: messagebox.showerror("Error de Actualización", f"Fallo automático: {e}"))
            self.after(0, lambda: webbrowser.open(url)) # Fallback to browser

    def show_update_dialog(self, version, url):
        # Deprecated
        pass

        # Load Data
        self.load_bar_info()
        
        # Setup UI
        self.create_widgets()
        
        # Start connection checker
        self.check_bot_connection()

    def start_bot_server(self):
        try:
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller bundle
                base_path = sys._MEIPASS
            else:
                # Running in normal Python environment
                base_path = os.path.dirname(os.path.abspath(__file__))

            bot_exe = os.path.join(base_path, "bot-server.exe")
            
            if os.path.exists(bot_exe):
                # Start bot-server.exe hidden
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                self.bot_process = subprocess.Popen(
                    [bot_exe], 
                    startupinfo=startupinfo
                )
                logging.info(f"Started bot-server.exe from {bot_exe}")
            else:
                logging.warning(f"bot-server.exe not found at {bot_exe}")
                
        except Exception as e:
            logging.error(f"Failed to start bot-server: {e}")

    def on_closing(self):
        if self.bot_process:
            try:
                self.bot_process.terminate()
                logging.info("Terminated bot-server process")
            except Exception as e:
                logging.error(f"Error terminating bot-server: {e}")
        self.destroy()

    def create_widgets(self):
        # Header (Top Bar)
        header = tk.Frame(self, bg=Colors.CARD_BG, height=80)
        header.pack(fill="x", side="top")
        
        # Shadow effect (simple line)
        tk.Frame(self, bg=Colors.BORDER, height=1).pack(fill="x", side="top")
        
        tk.Label(header, text="MenuSpreader", font=("Segoe UI", 24, "bold"), bg=Colors.CARD_BG, fg=Colors.PRIMARY).pack(side="left", padx=30, pady=20)
        
        # Status Badge in Header
        self.status_label = tk.Label(header, textvariable=self.status_var, bg="#ECFDF5", fg=Colors.SUCCESS, font=("Segoe UI", 9, "bold"), padx=10, pady=5)
        self.status_label.pack(side="right", padx=30)
        
        # Main Container
        self.main_container = tk.Frame(self, bg=Colors.BG)
        self.main_container.pack(fill="both", expand=True, padx=40, pady=30)
        
        # -- QR / Login View --
        self.login_frame = tk.Frame(self.main_container, bg=Colors.CARD_BG, padx=40, pady=40)
        # Show initially (Loading state)
        self.login_frame.pack(fill="both", expand=True)

        self.qr_label = tk.Label(self.login_frame, bg=Colors.CARD_BG)
        self.qr_label.pack(pady=20)
        tk.Label(self.login_frame, text="Escanea el código para vincular WhatsApp", font=("Segoe UI", 14), bg=Colors.CARD_BG).pack()
        
        # -- Dashboard View --
        self.dashboard_frame = ttk.Notebook(self.main_container)
        
        # Tab 1: Enviar Menú
        self.tab_send = tk.Frame(self.dashboard_frame, bg=Colors.CARD_BG)
        self.dashboard_frame.add(self.tab_send, text=" 📤 Enviar Menú ")
        self.setup_send_tab()
        
        # Tab 2: Contactos
        self.tab_contacts = tk.Frame(self.dashboard_frame, bg=Colors.CARD_BG)
        self.dashboard_frame.add(self.tab_contacts, text=" 👥 Gestionar Contactos ")
        self.setup_contacts_tab()
        
        # Tab 3: Ajustes
        self.tab_settings = tk.Frame(self.dashboard_frame, bg=Colors.CARD_BG)
        self.dashboard_frame.add(self.tab_settings, text=" ⚙ Ajustes ")
        self.setup_settings_tab()

    def setup_send_tab(self):
        frame = tk.Frame(self.tab_send, bg=Colors.CARD_BG, padx=40, pady=40)
        frame.pack(fill="both", expand=True)

        # File Selection Card
        self.file_label = tk.Label(frame, text="Ningún archivo seleccionado", bg=Colors.BG, fg=Colors.TEXT_LIGHT, padx=20, pady=50, width=50, relief="flat", font=("Segoe UI", 10))
        self.file_label.pack(pady=20)
        
        btn_select = tk.Button(frame, text="📷 Seleccionar Imagen del Menú", command=self.select_file, bg=Colors.PRIMARY, fg="white", font=("Segoe UI", 11, "bold"), padx=25, pady=12, relief="flat", cursor="hand2")
        btn_select.pack(pady=5)
        
        # Message Area (Template System)
        tk.Label(frame, text="Mensaje Personalizado:", bg=Colors.CARD_BG, font=("Segoe UI", 11, "bold"), fg=Colors.TEXT).pack(anchor="w", pady=(30, 10))

        # --- Template Controls ---
        tmpl_frame = tk.Frame(frame, bg=Colors.CARD_BG)
        tmpl_frame.pack(fill="x", pady=(0, 5))
        
        self.saved_msgs_combo = ttk.Combobox(tmpl_frame, state="readonly", font=("Segoe UI", 10), width=30)
        self.saved_msgs_combo.pack(side="left", padx=(0, 10))
        self.saved_msgs_combo.bind("<<ComboboxSelected>>", self.load_selected_message)
        
        tk.Button(tmpl_frame, text="💾 Guardar", command=self.save_message_template, bg=Colors.SECONDARY, fg="white", font=("Segoe UI", 9), padx=10, relief="flat").pack(side="left", padx=5)
        tk.Button(tmpl_frame, text="🗑️ Borrar", command=self.delete_message_template, bg=Colors.DANGER, fg="white", font=("Segoe UI", 9), padx=10, relief="flat").pack(side="left", padx=5)
        # -------------------------
        
        msg_frame = tk.Frame(frame, bg="white", highlightbackground=Colors.BORDER, highlightthickness=1)
        msg_frame.pack(fill="x")
        
        self.msg_text = tk.Text(msg_frame, height=4, font=("Segoe UI", 11), bg="white", relief="flat", padx=10, pady=10)
        self.msg_text.pack(fill="both", expand=True)
        self.msg_text.insert("1.0", f"Hola {{nombre}}, *{self.bar_name_var.get()}* ha publicado el menú de hoy.")
        
        tk.Label(frame, text="Info: {nombre} se reemplaza automáticamente.", bg=Colors.CARD_BG, fg=Colors.TEXT_LIGHT, font=("Segoe UI", 9)).pack(anchor="w", pady=5)
        
        # Send Button
        tk.Frame(frame, height=20, bg=Colors.CARD_BG).pack() # Spacer
        btn_send = tk.Button(frame, text="🚀 ENVIAR MENÚ AHORA", command=self.send_menu, bg=Colors.SUCCESS, fg="white", font=("Segoe UI", 12, "bold"), padx=30, pady=15, relief="flat", cursor="hand2")
        btn_send.pack(pady=10, fill="x")
        
        self.refresh_saved_messages()

    def refresh_saved_messages(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Ensure table exists
            c.execute("CREATE TABLE IF NOT EXISTS SavedMessages (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, content TEXT)")
            
            c.execute("SELECT name FROM SavedMessages")
            rows = c.fetchall()
            conn.close()
            
            values = [r[0] for r in rows]
            self.saved_msgs_combo['values'] = values
            
            if values:
                self.saved_msgs_combo.set("Cargar plantilla...")
            else:
                self.saved_msgs_combo.set("Sin plantillas")
                
        except Exception as e:
            logging.error(f"Error refreshing messages: {e}")

    def save_message_template(self):
        content = self.msg_text.get("1.0", "end-1c").strip()
        if not content:
            messagebox.showwarning("Aviso", "El mensaje está vacío")
            return
            
        # Dialog to get name
        name = tk.simpledialog.askstring("Guardar", "Nombre de la plantilla:")
        if not name: return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Check limit 5
            c.execute("SELECT COUNT(*) FROM SavedMessages")
            count = c.fetchone()[0]
            
            if count >= 5:
                messagebox.showwarning("Límite Alcanzado", "Ya tienes 5 plantillas. Borra una para guardar nueva.")
                conn.close()
                return
            
            # Check duplicates
            c.execute("SELECT id FROM SavedMessages WHERE name = ?", (name,))
            if c.fetchone():
                 if messagebox.askyesno("Sobrescribir", "Ya existe una plantilla con este nombre. ¿Sobrescribir?"):
                     c.execute("UPDATE SavedMessages SET content = ? WHERE name = ?", (content, name))
                 else:
                     conn.close()
                     return
            else:
                c.execute("INSERT INTO SavedMessages (name, content) VALUES (?, ?)", (name, content))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Plantilla guardada")
            self.refresh_saved_messages()
            self.saved_msgs_combo.set(name)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_message_template(self):
        name = self.saved_msgs_combo.get()
        if not name or name in ["Cargar plantilla...", "Sin plantillas"]:
            return
            
        if not messagebox.askyesno("Confirmar", f"¿Borrar plantilla '{name}'?"):
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM SavedMessages WHERE name = ?", (name,))
            conn.commit()
            conn.close()
            
            self.refresh_saved_messages()
            self.msg_text.delete("1.0", "end")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def load_selected_message(self, event):
        name = self.saved_msgs_combo.get()
        if not name or name in ["Cargar plantilla...", "Sin plantillas"]:
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT content FROM SavedMessages WHERE name = ?", (name,))
            row = c.fetchone()
            conn.close()
            
            if row:
                self.msg_text.delete("1.0", "end")
                self.msg_text.insert("1.0", row[0])
                
        except Exception as e:
            logging.error(f"Error loading message: {e}")

    def setup_contacts_tab(self):
        frame = tk.Frame(self.tab_contacts, bg=Colors.CARD_BG, padx=30, pady=30)
        frame.pack(fill="both", expand=True)
        
        # Add Contact Layout (Top)
        form_label = tk.Label(frame, text="Nuevo Registro", font=("Segoe UI", 12, "bold"), bg=Colors.CARD_BG, fg=Colors.TEXT)
        form_label.pack(anchor="w", pady=(0, 15))
        
        form_frame = tk.Frame(frame, bg=Colors.BG, padx=20, pady=20)
        form_frame.pack(fill="x", pady=(0, 30))
        
        def create_entry(parent, label, width=15):
            container = tk.Frame(parent, bg=Colors.BG)
            container.pack(side="left", padx=10)
            tk.Label(container, text=label, bg=Colors.BG, fg=Colors.TEXT_LIGHT, font=("Segoe UI", 9)).pack(anchor="w")
            entry = tk.Entry(container, width=width, font=("Segoe UI", 11), relief="flat", highlightbackground=Colors.BORDER, highlightthickness=1)
            entry.pack(fill="x", pady=5, ipady=5)
            return entry

        self.entry_comp_name = create_entry(form_frame, "Hora", width=8) 
        self.entry_comp_duration = create_entry(form_frame, "Duración", width=8)
        self.entry_comp_contact_name = create_entry(form_frame, "Nombre", width=18)
        
        # Phone with Prefix
        container_phone = tk.Frame(form_frame, bg=Colors.BG)
        container_phone.pack(side="left", padx=10)
        tk.Label(container_phone, text="Teléfono", bg=Colors.BG, fg=Colors.TEXT_LIGHT, font=("Segoe UI", 9)).pack(anchor="w")
        
        phone_box = tk.Frame(container_phone)
        phone_box.pack(pady=5)
        
        self.combo_prefix = ttk.Combobox(phone_box, values=["+34", "+1", "+44", "+33", "+49", "+39"], width=5, state="readonly", font=("Segoe UI", 11))
        self.combo_prefix.current(0)
        self.combo_prefix.pack(side="left")
        
        self.entry_comp_phone = tk.Entry(phone_box, width=15, font=("Segoe UI", 11), relief="flat", highlightbackground=Colors.BORDER, highlightthickness=1)
        self.entry_comp_phone.pack(side="left", padx=(5,0), ipady=5)

        # Buttons
        btn_add = tk.Button(form_frame, text="Añadir", command=self.add_contact, bg=Colors.PRIMARY, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=5, cursor="hand2")
        btn_add.pack(side="left", padx=20, pady=10)


        # Table Area
        tk.Label(frame, text="Lista de Reservas", font=("Segoe UI", 12, "bold"), bg=Colors.CARD_BG, fg=Colors.TEXT).pack(anchor="w", pady=(0, 10))
        
        columns = ("hora", "duracion", "nombre", "telefono")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.tree.heading("hora", text="Hora")
        self.tree.heading("duracion", text="Duración")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("telefono", text="Teléfono")
        
        self.tree.column("hora", width=100, anchor="center")
        self.tree.column("duracion", width=100, anchor="center")
        self.tree.column("nombre", width=200, anchor="w")
        self.tree.column("telefono", width=200, anchor="w")
        self.tree.pack(fill="both", expand=True)
        
        # Styled Scrollbar
        # (Standard ttk scrollbar is fine, already styled by theme)
        
        # Delete Button
        tk.Button(frame, text="Eliminar Seleccionado", command=self.delete_contact, bg=Colors.DANGER, fg="white", font=("Segoe UI", 9), relief="flat", pady=8).pack(anchor="e", pady=20)
        
        self.refresh_contacts()

    def setup_settings_tab(self):
        frame = tk.Frame(self.tab_settings, bg=Colors.CARD_BG, padx=40, pady=40)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="Configuración del Negocio", font=("Segoe UI", 16, "bold"), bg=Colors.CARD_BG, fg=Colors.TEXT).pack(anchor="w", pady=(0, 20))
        
        tk.Label(frame, text="Nombre del Establecimiento", bg=Colors.CARD_BG, fg=Colors.TEXT_LIGHT, font=("Segoe UI", 10)).pack(anchor="w")
        entry_name = tk.Entry(frame, textvariable=self.bar_name_var, font=("Segoe UI", 12), width=40, relief="solid", bd=1)
        entry_name.pack(anchor="w", pady=(5, 20), ipady=5)
        
        tk.Button(frame, text="Guardar Cambios", command=self.save_bar_name, bg=Colors.SECONDARY, fg="white", font=("Segoe UI", 10), padx=20, pady=10, relief="flat").pack(anchor="w")

    # --- Logic ---

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.pdf")])
        if file_path:
            self.selected_file_path = file_path
            self.file_label.config(text=os.path.basename(file_path), fg="#4f46e5")

    def check_bot_connection(self):
        # Run check in background so we don't block the UI (Fix "White Screen" issue)
        threading.Thread(target=self._background_check_loop, daemon=True).start()

    def _background_check_loop(self):
        try:
            # Short timeout to avoid hanging threads
            response = requests.get(f"{BOT_API_URL}/status", timeout=2)
            data = response.json()
            # Update UI on Main Thread
            self.after(0, lambda: self._handle_bot_response(data))
        except Exception as e:
            # Update UI on Main Thread
            self.after(0, lambda: self._handle_bot_error(str(e)))
        
    def _handle_bot_response(self, data):
        status = data.get("status")
        qr_data = data.get("qr")
        
        logging.debug(f"Status check - Status: {status}")
        self.status_var.set(f"Estado del Sistema: {status}")
        
        if status == "READY":
            logging.info("System is READY")
            self.login_frame.pack_forget()
            self.dashboard_frame.pack(fill="both", expand=True)

            # --- Donation Popup Logic ---
            if not self.has_shown_donation:
                self.has_shown_donation = True
                response = messagebox.askyesno(
                    "¡Conexión Exitosa!",
                    "MenuSpreader funciona gracias a horas de trabajo gratuito.\n\n"
                    "Si te ayuda a facturar más en tu bar, ¿considerarías apoyarme con un café?\n\n"
                    "Ir a PayPal.me/MutenRos"
                )
                if response:
                    webbrowser.open("https://paypal.me/MutenRos")
            # ----------------------------

        elif status == "QR_READY" and qr_data:
            logging.info("QR is READY, attempting to show")
            self.show_qr(qr_data)
            self.dashboard_frame.pack_forget()
            self.login_frame.pack(fill="both", expand=True)
            
        # Schedule next check
        self.after(2000, self.check_bot_connection)
    
    def _handle_bot_error(self, error_msg):
        logging.error(f"Connection check failed: {error_msg}")
        self.status_var.set("Esperando al servidor local (node bot-server.js)...")
        # Schedule next check
        self.after(2000, self.check_bot_connection)

    def show_qr(self, qr_data):
        logging.info("show_qr called")
        try:
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize safely
            img = img.resize((350, 350), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.qr_photo = ImageTk.PhotoImage(img) # Keep reference
            self.qr_label.config(image=self.qr_photo)
            logging.info("QR Code displayed successfully")
        except Exception as e:
            logging.error(f"Error displaying QR: {e}")

    def load_bar_info(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT name FROM Bar LIMIT 1")
            row = c.fetchone()
            if row:
                self.bar_name_var.set(row[0])
            else:
                self.bar_name_var.set("Mi Bar")
                # Create if not exists
                import uuid
                bar_id = str(uuid.uuid4()) # simple way, cuids are better but this works for local
                c.execute("INSERT INTO Bar (id, name, email) VALUES (?, ?, ?)", (bar_id, "Mi Bar", "admin@bar.com"))
                conn.commit()
            conn.close()
        except Exception as e:
            print("DB Error:", e)

    def save_bar_name(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE Bar SET name = ?", (self.bar_name_var.get(),))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Nombre guardado")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_contacts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Ensure duration column exists (migracion al vuelo)
            try:
                c.execute("ALTER TABLE Company ADD COLUMN duration TEXT DEFAULT ''")
                conn.commit()
            except:
                pass

            c.execute("SELECT id, name, duration, contactName, contactPhone FROM Company")
            rows = c.fetchall()
            for row in rows:
                # row structure: id, name(Hora), duration, contactName(Nombre), contactPhone
                self.tree.insert("", "end", iid=row[0], values=(row[1], row[2], row[3], row[4]))
            conn.close()
        except:
            pass

    def add_contact(self):
        try:
            # Validar campos obligatorios antes de insertar
            nombre = self.entry_comp_contact_name.get().strip()
            raw_phone = self.entry_comp_phone.get().strip()
            
            if not nombre:
                messagebox.showwarning("Campo vacío", "El nombre del contacto es obligatorio.")
                return
            if not raw_phone or len(raw_phone) < 9:
                messagebox.showwarning("Teléfono inválido", "Introduce un número de teléfono válido (mín. 9 dígitos).")
                return
            # Comprobar que solo contiene dígitos
            if not raw_phone.replace(" ", "").isdigit():
                messagebox.showwarning("Formato incorrecto", "El teléfono solo puede contener números.")
                return
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            import uuid
            new_id = str(uuid.uuid4())
            
            # Combine Prefix + Phone
            prefix = self.combo_prefix.get()
            full_phone = prefix + raw_phone
            
            c.execute("INSERT INTO Company (id, name, duration, contactName, contactPhone) VALUES (?, ?, ?, ?, ?)", 
                      (new_id, self.entry_comp_name.get(), self.entry_comp_duration.get(), self.entry_comp_contact_name.get(), full_phone))
            conn.commit()
            conn.close()
            
            # Clear fields
            self.entry_comp_name.delete(0, 'end')
            self.entry_comp_duration.delete(0, 'end')
            self.entry_comp_contact_name.delete(0, 'end')
            self.entry_comp_phone.delete(0, 'end')
            
            self.refresh_contacts()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_contact(self):
        selected = self.tree.selection()
        if not selected: return
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM Company WHERE id = ?", (selected[0],))
            conn.commit()
            conn.close()
            self.refresh_contacts()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_menu(self):
        if not self.selected_file_path:
            messagebox.showwarning("Falta imagen", "Selecciona una imagen primero.")
            return

        # 1. Get recipients
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT contactName, contactPhone FROM Company")
        companies = c.fetchall()
        conn.close()
        
        if not companies:
            messagebox.showwarning("Sin contactos", "No hay empresas en la lista.")
            return

        # Confirmación antes de enviar (evita envíos accidentales)
        if not messagebox.askyesno("Confirmar envío",
                f"¿Enviar el menú a {len(companies)} contacto(s)?\n\n"
                f"Imagen: {os.path.basename(self.selected_file_path)}"):
            return
            
        base_msg = self.msg_text.get("1.0", "end-1c")
        
        # Start sending in background
        self.status_var.set("⏳ Enviando menús... Por favor espere.")
        threading.Thread(target=self._background_send, args=(companies, base_msg), daemon=True).start()

    def _background_send(self, companies, base_msg):
        # 2. Iterate and send via API
        success_count = 0
        total = len(companies)
        
        for i, (name, phone) in enumerate(companies):
            # Update status during loop
            self.after(0, lambda idx=i: self.status_var.set(f"⏳ Enviando {idx+1}/{total}..."))
            
            # Personalize message
            msg = base_msg.replace("{nombre}", name)
            
            try:
                payload = {
                     "phone": phone,
                     "caption": msg,
                     "imagePath": self.selected_file_path
                }
                # Timeout to prevent infinite hang
                requests.post(f"{BOT_API_URL}/send-menu", json=payload, timeout=30)
                success_count += 1
            except Exception as e:
                print(f"Error sending to {phone}: {e}")
        
        # Finished
        self.after(0, lambda: self._sending_complete(success_count, total))

    def _sending_complete(self, success, total):
        self.status_var.set("✅ Envío completado")
        messagebox.showinfo("Enviado", f"Proceso finalizado.\nEnviados con éxito: {success}/{total}")

if __name__ == "__main__":
    try:
        app = MenuAppLocal()
        app.mainloop()
    except Exception as e:
        # Emergency error handler for startup crashes
        import traceback
        error_msg = f"Error crítico al iniciar:\n{str(e)}\n\n{traceback.format_exc()}"
        try:
            logging.critical(error_msg)
            messagebox.showerror("Error Fatal", error_msg)
        except:
            # If tkinter fails, try writing to a file at least
            with open("CRITICAL_ERROR.txt", "w") as f:
                f.write(error_msg)
