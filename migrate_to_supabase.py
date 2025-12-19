"""
Script de migración de datos de PostgreSQL local a Supabase

Uso:
1. Asegúrate de que USE_LOCAL_DB=True en app/.env
2. Ejecuta: python migrate_to_supabase.py
3. Los datos se copiarán de local a Supabase
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(__file__), 'app', '.env')
load_dotenv(env_path)

# Configuración
LOCAL_DB_URI = 'postgresql://ilse:vkinessia2@localhost:5432/vkapp_db'
SUPABASE_DB_URI = os.environ.get('SUPABASE_DB_URI')

if not SUPABASE_DB_URI:
    print("❌ Error: SUPABASE_DB_URI no está configurado en app/.env")
    exit(1)

print("🔄 Iniciando migración de datos...")
print(f"   Origen: PostgreSQL Local")
print(f"   Destino: Supabase\n")

# Crear conexiones
print("📡 Conectando a bases de datos...")
try:
    local_engine = create_engine(LOCAL_DB_URI)
    supabase_engine = create_engine(SUPABASE_DB_URI)

    LocalSession = sessionmaker(bind=local_engine)
    SupabaseSession = sessionmaker(bind=supabase_engine)

    local_session = LocalSession()
    supabase_session = SupabaseSession()

    print("✅ Conexiones establecidas\n")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    exit(1)

# Lista de tablas en orden de dependencias
TABLES = [
    'roles',
    'aerolineas',
    'empresas_booking',
    'empresas',
    'usuarios',
    'cargos_servicio',
    'descuentos',
    'tarifas_fijas',
    'desgloses',
    'papeletas'
]

try:
    # Migrar cada tabla
    for table in TABLES:
        print(f"📦 Migrando tabla: {table}")

        # Contar registros en origen
        count_query = text(f"SELECT COUNT(*) FROM {table}")
        count = local_session.execute(count_query).scalar()

        if count == 0:
            print(f"   ⚠️  Tabla vacía, omitiendo...")
            continue

        print(f"   📊 Registros encontrados: {count}")

        # Obtener datos
        select_query = text(f"SELECT * FROM {table}")
        rows = local_session.execute(select_query).fetchall()

        if not rows:
            continue

        # Obtener nombres de columnas
        columns = rows[0]._mapping.keys()
        columns_str = ', '.join(columns)
        placeholders = ', '.join([f':{col}' for col in columns])

        # Insertar en Supabase (con ON CONFLICT para evitar duplicados)
        insert_query = text(f"""
            INSERT INTO {table} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """)

        inserted = 0
        for row in rows:
            try:
                supabase_session.execute(insert_query, dict(row._mapping))
                inserted += 1
            except Exception as e:
                print(f"   ⚠️  Error insertando registro: {e}")

        supabase_session.commit()
        print(f"   ✅ Insertados: {inserted}/{count}\n")

    print("\n🎉 Migración completada exitosamente!")
    print("\n⚙️  Pasos siguientes:")
    print("   1. Verifica los datos en Supabase Dashboard")
    print("   2. Cambia USE_LOCAL_DB=False en app/.env")
    print("   3. Reinicia la aplicación")

except Exception as e:
    print(f"\n❌ Error durante la migración: {e}")
    supabase_session.rollback()
    exit(1)
finally:
    local_session.close()
    supabase_session.close()
