/* 1. Permite a ilse usar el esquema público */
GRANT USAGE ON SCHEMA public TO ilse;

/* 2. Dale permiso total sobre TODAS las tablas actuales */
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ilse;

/* 3. Dale permiso sobre los contadores de ID (importante para crear nuevos usuarios) */
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ilse;