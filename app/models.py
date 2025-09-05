from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Inicializa la extensión de SQLAlchemy
db = SQLAlchemy()

# --- Modelo de Usuario ---
# Se conecta a la tabla 'usuarios' y añade la lógica de Flask-Login.
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    correo = db.Column(db.Text, unique=True, nullable=False)
    contrasena = db.Column(db.Text, nullable=False)  # Aquí se guardará el hash
    rol_id = db.Column(db.BigInteger, db.ForeignKey('roles.id'))

    # --- Relaciones (Links a otras tablas) ---
    rol = db.relationship("Rol", back_populates="usuarios")
    papeletas = db.relationship("Papeleta", back_populates="usuario")
    desgloses = db.relationship("Desglose", back_populates="usuario")
    
    # --- Métodos de Seguridad para Contraseñas ---
    def set_password(self, password):
        self.contrasena = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasena, password)

# --- Modelo de Roles ---
class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.Text, unique=True, nullable=False)
    usuarios = db.relationship("Usuario", back_populates="rol")

# --- Modelo de Empresas ---
class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre_empresa = db.Column(db.Text, nullable=False)
    
    # Relaciones que "salen" de Empresa hacia otras tablas
    papeletas = db.relationship("Papeleta", back_populates="empresa")
    desgloses = db.relationship("Desglose", back_populates="empresa")
    cargos_servicio = db.relationship("CargoServicio", back_populates="empresa")
    descuentos = db.relationship("Descuento", back_populates="empresa")
    tarifas_fijas = db.relationship("TarifaFija", back_populates="empresa")

# --- Modelo de Papeletas ---
class Papeleta(db.Model):
    __tablename__ = 'papeletas'
    id = db.Column(db.BigInteger, primary_key=True)
    folio = db.Column(db.Text, nullable=False)
    tarjeta = db.Column(db.Text, nullable=False)
    fecha_venta = db.Column(db.Date, nullable=False)
    total_ticket = db.Column(db.Numeric(10, 2), nullable=False)
    diez_porciento = db.Column(db.Numeric(10, 2), nullable=False)
    cargo = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    facturar_a = db.Column(db.Text, nullable=False)
    solicito = db.Column(db.Text, nullable=False)
    clave_sabre = db.Column(db.Text, nullable=False)
    forma_pago = db.Column(db.Text, nullable=False)
    
    # Claves foráneas que "entran" a Papeleta
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'))

    # Relaciones para acceder a los objetos completos
    usuario = db.relationship("Usuario", back_populates="papeletas")
    empresa = db.relationship("Empresa", back_populates="papeletas")

# --- Modelo de Desgloses ---
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
    clave_reserva = db.Column(db.Text, nullable=False)
    
    # Claves foráneas
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    aerolinea_id = db.Column(db.BigInteger, db.ForeignKey('aerolineas.id'), nullable=False)
    empresa_booking_id = db.Column(db.BigInteger, db.ForeignKey('empresas_booking.id'), nullable=False)

    # Relaciones
    usuario = db.relationship("Usuario", back_populates="desgloses")
    empresa = db.relationship("Empresa", back_populates="desgloses")
    aerolinea = db.relationship("Aerolinea")
    empresa_booking = db.relationship("EmpresaBooking")

# --- Modelos adicionales de tu base de datos ---

class Aerolinea(db.Model):
    __tablename__ = 'aerolineas'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.Text, unique=True, nullable=False)

class EmpresaBooking(db.Model):
    __tablename__ = 'empresas_booking'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.Text, unique=True, nullable=False)

class CargoServicio(db.Model):
    __tablename__ = 'cargos_servicio'
    id = db.Column(db.BigInteger, primary_key=True)
    tipo = db.Column(db.Text, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship("Empresa", back_populates="cargos_servicio")

class Descuento(db.Model):
    __tablename__ = 'descuentos'
    id = db.Column(db.BigInteger, primary_key=True)
    tipo = db.Column(db.Text, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship("Empresa", back_populates="descuentos")

class TarifaFija(db.Model):
    __tablename__ = 'tarifas_fijas'
    id = db.Column(db.BigInteger, primary_key=True)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    empresa_id = db.Column(db.BigInteger, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship("Empresa", back_populates="tarifas_fijas")

