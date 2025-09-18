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
    """Muestra la lista de todas las papeletas registradas."""
    papeletas_list = Papeleta.query.order_by(Papeleta.id.desc()).all()
    return render_template(
        'papeletas.html',
        papeletas_registradas=papeletas_list
    )

@main.route('/papeletas/nueva', methods=['GET'])
@login_required
def nueva_papeleta_form():
    """Muestra el formulario para crear una nueva papeleta."""
    # Esta es la lógica clave: obtenemos la lista de empresas para el menú desplegable.
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
        # 1. Convertir la fecha del formulario al formato correcto para la BD
        fecha_venta_str = request.form.get('fecha_venta')
        fecha_venta = datetime.strptime(fecha_venta_str, '%Y-%m-%d').date() if fecha_venta_str else None

        # 2. Crear el nuevo objeto Papeleta con todos los datos del formulario
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
            usuario_id=current_user.id  # Asignamos el ID del usuario logueado
        )
        
        # 3. Guardar en la base de datos
        db.session.add(nueva)
        db.session.commit()
        
        flash(f'Papeleta con folio {nueva.folio} creada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la papeleta: {str(e)}', 'danger')

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

        # 1. Crear la empresa principal
        nueva = Empresa(nombre_empresa=nombre)
        db.session.add(nueva)
        db.session.flush() # Obtenemos el ID de la nueva empresa

        # 2. Procesar y guardar los Cargos por Servicio
        cargo_facturado = request.form.get('cargoServicioFacturado')
        if cargo_facturado:
            nuevo_cargo_vis = CargoServicio(empresa_id=nueva.id, tipo='visible', monto=float(cargo_facturado))
            db.session.add(nuevo_cargo_vis)
        
        cargo_oculto = request.form.get('cargoServicioOculto')
        if cargo_oculto:
            nuevo_cargo_ocu = CargoServicio(empresa_id=nueva.id, tipo='oculto', monto=float(cargo_oculto))
            db.session.add(nuevo_cargo_ocu)

        # 3. Procesar y guardar los Descuentos
        monto_descuento = request.form.get('montoDescuento')
        if monto_descuento:
            nuevo_descuento = Descuento(empresa_id=nueva.id, tipo='monto', valor=float(monto_descuento))
            db.session.add(nuevo_descuento)
        
        # 4. Procesar y guardar las Tarifas Fijas
        tarifa_fija = request.form.get('tarifaFija')
        if tarifa_fija:
            nueva_tarifa = TarifaFija(empresa_id=nueva.id, monto=float(tarifa_fija))
            db.session.add(nueva_tarifa)

        db.session.commit()
        flash(f'Empresa "{nombre}" registrada con éxito.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al registrar la empresa: {str(e)}', 'danger')

    return redirect(url_for('main.empresas'))

@main.route('/empresas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_empresa(id):
    """
    Maneja tanto la visualización (GET) como la actualización (POST) 
    del formulario de edición de una empresa.
    """
    if current_user.rol_relacion.nombre != 'administrador':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    empresa = Empresa.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # 1. Actualizar el nombre de la empresa
            empresa.nombre_empresa = request.form.get('nombre_empresa')

            # 2. Borrar los registros antiguos para evitar duplicados
            CargoServicio.query.filter_by(empresa_id=id).delete()
            Descuento.query.filter_by(empresa_id=id).delete()
            TarifaFija.query.filter_by(empresa_id=id).delete()

            # 3. Crear los nuevos registros con la información del formulario
            cargo_facturado = request.form.get('cargoServicioFacturado')
            if cargo_facturado:
                nuevo_cargo_vis = CargoServicio(empresa_id=id, tipo='visible', monto=float(cargo_facturado))
                db.session.add(nuevo_cargo_vis)
            
            cargo_oculto = request.form.get('cargoServicioOculto')
            if cargo_oculto:
                nuevo_cargo_ocu = CargoServicio(empresa_id=id, tipo='oculto', monto=float(cargo_oculto))
                db.session.add(nuevo_cargo_ocu)
            
            monto_descuento = request.form.get('montoDescuento')
            if monto_descuento:
                nuevo_descuento = Descuento(empresa_id=id, tipo='monto', valor=float(monto_descuento))
                db.session.add(nuevo_descuento)
            
            tarifa_fija = request.form.get('tarifaFija')
            if tarifa_fija:
                nueva_tarifa = TarifaFija(empresa_id=id, monto=float(tarifa_fija))
                db.session.add(nueva_tarifa)

            db.session.commit()
            flash(f'Empresa "{empresa.nombre_empresa}" actualizada con éxito.', 'success')
            return redirect(url_for('main.empresas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar la empresa: {str(e)}', 'danger')
            # Si hay un error, redirigimos de vuelta al formulario de edición
            return redirect(url_for('main.editar_empresa', id=id))
    
    # Si es un método GET, simplemente mostramos el formulario de edición
    return render_template('empresa_edit.html', empresa=empresa)

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
