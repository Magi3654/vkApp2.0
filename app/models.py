# models.py - Kinessia Hub v2.0
# Modelos actualizados con nuevas tablas: Sucursales, Tarjetas, Autorizaciones, Créditos

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from datetime import datetime, date
from decimal import Decimal

db = SQLAlchemy()


# =============================================================================
# MODELOS DE AUTENTICACIÓN Y USUARIOS
# =============================================================================

class Sucursal(db.Model):
    """Sucursales para segregación de datos (Ensenada/Mexicali)"""
    __tablename__ = 'sucursales'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, unique=True, nullable=False)
    ciudad = db.Column(db.String, nullable=False)
    direccion = db.Column(db.String)
    telefono = db.Column(db.String)
    activa = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuarios = db.relationship('Usuario', back_populates='sucursal', lazy='dynamic')
    empresas = db.relationship('Empresa', back_populates='sucursal', lazy='dynamic')
    tarjetas = db.relationship('TarjetaCorporativa', back_populates='sucursal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Sucursal {self.nombre}>'


class Rol(db.Model):
    """Roles de usuario con niveles de permiso"""
    __tablename__ = 'roles'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, unique=True, nullable=False)
    descripcion = db.Column(db.String)
    permisos = db.Column(db.JSON, default={})
    nivel = db.Column(db.Integer, default=0)  # Para jerarquía de permisos
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    usuarios = db.relationship("Usuario", back_populates="rol_relacion")
    
    def __repr__(self):
        return f'<Rol {self.nombre}>'


class Usuario(UserMixin, db.Model):
    """Usuarios del sistema con sucursal asignada"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    correo = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column('contrasena', db.String(255), nullable=False)
    rol = db.Column(db.String, nullable=False)
    rol_id = db.Column(db.BigInteger, db.ForeignKey('roles.id'))
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    activo = db.Column(db.Boolean, default=True)
    telefono = db.Column(db.String)
    tipo_agente = db.Column(db.String)  # 'in_house' o 'home_office'
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    rol_relacion = db.relationship('Rol', back_populates='usuarios')
    sucursal = db.relationship('Sucursal', back_populates='usuarios')
    papeletas = db.relationship('Papeleta', foreign_keys='Papeleta.usuario_id', back_populates='usuario', lazy='dynamic')
    desgloses = db.relationship('Desglose', back_populates='usuario', lazy='dynamic')
    autorizaciones_solicitadas = db.relationship(
        'Autorizacion', 
        foreign_keys='Autorizacion.solicitante_id',
        back_populates='solicitante', 
        lazy='dynamic'
    )
    autorizaciones_aprobadas = db.relationship(
        'Autorizacion', 
        foreign_keys='Autorizacion.autorizador_id',
        back_populates='autorizador', 
        lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def es_admin(self):
        """Verifica si el usuario es administrador o director"""
        return self.rol in ['administrador', 'admin', 'director', 'sistemas']
    
    def es_gerente_o_superior(self):
        """Verifica si el usuario es gerente o tiene rol superior"""
        if self.rol_relacion:
            return self.rol_relacion.nivel >= 80
        return self.rol in ['administrador', 'admin', 'director', 'gerente', 'sistemas']
    
    def puede_acceder_sucursal(self, sucursal_id):
        """Verifica si el usuario puede acceder a datos de una sucursal"""
        if self.es_admin():
            return True
        return self.sucursal_id == sucursal_id
    
    def __repr__(self):
        return f'<Usuario {self.nombre}>'


# =============================================================================
# MODELOS DE EMPRESAS Y CONFIGURACIÓN
# =============================================================================

class Empresa(db.Model):
    """Empresas clientes (corporativos y gobierno)"""
    __tablename__ = 'empresas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre_empresa = db.Column(db.String, nullable=False)
    tipo_cliente = db.Column(db.String, default='corporativo')  # 'corporativo', 'gobierno', 'particular'
    rfc = db.Column(db.String)
    razon_social = db.Column(db.String)
    direccion_fiscal = db.Column(db.String)
    contacto_nombre = db.Column(db.String)
    contacto_email = db.Column(db.String)
    contacto_telefono = db.Column(db.String)
    
    # Campos de crédito
    limite_credito = db.Column(db.Numeric(12, 2), default=0)
    credito_disponible = db.Column(db.Numeric(12, 2), default=0)
    dias_credito = db.Column(db.Integer, default=0)
    credito_activo = db.Column(db.Boolean, default=False)
    
    # Especificaciones técnicas para licitaciones (JSONB)
    especificaciones_tecnicas = db.Column(db.JSON, default={})
    
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    sucursal = db.relationship('Sucursal', back_populates='empresas')
    papeletas = db.relationship('Papeleta', back_populates='empresa', cascade="all, delete-orphan")
    desgloses = db.relationship('Desglose', back_populates='empresa', cascade="all, delete-orphan")
    cargos_servicio = db.relationship('CargoServicio', back_populates='empresa', cascade="all, delete-orphan")
    descuentos = db.relationship('Descuento', back_populates='empresa', cascade="all, delete-orphan")
    tarifas_fijas = db.relationship('TarifaFija', back_populates='empresa', cascade="all, delete-orphan")
    creditos_movimientos = db.relationship('CreditoMovimiento', back_populates='empresa', lazy='dynamic')
    
    def credito_utilizado(self):
        """Retorna el crédito utilizado"""
        return float(self.limite_credito or 0) - float(self.credito_disponible or 0)
    
    def porcentaje_credito_utilizado(self):
        """Retorna el porcentaje de crédito utilizado"""
        if self.limite_credito and self.limite_credito > 0:
            return round((self.credito_utilizado() / float(self.limite_credito)) * 100, 2)
        return 0
    
    def tiene_credito_suficiente(self, monto):
        """Verifica si la empresa tiene crédito suficiente para un monto"""
        if not self.credito_activo:
            return True  # Si no tiene crédito activo, no aplica validación
        return float(self.credito_disponible or 0) >= monto
    
    def __repr__(self):
        return f'<Empresa {self.nombre_empresa}>'


class CargoServicio(db.Model):
    """Cargos por servicio por empresa"""
    __tablename__ = 'cargos_servicio'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)  # 'visible', 'oculto', 'mixto'
    tipo_servicio = db.Column(db.String)  # 'nacional', 'internacional', 'hotel', 'auto', 'otro'
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.String)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    empresa = db.relationship('Empresa', back_populates='cargos_servicio')


class Descuento(db.Model):
    """Descuentos por empresa"""
    __tablename__ = 'descuentos'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    
    empresa = db.relationship('Empresa', back_populates='descuentos')


class TarifaFija(db.Model):
    """Tarifas fijas por empresa"""
    __tablename__ = 'tarifas_fijas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, default='nacional')  # 'nacional', 'internacional', 'hotel', 'auto', 'otro'
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.String)
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    empresa = db.relationship('Empresa', back_populates='tarifas_fijas')


# =============================================================================
# MODELOS DE TARJETAS Y AUTORIZACIONES
# =============================================================================

class TarjetaCorporativa(db.Model):
    """Catálogo de tarjetas de crédito corporativas"""
    __tablename__ = 'tarjetas_corporativas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    numero_tarjeta = db.Column(db.String, unique=True, nullable=False)  # Últimos 4 dígitos o código
    nombre_tarjeta = db.Column(db.String, nullable=False)
    banco = db.Column(db.String)
    titular = db.Column(db.String)
    limite_credito = db.Column(db.Numeric(12, 2), default=0)
    fecha_corte = db.Column(db.Integer)  # Día del mes (1-31)
    fecha_pago = db.Column(db.Integer)   # Día del mes (1-31)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    activa = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    sucursal = db.relationship('Sucursal', back_populates='tarjetas')
    papeletas = db.relationship('Papeleta', back_populates='tarjeta_rel', lazy='dynamic')
    autorizaciones = db.relationship('Autorizacion', back_populates='tarjeta', lazy='dynamic')
    asignaciones = db.relationship('TarjetaUsuario', back_populates='tarjeta', lazy='dynamic')
    
    def requiere_autorizacion(self, usuario):
        """Verifica si un usuario necesita autorización para usar esta tarjeta"""
        # Primero verificar si tiene asignaciones específicas
        asignaciones_activas = TarjetaUsuario.query.filter_by(
            tarjeta_id=self.id, 
            activo=True
        ).all()
        
        if asignaciones_activas:
            # Si hay asignaciones, solo los usuarios asignados pueden usarla
            usuario_asignado = any(a.usuario_id == usuario.id for a in asignaciones_activas)
            return not usuario_asignado  # Requiere autorización si NO está asignado
        
        # Si no hay asignaciones específicas, usar lógica de sucursal
        if self.sucursal_id is None:
            return False
        return self.sucursal_id != usuario.sucursal_id
    
    def get_usuarios_asignados(self):
        """Retorna los usuarios asignados a esta tarjeta"""
        return [asig.usuario for asig in self.asignaciones if asig.activo]
    
    def __repr__(self):
        return f'<TarjetaCorporativa {self.nombre_tarjeta}>'


class TarjetaUsuario(db.Model):
    """Relación muchos a muchos entre tarjetas y usuarios"""
    __tablename__ = 'tarjetas_usuarios'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tarjeta_id = db.Column(db.BigInteger, db.ForeignKey('tarjetas_corporativas.id'), nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    asignado_por = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    fecha_asignacion = db.Column(db.DateTime(timezone=True), default=func.now())
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    tarjeta = db.relationship('TarjetaCorporativa', back_populates='asignaciones')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='tarjetas_asignadas')
    asignador = db.relationship('Usuario', foreign_keys=[asignado_por])
    
    def __repr__(self):
        return f'<TarjetaUsuario tarjeta={self.tarjeta_id} usuario={self.usuario_id}>'


class Autorizacion(db.Model):
    """Sistema de autorizaciones para excepciones"""
    __tablename__ = 'autorizaciones'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tipo = db.Column(db.String, nullable=False)  # 'uso_tarjeta', 'exceso_credito', 'descuento_especial', 'otro'
    solicitante_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    autorizador_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    
    # Referencias opcionales
    tarjeta_id = db.Column(db.BigInteger, db.ForeignKey('tarjetas_corporativas.id'))
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    
    motivo = db.Column(db.Text, nullable=False)
    monto_solicitado = db.Column(db.Numeric(12, 2))
    estatus = db.Column(db.String, default='pendiente', nullable=False)  # 'pendiente', 'aprobada', 'rechazada', 'expirada'
    
    fecha_solicitud = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    fecha_respuesta = db.Column(db.DateTime(timezone=True))
    comentario_respuesta = db.Column(db.Text)
    
    notificado_google_chat = db.Column(db.Boolean, default=False)
    token = db.Column(db.String(64))  # Token para autorización por email
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], back_populates='autorizaciones_solicitadas')
    autorizador = db.relationship('Usuario', foreign_keys=[autorizador_id], back_populates='autorizaciones_aprobadas')
    tarjeta = db.relationship('TarjetaCorporativa', back_populates='autorizaciones')
    sucursal = db.relationship('Sucursal')
    
    def aprobar(self, autorizador, comentario=None):
        """Aprueba la autorización"""
        self.estatus = 'aprobada'
        self.autorizador_id = autorizador.id
        self.fecha_respuesta = datetime.utcnow()
        self.comentario_respuesta = comentario
    
    def rechazar(self, autorizador, comentario=None):
        """Rechaza la autorización"""
        self.estatus = 'rechazada'
        self.autorizador_id = autorizador.id
        self.fecha_respuesta = datetime.utcnow()
        self.comentario_respuesta = comentario
    
    
    @staticmethod
    def generar_token():
        """Genera un token único para autorización por email"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def aprobar_por_token(self, usuario_id=None):
        """Aprueba la autorización usando token"""
        self.estatus = 'aprobada'
        self.autorizador_id = usuario_id
        self.fecha_respuesta = datetime.utcnow()
        self.comentario_respuesta = 'Aprobado via email'
    
    def rechazar_por_token(self, usuario_id=None):
        """Rechaza la autorización usando token"""
        self.estatus = 'rechazada'
        self.autorizador_id = usuario_id
        self.fecha_respuesta = datetime.utcnow()
        self.comentario_respuesta = 'Rechazado via email'
    
    def esta_vigente(self, horas=24):
        """Verifica si la autorización sigue vigente"""
        if self.estatus != 'aprobada':
            return False
        if not self.fecha_respuesta:
            return False
        from datetime import timedelta
        
        # Usar datetime con timezone para comparación correcta
        ahora = datetime.utcnow()
        fecha_resp = self.fecha_respuesta
        
        # Si fecha_respuesta tiene timezone, quitarlo para comparar
        if fecha_resp.tzinfo is not None:
            fecha_resp = fecha_resp.replace(tzinfo=None)
        
        return ahora < fecha_resp + timedelta(hours=horas)
    
    def __repr__(self):
        return f'<Autorizacion {self.id} - {self.tipo}>'


