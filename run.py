import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

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
