# 🚀 Pasos para Configurar Supabase

## 📋 Checklist Rápido

### **1. Instalar dependencias**
```bash
pip install -r requirements.txt
```

### **2. Obtener credenciales de Supabase**

1. Ve a [Supabase Dashboard](https://app.supabase.com)
2. Selecciona tu proyecto
3. Click en **Settings** ⚙️ → **Database**
4. En **Connection String**, copia la URI que empieza con `postgresql://`

**Formato:**
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### **3. Ejecutar script de corrección en Supabase**

1. En Supabase Dashboard → **SQL Editor**
2. Abre el archivo `supabase_fix.sql`
3. Copia todo el contenido
4. Pégalo en SQL Editor
5. Click en **Run**

### **4. Actualizar archivo `.env`**

Edita `app/.env` (línea 17):

```env
SUPABASE_DB_URI=postgresql://postgres.XXXXXXXX:TU_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Reemplaza:
- `XXXXXXXX` → Tu PROJECT-REF
- `TU_PASSWORD` → Tu contraseña de Supabase

### **5. Probar la conexión**

```bash
python run.py
```

Si ves errores, verifica:
- ✅ La Connection String está correcta
- ✅ Ejecutaste `supabase_fix.sql`
- ✅ `python-dotenv` está instalado

---

## 🔄 Cambiar entre Supabase y Local

### Usar Supabase (por defecto):
```env
# En app/.env
USE_LOCAL_DB=False
```

### Usar PostgreSQL Local:
```env
# En app/.env
USE_LOCAL_DB=True
```

---

## ✅ Verificación

Ejecuta en Python:
```python
from app import create_app
from app.models import db, Rol

app = create_app()
with app.app_context():
    roles = Rol.query.all()
    print(f"Roles: {[r.nombre for r in roles]}")
```

Deberías ver: `Roles: ['administrador', 'agente', 'contabilidad']`

---

**¡Listo!** 🎉
