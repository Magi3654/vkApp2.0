"""
Script para insertar datos iniciales en las tablas auxiliares
Ejecutar: python seed_data.py
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
from app.models import db, Aerolinea, EmpresaBooking

app = create_app()

with app.app_context():
    print("Insertando datos iniciales...\n")

    # Aerolíneas comunes en México
    aerolineas = [
        'Aeroméxico',
        'Volaris',
        'Viva Aerobus',
        'Aeromar',
        'TAR Aerolíneas',
        'United Airlines',
        'American Airlines',
        'Delta Air Lines',
        'Copa Airlines',
        'Interjet'
    ]

    for nombre in aerolineas:
        # Verificar si ya existe
        existe = Aerolinea.query.filter_by(nombre=nombre).first()
        if not existe:
            nueva = Aerolinea(nombre=nombre)
            db.session.add(nueva)
            print(f"OK Aerolinea agregada: {nombre}")
        else:
            print(f"AVISO Ya existe: {nombre}")

    # Empresas Booking comunes
    empresas_booking = [
        'Amadeus',
        'Sabre',
        'Worldspan',
        'Galileo',
        'Directo Aerolínea',
        'Kiwi.com',
        'Booking.com',
        'Expedia',
        'Despegar'
    ]

    for nombre in empresas_booking:
        # Verificar si ya existe
        existe = EmpresaBooking.query.filter_by(nombre=nombre).first()
        if not existe:
            nueva = EmpresaBooking(nombre=nombre)
            db.session.add(nueva)
            print(f"OK Empresa Booking agregada: {nombre}")
        else:
            print(f"AVISO Ya existe: {nombre}")

    # Guardar cambios
    db.session.commit()

    print("\nDatos iniciales insertados correctamente!")
    print(f"   - Aerolineas: {Aerolinea.query.count()}")
    print(f"   - Empresas Booking: {EmpresaBooking.query.count()}")
