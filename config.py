# config.py

import os

class Config:
    # --- SECRET KEY ---
    # IMPORTANTE: En producción, usa una variable de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-llave-secreta-muy-muy-dificil-de-adivinar'

    # --- Configuración de Base de Datos ---
    # Supabase como base de datos principal
    # PostgreSQL local como respaldo

    # SUPABASE (Principal) - Session Pooler IPv4 compatible
    SUPABASE_DB_URI = os.environ.get('SUPABASE_DB_URI') or \
    'postgresql://postgres.fosbnyihupueithcogfe:kinessia2025@aws-1-us-west-1.pooler.supabase.com:5432/postgres'

    # PostgreSQL Local (Respaldo) - Windows
    LOCAL_DB_URI = os.environ.get('LOCAL_DB_URI') or \
        'postgresql://postgres:kinessialinx@127.0.0.1:5432/vkapp_db'

    # Conexión activa - Usa Supabase por defecto, o local si USE_LOCAL_DB está en True
    USE_LOCAL_DB = os.environ.get('USE_LOCAL_DB', 'False').lower() == 'true'

    SQLALCHEMY_DATABASE_URI = LOCAL_DB_URI if USE_LOCAL_DB else SUPABASE_DB_URI

    # Desactiva el sistema de seguimiento de modificaciones (ahorra recursos)
    SQLALCHEMY_TRACK_MODIFICATIONS = False