# =============================================================================
# MODELOS OPERATIVOS
# =============================================================================

class Aerolinea(db.Model):
    """Catálogo de aerolíneas"""
    __tablename__ = 'aerolineas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False, unique=True)
    codigo_iata = db.Column(db.String(2))
    codigo_icao = db.Column(db.String(3))
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    desgloses = db.relationship('Desglose', back_populates='aerolinea')
    papeletas = db.relationship('Papeleta', backref='aerolinea_rel')
    
    def __repr__(self):
        return f'<Aerolinea {self.nombre}>'


class EmpresaBooking(db.Model):
    """Empresas de booking/reservaciones"""
    __tablename__ = 'empresas_booking'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False, unique=True)
    
    desgloses = db.relationship('Desglose', back_populates='empresa_booking')
    
    def __repr__(self):
        return f'<EmpresaBooking {self.nombre}>'


class Desglose(db.Model):
    """Desgloses de boletos aéreos"""
    __tablename__ = 'desgloses'
    
    folio = db.Column(db.BigInteger, primary_key=True)
    empresa_booking_id = db.Column(db.BigInteger, db.ForeignKey('empresas_booking.id'), nullable=False)
    aerolinea_id = db.Column(db.BigInteger, db.ForeignKey('aerolineas.id'), nullable=False)
    tarifa_base = db.Column(db.Numeric(10, 2), nullable=False)
    iva = db.Column(db.Numeric(10, 2), nullable=False)
    tua = db.Column(db.Numeric(10, 2), nullable=False)
    yr = db.Column(db.Numeric(10, 2), nullable=False)
    otros_cargos = db.Column(db.Numeric(10, 2), nullable=False)
    cargo_por_servicio = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    clave_reserva = db.Column(db.String, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    
    # Nuevos campos
    numero_boleto = db.Column(db.String, unique=True)
    fecha_emision = db.Column(db.Date, default=datetime.utcnow)
    fecha_viaje = db.Column(db.Date)
    estatus = db.Column(db.String, default='pendiente')  # 'pendiente', 'emitido', 'cancelado', 'reembolsado'
    pasajero_nombre = db.Column(db.String)
    ruta = db.Column(db.String)  # Ej: "TIJ-MEX-TIJ"
    clase = db.Column(db.String)  # Económica, Ejecutiva, etc.
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    empresa_booking = db.relationship('EmpresaBooking', back_populates='desgloses')
    aerolinea = db.relationship('Aerolinea', back_populates='desgloses')
    usuario = db.relationship('Usuario', back_populates='desgloses')
    empresa = db.relationship('Empresa', back_populates='desgloses')
    sucursal = db.relationship('Sucursal')
    
    def __repr__(self):
        return f'<Desglose {self.folio}>'


class Papeleta(db.Model):
    """Papeletas de tarjeta de crédito"""
    __tablename__ = 'papeletas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    folio = db.Column(db.String, nullable=False, unique=True)
    tarjeta = db.Column(db.String, nullable=False)  # Campo legacy
    tarjeta_id = db.Column(db.BigInteger, db.ForeignKey('tarjetas_corporativas.id'))
    fecha_venta = db.Column(db.Date, nullable=False)
    total_ticket = db.Column(db.Numeric(10, 2), nullable=False)
    diez_porciento = db.Column(db.Numeric(10, 2), nullable=False)
    cargo = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    facturar_a = db.Column(db.String, nullable=False)
    solicito = db.Column(db.String, nullable=False)
    clave_sabre = db.Column(db.String, nullable=False)
    forma_pago = db.Column(db.String, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    aerolinea_id = db.Column(db.BigInteger, db.ForeignKey('aerolineas.id'))
    tipo_cargo = db.Column(db.String(50))  # 'aerolinea', 'hotel', 'auto', 'otro'
    proveedor = db.Column(db.String(255))   # Nombre del hotel, rentadora, etc.
    
    # Campos para papeletas extemporáneas
    extemporanea = db.Column(db.Boolean, default=False)
    motivo_extemporanea = db.Column(db.Text)
    fecha_cargo_real = db.Column(db.Date)  # Fecha real del cargo a la tarjeta
    
    # Campos para reembolsos
    tiene_reembolso = db.Column(db.Boolean, default=False)
    estatus_reembolso = db.Column(db.String(50))  # 'pendiente', 'en_proceso', 'completado', 'rechazado'
    motivo_reembolso = db.Column(db.Text)
    monto_reembolso = db.Column(db.Numeric(10, 2))
    fecha_solicitud_reembolso = db.Column(db.Date)
    fecha_reembolso = db.Column(db.Date)
    referencia_reembolso = db.Column(db.String(100))
    papeleta_relacionada_id = db.Column(db.BigInteger, db.ForeignKey('papeletas.id'))
    
    # Nuevos campos
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    autorizacion_id = db.Column(db.BigInteger, db.ForeignKey('autorizaciones.id'))
    conciliada = db.Column(db.Boolean, default=False)
    fecha_conciliacion = db.Column(db.Date)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    reporte_venta_id = db.Column(db.BigInteger, db.ForeignKey('reportes_ventas.id'))
    numero_factura = db.Column(db.String(50))  # Número de factura asignada
    archivo_boleto = db.Column(db.String(255))  # Nombre del archivo PDF del boleto
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # Campos de control de papeletas (agregar después de los otros campos)
    estatus_control = db.Column(db.String(20), default='activa')
    justificacion_pendiente = db.Column(db.Text)
    fecha_justificacion = db.Column(db.DateTime)
    revisada_por_id = db.Column(db.BigInteger)  # Sin FK para evitar conflicto
    fecha_revision = db.Column(db.DateTime)
    cerrada_por_id = db.Column(db.BigInteger)   # Sin FK para evitar conflicto
    fecha_cierre = db.Column(db.DateTime)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='papeletas')
    empresa = db.relationship('Empresa', back_populates='papeletas')
    aerolinea = db.relationship('Aerolinea')
    tarjeta_rel = db.relationship('TarjetaCorporativa', back_populates='papeletas')
    autorizacion = db.relationship('Autorizacion')
    sucursal = db.relationship('Sucursal')
    papeleta_relacionada = db.relationship('Papeleta', remote_side=[id], backref='papeletas_vinculadas')
    reporte_venta = db.relationship('ReporteVenta', backref='papeletas')
    
    def __repr__(self):
        return f'<Papeleta {self.folio}>'


# =============================================================================
# MODELOS DE CRÉDITO Y PAGOS
# =============================================================================

class CreditoMovimiento(db.Model):
    """Historial de movimientos de crédito por empresa"""
    __tablename__ = 'creditos_movimientos'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)  # 'cargo', 'abono', 'ajuste', 'inicial'
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    saldo_anterior = db.Column(db.Numeric(12, 2), nullable=False)
    saldo_nuevo = db.Column(db.Numeric(12, 2), nullable=False)
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    comprobante_id = db.Column(db.BigInteger, db.ForeignKey('comprobantes_pago.id'))
    concepto = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    empresa = db.relationship('Empresa', back_populates='creditos_movimientos')
    usuario = db.relationship('Usuario')
    sucursal = db.relationship('Sucursal')
    
    def __repr__(self):
        return f'<CreditoMovimiento {self.id} - {self.tipo}>'


