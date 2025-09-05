from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import db, Papeleta, Desglose, Empresa, Usuario, Rol, Aerolinea, EmpresaBooking, CargoServicio, Descuento, TarifaFija
from datetime import datetime

# Un Blueprint es una forma de organizar un grupo de rutas relacionadas.
main = Blueprint('main', __name__)

# --- ¡RUTA TEMPORAL PARA INICIALIZAR USUARIO ADMIN! ---
# Visita esta URL UNA SOLA VEZ para crear tu primer usuario administrador.
# ¡RECUERDA BORRAR ESTA RUTA DESPUÉS DE USARLA POR SEGURIDAD!
@main.route('/inicializar-admin-secreto')
def inicializar_admin():
    try:
        # Busca el rol 'administrador' que ya debe existir en tu BD
        rol_admin = Rol.query.filter_by(nombre='administrador').first()
        if not rol_admin:
            return "<h1>Error: El rol 'administrador' no se encontró en la base de datos.</h1><p>Asegúrate de que tu tabla 'roles' tenga este registro.</p>"

        # Crea el primer usuario administrador si no existe
        admin_user = Usuario.query.filter_by(correo='admin@tuagencia.com').first()
        if not admin_user:
            admin_user = Usuario(
                nombre='Administrador Principal',
                correo='admin@tuagencia.com',
                rol_id=rol_admin.id
            )
            # ¡IMPORTANTE! Puedes cambiar esta contraseña por defecto
            admin_user.set_password('admin12345') 
            db.session.add(admin_user)
            db.session.commit()
            msg = "<h1>¡Usuario administrador creado con éxito!</h1>"
        else:
            msg = "<h1>El usuario administrador ya existía. No se realizaron cambios.</h1>"
            
        return f"{msg}<p><strong>Ahora lo más importante: ¡ve y borra esta función ('inicializar_admin') del archivo app/routes.py!</strong></p><a href='/auth/login'>Ir a la página de inicio de sesión</a>"
    
    except Exception as e:
        db.session.rollback()
        return f"<h1>Ocurrió un error:</h1><p>{str(e)}</p>"

# --- Rutas Principales de la Aplicación ---

@main.route('/')
@login_required 
def index():
    # Redirige al dashboard principal, que será la página de desgloses.
    return redirect(url_for('main.ver_desgloses'))

# --- RUTAS PARA DESGLOSES ---
@main.route('/desgloses')
@login_required
def ver_desgloses():
    # Obtenemos todos los datos necesarios para los menús desplegables del formulario
    empresas = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas = Aerolinea.query.order_by(Aerolinea.nombre).all()
    empresas_booking = EmpresaBooking.query.order_by(EmpresaBooking.nombre).all()
    
    # Obtenemos la lista de desgloses existentes para mostrarlos
    lista_desgloses = Desglose.query.order_by(Desglose.folio.desc()).all()
    
    # Enviamos todos los datos a la plantilla HTML
    return render_template('desglose.html', 
                           empresas=empresas, 
                           aerolineas=aerolineas,
                           empresas_booking=empresas_booking,
                           desgloses=lista_desgloses)

@main.route('/desgloses/nuevo', methods=['POST'])
@login_required
def nuevo_desglose():
    # Crea un nuevo objeto Desglose con los datos del formulario
    nuevo = Desglose(
        folio=request.form.get('folio'),
        tarifa_base=request.form.get('tarifaBase'),
        iva=request.form.get('iva'),
        tua=request.form.get('tua'),
        total=request.form.get('total'),
        yr=request.form.get('yr'),
        otros_cargos=request.form.get('otrosCargos'),
        cargo_por_servicio=request.form.get('cargoPorServicio'),
        clave_reserva=request.form.get('clave_reserva', "PENDIENTE"),
        empresa_id=request.form.get('empresa_id'),
        aerolinea_id=request.form.get('aerolinea_id'),
        empresa_booking_id=request.form.get('empresa_booking_id'),
        usuario_id=current_user.id
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('¡Desglose registrado con éxito!', 'success')
    return redirect(url_for('main.ver_desgloses'))

# --- RUTAS PARA PAPELETAS ---
@main.route('/papeletas')
@login_required
def ver_papeletas():
    # Similar a desgloses, pasamos los datos necesarios para los formularios
    empresas = Empresa.query.order_by(Empresa.nombre_empresa).all()
    lista_papeletas = Papeleta.query.order_by(Papeleta.id.desc()).all()
    return render_template('papeletas.html', empresas=empresas, papeletas=lista_papeletas)

@main.route('/papeletas/nueva', methods=['POST'])
@login_required
def nueva_papeleta():
    # Convertimos la fecha de texto a un objeto de fecha de Python
    fecha_str = request.form.get('fechaVenta')
    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    nueva = Papeleta(
        folio=request.form.get('folio'),
        tarjeta=request.form.get('tarjeta'),
        fecha_venta=fecha_obj,
        total_ticket=request.form.get('totalTicket'),
        diez_porciento=request.form.get('diezPorciento'),
        cargo=request.form.get('cargo'),
        total=request.form.get('total'),
        facturar_a=request.form.get('facturarA'),
        solicito=request.form.get('solicito'),
        clave_sabre=request.form.get('claveSabre'),
        forma_pago=request.form.get('formaPago'),
        usuario_id=current_user.id,
        empresa_id=request.form.get('empresa_id')
    )
    db.session.add(nueva)
    db.session.commit()
    flash('¡Papeleta registrada con éxito!', 'success')
    return redirect(url_for('main.ver_papeletas'))

# --- RUTAS PARA EMPRESAS (Solo para Administradores) ---
@main.route('/empresas')
@login_required
def ver_empresas():
    # Protegemos la ruta para que solo los administradores puedan acceder
    if current_user.rol.nombre != 'administrador':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.index'))
    
    lista_empresas = Empresa.query.all()
    return render_template('empresas.html', empresas=lista_empresas)

@main.route('/empresas/nueva', methods=['POST'])
@login_required
def nueva_empresa():
    if current_user.rol.nombre != 'administrador':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.index'))
    
    # 1. Creamos la empresa principal
    nueva = Empresa(nombre_empresa=request.form.get('nombreEmpresa'))
    db.session.add(nueva)
    db.session.commit() # Hacemos commit para obtener el ID de la nueva empresa

    # 2. Creamos los registros en las tablas relacionadas (cargos, descuentos, etc.)
    if request.form.get('cargoServicioFacturado'):
        cargo = CargoServicio(empresa_id=nueva.id, tipo='visible', monto=request.form.get('cargoServicioFacturado'))
        db.session.add(cargo)
    
    if request.form.get('montoDescuento'):
        descuento = Descuento(empresa_id=nueva.id, tipo='monto', valor=request.form.get('montoDescuento'))
        db.session.add(descuento)

    if request.form.get('tarifaFija'):
        tarifa = TarifaFija(empresa_id=nueva.id, monto=request.form.get('tarifaFija'))
        db.session.add(tarifa)

    db.session.commit() # Hacemos el commit final para guardar todo
    flash(f'Empresa {nueva.nombre_empresa} registrada con éxito!', 'success')
    return redirect(url_for('main.ver_empresas'))

