from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
# Importa todos los modelos que necesitarás
from .models import db, Usuario, Rol, Papeleta, Desglose, Empresa, CargoServicio, Descuento, TarifaFija

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    # Redirige a la página principal después del login
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Pasa el objeto del usuario actual a la plantilla del dashboard
    return render_template('dashboard.html', usuario=current_user)

# --- RUTA TEMPORAL PARA CREAR EL PRIMER USUARIO ---
# ¡RECUERDA BORRAR ESTA RUTA DESPUÉS DE USARLA!
@main.route('/inicializar-admin-secreto')
def inicializar_admin():
    try:
        # 1. Busca el rol 'administrador' en la base de datos
        rol_admin = Rol.query.filter_by(nombre='administrador').first()
        if not rol_admin:
            return "Error: El rol 'administrador' no existe en la tabla de roles."

        # 2. Verifica si el usuario administrador ya existe
        if Usuario.query.filter_by(correo='admin@tuagencia.com').first():
            return "El usuario administrador ya existe."

        # --- LÍNEAS CORREGIDAS ---
        # 3. Crea el nuevo usuario, proporcionando valores para AMBAS columnas de rol
        admin_user = Usuario(
            nombre='Admin Principal',
            correo='admin@tuagencia.com',
            rol_id=rol_admin.id,      # El ID para la clave foránea
            rol=rol_admin.nombre    # El texto para la columna 'rol'
        )
        admin_user.set_password('admin12345')
        
        db.session.add(admin_user)
        db.session.commit()
        
        flash('¡Usuario administrador creado con éxito!', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback() # Revierte los cambios si algo sale mal
        return f"Ocurrió un error al crear el usuario: {str(e)}"

# --- AQUÍ PUEDES AÑADIR LAS RUTAS PARA PAPELETAS, DESGLOSES, ETC. ---
# Ejemplo:
# @main.route('/papeletas')
# @login_required
# def papeletas():
#     # Lógica para mostrar las papeletas
#     return render_template('papeletas.html')

