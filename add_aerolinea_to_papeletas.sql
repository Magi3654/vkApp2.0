-- Agregar columna aerolinea_id a la tabla papeletas
ALTER TABLE public.papeletas
ADD COLUMN aerolinea_id bigint;

-- Agregar constraint de foreign key
ALTER TABLE public.papeletas
ADD CONSTRAINT fk_papeletas_aerolinea
FOREIGN KEY (aerolinea_id) REFERENCES public.aerolineas(id);

-- Crear índice para mejorar el rendimiento de las consultas
CREATE INDEX idx_papeletas_aerolinea ON public.papeletas(aerolinea_id);

-- Mensaje de confirmación
SELECT 'Columna aerolinea_id agregada exitosamente a la tabla papeletas' AS resultado;
