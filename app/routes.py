from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .models import db, Usuario, Rol, Papeleta, Desglose, Empresa, Aerolinea, EmpresaBooking, CargoServicio, Descuento, TarifaFija
from datetime import datetime
from sqlalchemy import func

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

# --- API ENDPOINTS ---

@main.route('/api/siguiente-folio-desglose')
@login_required
def siguiente_folio_desglose():
    """Retorna el siguiente folio disponible para desgloses."""
    ultimo_folio = db.session.query(func.max(Desglose.folio)).scalar()
    siguiente = (ultimo_folio or 0) + 1
    return jsonify({'folio': siguiente})

@main.route('/api/siguiente-folio-papeleta')
@login_required
def siguiente_folio_papeleta():
    """Retorna el siguiente folio disponible para una tarjeta específica."""
    tarjeta = request.args.get('tarjeta', '')

    if not tarjeta or len(tarjeta) != 4:
        return jsonify({'error': 'Tarjeta inválida'}), 400

    # Buscar el último folio para esta tarjeta
    ultima_papeleta = Papeleta.query.filter_by(tarjeta=tarjeta).order_by(Papeleta.id.desc()).first()

    if ultima_papeleta:
        # Extraer el número del folio (formato: XXXX-001)
        try:
            ultimo_numero = int(ultima_papeleta.folio.split('-')[1])
            siguiente = ultimo_numero + 1
        except:
            siguiente = 1
    else:
        siguiente = 1

    # Formato: 1234-001
    folio = f"{tarjeta}-{siguiente:03d}"

    return jsonify({'folio': folio, 'numero': siguiente})

@main.route('/api/cargos-empresa/<int:empresa_id>')
@login_required
def cargos_empresa(empresa_id):
    """Retorna los cargos por servicio de una empresa."""
    empresa = Empresa.query.get_or_404(empresa_id)

    cargo_visible = None
    cargo_oculto = None

    for cargo in empresa.cargos_servicio:
        if cargo.tipo == 'visible':
            cargo_visible = float(cargo.monto)
        elif cargo.tipo == 'oculto':
            cargo_oculto = float(cargo.monto)

    return jsonify({
        'cargo_visible': cargo_visible,
        'cargo_oculto': cargo_oculto
    })

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
    """Recibe los datos del formulario y crea un nuevo desglose."""
    try:
        # Crear el nuevo objeto Desglose con todos los datos del formulario
        nuevo = Desglose(
            folio=int(request.form.get('folio')),
            empresa_id=int(request.form.get('empresa_id')),
            aerolinea_id=int(request.form.get('aerolinea_id')),
            empresa_booking_id=int(request.form.get('empresa_booking_id')),
            tarifa_base=float(request.form.get('tarifa_base')),
            iva=float(request.form.get('iva')),
            tua=float(request.form.get('tua')),
            yr=float(request.form.get('yr')),
            otros_cargos=float(request.form.get('otros_cargos')),
            cargo_por_servicio=float(request.form.get('cargo_por_servicio')),
            total=float(request.form.get('total')),
            clave_reserva=request.form.get('clave_reserva'),
            usuario_id=current_user.id  # Asignamos el ID del usuario logueado
        )

        # Guardar en la base de datos
        db.session.add(nuevo)
        db.session.commit()

        flash(f'Desglose con folio {nuevo.folio} creado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el desglose: {str(e)}', 'danger')

    return redirect(url_for('main.desgloses'))

