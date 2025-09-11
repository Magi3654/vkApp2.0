from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import db, Usuario, Rol, Papeleta, Desglose, Empresa

# --- LÍNEA CLAVE ---
# Aquí definimos el Blueprint 'main' que tu archivo __init__.py está buscando.
main = Blueprint('main', __name__)


# --- RUTAS PRINCIPALES DE LA APLICACIÓN ---

@main.route('/')
@login_required
def index():
    # La página de inicio redirige al dashboard.
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Muestra el dashboard principal.
    return render_template('dashboard.html', usuario=current_user)

@main.route('/desgloses')
@login_required
def desgloses():
    # Muestra la página para gestionar desgloses.
    return render_template('desglose.html')

@main.route('/papeletas')
@login_required
def papeletas():
    # Muestra la página para gestionar papeletas.
    return render_template('papeletas.html')

@main.route('/empresas')
@login_required
def empresas():
    # Ruta para administrar empresas (solo para administradores).
    if current_user.rol_relacion.nombre != 'administrador':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Asegúrate de que tu plantilla se llame 'empresas.html' o 'registroEmpresas.html'
    return render_template('empresas.html')

