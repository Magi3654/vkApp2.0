# fix_models.py - Ejecutar en la carpeta del proyecto
# Este script limpia el archivo models.py

import re

# Leer el archivo
with open('app/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Eliminar líneas en blanco duplicadas
content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

# Buscar si hay clases duplicadas
lines = content.split('\n')
new_lines = []
seen_classes = set()
skip_until_next_class = False
current_class = None

i = 0
while i < len(lines):
    line = lines[i]
    
    # Detectar inicio de clase
    class_match = re.match(r'^class (\w+)\(', line)
    if class_match:
        class_name = class_match.group(1)
        if class_name in seen_classes:
            # Clase duplicada - saltar hasta la siguiente clase o fin
            skip_until_next_class = True
            i += 1
            continue
        else:
            seen_classes.add(class_name)
            skip_until_next_class = False
    
    if skip_until_next_class:
        # Verificar si encontramos otra clase
        if re.match(r'^class \w+\(', line) or re.match(r'^# =+', line):
            skip_until_next_class = False
        else:
            i += 1
            continue
    
    new_lines.append(line)
    i += 1

content = '\n'.join(new_lines)

# Corregir la relación usuario en Papeleta
old_relation = "usuario = db.relationship('Usuario', back_populates='papeletas')"
new_relation = "usuario = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='papeletas')"
content = content.replace(old_relation, new_relation)

# Eliminar campos duplicados de facturación (si los hay)
# Buscar y eliminar duplicados de facturada_por_id, etc.
lines = content.split('\n')
final_lines = []
seen_fields = set()
skip_duplicates = {'facturada_por_id', 'fecha_facturacion', 'aprobada_por_id', 'fecha_aprobacion'}

for line in lines:
    # Detectar definición de campo
    field_match = re.match(r'\s+(facturada_por_id|fecha_facturacion|aprobada_por_id|fecha_aprobacion)\s*=', line)
    if field_match:
        field_name = field_match.group(1)
        if field_name in seen_fields:
            continue  # Saltar duplicado
        seen_fields.add(field_name)
    final_lines.append(line)

content = '\n'.join(final_lines)

# Guardar archivo limpio
with open('app/models.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print('Archivo models.py limpiado y corregido')
print(f'Líneas finales: {len(final_lines)}')

# Verificar
try:
    import sys
    # Limpiar cache
    mods = [m for m in sys.modules.keys() if m.startswith('app')]
    for m in mods:
        del sys.modules[m]
    
    from app.models import Papeleta
    print(f'estatus_facturacion existe: {hasattr(Papeleta, "estatus_facturacion")}')
except Exception as e:
    print(f'Error al verificar: {e}')