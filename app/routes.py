from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import db, Usuario, Rol, Papeleta, Desglose, Empresa, Aerolinea, EmpresaBooking, CargoServicio, Descuento, TarifaFija
from datetime import datetime

main = Blueprint('main', __name__)

# --- RUTAS PRINCIPALES ---

@main.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

# --- RUTAS DE DESGLOSES (Refactorizadas) ---

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
    # ... (lógica para guardar desglose) ...
    flash('Desglose creado con éxito.', 'success')
    return redirect(url_for('main.desgloses'))

# --- RUTAS DE PAPELETAS (Refactorizadas) ---

@main.route('/papeletas', methods=['GET'])
@login_required
def consulta_papeletas():
    papeletas_list = Papeleta.query.order_by(Papeleta.id.desc()).all()
    return render_template('consulta_papeletas.html', papeletas_registradas=papeletas_list)

@main.route('/papeletas/nueva', methods=['GET'])
@login_required
def nueva_papeleta_form():
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    return render_template('papeletas.html', empresas=empresas_list)

@main.route('/papeletas/nueva', methods=['POST'])
@login_required
def nueva_papeleta_post():
    # ... (lógica para guardar papeleta) ...
    flash('Papeleta creada con éxito.', 'success')
    return redirect(url_for('main.consulta_papeletas'))

# --- RUTAS DE EMPRESAS (CRUD COMPLETO) ---

@main.route('/empresas', methods=['GET'])
@login_required
def empresas():
    """Muestra el formulario y la lista de empresas existentes."""
    if current_user.rol_relacion.nombre != 'administrador':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    lista_empresas = Empresa.query.order_by(Empresa.nombre_empresa).all()
    return render_template('empresas.html', empresas_registradas=lista_empresas)

@main.route('/empresas/nueva', methods=['POST'])
@login_required
def nueva_empresa():
    """Recibe los datos del formulario y crea una nueva empresa con sus reglas de negocio."""
    if current_user.rol_relacion.nombre != 'administrador':
        return redirect(url_for('main.dashboard'))

    try:
        nombre = request.form.get('nombre_empresa')
        if not nombre:
            flash('El nombre de la empresa no puede estar vacío.', 'warning')
            return redirect(url_for('main.empresas'))

        nueva = Empresa(nombre_empresa=nombre)
        db.session.add(nueva)
        db.session.flush()

        # ... (lógica para guardar cargos, descuentos, etc.) ...
        
        db.session.commit()
        flash(f'Empresa "{nombre}" registrada con éxito.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al registrar la empresa: {str(e)}', 'danger')

    return redirect(url_for('main.empresas'))


# --- ¡NUEVAS RUTAS PARA EDITAR EMPRESAS! ---

@main.route('/empresas/editar/<int:id>', methods=['GET'])
@login_required
def editar_empresa_form(id):
    """Muestra el formulario para editar una empresa, pre-llenado con sus datos."""
    if current_user.rol_relacion.nombre != 'administrador':
        return redirect(url_for('main.dashboard'))
        
    empresa = Empresa.query.get_or_404(id)
    return render_template('empresa_edit.html', empresa=empresa)

@main.route('/empresas/editar/<int:id>', methods=['POST'])
@login_required
def editar_empresa_post(id):
    """Procesa los datos del formulario de edición y actualiza la empresa."""
    if current_user.rol_relacion.nombre != 'administrador':
        return redirect(url_for('main.dashboard'))

    empresa = Empresa.query.get_or_404(id)
    try:
        # Actualizar el nombre de la empresa
        empresa.nombre_empresa = request.form.get('nombre_empresa')

        # Lógica para actualizar cargos, descuentos, etc.
        # La forma más simple es borrar los antiguos y crear los nuevos.
        CargoServicio.query.filter_by(empresa_id=id).delete()
        Descuento.query.filter_by(empresa_id=id).delete()
        TarifaFija.query.filter_by(empresa_id=id).delete()

        # ... (pegar aquí la misma lógica de creación que en 'nueva_empresa') ...
        
        db.session.commit()
        flash(f'Empresa "{empresa.nombre_empresa}" actualizada con éxito.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al actualizar la empresa: {str(e)}', 'danger')

    return redirect(url_for('main.empresas'))


@main.route('/empresas/eliminar/<int:id>')
@login_required
def eliminar_empresa(id):
    """Elimina una empresa y todos sus registros asociados en cascada."""
    if current_user.rol_relacion.nombre != 'administrador':
        return redirect(url_for('main.dashboard'))

    empresa_a_eliminar = Empresa.query.get_or_404(id)
    db.session.delete(empresa_a_eliminar)
    db.session.commit()
    
    flash(f'La empresa "{empresa_a_eliminar.nombre_empresa}" ha sido eliminada.', 'info')
    return redirect(url_for('main.empresas'))

