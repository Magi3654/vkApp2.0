from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, String, Numeric, Boolean, Date, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class Embedding(db.Model):
    __tablename__ = 'embeddings'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)  # Cambiado a TIMESTAMP con zona horaria
    content = Column(String, nullable=False)
    embedding = Column('embedding', Numeric(384), nullable=False)  # Cambiado a Numeric, ajusta según tu implementación

class Desglose(db.Model):
    __tablename__ = 'desgloses'

    folio = Column(BigInteger, primary_key=True, nullable=False)
    tarifa_base = Column(Numeric(10, 2), nullable=False)
    iva = Column(Numeric(10, 2), nullable=False)
    tua = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    yr = Column(Numeric(10, 2), nullable=False)
    otros_cargos = Column(Numeric(10, 2), nullable=False)
    cargo_por_servicio = Column(Numeric(10, 2), nullable=False)
    empresa = Column(String, nullable=False)
    aerolinea = Column(String, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuarios.id'), nullable=False)
    clave_reserva = Column(String, nullable=False)
    empresa_id = Column(BigInteger, ForeignKey('empresas.id'), nullable=False)

    # Relación con Usuario y Empresa
    usuario = relationship("Usuario", back_populates="desgloses")
    empresa_rel = relationship("Empresa", back_populates="desgloses")

class Empresa(db.Model):
    __tablename__ = 'empresas'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre_empresa = Column(String, nullable=False)
    cargo_servicio_visible = Column(Boolean, default=False)
    cargo_servicio_mixto = Column(Boolean, default=False)
    cargo_servicio_facturado = Column(Numeric(10, 2))
    cargo_servicio_oculto = Column(Numeric(10, 2))
    descuento_monto = Column(Boolean, default=False)
    descuento_porcentaje = Column(Boolean, default=False)
    monto_descuento = Column(Numeric(10, 2))
    porcentaje_descuento = Column(Numeric(5, 2))
    tarifa_fija = Column(Numeric(10, 2))

    # Relación con Desglose y Papeleta
    desgloses = relationship("Desglose", back_populates="empresa_rel")
    papeletas = relationship("Papeleta", back_populates="empresa")

class Papeleta(db.Model):
    __tablename__ = 'papeletas'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    folio = Column(String, nullable=False)
    tarjeta = Column(String, nullable=False)
    fecha_venta = Column(Date, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuarios.id'), nullable=False)
    total_ticket = Column(Numeric(10, 2), nullable=False)
    diez_porciento = Column(Numeric(10, 2), nullable=False)
    cargo = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    facturar_a = Column(String, nullable=False)
    solicito = Column(String, nullable=False)
    clave_sabre = Column(String, nullable=False)
    forma_pago = Column(String, nullable=False)
    empresa_id = Column(BigInteger, ForeignKey('empresas.id'))

    # Relación con Usuario y Empresa
    usuario = relationship("Usuario", back_populates="papeletas")
    empresa = relationship("Empresa", back_populates="papeletas")

class Rol(db.Model):
    __tablename__ = 'roles'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    
    # Relación con Usuario
    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    contrasena = Column(String, nullable=False)
    # Relación inversa
    rol = relationship("Rol", back_populates="usuarios")