class ComprobantePago(db.Model):
    """Comprobantes de pago adjuntos"""
    __tablename__ = 'comprobantes_pago'
    
    id = db.Column(db.BigInteger, primary_key=True)
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    papeleta_id = db.Column(db.BigInteger, db.ForeignKey('papeletas.id'))
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    tipo = db.Column(db.String, nullable=False)  # 'transferencia', 'deposito', 'cheque', 'otro'
    archivo_url = db.Column(db.String, nullable=False)
    archivo_nombre = db.Column(db.String, nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    referencia = db.Column(db.String)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    agente_notificado = db.Column(db.Boolean, default=False)
    fecha_notificacion = db.Column(db.DateTime(timezone=True))
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuario = db.relationship('Usuario')
    empresa = db.relationship('Empresa')
    sucursal = db.relationship('Sucursal')
    
    def __repr__(self):
        return f'<ComprobantePago {self.id}>'


# =============================================================================
# MODELOS DE AUDITORÍA Y NOTIFICACIONES
# =============================================================================

class AuditLog(db.Model):
    """Registro de auditoría de acciones"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tabla_nombre = db.Column(db.String, nullable=False)
    registro_id = db.Column(db.String, nullable=False)
    accion = db.Column(db.String, nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    datos_anteriores = db.Column(db.JSON)
    datos_nuevos = db.Column(db.JSON)
    campos_modificados = db.Column(db.ARRAY(db.String))
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    usuario_email = db.Column(db.String)
    ip_address = db.Column(db.String)
    user_agent = db.Column(db.String)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    def __repr__(self):
        return f'<AuditLog {self.id} - {self.accion}>'


class Notificacion(db.Model):
    """Cola de notificaciones para webhooks"""
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tipo = db.Column(db.String, nullable=False)  # 'autorizacion_solicitada', 'autorizacion_respondida', etc.
    destinatario = db.Column(db.String, nullable=False)
    canal = db.Column(db.String, default='google_chat', nullable=False)
    titulo = db.Column(db.String, nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    payload = db.Column(db.JSON)
    autorizacion_id = db.Column(db.BigInteger, db.ForeignKey('autorizaciones.id'))
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    estatus = db.Column(db.String, default='pendiente', nullable=False)  # 'pendiente', 'enviada', 'fallida'
    intentos = db.Column(db.Integer, default=0)
    ultimo_error = db.Column(db.Text)
    fecha_programada = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    fecha_enviada = db.Column(db.DateTime(timezone=True))
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    def __repr__(self):
        return f'<Notificacion {self.id} - {self.tipo}>'
    # =============================================================================
# MODELOS DE REPORTES DE VENTAS
# Agregar al final de models.py
# =============================================================================

class ReporteVenta(db.Model):
    """Reporte de ventas diario por agente"""
    __tablename__ = 'reportes_ventas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    folio = db.Column(db.String(20), unique=True)
    fecha = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    
    # Totales por tipo de boleto
    total_bsp = db.Column(db.Numeric(12, 2), default=0)
    total_volaris = db.Column(db.Numeric(12, 2), default=0)
    total_vivaerobus = db.Column(db.Numeric(12, 2), default=0)
    total_compra_tc = db.Column(db.Numeric(12, 2), default=0)
    
    # Otros cargos
    total_cargo_expedicion = db.Column(db.Numeric(12, 2), default=0)
    total_cargo_315 = db.Column(db.Numeric(12, 2), default=0)
    total_seguros = db.Column(db.Numeric(12, 2), default=0)
    total_hoteles_paquetes = db.Column(db.Numeric(12, 2), default=0)
    total_transporte_terrestre = db.Column(db.Numeric(12, 2), default=0)
    
    # Formas de pago
    total_pago_directo_tc = db.Column(db.Numeric(12, 2), default=0)
    total_voucher_tc = db.Column(db.Numeric(12, 2), default=0)
    total_efectivo = db.Column(db.Numeric(12, 2), default=0)
    total_general = db.Column(db.Numeric(12, 2), default=0)
    
    # Depósitos
    deposito_pesos_efectivo = db.Column(db.Numeric(12, 2), default=0)
    deposito_dolares_efectivo = db.Column(db.Numeric(12, 2), default=0)
    deposito_pesos_cheques = db.Column(db.Numeric(12, 2), default=0)
    tipo_cambio = db.Column(db.Numeric(8, 4), default=0)
    cuenta_deposito = db.Column(db.String(50))
    
    # Contadores
    total_boletos = db.Column(db.Integer, default=0)
    total_recibos = db.Column(db.Integer, default=0)
    
    # Control
    estatus = db.Column(db.String(20), default='borrador')
    fecha_envio = db.Column(db.DateTime(timezone=True))
    fecha_aprobacion = db.Column(db.DateTime(timezone=True))
    aprobado_por = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    notas = db.Column(db.Text)
    
    # Auditoría
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='reportes_ventas')
    sucursal = db.relationship('Sucursal', backref='reportes_ventas')
    aprobador = db.relationship('Usuario', foreign_keys=[aprobado_por])
    detalles = db.relationship('DetalleReporteVenta', back_populates='reporte', cascade='all, delete-orphan', lazy='dynamic')
    
    def __repr__(self):
        return f'<ReporteVenta {self.folio}>'
    
    @property
    def puede_editar(self):
        return self.estatus == 'borrador'
    
    @property
    def puede_enviar(self):
        return self.estatus == 'borrador' and self.total_recibos > 0


class DetalleReporteVenta(db.Model):
    """Líneas de detalle del reporte de ventas"""
    __tablename__ = 'detalle_reporte_ventas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    reporte_id = db.Column(db.BigInteger, db.ForeignKey('reportes_ventas.id', ondelete='CASCADE'), nullable=False)
    papeleta_id = db.Column(db.BigInteger, db.ForeignKey('papeletas.id'))
    
    # Datos de la línea
    clave_aerolinea = db.Column(db.String(10))
    num_boletos = db.Column(db.Integer, default=1)
    reserva = db.Column(db.String(20))
    num_recibo = db.Column(db.String(20))
    num_papeleta = db.Column(db.String(20))
    
    # Costos por tipo
    monto_bsp = db.Column(db.Numeric(12, 2), default=0)
    monto_volaris = db.Column(db.Numeric(12, 2), default=0)
    monto_vivaerobus = db.Column(db.Numeric(12, 2), default=0)
    monto_compra_tc = db.Column(db.Numeric(12, 2), default=0)
    
    # Otros cargos
    cargo_expedicion = db.Column(db.Numeric(12, 2), default=0)
    cargo_315 = db.Column(db.Numeric(12, 2), default=0)
    monto_seguros = db.Column(db.Numeric(12, 2), default=0)
    monto_hoteles_paquetes = db.Column(db.Numeric(12, 2), default=0)
    monto_transporte_terrestre = db.Column(db.Numeric(12, 2), default=0)
    
    # Forma de pago
    pago_directo_tc = db.Column(db.Numeric(12, 2), default=0)
    voucher_tc = db.Column(db.Numeric(12, 2), default=0)
    efectivo = db.Column(db.Numeric(12, 2), default=0)
    total_linea = db.Column(db.Numeric(12, 2), default=0)
    
    orden = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    reporte = db.relationship('ReporteVenta', back_populates='detalles')
    papeleta = db.relationship('Papeleta', backref='detalle_reporte')
    
    def __repr__(self):
        return f'<DetalleReporte {self.id} - {self.num_papeleta}>'


# models_entregas.py
# Modelos para el Sistema de Entregas de Corte
# Flujo: Agente → Administrativo → Encargado Depósitos → Director




class EntregaCorte(db.Model):
    """
    Registro de entrega de corte de caja.
    Representa el vale de entrega que genera cada agente al cerrar su turno.
    """
    __tablename__ = 'entregas_corte'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificación
    folio = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    fecha_hora_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Quien entrega (Agente)
    agente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey('sucursales.id'))
    
    # Reporte de ventas asociado
    reporte_venta_id = db.Column(db.Integer, db.ForeignKey('reportes_ventas.id'))
    
    # Montos a entregar
    efectivo_pesos = db.Column(db.Numeric(12, 2), default=0)
    efectivo_dolares = db.Column(db.Numeric(12, 2), default=0)
    tipo_cambio = db.Column(db.Numeric(10, 4), default=0)
    equivalente_pesos = db.Column(db.Numeric(12, 2), default=0)
    cheques = db.Column(db.Numeric(12, 2), default=0)
    vouchers_tc = db.Column(db.Numeric(12, 2), default=0)
    
    # Total físico a entregar
    total_fisico = db.Column(db.Numeric(12, 2), default=0)
    
    # Estatus del flujo
    estatus = db.Column(db.String(20), default='pendiente')
    # pendiente → entregado → en_custodia → depositado → revisado
    
    # Paso 1: Entrega a Administrativo
    recibido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_recepcion = db.Column(db.DateTime)
    firma_agente = db.Column(db.Text)
    firma_receptor = db.Column(db.Text)
    notas_entrega = db.Column(db.Text)
    
    # Paso 2: Retiro por Encargado de Depósitos
    retirado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_retiro = db.Column(db.DateTime)
    firma_retiro = db.Column(db.Text)
    notas_retiro = db.Column(db.Text)
    
    # Paso 3: Depósito en banco
    depositado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_deposito = db.Column(db.DateTime)
    cuenta_deposito = db.Column(db.String(100))
    referencia_deposito = db.Column(db.String(100))
    comprobante_deposito = db.Column(db.Text)
    notas_deposito = db.Column(db.Text)
    
    # Paso 4: Revisión por Director
    revisado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_revision = db.Column(db.DateTime)
    aprobado = db.Column(db.Boolean, default=False)
    notas_revision = db.Column(db.Text)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    agente = db.relationship('Usuario', foreign_keys=[agente_id], backref='entregas_realizadas')
    receptor = db.relationship('Usuario', foreign_keys=[recibido_por_id], backref='entregas_recibidas')
    encargado_retiro = db.relationship('Usuario', foreign_keys=[retirado_por_id], backref='entregas_retiradas')
    encargado_deposito = db.relationship('Usuario', foreign_keys=[depositado_por_id], backref='entregas_depositadas')
    revisor = db.relationship('Usuario', foreign_keys=[revisado_por_id], backref='entregas_revisadas')
    reporte_venta = db.relationship('ReporteVenta', backref='entrega_corte')
    sucursal = db.relationship('Sucursal', backref='entregas')
    detalles_arqueo = db.relationship('DetalleArqueo', backref='entrega', lazy='dynamic', cascade='all, delete-orphan')
    historial = db.relationship('HistorialEntrega', backref='entrega', lazy='dynamic', cascade='all, delete-orphan', order_by='HistorialEntrega.fecha_hora.desc()')
    
    def __repr__(self):
        return f'<EntregaCorte {self.folio}>'
    
    @staticmethod
    def generar_folio():
        """Genera folio automático EC-YYYY-NNNN"""
        anio = date.today().strftime('%Y')
        ultimo = EntregaCorte.query.filter(
            EntregaCorte.folio.like(f'EC-{anio}-%')
        ).order_by(EntregaCorte.id.desc()).first()
        
        if ultimo:
            try:
                num = int(ultimo.folio.split('-')[-1]) + 1
            except:
                num = 1
        else:
            num = 1
        
        return f'EC-{anio}-{num:04d}'
    
    def calcular_totales(self):
        """Calcula equivalente en pesos y total físico"""
        self.equivalente_pesos = float(self.efectivo_dolares or 0) * float(self.tipo_cambio or 0)
        self.total_fisico = (
            float(self.efectivo_pesos or 0) + 
            float(self.cheques or 0) + 
            self.equivalente_pesos
        )
    
    def registrar_historial(self, accion, usuario_id, estatus_anterior=None, notas=None, ip=None):
        """Registra un movimiento en el historial"""
        historial = HistorialEntrega(
            entrega_id=self.id,
            accion=accion,
            usuario_id=usuario_id,
            estatus_anterior=estatus_anterior,
            estatus_nuevo=self.estatus,
            notas=notas,
            ip_address=ip
        )
        db.session.add(historial)
    
    # Métodos de transición de estatus
    def entregar_a_admin(self, receptor_id, notas=None):
        """Paso 1: Agente entrega a administrativo"""
        estatus_anterior = self.estatus
        self.estatus = 'entregado'
        self.recibido_por_id = receptor_id
        self.fecha_recepcion = datetime.utcnow()
        self.firma_receptor = 'CONFIRMADO'
        self.notas_entrega = notas
        self.registrar_historial('entregado', receptor_id, estatus_anterior, notas)
    
    def confirmar_custodia(self, admin_id, notas=None):
        """Administrativo confirma que tiene el dinero en custodia"""
        estatus_anterior = self.estatus
        self.estatus = 'en_custodia'
        self.registrar_historial('en_custodia', admin_id, estatus_anterior, notas)
    
    def retirar_para_deposito(self, encargado_id, notas=None):
        """Paso 2: Encargado de depósitos retira el dinero"""
        estatus_anterior = self.estatus
        self.estatus = 'retirado'
        self.retirado_por_id = encargado_id
        self.fecha_retiro = datetime.utcnow()
        self.firma_retiro = 'CONFIRMADO'
        self.notas_retiro = notas
        self.registrar_historial('retirado', encargado_id, estatus_anterior, notas)
    
    def registrar_deposito(self, encargado_id, cuenta, referencia, notas=None):
        """Paso 3: Registrar el depósito bancario"""
        estatus_anterior = self.estatus
        self.estatus = 'depositado'
        self.depositado_por_id = encargado_id
        self.fecha_deposito = datetime.utcnow()
        self.cuenta_deposito = cuenta
        self.referencia_deposito = referencia
        self.notas_deposito = notas
        self.registrar_historial('depositado', encargado_id, estatus_anterior, f'Cuenta: {cuenta}, Ref: {referencia}')
    
    def revisar_y_aprobar(self, director_id, aprobado=True, notas=None):
        """Paso 4: Director revisa y cierra"""
        estatus_anterior = self.estatus
        self.estatus = 'revisado'
        self.revisado_por_id = director_id
        self.fecha_revision = datetime.utcnow()
        self.aprobado = aprobado
        self.notas_revision = notas
        accion = 'aprobado' if aprobado else 'rechazado'
        self.registrar_historial(accion, director_id, estatus_anterior, notas)
    
    @property
    def puede_entregar(self):
        """Verifica si se puede entregar (solo en estatus pendiente)"""
        return self.estatus == 'pendiente'
    
    @property
    def puede_retirar(self):
        """Verifica si se puede retirar (en custodia o entregado)"""
        return self.estatus in ['entregado', 'en_custodia']
    
    @property
    def puede_depositar(self):
        """Verifica si se puede registrar depósito"""
        return self.estatus == 'retirado'
    
    @property
    def puede_revisar(self):
        """Verifica si puede ser revisado por director"""
        return self.estatus == 'depositado'
    
    @property
    def estatus_badge(self):
        """Retorna clase CSS para badge según estatus"""
        badges = {
            'pendiente': 'warning',
            'entregado': 'info',
            'en_custodia': 'primary',
            'retirado': 'secondary',
            'depositado': 'success',
            'revisado': 'dark'
        }
        return badges.get(self.estatus, 'secondary')
    
    @property
    def estatus_descripcion(self):
        """Descripción amigable del estatus"""
        descripciones = {
            'pendiente': 'Pendiente de entrega',
            'entregado': 'Entregado a Admin',
            'en_custodia': 'En custodia',
            'retirado': 'Retirado para depósito',
            'depositado': 'Depositado - Pendiente revisión',
            'revisado': 'Revisado y cerrado'
        }
        return descripciones.get(self.estatus, self.estatus)
    
    def to_dict(self):
        """Serializa a diccionario para API"""
        return {
            'id': self.id,
            'folio': self.folio,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'agente': self.agente.nombre if self.agente else None,
            'efectivo_pesos': float(self.efectivo_pesos or 0),
            'efectivo_dolares': float(self.efectivo_dolares or 0),
            'tipo_cambio': float(self.tipo_cambio or 0),
            'equivalente_pesos': float(self.equivalente_pesos or 0),
            'cheques': float(self.cheques or 0),
            'vouchers_tc': float(self.vouchers_tc or 0),
            'total_fisico': float(self.total_fisico or 0),
            'estatus': self.estatus,
            'estatus_descripcion': self.estatus_descripcion,
            'receptor': self.receptor.nombre if self.receptor else None,
            'fecha_recepcion': self.fecha_recepcion.isoformat() if self.fecha_recepcion else None
        }


class DetalleArqueo(db.Model):
    """Detalle de denominaciones para arqueo de caja"""
    __tablename__ = 'detalle_arqueo'
    
    id = db.Column(db.Integer, primary_key=True)
    entrega_id = db.Column(db.Integer, db.ForeignKey('entregas_corte.id', ondelete='CASCADE'), nullable=False)
    
    tipo = db.Column(db.String(10), nullable=False)  # 'billete', 'moneda', 'dolar'
    denominacion = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Integer, default=0)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DetalleArqueo {self.tipo} ${self.denominacion} x{self.cantidad}>'
    
    def calcular_subtotal(self):
        self.subtotal = float(self.denominacion or 0) * (self.cantidad or 0)


class HistorialEntrega(db.Model):
    """Bitácora de movimientos de entregas"""
    __tablename__ = 'historial_entregas'
    
    id = db.Column(db.Integer, primary_key=True)
    entrega_id = db.Column(db.Integer, db.ForeignKey('entregas_corte.id', ondelete='CASCADE'), nullable=False)
    
    accion = db.Column(db.String(50), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    estatus_anterior = db.Column(db.String(20))
    estatus_nuevo = db.Column(db.String(20))
    notas = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    usuario = db.relationship('Usuario', backref='acciones_entregas')
    
    def __repr__(self):
        return f'<HistorialEntrega {self.accion} - {self.fecha_hora}>'
    
    @property
    def accion_descripcion(self):
        """Descripción amigable de la acción"""
        descripciones = {
            'creado': 'Vale creado',
            'entregado': 'Entregado a administrativo',
            'en_custodia': 'Confirmado en custodia',
            'retirado': 'Retirado para depósito',
            'depositado': 'Depósito registrado',
            'aprobado': 'Aprobado por dirección',
            'rechazado': 'Rechazado por dirección'
        }
        return descripciones.get(self.accion, self.accion)


# ============================================================
# Funciones auxiliares
# ============================================================

def crear_entrega_desde_reporte(reporte, usuario_id):
    """
    Crea una entrega de corte a partir de un reporte de ventas.
    
    Args:
        reporte: Objeto ReporteVenta
        usuario_id: ID del usuario que crea la entrega
    
    Returns:
        EntregaCorte: Nueva entrega creada
    """
    entrega = EntregaCorte(
        folio=EntregaCorte.generar_folio(),
        fecha=reporte.fecha,
        agente_id=reporte.usuario_id,
        sucursal_id=reporte.sucursal_id if hasattr(reporte, 'sucursal_id') else None,
        reporte_venta_id=reporte.id,
        efectivo_pesos=float(reporte.total_efectivo or 0) - (float(reporte.deposito_dolares_efectivo or 0) * float(reporte.tipo_cambio or 0)),
        efectivo_dolares=float(reporte.deposito_dolares_efectivo or 0),
        tipo_cambio=float(reporte.tipo_cambio or 0),
        cheques=float(reporte.deposito_pesos_cheques or 0),
        vouchers_tc=float(reporte.total_voucher_tc or 0),
        estatus='pendiente'
    )
    
    entrega.calcular_totales()
    
    db.session.add(entrega)
    db.session.flush()  # Para obtener el ID
    
    # Registrar en historial
    entrega.registrar_historial('creado', usuario_id, None, f'Creado desde reporte {reporte.folio}')
    
    return entrega


def obtener_entregas_por_rol(usuario):
    """
    Obtiene las entregas relevantes según el rol del usuario.
    
    Args:
        usuario: Objeto Usuario con método es_admin(), es_director(), etc.
    
    Returns:
        Query de entregas filtradas
    """
    query = EntregaCorte.query
    
    if hasattr(usuario, 'es_director') and usuario.es_director():
        # Director ve todas, especialmente las pendientes de revisión
        return query.order_by(EntregaCorte.fecha.desc())
    
    elif hasattr(usuario, 'es_admin') and usuario.es_admin():
        # Admin ve las que debe recibir y las que tiene en custodia
        return query.filter(
            db.or_(
                EntregaCorte.estatus == 'pendiente',
                EntregaCorte.estatus == 'entregado',
                EntregaCorte.recibido_por_id == usuario.id
            )
        ).order_by(EntregaCorte.fecha.desc())
    
    elif hasattr(usuario, 'puede_depositar') and usuario.puede_depositar:
        # Encargado de depósitos ve las que puede retirar y depositar
        return query.filter(
            db.or_(
                EntregaCorte.estatus.in_(['en_custodia', 'retirado']),
                EntregaCorte.retirado_por_id == usuario.id
            )
        ).order_by(EntregaCorte.fecha.desc())
    
    else:
        # Agente solo ve sus propias entregas
        return query.filter(
            EntregaCorte.agente_id == usuario.id
        ).order_by(EntregaCorte.fecha.desc())# models.py - Kinessia Hub v2.0
# Modelos actualizados con nuevas tablas: Sucursales, Tarjetas, Autorizaciones, Créditos

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from datetime import datetime, date
from decimal import Decimal

db = SQLAlchemy()


# =============================================================================
# MODELOS DE AUTENTICACIÓN Y USUARIOS
# =============================================================================

class Sucursal(db.Model):
    """Sucursales para segregación de datos (Ensenada/Mexicali)"""
    __tablename__ = 'sucursales'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, unique=True, nullable=False)
    ciudad = db.Column(db.String, nullable=False)
    direccion = db.Column(db.String)
    telefono = db.Column(db.String)
    activa = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuarios = db.relationship('Usuario', back_populates='sucursal', lazy='dynamic')
    empresas = db.relationship('Empresa', back_populates='sucursal', lazy='dynamic')
    tarjetas = db.relationship('TarjetaCorporativa', back_populates='sucursal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Sucursal {self.nombre}>'


class Rol(db.Model):
    """Roles de usuario con niveles de permiso"""
    __tablename__ = 'roles'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, unique=True, nullable=False)
    descripcion = db.Column(db.String)
    permisos = db.Column(db.JSON, default={})
    nivel = db.Column(db.Integer, default=0)  # Para jerarquía de permisos
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    usuarios = db.relationship("Usuario", back_populates="rol_relacion")
    
    def __repr__(self):
        return f'<Rol {self.nombre}>'


class Usuario(UserMixin, db.Model):
    """Usuarios del sistema con sucursal asignada"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    correo = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column('contrasena', db.String(255), nullable=False)
    rol = db.Column(db.String, nullable=False)
    rol_id = db.Column(db.BigInteger, db.ForeignKey('roles.id'))
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    activo = db.Column(db.Boolean, default=True)
    telefono = db.Column(db.String)
    tipo_agente = db.Column(db.String)  # 'in_house' o 'home_office'
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    rol_relacion = db.relationship('Rol', back_populates='usuarios')
    sucursal = db.relationship('Sucursal', back_populates='usuarios')
    papeletas = db.relationship('Papeleta', foreign_keys='Papeleta.usuario_id', back_populates='usuario', lazy='dynamic')
    desgloses = db.relationship('Desglose', back_populates='usuario', lazy='dynamic')
    autorizaciones_solicitadas = db.relationship(
        'Autorizacion', 
        foreign_keys='Autorizacion.solicitante_id',
        back_populates='solicitante', 
        lazy='dynamic'
    )
    autorizaciones_aprobadas = db.relationship(
        'Autorizacion', 
        foreign_keys='Autorizacion.autorizador_id',
        back_populates='autorizador', 
        lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def es_admin(self):
        """Verifica si el usuario es administrador o director"""
        return self.rol in ['administrador', 'admin', 'director', 'sistemas']
    
    def es_gerente_o_superior(self):
        """Verifica si el usuario es gerente o tiene rol superior"""
        if self.rol_relacion:
            return self.rol_relacion.nivel >= 80
        return self.rol in ['administrador', 'admin', 'director', 'gerente', 'sistemas']
    
    def puede_acceder_sucursal(self, sucursal_id):
        """Verifica si el usuario puede acceder a datos de una sucursal"""
        if self.es_admin():
            return True
        return self.sucursal_id == sucursal_id
    
    def __repr__(self):
        return f'<Usuario {self.nombre}>'


# =============================================================================
# MODELOS DE EMPRESAS Y CONFIGURACIÓN
# =============================================================================

class Empresa(db.Model):
    """Empresas clientes (corporativos y gobierno)"""
    __tablename__ = 'empresas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre_empresa = db.Column(db.String, nullable=False)
    tipo_cliente = db.Column(db.String, default='corporativo')  # 'corporativo', 'gobierno', 'particular'
    rfc = db.Column(db.String)
    razon_social = db.Column(db.String)
    direccion_fiscal = db.Column(db.String)
    contacto_nombre = db.Column(db.String)
    contacto_email = db.Column(db.String)
    contacto_telefono = db.Column(db.String)
    
    # Campos de crédito
    limite_credito = db.Column(db.Numeric(12, 2), default=0)
    credito_disponible = db.Column(db.Numeric(12, 2), default=0)
    dias_credito = db.Column(db.Integer, default=0)
    credito_activo = db.Column(db.Boolean, default=False)
    
    # Especificaciones técnicas para licitaciones (JSONB)
    especificaciones_tecnicas = db.Column(db.JSON, default={})
    
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    sucursal = db.relationship('Sucursal', back_populates='empresas')
    papeletas = db.relationship('Papeleta', back_populates='empresa', cascade="all, delete-orphan")
    desgloses = db.relationship('Desglose', back_populates='empresa', cascade="all, delete-orphan")
    cargos_servicio = db.relationship('CargoServicio', back_populates='empresa', cascade="all, delete-orphan")
    descuentos = db.relationship('Descuento', back_populates='empresa', cascade="all, delete-orphan")
    tarifas_fijas = db.relationship('TarifaFija', back_populates='empresa', cascade="all, delete-orphan")
    creditos_movimientos = db.relationship('CreditoMovimiento', back_populates='empresa', lazy='dynamic')
    
    def credito_utilizado(self):
        """Retorna el crédito utilizado"""
        return float(self.limite_credito or 0) - float(self.credito_disponible or 0)
    
    def porcentaje_credito_utilizado(self):
        """Retorna el porcentaje de crédito utilizado"""
        if self.limite_credito and self.limite_credito > 0:
            return round((self.credito_utilizado() / float(self.limite_credito)) * 100, 2)
        return 0
    
    def tiene_credito_suficiente(self, monto):
        """Verifica si la empresa tiene crédito suficiente para un monto"""
        if not self.credito_activo:
            return True  # Si no tiene crédito activo, no aplica validación
        return float(self.credito_disponible or 0) >= monto
    
    def __repr__(self):
        return f'<Empresa {self.nombre_empresa}>'


class CargoServicio(db.Model):
    """Cargos por servicio por empresa"""
    __tablename__ = 'cargos_servicio'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)  # 'visible', 'oculto', 'mixto'
    tipo_servicio = db.Column(db.String)  # 'nacional', 'internacional', 'hotel', 'auto', 'otro'
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.String)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    empresa = db.relationship('Empresa', back_populates='cargos_servicio')


