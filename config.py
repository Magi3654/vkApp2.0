# config.py

import os

class Config:
    # --- ¡ESTA LÍNEA ES LA CLAVE! ---
    # Asegúrate de que esta línea exista y no esté comentada.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-llave-secreta-muy-muy-dificil-de-adivinar'

    # --- Configuración de la Base de Datos ---
    SQLALCHEMY_DATABASE_URI = 'postgresql://ilse:kinessia1@localhost:5432/kinessia_db'
    
    # Esto desactiva una función de Flask-SQLAlchemy que no necesitamos y consume recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

