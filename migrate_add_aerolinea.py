"""
Script para agregar columna aerolinea_id a la tabla papeletas
Ejecutar: python migrate_add_aerolinea.py
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Cargar variables de entorno ANTES de importar app
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), 'app', '.env')
load_dotenv(env_path)

from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Aplicando migración: Agregar aerolinea_id a papeletas...\n")

    try:
        # Verificar si la columna ya existe
        result = db.session.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='papeletas' AND column_name='aerolinea_id'
        """))

        if result.fetchone():
            print("AVISO: La columna aerolinea_id ya existe en la tabla papeletas.")
        else:
            # Agregar columna aerolinea_id
            db.session.execute(text("""
                ALTER TABLE public.papeletas
                ADD COLUMN aerolinea_id bigint;
            """))

            # Agregar constraint de foreign key
            db.session.execute(text("""
                ALTER TABLE public.papeletas
                ADD CONSTRAINT fk_papeletas_aerolinea
                FOREIGN KEY (aerolinea_id) REFERENCES public.aerolineas(id);
            """))

            # Crear índice
            db.session.execute(text("""
                CREATE INDEX idx_papeletas_aerolinea ON public.papeletas(aerolinea_id);
            """))

            db.session.commit()
            print("OK: Columna aerolinea_id agregada exitosamente a la tabla papeletas.")
            print("OK: Foreign key constraint agregado.")
            print("OK: Índice creado.")

    except Exception as e:
        db.session.rollback()
        print(f"ERROR: {str(e)}")
        sys.exit(1)

    print("\nMigración completada exitosamente!")