class Descuento(db.Model):
    """Descuentos por empresa"""
    __tablename__ = 'descuentos'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    
    empresa = db.relationship('Empresa', back_populates='descuentos')


class TarifaFija(db.Model):
    """Tarifas fijas por empresa"""
    __tablename__ = 'tarifas_fijas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, default='nacional')  # 'nacional', 'internacional', 'hotel', 'auto', 'otro'
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.String)
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    empresa = db.relationship('Empresa', back_populates='tarifas_fijas')


# =============================================================================
# MODELOS DE TARJETAS Y AUTORIZACIONES
# =============================================================================

class TarjetaCorporativa(db.Model):
    """Catálogo de tarjetas de crédito corporativas"""
    __tablename__ = 'tarjetas_corporativas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    numero_tarjeta = db.Column(db.String, unique=True, nullable=False)  # Últimos 4 dígitos o código
    nombre_tarjeta = db.Column(db.String, nullable=False)
    banco = db.Column(db.String)
    titular = db.Column(db.String)
    limite_credito = db.Column(db.Numeric(12, 2), default=0)
    fecha_corte = db.Column(db.Integer)  # Día del mes (1-31)
    fecha_pago = db.Column(db.Integer)   # Día del mes (1-31)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    activa = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    sucursal = db.relationship('Sucursal', back_populates='tarjetas')
    papeletas = db.relationship('Papeleta', back_populates='tarjeta_rel', lazy='dynamic')
    autorizaciones = db.relationship('Autorizacion', back_populates='tarjeta', lazy='dynamic')
    asignaciones = db.relationship('TarjetaUsuario', back_populates='tarjeta', lazy='dynamic')
    
    def requiere_autorizacion(self, usuario):
        """Verifica si un usuario necesita autorización para usar esta tarjeta"""
        # Primero verificar si tiene asignaciones específicas
        asignaciones_activas = TarjetaUsuario.query.filter_by(
            tarjeta_id=self.id, 
            activo=True
        ).all()
        
        if asignaciones_activas:
            # Si hay asignaciones, solo los usuarios asignados pueden usarla
            usuario_asignado = any(a.usuario_id == usuario.id for a in asignaciones_activas)
            return not usuario_asignado  # Requiere autorización si NO está asignado
        
        # Si no hay asignaciones específicas, usar lógica de sucursal
        if self.sucursal_id is None:
            return False
        return self.sucursal_id != usuario.sucursal_id
    
    def get_usuarios_asignados(self):
        """Retorna los usuarios asignados a esta tarjeta"""
        return [asig.usuario for asig in self.asignaciones if asig.activo]
    
    def __repr__(self):
        return f'<TarjetaCorporativa {self.nombre_tarjeta}>'


