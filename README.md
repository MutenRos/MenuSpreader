# MenuSpreader - Distribución

## Generar Versión Portable
Este proyecto se compila creando una carpeta portable (ZIP) que contiene el frontend (Python/Tkinter), el backend (Node.js) y todas las dependencias.

### 1. Requisitos
- Python 3.11+
- Node.js 18+
- Entorno Virtual de Python (recomendado para evitar errores de DLL)

### 2. Preparación del Entorno
Si es la primera vez:
```bash
# Crear entorno virtual
python -m venv venv

# Activar (PowerShell)
.\venv\Scripts\Activate

# Instalar dependencias
pip install requests pillow qrcode[pil] pyinstaller
```

### 3. Compilar bot-server.exe (Backend)
Primero convertimos el servidor Node a ejecutable:
```bash
npm install -g pkg
pkg bot-server.js --targets node18-win-x64 --output bot-server.exe
```

### 4. Compilar MenuSpreader (Portable)
Usamos PyInstaller en modo carpeta (`onedir`) para máxima estabilidad.
```bash
# Asegúrate de estar en el entorno virtual
python -m PyInstaller MenuSpreader.spec --noconfirm
```

### 5. Empaquetar
Para distribuir, comprime el contenido de `dist/MenuSpreader` en un ZIP.
```powershell
Compress-Archive -Path "dist\MenuSpreader\*" -DestinationPath "dist\MenuSpreader_Portable.zip" -Force
```

## Ejecución por el Usuario
1. Descargar `MenuSpreader_Portable.zip`.
2. Descomprimir en una carpeta (ej. Documentos).
3. Ejecutar `MenuSpreader.exe` (dentro de la carpeta).
   - El servidor `bot-server.exe` arranca automáticamente en segundo plano.
   - La sesión de WhatsApp se guarda en la subcarpeta `.wwebjs_auth`.
