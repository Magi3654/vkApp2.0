from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, Usuario, Rol

# Creamos un Blueprint para las rutas de autenticación
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        
        # Buscamos al usuario por su correo electrónico
        usuario = Usuario.query.filter_by(correo=correo).first()

        # Verificamos que el usuario exista y que la contraseña sea correcta
        if not usuario or not usuario.check_password(contrasena):
            flash('Correo o contraseña incorrectos. Por favor, verifica tus datos.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Si todo es correcto, iniciamos la sesión del usuario
        login_user(usuario)
        flash('¡Inicio de sesión exitoso!', 'success')
        return redirect(url_for('main.index')) # Lo redirigimos a la página principal

    # Si el método es GET, simplemente mostramos la página de login
    return render_template('login.html')

@auth.route('/logout')
@login_required # Solo un usuario logueado puede cerrar sesión
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # PROTECCIÓN: Solo los administradores pueden registrar nuevos usuarios
    if current_user.rol.nombre != 'admin':
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Obtenemos los datos del formulario de registro
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        rol_id = request.form.get('rol')

        # Verificamos que el correo no esté ya en uso
        if Usuario.query.filter_by(correo=correo).first():
            flash('Ese correo electrónico ya está registrado.', 'warning')
            return redirect(url_for('auth.register'))

        # Creamos la nueva instancia del usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            rol_id=rol_id
        )
        nuevo_usuario.set_password(contrasena) # Hasheamos la contraseña

        # Guardamos el nuevo usuario en la base de datos
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash(f'Usuario {nombre} creado con éxito.', 'success')
        return redirect(url_for('main.index'))

    # Si es GET, preparamos los datos para el formulario (la lista de roles)
    roles = Rol.query.all()
    return render_template('registro_usuarios.html', roles=roles)