class TarjetaUsuario(db.Model):
    """Relación muchos a muchos entre tarjetas y usuarios"""
    __tablename__ = 'tarjetas_usuarios'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tarjeta_id = db.Column(db.BigInteger, db.ForeignKey('tarjetas_corporativas.id'), nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    asignado_por = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    fecha_asignacion = db.Column(db.DateTime(timezone=True), default=func.now())
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    tarjeta = db.relationship('TarjetaCorporativa', back_populates='asignaciones')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='tarjetas_asignadas')
    asignador = db.relationship('Usuario', foreign_keys=[asignado_por])
    
    def __repr__(self):
        return f'<TarjetaUsuario tarjeta={self.tarjeta_id} usuario={self.usuario_id}>'


class Autorizacion(db.Model):
    """Sistema de autorizaciones para excepciones"""
    __tablename__ = 'autorizaciones'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tipo = db.Column(db.String, nullable=False)  # 'uso_tarjeta', 'exceso_credito', 'descuento_especial', 'otro'
    solicitante_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    autorizador_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    
    # Referencias opcionales
    tarjeta_id = db.Column(db.BigInteger, db.ForeignKey('tarjetas_corporativas.id'))
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    
    motivo = db.Column(db.Text, nullable=False)
    monto_solicitado = db.Column(db.Numeric(12, 2))
    estatus = db.Column(db.String, default='pendiente', nullable=False)  # 'pendiente', 'aprobada', 'rechazada', 'expirada'
    
    fecha_solicitud = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    fecha_respuesta = db.Column(db.DateTime(timezone=True))
    comentario_respuesta = db.Column(db.Text)
    
    notificado_google_chat = db.Column(db.Boolean, default=False)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], back_populates='autorizaciones_solicitadas')
    autorizador = db.relationship('Usuario', foreign_keys=[autorizador_id], back_populates='autorizaciones_aprobadas')
    tarjeta = db.relationship('TarjetaCorporativa', back_populates='autorizaciones')
    sucursal = db.relationship('Sucursal')
    
    def aprobar(self, autorizador, comentario=None):
        """Aprueba la autorización"""
        self.estatus = 'aprobada'
        self.autorizador_id = autorizador.id
        self.fecha_respuesta = datetime.utcnow()
        self.comentario_respuesta = comentario
    
    def rechazar(self, autorizador, comentario=None):
        """Rechaza la autorización"""
        self.estatus = 'rechazada'
        self.autorizador_id = autorizador.id
        self.fecha_respuesta = datetime.utcnow()
        self.comentario_respuesta = comentario
    
    def esta_vigente(self, horas=24):
        """Verifica si la autorización sigue vigente"""
        if self.estatus != 'aprobada':
            return False
        if not self.fecha_respuesta:
            return False
        from datetime import timedelta
        
        # Usar datetime con timezone para comparación correcta
        ahora = datetime.utcnow()
        fecha_resp = self.fecha_respuesta
        
        # Si fecha_respuesta tiene timezone, quitarlo para comparar
        if fecha_resp.tzinfo is not None:
            fecha_resp = fecha_resp.replace(tzinfo=None)
        
        return ahora < fecha_resp + timedelta(hours=horas)
    
    def __repr__(self):
        return f'<Autorizacion {self.id} - {self.tipo}>'


