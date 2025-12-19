# Migración: Agregar Aerolínea a Papeletas

## Cambios Realizados

Se ha reorganizado el formulario de papeletas:

1. **"Facturar a"** ahora es un selector de empresas (antes era texto libre)
2. Se agregó un nuevo campo **"Aerolínea"** para indicar con qué aerolínea se hace el cargo

## Aplicar la Migración a la Base de Datos

### Opción 1: Usando pgAdmin o interfaz gráfica de PostgreSQL

1. Abre pgAdmin u otra herramienta de PostgreSQL
2. Conéctate a la base de datos `vkapp_db`
3. Ejecuta el siguiente SQL:

```sql
-- Agregar columna aerolinea_id a la tabla papeletas
ALTER TABLE public.papeletas
ADD COLUMN aerolinea_id bigint;

-- Agregar constraint de foreign key
ALTER TABLE public.papeletas
ADD CONSTRAINT fk_papeletas_aerolinea
FOREIGN KEY (aerolinea_id) REFERENCES public.aerolineas(id);

-- Crear índice para mejorar el rendimiento
CREATE INDEX idx_papeletas_aerolinea ON public.papeletas(aerolinea_id);
```

### Opción 2: Usando psql desde línea de comandos

```bash
psql -U ilse -d vkapp_db -f add_aerolinea_to_papeletas.sql
```

### Opción 3: Conectarse manualmente y ejecutar

```bash
psql -U ilse -d vkapp_db
```

Luego copia y pega el SQL del archivo `add_aerolinea_to_papeletas.sql`

## Verificar que la migración se aplicó correctamente

Después de ejecutar la migración, verifica que la columna se agregó:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'papeletas'
ORDER BY ordinal_position;
```

Deberías ver la columna `aerolinea_id` de tipo `bigint`.

## Archivos Modificados

- `app/models.py` - Agregado campo `aerolinea_id` al modelo Papeleta
- `app/routes.py` - Actualizado para manejar aerolínea en papeletas
- `app/templates/papeletas.html` - "Facturar a" ahora es selector, agregado selector de aerolínea
- `app/templates/consulta_papeletas.html` - Muestra columna de aerolínea

## Después de Aplicar la Migración

1. Reinicia la aplicación Flask
2. Navega a "Nueva Papeleta"
3. Verás que "Facturar a" ahora es un selector de empresas
4. Verás el nuevo campo "Aerolínea" para seleccionar la aerolínea del cargo
