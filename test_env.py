import os
from dotenv import load_dotenv

# Cargar .env
env_path = os.path.join(os.path.dirname(__file__), 'app', '.env')
print(f"📂 Cargando .env desde: {env_path}")
print(f"   ¿Existe el archivo? {os.path.exists(env_path)}")

load_dotenv(env_path)

# Mostrar variables
print("\n📊 Variables de entorno cargadas:")
print(f"   SUPABASE_DB_URI: {os.environ.get('SUPABASE_DB_URI', 'NO ENCONTRADA')}")
print(f"   USE_LOCAL_DB: {os.environ.get('USE_LOCAL_DB', 'NO ENCONTRADA')}")
print(f"   SECRET_KEY: {os.environ.get('SECRET_KEY', 'NO ENCONTRADA')[:20]}...")

# Importar config
from config import Config
print("\n⚙️  Configuración de Flask:")
print(f"   USE_LOCAL_DB (bool): {Config.USE_LOCAL_DB}")
print(f"   SQLALCHEMY_DATABASE_URI:")
print(f"      {Config.SQLALCHEMY_DATABASE_URI}")
