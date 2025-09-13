--
-- PostgreSQL database dump (Versión Final, Corregida e Idempotente)
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- Limpiamos las tablas existentes antes de crearlas para evitar errores.
DROP TABLE IF EXISTS public.papeletas CASCADE;
DROP TABLE IF EXISTS public.desgloses CASCADE;
DROP TABLE IF EXISTS public.cargos_servicio CASCADE;
DROP TABLE IF EXISTS public.descuentos CASCADE;
DROP TABLE IF EXISTS public.tarifas_fijas CASCADE;
DROP TABLE IF EXISTS public.usuarios CASCADE;
DROP TABLE IF EXISTS public.empresas CASCADE;
DROP TABLE IF EXISTS public.roles CASCADE;
DROP TABLE IF EXISTS public.aerolineas CASCADE;
DROP TABLE IF EXISTS public.empresas_booking CASCADE;


SET default_tablespace = '';
SET default_table_access_method = heap;

--
-- Name: aerolineas; Type: TABLE; Schema: public;
--
CREATE TABLE public.aerolineas (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    nombre text NOT NULL,
    CONSTRAINT aerolineas_pkey PRIMARY KEY (id),
    CONSTRAINT aerolineas_nombre_key UNIQUE (nombre)
);

--
-- Name: empresas_booking; Type: TABLE; Schema: public;
--
CREATE TABLE public.empresas_booking (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    nombre text NOT NULL,
    CONSTRAINT empresas_booking_pkey PRIMARY KEY (id),
    CONSTRAINT empresas_booking_nombre_key UNIQUE (nombre)
);

--
-- Name: roles; Type: TABLE; Schema: public;
--
CREATE TABLE public.roles (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    nombre text NOT NULL,
    CONSTRAINT roles_pkey PRIMARY KEY (id),
    CONSTRAINT roles_nombre_key UNIQUE (nombre)
);

--
-- Name: empresas; Type: TABLE; Schema: public;
--
CREATE TABLE public.empresas (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    nombre_empresa text NOT NULL,
    CONSTRAINT empresas_pkey PRIMARY KEY (id)
);

--
-- Name: usuarios; Type: TABLE; Schema: public;
--
CREATE TABLE public.usuarios (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    nombre text NOT NULL,
    correo text NOT NULL,
    contrasena text NOT NULL,
    rol text NOT NULL,
    rol_id bigint,
    CONSTRAINT usuarios_pkey PRIMARY KEY (id),
    CONSTRAINT usuarios_correo_key UNIQUE (correo),
    CONSTRAINT fk_rol FOREIGN KEY (rol_id) REFERENCES public.roles(id),
    CONSTRAINT usuarios_rol_check CHECK ((rol = ANY (ARRAY['administrador'::text, 'agente'::text, 'contabilidad'::text])))
);

--
-- Name: desgloses; Type: TABLE; Schema: public;
--
CREATE TABLE public.desgloses (
    folio bigint NOT NULL,
    empresa_booking_id bigint NOT NULL,
    aerolinea_id bigint NOT NULL,
    tarifa_base numeric(10,2) NOT NULL,
    iva numeric(10,2) NOT NULL,
    tua numeric(10,2) NOT NULL,
    yr numeric(10,2) NOT NULL,
    otros_cargos numeric(10,2) NOT NULL,
    cargo_por_servicio numeric(10,2) NOT NULL,
    total numeric(10,2) NOT NULL,
    usuario_id bigint NOT NULL,
    empresa_id bigint NOT NULL,
    clave_reserva text NOT NULL,
    CONSTRAINT desgloses_pkey PRIMARY KEY (folio),
    CONSTRAINT fk_aerolinea FOREIGN KEY (aerolinea_id) REFERENCES public.aerolineas(id),
    CONSTRAINT fk_empresa FOREIGN KEY (empresa_id) REFERENCES public.empresas(id),
    CONSTRAINT fk_empresa_booking FOREIGN KEY (empresa_booking_id) REFERENCES public.empresas_booking(id),
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id)
);

--
-- Name: papeletas; Type: TABLE; Schema: public;
--
CREATE TABLE public.papeletas (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    folio text NOT NULL,
    tarjeta text NOT NULL,
    fecha_venta date NOT NULL,
    usuario_id bigint NOT NULL,
    total_ticket numeric(10,2) NOT NULL,
    diez_porciento numeric(10,2) NOT NULL,
    cargo numeric(10,2) NOT NULL,
    total numeric(10,2) NOT NULL,
    facturar_a text NOT NULL,
    solicito text NOT NULL,
    clave_sabre text NOT NULL,
    forma_pago text NOT NULL,
    empresa_id bigint,
    CONSTRAINT papeletas_pkey PRIMARY KEY (id),
    CONSTRAINT fk_empresa_papeletas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id),
    CONSTRAINT fk_usuario_papeletas FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id)
);

--
-- Name: cargos_servicio; Type: TABLE; Schema: public;
--
CREATE TABLE public.cargos_servicio (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    empresa_id bigint NOT NULL,
    tipo text NOT NULL,
    monto numeric(10,2) NOT NULL,
    CONSTRAINT cargos_servicio_pkey PRIMARY KEY (id),
    CONSTRAINT fk_empresa_cargos_servicio FOREIGN KEY (empresa_id) REFERENCES public.empresas(id),
    CONSTRAINT cargos_servicio_tipo_check CHECK ((tipo = ANY (ARRAY['visible'::text, 'oculto'::text, 'mixto'::text])))
);

--
-- Name: descuentos; Type: TABLE; Schema: public;
--
CREATE TABLE public.descuentos (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    empresa_id bigint NOT NULL,
    tipo text NOT NULL,
    valor numeric(10,2) NOT NULL,
    CONSTRAINT descuentos_pkey PRIMARY KEY (id),
    CONSTRAINT fk_empresa_descuentos FOREIGN KEY (empresa_id) REFERENCES public.empresas(id),
    CONSTRAINT descuentos_tipo_check CHECK ((tipo = ANY (ARRAY['monto'::text, 'porcentaje'::text])))
);

--
-- Name: tarifas_fijas; Type: TABLE; Schema: public;
--
CREATE TABLE public.tarifas_fijas (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    empresa_id bigint NOT NULL,
    monto numeric(10,2) NOT NULL,
    CONSTRAINT tarifas_fijas_pkey PRIMARY KEY (id),
    CONSTRAINT fk_empresa_tarifas_fijas FOREIGN KEY (empresa_id) REFERENCES public.empresas(id)
);

--
-- Data for Name: roles; Type: TABLE DATA; Schema: public;
--
INSERT INTO public.roles (id, nombre) OVERRIDING SYSTEM VALUE VALUES (1, 'administrador');
INSERT INTO public.roles (id, nombre) OVERRIDING SYSTEM VALUE VALUES (2, 'agente');
INSERT INTO public.roles (id, nombre) OVERRIDING SYSTEM VALUE VALUES (3, 'contabilidad');

--
-- PostgreSQL database dump complete
--

