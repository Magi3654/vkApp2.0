from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
# from sqlalchemy.dialects.postgresql import VECTOR # LÍNEA ELIMINADA

db = SQLAlchemy()

# --- Modelos de Autenticación y Usuarios ---

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    correo = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column('contrasena', db.String(255), nullable=False)
    rol = db.Column(db.String, nullable=False)
    rol_id = db.Column(db.BigInteger, db.ForeignKey('roles.id'))
    
    rol_relacion = db.relationship('Rol', back_populates='usuarios')
    papeletas = db.relationship('Papeleta', back_populates='usuario', lazy='dynamic')
    desgloses = db.relationship('Desglose', back_populates='usuario', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f'<Usuario {self.nombre}>'

class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, unique=True, nullable=False)
    usuarios = db.relationship("Usuario", back_populates="rol_relacion")

    def __repr__(self):
        return f'<Rol {self.nombre}>'

# --- Modelos de Empresas y Configuración ---

class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre_empresa = db.Column(db.String, nullable=False)

    # --- RELACIONES ACTUALIZADAS ---
    # Añadimos 'cascade' para que al borrar una empresa, se borren
    # automáticamente todos sus registros asociados.
    papeletas = db.relationship('Papeleta', back_populates='empresa', cascade="all, delete-orphan")
    desgloses = db.relationship('Desglose', back_populates='empresa', cascade="all, delete-orphan")
    cargos_servicio = db.relationship('CargoServicio', back_populates='empresa', cascade="all, delete-orphan")
    descuentos = db.relationship('Descuento', back_populates='empresa', cascade="all, delete-orphan")
    tarifas_fijas = db.relationship('TarifaFija', back_populates='empresa', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Empresa {self.nombre_empresa}>'

# (El resto de las clases no necesitan cambios)
# ... (Pega aquí el resto de tus clases: CargoServicio, Descuento, etc.)
class CargoServicio(db.Model):
    __tablename__ = 'cargos_servicio'
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    empresa = db.relationship('Empresa', back_populates='cargos_servicio')

class Descuento(db.Model):
    __tablename__ = 'descuentos'
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    tipo = db.Column(db.String, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    empresa = db.relationship('Empresa', back_populates='descuentos')

class TarifaFija(db.Model):
    __tablename__ = 'tarifas_fijas'
    id = db.Column(db.BigInteger, primary_key=True)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    empresa = db.relationship('Empresa', back_populates='tarifas_fijas')
# --- Modelos Operativos ---

class Papeleta(db.Model):
    __tablename__ = 'papeletas'
    id = db.Column(db.BigInteger, primary_key=True)
    folio = db.Column(db.String, nullable=False)
    tarjeta = db.Column(db.String, nullable=False)
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
    usuario = db.relationship('Usuario', back_populates='papeletas')
    empresa = db.relationship('Empresa', back_populates='papeletas')

class Desglose(db.Model):
    __tablename__ = 'desgloses'
    folio = db.Column(db.BigInteger, primary_key=True)
    tarifa_base = db.Column(db.Numeric(10, 2), nullable=False)
    iva = db.Column(db.Numeric(10, 2), nullable=False)
    tua = db.Column(db.Numeric(10, 2), nullable=False)
    yr = db.Column(db.Numeric(10, 2), nullable=False)
    otros_cargos = db.Column(db.Numeric(10, 2), nullable=False)
    cargo_por_servicio = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    clave_reserva = db.Column(db.String, nullable=False)
    empresa_booking_id = db.Column(db.BigInteger, db.ForeignKey('empresas_booking.id'), nullable=False)
    aerolinea_id = db.Column(db.BigInteger, db.ForeignKey('aerolineas.id'), nullable=False)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    empresa_booking = db.relationship('EmpresaBooking', back_populates='desgloses')
    aerolinea = db.relationship('Aerolinea', back_populates='desgloses')
    usuario = db.relationship('Usuario', back_populates='desgloses')
    empresa = db.relationship('Empresa', back_populates='desgloses')

# --- Modelos Auxiliares ---

class Aerolinea(db.Model):
    __tablename__ = 'aerolineas'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False, unique=True)
    desgloses = db.relationship('Desglose', back_populates='aerolinea')

class EmpresaBooking(db.Model):
    __tablename__ = 'empresas_booking'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String, nullable=False, unique=True)
    desgloses = db.relationship('Desglose', back_populates='empresa_booking')

# --- Modelos de Metadatos (Comentados para no causar error) ---

# class Embedding(db.Model):
#     __tablename__ = 'embeddings'
#     __table_args__ = {'schema': 'meta'}
#     id = db.Column(db.BigInteger, primary_key=True)
#     created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)
#     content = db.Column(db.Text, nullable=False)
#     embedding = db.Column(VECTOR(384), nullable=False)