@main.route('/desgloses/editar/<int:folio>', methods=['GET', 'POST'])
@login_required
def editar_desglose(folio):
    """Maneja la edición de un desglose existente."""
    desglose = Desglose.query.get_or_404(folio)

    if request.method == 'POST':
        try:
            # Actualizar los campos del desglose
            desglose.empresa_id = int(request.form.get('empresa_id'))
            desglose.aerolinea_id = int(request.form.get('aerolinea_id'))
            desglose.empresa_booking_id = int(request.form.get('empresa_booking_id'))
            desglose.tarifa_base = float(request.form.get('tarifa_base'))
            desglose.iva = float(request.form.get('iva'))
            desglose.tua = float(request.form.get('tua'))
            desglose.yr = float(request.form.get('yr'))
            desglose.otros_cargos = float(request.form.get('otros_cargos'))
            desglose.cargo_por_servicio = float(request.form.get('cargo_por_servicio'))
            desglose.total = float(request.form.get('total'))
            desglose.clave_reserva = request.form.get('clave_reserva')

            db.session.commit()
            flash(f'Desglose con folio {desglose.folio} actualizado con éxito.', 'success')
            return redirect(url_for('main.desgloses'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el desglose: {str(e)}', 'danger')
            return redirect(url_for('main.editar_desglose', folio=folio))

    # GET: Mostrar formulario de edición
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    empresas_booking_list = EmpresaBooking.query.order_by(EmpresaBooking.nombre).all()

    return render_template(
        'desglose_edit.html',
        desglose=desglose,
        empresas=empresas_list,
        aerolineas=aerolineas_list,
        empresas_booking=empresas_booking_list
    )

@main.route('/desgloses/eliminar/<int:folio>')
@login_required
def eliminar_desglose(folio):
    """Elimina un desglose."""
    desglose_a_eliminar = Desglose.query.get_or_404(folio)

    try:
        db.session.delete(desglose_a_eliminar)
        db.session.commit()
        flash(f'Desglose con folio {folio} eliminado con éxito.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el desglose: {str(e)}', 'danger')

    return redirect(url_for('main.desgloses'))

# --- RUTAS DE PAPELETAS (Refactorizadas) ---

@main.route('/papeletas', methods=['GET'])
@login_required
def consulta_papeletas():
    """Muestra la lista de todas las papeletas registradas."""
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
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    return render_template(
        'papeletas.html',
        empresas=empresas_list,
        aerolineas=aerolineas_list
    )

@main.route('/papeletas/nueva', methods=['POST'])
@login_required
def nueva_papeleta_post():
    """Recibe los datos del formulario y crea una nueva papeleta."""
    try:
        # 1. Convertir la fecha del formulario al formato correcto para la BD
        fecha_venta_str = request.form.get('fecha_venta')
        fecha_venta = datetime.strptime(fecha_venta_str, '%Y-%m-%d').date() if fecha_venta_str else None

        # 2. Procesar empresa_id (ahora viene de facturar_a)
        empresa_id_str = request.form.get('facturar_a')
        empresa_id = int(empresa_id_str) if empresa_id_str else None

        # 3. Procesar aerolinea_id (puede ser None)
        aerolinea_id_str = request.form.get('aerolinea_id')
        aerolinea_id = int(aerolinea_id_str) if aerolinea_id_str else None

        # 4. Obtener nombre de empresa para facturar_a
        facturar_a_nombre = ''
        if empresa_id:
            empresa = Empresa.query.get(empresa_id)
            facturar_a_nombre = empresa.nombre_empresa if empresa else ''

        # 5. Crear el nuevo objeto Papeleta con todos los datos del formulario
        nueva = Papeleta(
            folio=request.form.get('folio'),
            tarjeta=request.form.get('tarjeta'),
            fecha_venta=fecha_venta,
            total_ticket=float(request.form.get('total_ticket')),
            diez_porciento=float(request.form.get('diez_porciento')),
            cargo=float(request.form.get('cargo')),
            total=float(request.form.get('total')),
            facturar_a=facturar_a_nombre,
            solicito=request.form.get('solicito'),
            clave_sabre=request.form.get('clave_sabre'),
            forma_pago=request.form.get('forma_pago'),
            empresa_id=empresa_id,
            aerolinea_id=aerolinea_id,
            usuario_id=current_user.id  # Asignamos el ID del usuario logueado
        )

        # 6. Guardar en la base de datos
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