# =============================================================================
# MODELOS OPERATIVOS
# =============================================================================

class Aerolinea(db.Model):
    """Catálogo de aerolíneas"""
    __tablename__ = 'aerolineas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False, unique=True)
    codigo_iata = db.Column(db.String(2))
    codigo_icao = db.Column(db.String(3))
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    desgloses = db.relationship('Desglose', back_populates='aerolinea')
    papeletas = db.relationship('Papeleta', backref='aerolinea_rel')
    
    def __repr__(self):
        return f'<Aerolinea {self.nombre}>'


class EmpresaBooking(db.Model):
    """Empresas de booking/reservaciones"""
    __tablename__ = 'empresas_booking'
    
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False, unique=True)
    
    desgloses = db.relationship('Desglose', back_populates='empresa_booking')
    
    def __repr__(self):
        return f'<EmpresaBooking {self.nombre}>'


class Desglose(db.Model):
    """Desgloses de boletos aéreos"""
    __tablename__ = 'desgloses'
    
    folio = db.Column(db.BigInteger, primary_key=True)
    empresa_booking_id = db.Column(db.BigInteger, db.ForeignKey('empresas_booking.id'), nullable=False)
    aerolinea_id = db.Column(db.BigInteger, db.ForeignKey('aerolineas.id'), nullable=False)
    tarifa_base = db.Column(db.Numeric(10, 2), nullable=False)
    iva = db.Column(db.Numeric(10, 2), nullable=False)
    tua = db.Column(db.Numeric(10, 2), nullable=False)
    yr = db.Column(db.Numeric(10, 2), nullable=False)
    otros_cargos = db.Column(db.Numeric(10, 2), nullable=False)
    cargo_por_servicio = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    clave_reserva = db.Column(db.String, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    
    # Nuevos campos
    numero_boleto = db.Column(db.String, unique=True)
    fecha_emision = db.Column(db.Date, default=datetime.utcnow)
    fecha_viaje = db.Column(db.Date)
    estatus = db.Column(db.String, default='pendiente')  # 'pendiente', 'emitido', 'cancelado', 'reembolsado'
    pasajero_nombre = db.Column(db.String)
    ruta = db.Column(db.String)  # Ej: "TIJ-MEX-TIJ"
    clase = db.Column(db.String)  # Económica, Ejecutiva, etc.
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    empresa_booking = db.relationship('EmpresaBooking', back_populates='desgloses')
    aerolinea = db.relationship('Aerolinea', back_populates='desgloses')
    usuario = db.relationship('Usuario', back_populates='desgloses')
    empresa = db.relationship('Empresa', back_populates='desgloses')
    sucursal = db.relationship('Sucursal')
    
    def __repr__(self):
        return f'<Desglose {self.folio}>'


class Papeleta(db.Model):
    """Papeletas de tarjeta de crédito"""
    __tablename__ = 'papeletas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    folio = db.Column(db.String, nullable=False, unique=True)
    tarjeta = db.Column(db.String, nullable=False)  # Campo legacy
    tarjeta_id = db.Column(db.BigInteger, db.ForeignKey('tarjetas_corporativas.id'))
    fecha_venta = db.Column(db.Date, nullable=False)
    total_ticket = db.Column(db.Numeric(10, 2), nullable=False)
    diez_porciento = db.Column(db.Numeric(10, 2), nullable=False)
    cargo = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    facturar_a = db.Column(db.String, nullable=False)
    solicito = db.Column(db.String, nullable=False)
    clave_sabre = db.Column(db.String, nullable=False)
    forma_pago = db.Column(db.String, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    aerolinea_id = db.Column(db.BigInteger, db.ForeignKey('aerolineas.id'))
    tipo_cargo = db.Column(db.String(50))  # 'aerolinea', 'hotel', 'auto', 'otro'
    proveedor = db.Column(db.String(255))   # Nombre del hotel, rentadora, etc.
    
    # Campos para papeletas extemporáneas
    extemporanea = db.Column(db.Boolean, default=False)
    motivo_extemporanea = db.Column(db.Text)
    fecha_cargo_real = db.Column(db.Date)  # Fecha real del cargo a la tarjeta
    
    # Campos para reembolsos
    tiene_reembolso = db.Column(db.Boolean, default=False)
    estatus_reembolso = db.Column(db.String(50))  # 'pendiente', 'en_proceso', 'completado', 'rechazado'
    motivo_reembolso = db.Column(db.Text)
    monto_reembolso = db.Column(db.Numeric(10, 2))
    fecha_solicitud_reembolso = db.Column(db.Date)
    fecha_reembolso = db.Column(db.Date)
    referencia_reembolso = db.Column(db.String(100))
    papeleta_relacionada_id = db.Column(db.BigInteger, db.ForeignKey('papeletas.id'))
    
    # Nuevos campos
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    autorizacion_id = db.Column(db.BigInteger, db.ForeignKey('autorizaciones.id'))
    conciliada = db.Column(db.Boolean, default=False)
    fecha_conciliacion = db.Column(db.Date)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    reporte_venta_id = db.Column(db.BigInteger, db.ForeignKey('reportes_ventas.id'))
    numero_factura = db.Column(db.String(50))  # Número de factura asignada
    archivo_boleto = db.Column(db.String(255))  # Nombre del archivo PDF del boleto
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # Campos de control de papeletas (agregar después de los otros campos)
    estatus_control = db.Column(db.String(20), default='activa')
    justificacion_pendiente = db.Column(db.Text)
    fecha_justificacion = db.Column(db.DateTime)
    revisada_por_id = db.Column(db.BigInteger)  # Sin FK para evitar conflicto
    fecha_revision = db.Column(db.DateTime)
    cerrada_por_id = db.Column(db.BigInteger)   # Sin FK para evitar conflicto
    fecha_cierre = db.Column(db.DateTime)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='papeletas')
    empresa = db.relationship('Empresa', back_populates='papeletas')
    aerolinea = db.relationship('Aerolinea')
    tarjeta_rel = db.relationship('TarjetaCorporativa', back_populates='papeletas')
    autorizacion = db.relationship('Autorizacion')
    sucursal = db.relationship('Sucursal')
    papeleta_relacionada = db.relationship('Papeleta', remote_side=[id], backref='papeletas_vinculadas')
    reporte_venta = db.relationship('ReporteVenta', backref='papeletas')
    
    def __repr__(self):
        return f'<Papeleta {self.folio}>'


# =============================================================================
# MODELOS DE CRÉDITO Y PAGOS
# =============================================================================

class CreditoMovimiento(db.Model):
    """Historial de movimientos de crédito por empresa"""
    __tablename__ = 'creditos_movimientos'
    
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)  # 'cargo', 'abono', 'ajuste', 'inicial'
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    saldo_anterior = db.Column(db.Numeric(12, 2), nullable=False)
    saldo_nuevo = db.Column(db.Numeric(12, 2), nullable=False)
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    comprobante_id = db.Column(db.BigInteger, db.ForeignKey('comprobantes_pago.id'))
    concepto = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    empresa = db.relationship('Empresa', back_populates='creditos_movimientos')
    usuario = db.relationship('Usuario')
    sucursal = db.relationship('Sucursal')
    
    def __repr__(self):
        return f'<CreditoMovimiento {self.id} - {self.tipo}>'


