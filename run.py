import sys
import os

# Configurar path del proyecto
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Cargar variables de entorno desde .env en la raíz del proyecto
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), 'app', '.env')
load_dotenv(env_path)

# Debug: verificar que se cargaron las variables de email
print(f"=== Variables de Email ===")
print(f"EMAIL_SENDER: {os.environ.get('EMAIL_SENDER', 'NO CONFIGURADO')}")
print(f"EMAIL_PASSWORD: {'****' if os.environ.get('EMAIL_PASSWORD') else 'NO CONFIGURADO'}")
print(f"EMAIL_DIRECTOR: {os.environ.get('EMAIL_DIRECTOR', 'NO CONFIGURADO')}")
print(f"SMTP_SERVER: {os.environ.get('SMTP_SERVER', 'NO CONFIGURADO')}")

from app import create_app

# Llama a la función 'create_app' que está en app/__init__.py
app = create_app()

# Esta sección se asegura de que el servidor solo se inicie
# cuando ejecutas directamente el archivo 'run.py'.
if __name__ == '__main__':
    # 'debug=True' hace que el servidor se reinicie automáticamente
    # con cada cambio y muestra errores detallados en el navegador.
    # ¡Nunca uses debug=True en producción!
    app.run(debug=True)