--
-- Script de corrección para Supabase Database
-- Ejecutar en el SQL Editor de Supabase
--

-- ========================================
-- 1. ELIMINAR TABLAS NO UTILIZADAS
-- ========================================

DROP TABLE IF EXISTS public.aeropuertos_nacionales CASCADE;
DROP TABLE IF EXISTS public.reportes_procesados CASCADE;

-- ========================================
-- 2. CORREGIR PRECISIÓN DE COLUMNAS NUMERIC
-- ========================================

-- Tabla: cargos_servicio
ALTER TABLE public.cargos_servicio
  ALTER COLUMN monto TYPE numeric(10,2);

-- Tabla: descuentos
ALTER TABLE public.descuentos
  ALTER COLUMN valor TYPE numeric(10,2);

-- Tabla: tarifas_fijas
ALTER TABLE public.tarifas_fijas
  ALTER COLUMN monto TYPE numeric(10,2);

-- Tabla: desgloses
ALTER TABLE public.desgloses
  ALTER COLUMN tarifa_base TYPE numeric(10,2),
  ALTER COLUMN iva TYPE numeric(10,2),
  ALTER COLUMN tua TYPE numeric(10,2),
  ALTER COLUMN yr TYPE numeric(10,2),
  ALTER COLUMN otros_cargos TYPE numeric(10,2),
  ALTER COLUMN cargo_por_servicio TYPE numeric(10,2),
  ALTER COLUMN total TYPE numeric(10,2);

-- Tabla: papeletas
ALTER TABLE public.papeletas
  ALTER COLUMN total_ticket TYPE numeric(10,2),
  ALTER COLUMN diez_porciento TYPE numeric(10,2),
  ALTER COLUMN cargo TYPE numeric(10,2),
  ALTER COLUMN total TYPE numeric(10,2);

-- ========================================
-- 3. AGREGAR ON DELETE CASCADE A FOREIGN KEYS
-- ========================================

-- Tabla: cargos_servicio
ALTER TABLE public.cargos_servicio
  DROP CONSTRAINT IF EXISTS fk_empresa_cargos_servicio;

ALTER TABLE public.cargos_servicio
  ADD CONSTRAINT fk_empresa_cargos_servicio
  FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;

-- Tabla: descuentos
ALTER TABLE public.descuentos
  DROP CONSTRAINT IF EXISTS fk_empresa_descuentos;

ALTER TABLE public.descuentos
  ADD CONSTRAINT fk_empresa_descuentos
  FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;

-- Tabla: tarifas_fijas
ALTER TABLE public.tarifas_fijas
  DROP CONSTRAINT IF EXISTS fk_empresa_tarifas_fijas;

ALTER TABLE public.tarifas_fijas
  ADD CONSTRAINT fk_empresa_tarifas_fijas
  FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;

-- Tabla: papeletas
ALTER TABLE public.papeletas
  DROP CONSTRAINT IF EXISTS fk_empresa_papeletas;

ALTER TABLE public.papeletas
  ADD CONSTRAINT fk_empresa_papeletas
  FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;

-- Tabla: desgloses
ALTER TABLE public.desgloses
  DROP CONSTRAINT IF EXISTS fk_empresa;

ALTER TABLE public.desgloses
  ADD CONSTRAINT fk_empresa
  FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;

-- ========================================
-- 4. AGREGAR CHECK CONSTRAINTS
-- ========================================

-- Tabla: usuarios - validar rol
ALTER TABLE public.usuarios
  ADD CONSTRAINT usuarios_rol_check
  CHECK (rol IN ('administrador', 'agente', 'contabilidad'));

-- Tabla: cargos_servicio - validar tipo
ALTER TABLE public.cargos_servicio
  ADD CONSTRAINT cargos_servicio_tipo_check
  CHECK (tipo IN ('visible', 'oculto', 'mixto'));

-- Tabla: descuentos - validar tipo
ALTER TABLE public.descuentos
  ADD CONSTRAINT descuentos_tipo_check
  CHECK (tipo IN ('monto', 'porcentaje'));

-- ========================================
-- 5. INSERTAR DATOS INICIALES (ROLES)
-- ========================================

-- Insertar roles iniciales (usa ON CONFLICT para evitar duplicados)
INSERT INTO public.roles (nombre)
VALUES ('administrador')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO public.roles (nombre)
VALUES ('agente')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO public.roles (nombre)
VALUES ('contabilidad')
ON CONFLICT (nombre) DO NOTHING;

-- ========================================
-- 6. VERIFICACIÓN (OPCIONAL - COMENTAR PARA NO EJECUTAR)
-- ========================================

-- Verificar que los roles se insertaron correctamente
-- SELECT * FROM public.roles ORDER BY id;

-- Verificar constraints de usuarios
-- SELECT conname, contype, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'public.usuarios'::regclass;

-- Verificar constraints de cargos_servicio
-- SELECT conname, contype, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'public.cargos_servicio'::regclass;

-- ========================================
-- SCRIPT COMPLETADO
-- ========================================

-- Este script corrige:
-- ✅ Elimina tablas no utilizadas (aeropuertos_nacionales, reportes_procesados)
-- ✅ Agrega precisión numeric(10,2) a todas las columnas monetarias
-- ✅ Configura ON DELETE CASCADE en todas las FK de empresas
-- ✅ Agrega validaciones CHECK para roles y tipos
-- ✅ Inserta roles iniciales en la tabla roles
