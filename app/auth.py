from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, Usuario, Rol

# Creamos un Blueprint para organizar todas las rutas relacionadas con la autenticación.
auth = Blueprint('auth', __name__)


# --- RUTA DE INICIO DE SESIÓN ---
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión de los usuarios."""
    # Si el usuario ya está autenticado, lo redirigimos a la página principal.
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')

        # Buscamos al usuario por su correo en la base de datos.
        usuario = Usuario.query.filter_by(correo=correo).first()

        # Verificamos si el usuario existe y si la contraseña es correcta.
        if not usuario or not usuario.check_password(contrasena):
            flash('Correo o contraseña incorrectos. Por favor, inténtalo de nuevo.', 'danger')
            return redirect(url_for('auth.login'))

        # Si las credenciales son válidas, iniciamos la sesión.
        login_user(usuario)
        flash('¡Has iniciado sesión con éxito!', 'success')
        return redirect(url_for('main.index'))

    # Si el método es GET, solo mostramos el formulario de login.
    return render_template('login.html')


# --- RUTA PARA CERRAR SESIÓN ---
@auth.route('/logout')
@login_required  # El usuario debe estar logueado para poder cerrar sesión.
def logout():
    """Cierra la sesión del usuario actual."""
    logout_user()
    flash('Has cerrado la sesión.', 'success')
    return redirect(url_for('auth.login'))


# --- RUTA PARA REGISTRAR NUEVOS USUARIOS (SOLO ADMINS) ---
@auth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Permite a los administradores registrar nuevos usuarios."""
    # Verificamos si el rol del usuario actual es 'administrador'.
    if current_user.rol.nombre != 'administrador':
        flash('No tienes permiso para registrar nuevos usuarios.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        rol_id = request.form.get('rol_id')

        # Verificamos que el correo no esté ya en uso.
        if Usuario.query.filter_by(correo=correo).first():
            flash('Ese correo electrónico ya está registrado.', 'warning')
            return redirect(url_for('auth.register'))

        # Creamos la nueva instancia de usuario.
        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            rol_id=rol_id
        )
        nuevo_usuario.set_password(contrasena)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash(f'¡Usuario "{nombre}" registrado con éxito!', 'success')
        return redirect(url_for('main.index'))

    # Para la solicitud GET, pasamos la lista de roles a la plantilla.
    roles = Rol.query.all()
    return render_template('registro_usuarios.html', roles=roles)

