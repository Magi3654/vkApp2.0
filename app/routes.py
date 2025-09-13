from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
# Asegúrate de importar todos los modelos necesarios
from .models import db, Usuario, Rol, Papeleta, Desglose, Empresa, Aerolinea, EmpresaBooking
from datetime import datetime

main = Blueprint('main', __name__)

# --- RUTAS EXISTENTES ---
@main.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

@main.route('/empresas')
@login_required
def empresas():
    if current_user.rol_relacion.nombre != 'administrador':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('empresas.html')

# --- LÓGICA DE DESGLOSES (Se mantiene igual) ---
@main.route('/desgloses', methods=['GET'])
@login_required
def desgloses():
    desgloses_list = Desglose.query.order_by(Desglose.folio.desc()).all()
    return render_template('consulta_desgloses.html', desgloses_registrados=desgloses_list)

@main.route('/desgloses/nuevo', methods=['GET'])
@login_required
def nuevo_desglose_form():
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    empresas_booking_list = EmpresaBooking.query.order_by(EmpresaBooking.nombre).all()
    return render_template(
        'desgloses.html', 
        empresas=empresas_list, 
        aerolineas=aerolineas_list,
        empresas_booking=empresas_booking_list
    )

@main.route('/desgloses/nuevo', methods=['POST'])
@login_required
def nuevo_desglose_post():
    try:
        # ... (lógica para guardar desglose) ...
        folio = int(request.form.get('folio'))
        # (resto de la lógica de guardado)
        nuevo = Desglose(folio=folio, usuario_id=current_user.id) # Ejemplo simplificado
        db.session.add(nuevo)
        db.session.commit()
        flash(f'Desglose con folio {folio} creado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el desglose: {str(e)}', 'danger')
    return redirect(url_for('main.desgloses'))

# --- LÓGICA PARA PAPELETAS (REFACTORIZADA) ---

@main.route('/papeletas', methods=['GET'])
@login_required
def consulta_papeletas():
    """Muestra la lista de papeletas existentes."""
    papeletas_list = Papeleta.query.order_by(Papeleta.id.desc()).all()
    return render_template(
        'consulta_papeletas.html',
        papeletas_registradas=papeletas_list
    )

@main.route('/papeletas/nueva', methods=['GET'])
@login_required
def nueva_papeleta_form():
    """Muestra el formulario para crear una nueva papeleta."""
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    return render_template(
        'papeletas.html',
        empresas=empresas_list
    )

@main.route('/papeletas/nueva', methods=['POST'])
@login_required
def nueva_papeleta_post():
    """Recibe los datos del formulario y crea una nueva papeleta."""
    try:
        fecha_venta_str = request.form.get('fecha_venta')
        fecha_venta = datetime.strptime(fecha_venta_str, '%Y-%m-%d').date() if fecha_venta_str else None

        nueva = Papeleta(
            folio=request.form.get('folio'),
            tarjeta=request.form.get('tarjeta'),
            fecha_venta=fecha_venta,
            total_ticket=float(request.form.get('total_ticket')),
            diez_porciento=float(request.form.get('diez_porciento')),
            cargo=float(request.form.get('cargo')),
            total=float(request.form.get('total')),
            facturar_a=request.form.get('facturar_a'),
            solicito=request.form.get('solicito'),
            clave_sabre=request.form.get('clave_sabre'),
            forma_pago=request.form.get('forma_pago'),
            empresa_id=int(request.form.get('empresa_id')),
            usuario_id=current_user.id
        )
        
        db.session.add(nueva)
        db.session.commit()
        
        flash(f'Papeleta con folio {nueva.folio} creada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la papeleta: {str(e)}', 'danger')

    return redirect(url_for('main.consulta_papeletas'))