class ComprobantePago(db.Model):
    """Comprobantes de pago adjuntos"""
    __tablename__ = 'comprobantes_pago'
    
    id = db.Column(db.BigInteger, primary_key=True)
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    papeleta_id = db.Column(db.BigInteger, db.ForeignKey('papeletas.id'))
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    tipo = db.Column(db.String, nullable=False)  # 'transferencia', 'deposito', 'cheque', 'otro'
    archivo_url = db.Column(db.String, nullable=False)
    archivo_nombre = db.Column(db.String, nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    referencia = db.Column(db.String)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    agente_notificado = db.Column(db.Boolean, default=False)
    fecha_notificacion = db.Column(db.DateTime(timezone=True))
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuario = db.relationship('Usuario')
    empresa = db.relationship('Empresa')
    sucursal = db.relationship('Sucursal')
    
    def __repr__(self):
        return f'<ComprobantePago {self.id}>'


# =============================================================================
# MODELOS DE AUDITORÍA Y NOTIFICACIONES
# =============================================================================

class AuditLog(db.Model):
    """Registro de auditoría de acciones"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tabla_nombre = db.Column(db.String, nullable=False)
    registro_id = db.Column(db.String, nullable=False)
    accion = db.Column(db.String, nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    datos_anteriores = db.Column(db.JSON)
    datos_nuevos = db.Column(db.JSON)
    campos_modificados = db.Column(db.ARRAY(db.String))
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    usuario_email = db.Column(db.String)
    ip_address = db.Column(db.String)
    user_agent = db.Column(db.String)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    def __repr__(self):
        return f'<AuditLog {self.id} - {self.accion}>'


class Notificacion(db.Model):
    """Cola de notificaciones para webhooks"""
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.BigInteger, primary_key=True)
    tipo = db.Column(db.String, nullable=False)  # 'autorizacion_solicitada', 'autorizacion_respondida', etc.
    destinatario = db.Column(db.String, nullable=False)
    canal = db.Column(db.String, default='google_chat', nullable=False)
    titulo = db.Column(db.String, nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    payload = db.Column(db.JSON)
    autorizacion_id = db.Column(db.BigInteger, db.ForeignKey('autorizaciones.id'))
    desglose_folio = db.Column(db.BigInteger, db.ForeignKey('desgloses.folio'))
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))
    estatus = db.Column(db.String, default='pendiente', nullable=False)  # 'pendiente', 'enviada', 'fallida'
    intentos = db.Column(db.Integer, default=0)
    ultimo_error = db.Column(db.Text)
    fecha_programada = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    fecha_enviada = db.Column(db.DateTime(timezone=True))
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    def __repr__(self):
        return f'<Notificacion {self.id} - {self.tipo}>'
    # =============================================================================
# MODELOS DE REPORTES DE VENTAS
# Agregar al final de models.py
# =============================================================================

class ReporteVenta(db.Model):
    """Reporte de ventas diario por agente"""
    __tablename__ = 'reportes_ventas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    folio = db.Column(db.String(20), unique=True)
    fecha = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = db.Column(db.BigInteger, db.ForeignKey('sucursales.id'))
    
    # Totales por tipo de boleto
    total_bsp = db.Column(db.Numeric(12, 2), default=0)
    total_volaris = db.Column(db.Numeric(12, 2), default=0)
    total_vivaerobus = db.Column(db.Numeric(12, 2), default=0)
    total_compra_tc = db.Column(db.Numeric(12, 2), default=0)
    
    # Otros cargos
    total_cargo_expedicion = db.Column(db.Numeric(12, 2), default=0)
    total_cargo_315 = db.Column(db.Numeric(12, 2), default=0)
    total_seguros = db.Column(db.Numeric(12, 2), default=0)
    total_hoteles_paquetes = db.Column(db.Numeric(12, 2), default=0)
    total_transporte_terrestre = db.Column(db.Numeric(12, 2), default=0)
    
    # Formas de pago
    total_pago_directo_tc = db.Column(db.Numeric(12, 2), default=0)
    total_voucher_tc = db.Column(db.Numeric(12, 2), default=0)
    total_efectivo = db.Column(db.Numeric(12, 2), default=0)
    total_general = db.Column(db.Numeric(12, 2), default=0)
    
    # Depósitos
    deposito_pesos_efectivo = db.Column(db.Numeric(12, 2), default=0)
    deposito_dolares_efectivo = db.Column(db.Numeric(12, 2), default=0)
    deposito_pesos_cheques = db.Column(db.Numeric(12, 2), default=0)
    tipo_cambio = db.Column(db.Numeric(8, 4), default=0)
    cuenta_deposito = db.Column(db.String(50))
    
    # Contadores
    total_boletos = db.Column(db.Integer, default=0)
    total_recibos = db.Column(db.Integer, default=0)
    
    # Control
    estatus = db.Column(db.String(20), default='borrador')
    fecha_envio = db.Column(db.DateTime(timezone=True))
    fecha_aprobacion = db.Column(db.DateTime(timezone=True))
    aprobado_por = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    notas = db.Column(db.Text)
    
    # Auditoría
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='reportes_ventas')
    sucursal = db.relationship('Sucursal', backref='reportes_ventas')
    aprobador = db.relationship('Usuario', foreign_keys=[aprobado_por])
    detalles = db.relationship('DetalleReporteVenta', back_populates='reporte', cascade='all, delete-orphan', lazy='dynamic')
    
    def __repr__(self):
        return f'<ReporteVenta {self.folio}>'
    
    @property
    def puede_editar(self):
        # No editable si tiene vale de entrega asociado
        if self.entrega_corte:
            return False
        return self.estatus == 'borrador'
    
    @property
    def puede_enviar(self):
        return self.estatus == 'borrador' and self.total_recibos > 0


class DetalleReporteVenta(db.Model):
    """Líneas de detalle del reporte de ventas"""
    __tablename__ = 'detalle_reporte_ventas'
    
    id = db.Column(db.BigInteger, primary_key=True)
    reporte_id = db.Column(db.BigInteger, db.ForeignKey('reportes_ventas.id', ondelete='CASCADE'), nullable=False)
    papeleta_id = db.Column(db.BigInteger, db.ForeignKey('papeletas.id'))
    
    # Datos de la línea
    clave_aerolinea = db.Column(db.String(10))
    num_boletos = db.Column(db.Integer, default=1)
    reserva = db.Column(db.String(20))
    num_recibo = db.Column(db.String(20))
    num_papeleta = db.Column(db.String(20))
    
    # Costos por tipo
    monto_bsp = db.Column(db.Numeric(12, 2), default=0)
    monto_volaris = db.Column(db.Numeric(12, 2), default=0)
    monto_vivaerobus = db.Column(db.Numeric(12, 2), default=0)
    monto_compra_tc = db.Column(db.Numeric(12, 2), default=0)
    
    # Otros cargos
    cargo_expedicion = db.Column(db.Numeric(12, 2), default=0)
    cargo_315 = db.Column(db.Numeric(12, 2), default=0)
    monto_seguros = db.Column(db.Numeric(12, 2), default=0)
    monto_hoteles_paquetes = db.Column(db.Numeric(12, 2), default=0)
    monto_transporte_terrestre = db.Column(db.Numeric(12, 2), default=0)
    
    # Forma de pago
    pago_directo_tc = db.Column(db.Numeric(12, 2), default=0)
    voucher_tc = db.Column(db.Numeric(12, 2), default=0)
    efectivo = db.Column(db.Numeric(12, 2), default=0)
    total_linea = db.Column(db.Numeric(12, 2), default=0)
    
    orden = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relaciones
    reporte = db.relationship('ReporteVenta', back_populates='detalles')
    papeleta = db.relationship('Papeleta', backref='detalle_reporte')
    
    def __repr__(self):
        return f'<DetalleReporte {self.id} - {self.num_papeleta}>'


# models_entregas.py
# Modelos para el Sistema de Entregas de Corte
# Flujo: Agente → Administrativo → Encargado Depósitos → Director




class EntregaCorte(db.Model):
    """
    Registro de entrega de corte de caja.
    Representa el vale de entrega que genera cada agente al cerrar su turno.
    """
    __tablename__ = 'entregas_corte'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificación
    folio = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    fecha_hora_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Quien entrega (Agente)
    agente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey('sucursales.id'))
    
    # Reporte de ventas asociado
    reporte_venta_id = db.Column(db.Integer, db.ForeignKey('reportes_ventas.id'))
    
    # Montos a entregar
    efectivo_pesos = db.Column(db.Numeric(12, 2), default=0)
    efectivo_dolares = db.Column(db.Numeric(12, 2), default=0)
    tipo_cambio = db.Column(db.Numeric(10, 4), default=0)
    equivalente_pesos = db.Column(db.Numeric(12, 2), default=0)
    cheques = db.Column(db.Numeric(12, 2), default=0)
    vouchers_tc = db.Column(db.Numeric(12, 2), default=0)
    
    # Total físico a entregar
    total_fisico = db.Column(db.Numeric(12, 2), default=0)
    
    # Estatus del flujo
    estatus = db.Column(db.String(20), default='pendiente')
    # pendiente → entregado → en_custodia → depositado → revisado
    
    # Paso 1: Entrega a Administrativo
    recibido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_recepcion = db.Column(db.DateTime)
    firma_agente = db.Column(db.Text)
    firma_receptor = db.Column(db.Text)
    notas_entrega = db.Column(db.Text)
    
    # Paso 2: Retiro por Encargado de Depósitos
    retirado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_retiro = db.Column(db.DateTime)
    firma_retiro = db.Column(db.Text)
    notas_retiro = db.Column(db.Text)
    
    # Paso 3: Depósito en banco
    depositado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_deposito = db.Column(db.DateTime)
    cuenta_deposito = db.Column(db.String(100))
    referencia_deposito = db.Column(db.String(100))
    comprobante_deposito = db.Column(db.Text)
    notas_deposito = db.Column(db.Text)
    
    # Paso 4: Revisión por Director
    revisado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_revision = db.Column(db.DateTime)
    aprobado = db.Column(db.Boolean, default=False)
    notas_revision = db.Column(db.Text)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    agente = db.relationship('Usuario', foreign_keys=[agente_id], backref='entregas_realizadas')
    receptor = db.relationship('Usuario', foreign_keys=[recibido_por_id], backref='entregas_recibidas')
    encargado_retiro = db.relationship('Usuario', foreign_keys=[retirado_por_id], backref='entregas_retiradas')
    encargado_deposito = db.relationship('Usuario', foreign_keys=[depositado_por_id], backref='entregas_depositadas')
    revisor = db.relationship('Usuario', foreign_keys=[revisado_por_id], backref='entregas_revisadas')
    reporte_venta = db.relationship('ReporteVenta', backref='entrega_corte')
    sucursal = db.relationship('Sucursal', backref='entregas')
    detalles_arqueo = db.relationship('DetalleArqueo', backref='entrega', lazy='dynamic', cascade='all, delete-orphan')
    historial = db.relationship('HistorialEntrega', backref='entrega', lazy='dynamic', cascade='all, delete-orphan', order_by='HistorialEntrega.fecha_hora.desc()')
    
    def __repr__(self):
        return f'<EntregaCorte {self.folio}>'
    
    @staticmethod
    def generar_folio():
        """Genera folio automático EC-YYYY-NNNN"""
        anio = date.today().strftime('%Y')
        ultimo = EntregaCorte.query.filter(
            EntregaCorte.folio.like(f'EC-{anio}-%')
        ).order_by(EntregaCorte.id.desc()).first()
        
        if ultimo:
            try:
                num = int(ultimo.folio.split('-')[-1]) + 1
            except:
                num = 1
        else:
            num = 1
        
        return f'EC-{anio}-{num:04d}'
    
    def calcular_totales(self):
        """Calcula equivalente en pesos y total físico"""
        self.equivalente_pesos = float(self.efectivo_dolares or 0) * float(self.tipo_cambio or 0)
        self.total_fisico = (
            float(self.efectivo_pesos or 0) + 
            float(self.cheques or 0) + 
            self.equivalente_pesos
        )
    
    def registrar_historial(self, accion, usuario_id, estatus_anterior=None, notas=None, ip=None):
        """Registra un movimiento en el historial"""
        historial = HistorialEntrega(
            entrega_id=self.id,
            accion=accion,
            usuario_id=usuario_id,
            estatus_anterior=estatus_anterior,
            estatus_nuevo=self.estatus,
            notas=notas,
            ip_address=ip
        )
        db.session.add(historial)
    
    # Métodos de transición de estatus
    def entregar_a_admin(self, receptor_id, notas=None):
        """Paso 1: Agente entrega a administrativo"""
        estatus_anterior = self.estatus
        self.estatus = 'entregado'
        self.recibido_por_id = receptor_id
        self.fecha_recepcion = datetime.utcnow()
        self.firma_receptor = 'CONFIRMADO'
        self.notas_entrega = notas
        self.registrar_historial('entregado', receptor_id, estatus_anterior, notas)
    
    def confirmar_custodia(self, admin_id, notas=None):
        """Administrativo confirma que tiene el dinero en custodia"""
        estatus_anterior = self.estatus
        self.estatus = 'en_custodia'
        self.registrar_historial('en_custodia', admin_id, estatus_anterior, notas)
    
    def retirar_para_deposito(self, encargado_id, notas=None):
        """Paso 2: Encargado de depósitos retira el dinero"""
        estatus_anterior = self.estatus
        self.estatus = 'retirado'
        self.retirado_por_id = encargado_id
        self.fecha_retiro = datetime.utcnow()
        self.firma_retiro = 'CONFIRMADO'
        self.notas_retiro = notas
        self.registrar_historial('retirado', encargado_id, estatus_anterior, notas)
    
    def registrar_deposito(self, encargado_id, cuenta, referencia, notas=None):
        """Paso 3: Registrar el depósito bancario"""
        estatus_anterior = self.estatus
        self.estatus = 'depositado'
        self.depositado_por_id = encargado_id
        self.fecha_deposito = datetime.utcnow()
        self.cuenta_deposito = cuenta
        self.referencia_deposito = referencia
        self.notas_deposito = notas
        self.registrar_historial('depositado', encargado_id, estatus_anterior, f'Cuenta: {cuenta}, Ref: {referencia}')
    
    def revisar_y_aprobar(self, director_id, aprobado=True, notas=None):
        """Paso 4: Director revisa y cierra"""
        estatus_anterior = self.estatus
        self.estatus = 'revisado'
        self.revisado_por_id = director_id
        self.fecha_revision = datetime.utcnow()
        self.aprobado = aprobado
        self.notas_revision = notas
        accion = 'aprobado' if aprobado else 'rechazado'
        self.registrar_historial(accion, director_id, estatus_anterior, notas)
    
    @property
    def puede_entregar(self):
        """Verifica si se puede entregar (solo en estatus pendiente)"""
        return self.estatus == 'pendiente'
    
    @property
    def puede_retirar(self):
        """Verifica si se puede retirar (en custodia o entregado)"""
        return self.estatus in ['entregado', 'en_custodia']
    
    @property
    def puede_depositar(self):
        """Verifica si se puede registrar depósito"""
        return self.estatus == 'retirado'
    
    @property
    def puede_revisar(self):
        """Verifica si puede ser revisado por director"""
        return self.estatus == 'depositado'
    
    @property
    def estatus_badge(self):
        """Retorna clase CSS para badge según estatus"""
        badges = {
            'pendiente': 'warning',
            'entregado': 'info',
            'en_custodia': 'primary',
            'retirado': 'secondary',
            'depositado': 'success',
            'revisado': 'dark'
        }
        return badges.get(self.estatus, 'secondary')
    
    @property
    def estatus_descripcion(self):
        """Descripción amigable del estatus"""
        descripciones = {
            'pendiente': 'Pendiente de entrega',
            'entregado': 'Entregado a Admin',
            'en_custodia': 'En custodia',
            'retirado': 'Retirado para depósito',
            'depositado': 'Depositado - Pendiente revisión',
            'revisado': 'Revisado y cerrado'
        }
        return descripciones.get(self.estatus, self.estatus)
    
    def to_dict(self):
        """Serializa a diccionario para API"""
        return {
            'id': self.id,
            'folio': self.folio,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'agente': self.agente.nombre if self.agente else None,
            'efectivo_pesos': float(self.efectivo_pesos or 0),
            'efectivo_dolares': float(self.efectivo_dolares or 0),
            'tipo_cambio': float(self.tipo_cambio or 0),
            'equivalente_pesos': float(self.equivalente_pesos or 0),
            'cheques': float(self.cheques or 0),
            'vouchers_tc': float(self.vouchers_tc or 0),
            'total_fisico': float(self.total_fisico or 0),
            'estatus': self.estatus,
            'estatus_descripcion': self.estatus_descripcion,
            'receptor': self.receptor.nombre if self.receptor else None,
            'fecha_recepcion': self.fecha_recepcion.isoformat() if self.fecha_recepcion else None
        }


class DetalleArqueo(db.Model):
    """Detalle de denominaciones para arqueo de caja"""
    __tablename__ = 'detalle_arqueo'
    
    id = db.Column(db.Integer, primary_key=True)
    entrega_id = db.Column(db.Integer, db.ForeignKey('entregas_corte.id', ondelete='CASCADE'), nullable=False)
    
    tipo = db.Column(db.String(10), nullable=False)  # 'billete', 'moneda', 'dolar'
    denominacion = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Integer, default=0)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DetalleArqueo {self.tipo} ${self.denominacion} x{self.cantidad}>'
    
    def calcular_subtotal(self):
        self.subtotal = float(self.denominacion or 0) * (self.cantidad or 0)


class HistorialEntrega(db.Model):
    """Bitácora de movimientos de entregas"""
    __tablename__ = 'historial_entregas'
    
    id = db.Column(db.Integer, primary_key=True)
    entrega_id = db.Column(db.Integer, db.ForeignKey('entregas_corte.id', ondelete='CASCADE'), nullable=False)
    
    accion = db.Column(db.String(50), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    estatus_anterior = db.Column(db.String(20))
    estatus_nuevo = db.Column(db.String(20))
    notas = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    usuario = db.relationship('Usuario', backref='acciones_entregas')
    
    def __repr__(self):
        return f'<HistorialEntrega {self.accion} - {self.fecha_hora}>'
    
    @property
    def accion_descripcion(self):
        """Descripción amigable de la acción"""
        descripciones = {
            'creado': 'Vale creado',
            'entregado': 'Entregado a administrativo',
            'en_custodia': 'Confirmado en custodia',
            'retirado': 'Retirado para depósito',
            'depositado': 'Depósito registrado',
            'aprobado': 'Aprobado por dirección',
            'rechazado': 'Rechazado por dirección'
        }
        return descripciones.get(self.accion, self.accion)


# ============================================================
# Funciones auxiliares
# ============================================================

def crear_entrega_desde_reporte(reporte, usuario_id):
    """
    Crea una entrega de corte a partir de un reporte de ventas.
    
    Args:
        reporte: Objeto ReporteVenta
        usuario_id: ID del usuario que crea la entrega
    
    Returns:
        EntregaCorte: Nueva entrega creada
    """
    entrega = EntregaCorte(
        folio=EntregaCorte.generar_folio(),
        fecha=reporte.fecha,
        agente_id=reporte.usuario_id,
        sucursal_id=reporte.sucursal_id if hasattr(reporte, 'sucursal_id') else None,
        reporte_venta_id=reporte.id,
        efectivo_pesos=float(reporte.total_efectivo or 0) - (float(reporte.deposito_dolares_efectivo or 0) * float(reporte.tipo_cambio or 0)),
        efectivo_dolares=float(reporte.deposito_dolares_efectivo or 0),
        tipo_cambio=float(reporte.tipo_cambio or 0),
        cheques=float(reporte.deposito_pesos_cheques or 0),
        vouchers_tc=float(reporte.total_voucher_tc or 0),
        estatus='pendiente'
    )
    
    entrega.calcular_totales()
    
    db.session.add(entrega)
    db.session.flush()  # Para obtener el ID
    
    # Registrar en historial
    entrega.registrar_historial('creado', usuario_id, None, f'Creado desde reporte {reporte.folio}')
    
    return entrega


def obtener_entregas_por_rol(usuario):
    """
    Obtiene las entregas relevantes según el rol del usuario.
    
    Args:
        usuario: Objeto Usuario con método es_admin(), es_director(), etc.
    
    Returns:
        Query de entregas filtradas
    """
    query = EntregaCorte.query
    
    if hasattr(usuario, 'es_director') and usuario.es_director():
        # Director ve todas, especialmente las pendientes de revisión
        return query.order_by(EntregaCorte.fecha.desc())
    
    elif hasattr(usuario, 'es_admin') and usuario.es_admin():
        # Admin ve las que debe recibir y las que tiene en custodia
        return query.filter(
            db.or_(
                EntregaCorte.estatus == 'pendiente',
                EntregaCorte.estatus == 'entregado',
                EntregaCorte.recibido_por_id == usuario.id
            )
        ).order_by(EntregaCorte.fecha.desc())
    
    elif hasattr(usuario, 'puede_depositar') and usuario.puede_depositar:
        # Encargado de depósitos ve las que puede retirar y depositar
        return query.filter(
            db.or_(
                EntregaCorte.estatus.in_(['en_custodia', 'retirado']),
                EntregaCorte.retirado_por_id == usuario.id
            )
        ).order_by(EntregaCorte.fecha.desc())
    
    else:
        # Agente solo ve sus propias entregas
        return query.filter(
            EntregaCorte.agente_id == usuario.id
        ).order_by(EntregaCorte.fecha.desc())