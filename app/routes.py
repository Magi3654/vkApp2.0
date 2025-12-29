# routes.py - Kinessia Hub v2.0
# Rutas actualizadas con sistema de tarjetas corporativas y autorizaciones

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .models import (
    db, Usuario, Rol, Papeleta, Desglose, Empresa, Aerolinea, EmpresaBooking, 
    CargoServicio, Descuento, TarifaFija, Sucursal, TarjetaCorporativa, Autorizacion,
    TarjetaUsuario
)
from datetime import datetime
from sqlalchemy import func

main = Blueprint('main', __name__)


# =============================================================================
# RUTAS PRINCIPALES
# =============================================================================

@main.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))


@main.route('/dashboard')
@login_required
def dashboard():
    # Contar autorizaciones pendientes para mostrar badge (solo para director)
    autorizaciones_pendientes = 0
    if current_user.rol in ['director', 'administrador', 'admin']:
        autorizaciones_pendientes = Autorizacion.query.filter_by(estatus='pendiente').count()
    
    return render_template('dashboard.html', 
                           usuario=current_user,
                           autorizaciones_pendientes=autorizaciones_pendientes)


# =============================================================================
# API ENDPOINTS
# =============================================================================

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
    tarjeta_id = request.args.get('tarjeta_id', '')

    # Si viene tarjeta_id, obtener el número de la tarjeta
    if tarjeta_id:
        tarjeta_obj = TarjetaCorporativa.query.get(tarjeta_id)
        if tarjeta_obj:
            tarjeta = tarjeta_obj.numero_tarjeta

    if not tarjeta or len(tarjeta) < 2:
        return jsonify({'error': 'Tarjeta inválida'}), 400

    # Buscar el último folio para esta tarjeta
    ultima_papeleta = Papeleta.query.filter(
        Papeleta.folio.like(f"{tarjeta}-%")
    ).order_by(Papeleta.id.desc()).first()

    if ultima_papeleta:
        try:
            ultimo_numero = int(ultima_papeleta.folio.split('-')[1])
            siguiente = ultimo_numero + 1
        except:
            siguiente = 1
    else:
        siguiente = 1

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


@main.route('/api/verificar-tarjeta/<int:tarjeta_id>')
@login_required
def verificar_tarjeta(tarjeta_id):
    """Verifica si una tarjeta requiere autorización para el usuario actual."""
    tarjeta = TarjetaCorporativa.query.get_or_404(tarjeta_id)
    
    requiere_autorizacion = tarjeta.requiere_autorizacion(current_user)
    tiene_autorizacion = False
    autorizacion_id = None
    
    if requiere_autorizacion:
        # Buscar si tiene una autorización vigente
        autorizacion = Autorizacion.query.filter_by(
            tarjeta_id=tarjeta_id,
            solicitante_id=current_user.id,
            estatus='aprobada'
        ).order_by(Autorizacion.fecha_respuesta.desc()).first()
        
        if autorizacion and autorizacion.esta_vigente(horas=24):
            tiene_autorizacion = True
            autorizacion_id = autorizacion.id
    
    return jsonify({
        'tarjeta_id': tarjeta_id,
        'numero_tarjeta': tarjeta.numero_tarjeta,
        'nombre_tarjeta': tarjeta.nombre_tarjeta,
        'sucursal': tarjeta.sucursal.nombre if tarjeta.sucursal else 'Sin asignar',
        'requiere_autorizacion': requiere_autorizacion,
        'tiene_autorizacion': tiene_autorizacion,
        'autorizacion_id': autorizacion_id,
        'puede_usar': not requiere_autorizacion or tiene_autorizacion
    })


@main.route('/api/tarjetas-disponibles')
@login_required
def tarjetas_disponibles():
    """Retorna las tarjetas disponibles para el usuario actual."""
    tarjetas = TarjetaCorporativa.query.filter_by(activa=True).all()
    
    resultado = []
    for t in tarjetas:
        requiere_auth = t.requiere_autorizacion(current_user)
        
        # Verificar si tiene autorización vigente
        tiene_auth = False
        if requiere_auth:
            auth = Autorizacion.query.filter_by(
                tarjeta_id=t.id,
                solicitante_id=current_user.id,
                estatus='aprobada'
            ).order_by(Autorizacion.fecha_respuesta.desc()).first()
            tiene_auth = auth and auth.esta_vigente(horas=24)
        
        resultado.append({
            'id': t.id,
            'numero_tarjeta': t.numero_tarjeta,
            'nombre_tarjeta': t.nombre_tarjeta,
            'banco': t.banco,
            'sucursal': t.sucursal.nombre if t.sucursal else None,
            'requiere_autorizacion': requiere_auth,
            'tiene_autorizacion': tiene_auth,
            'puede_usar': not requiere_auth or tiene_auth
        })
    
    # Ordenar: primero las que puede usar, luego las que requieren autorización
    resultado.sort(key=lambda x: (not x['puede_usar'], x['nombre_tarjeta']))
    
    return jsonify(resultado)


# =============================================================================
# RUTAS DE TARJETAS CORPORATIVAS (CRUD)
# =============================================================================

@main.route('/tarjetas')
@login_required
def tarjetas():
    """Lista todas las tarjetas corporativas."""
    if not current_user.es_gerente_o_superior():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    tarjetas_list = TarjetaCorporativa.query.order_by(TarjetaCorporativa.nombre_tarjeta).all()
    sucursales = Sucursal.query.filter_by(activa=True).all()
    
    return render_template('tarjetas.html', 
                           tarjetas=tarjetas_list, 
                           sucursales=sucursales)


@main.route('/tarjetas/nueva', methods=['POST'])
@login_required
def nueva_tarjeta():
    """Crea una nueva tarjeta corporativa."""
    if not current_user.es_gerente_o_superior():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        numero = request.form.get('numero_tarjeta', '').strip()
        nombre = request.form.get('nombre_tarjeta', '').strip()
        
        if not numero or not nombre:
            flash('El número y nombre de la tarjeta son obligatorios.', 'warning')
            return redirect(url_for('main.tarjetas'))
        
        # Verificar si ya existe
        if TarjetaCorporativa.query.filter_by(numero_tarjeta=numero).first():
            flash(f'Ya existe una tarjeta con el número {numero}.', 'warning')
            return redirect(url_for('main.tarjetas'))
        
        sucursal_id = request.form.get('sucursal_id')
        
        nueva = TarjetaCorporativa(
            numero_tarjeta=numero,
            nombre_tarjeta=nombre,
            banco=request.form.get('banco', '').strip() or None,
            titular=request.form.get('titular', '').strip() or None,
            sucursal_id=int(sucursal_id) if sucursal_id else None,
            activa=True
        )
        
        db.session.add(nueva)
        db.session.commit()
        
        flash(f'Tarjeta "{nombre}" registrada con éxito.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar la tarjeta: {str(e)}', 'danger')
    
    return redirect(url_for('main.tarjetas'))


@main.route('/tarjetas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_tarjeta(id):
    """Edita una tarjeta corporativa y sus asignaciones de agentes."""
    if not current_user.es_gerente_o_superior():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    tarjeta = TarjetaCorporativa.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            tarjeta.numero_tarjeta = request.form.get('numero_tarjeta', '').strip()
            tarjeta.nombre_tarjeta = request.form.get('nombre_tarjeta', '').strip()
            tarjeta.banco = request.form.get('banco', '').strip() or None
            tarjeta.titular = request.form.get('titular', '').strip() or None
            
            sucursal_id = request.form.get('sucursal_id')
            tarjeta.sucursal_id = int(sucursal_id) if sucursal_id else None
            
            tarjeta.activa = request.form.get('activa') == 'on'
            
            # Procesar asignaciones de agentes
            agentes_ids = request.form.getlist('agentes_ids')
            agentes_ids = [int(aid) for aid in agentes_ids if aid]
            
            # Eliminar asignaciones anteriores
            TarjetaUsuario.query.filter_by(tarjeta_id=tarjeta.id).delete()
            
            # Crear nuevas asignaciones
            for usuario_id in agentes_ids:
                nueva_asignacion = TarjetaUsuario(
                    tarjeta_id=tarjeta.id,
                    usuario_id=usuario_id,
                    asignado_por=current_user.id,
                    activo=True
                )
                db.session.add(nueva_asignacion)
            
            db.session.commit()
            flash(f'Tarjeta "{tarjeta.nombre_tarjeta}" actualizada con {len(agentes_ids)} agente(s) asignado(s).', 'success')
            return redirect(url_for('main.tarjetas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    # GET: Cargar datos para el formulario
    sucursales = Sucursal.query.filter_by(activa=True).all()
    
    # Mostrar TODOS los usuarios
    usuarios = Usuario.query.order_by(Usuario.nombre).all()
    
    # IDs de usuarios ya asignados a esta tarjeta
    usuarios_asignados_ids = [
        asig.usuario_id for asig in TarjetaUsuario.query.filter_by(
            tarjeta_id=tarjeta.id, 
            activo=True
        ).all()
    ]
    
    return render_template('tarjeta_edit.html', 
                           tarjeta=tarjeta, 
                           sucursales=sucursales,
                           usuarios=usuarios,
                           usuarios_asignados_ids=usuarios_asignados_ids)


@main.route('/tarjetas/eliminar/<int:id>')
@login_required
def eliminar_tarjeta(id):
    """Elimina una tarjeta corporativa."""
    if not current_user.es_admin():
        flash('Solo los administradores pueden eliminar tarjetas.', 'danger')
        return redirect(url_for('main.tarjetas'))
    
    tarjeta = TarjetaCorporativa.query.get_or_404(id)
    
    # Verificar si tiene papeletas asociadas
    if tarjeta.papeletas.count() > 0:
        flash('No se puede eliminar: la tarjeta tiene papeletas asociadas.', 'warning')
        return redirect(url_for('main.tarjetas'))
    
    nombre = tarjeta.nombre_tarjeta
    db.session.delete(tarjeta)
    db.session.commit()
    
    flash(f'Tarjeta "{nombre}" eliminada.', 'info')
    return redirect(url_for('main.tarjetas'))


# =============================================================================
# RUTAS DE AUTORIZACIONES
# =============================================================================

@main.route('/autorizaciones')
@login_required
def autorizaciones():
    """Lista de autorizaciones (pendientes para director, propias para agentes)."""
    if current_user.rol in ['director', 'administrador', 'admin']:
        # Director ve todas las pendientes
        lista = Autorizacion.query.filter_by(estatus='pendiente').order_by(
            Autorizacion.fecha_solicitud.asc()
        ).all()
        es_director = True
    else:
        # Agentes ven solo las suyas
        lista = Autorizacion.query.filter_by(solicitante_id=current_user.id).order_by(
            Autorizacion.fecha_solicitud.desc()
        ).all()
        es_director = False
    
    return render_template('autorizaciones.html', 
                           autorizaciones=lista, 
                           es_director=es_director)


@main.route('/autorizaciones/solicitar', methods=['POST'])
@login_required
def solicitar_autorizacion():
    """Solicita autorización para usar una tarjeta."""
    try:
        tarjeta_id = request.form.get('tarjeta_id')
        motivo = request.form.get('motivo', '').strip()
        
        if not tarjeta_id or not motivo:
            flash('Debe seleccionar una tarjeta y proporcionar un motivo.', 'warning')
            return redirect(url_for('main.nueva_papeleta_form'))
        
        tarjeta = TarjetaCorporativa.query.get_or_404(tarjeta_id)
        
        # Verificar si ya tiene una solicitud pendiente para esta tarjeta
        existente = Autorizacion.query.filter_by(
            tarjeta_id=tarjeta_id,
            solicitante_id=current_user.id,
            estatus='pendiente'
        ).first()
        
        if existente:
            flash('Ya tienes una solicitud pendiente para esta tarjeta.', 'warning')
            return redirect(url_for('main.autorizaciones'))
        
        # Crear la solicitud
        nueva_auth = Autorizacion(
            tipo='uso_tarjeta',
            solicitante_id=current_user.id,
            tarjeta_id=tarjeta_id,
            motivo=motivo,
            sucursal_id=current_user.sucursal_id or 1  # Default a primera sucursal si no tiene
        )
        
        db.session.add(nueva_auth)
        db.session.commit()
        
        flash(f'Solicitud de autorización enviada para tarjeta {tarjeta.nombre_tarjeta}. '
              f'Espera la aprobación de Dirección.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al solicitar autorización: {str(e)}', 'danger')
    
    return redirect(url_for('main.autorizaciones'))


@main.route('/autorizaciones/responder/<int:id>', methods=['POST'])
@login_required
def responder_autorizacion(id):
    """Aprueba o rechaza una autorización (solo director)."""
    if current_user.rol not in ['director', 'administrador', 'admin']:
        flash('Solo Dirección puede aprobar autorizaciones.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    autorizacion = Autorizacion.query.get_or_404(id)
    
    if autorizacion.estatus != 'pendiente':
        flash('Esta autorización ya fue respondida.', 'warning')
        return redirect(url_for('main.autorizaciones'))
    
    accion = request.form.get('accion')
    comentario = request.form.get('comentario', '').strip()
    
    try:
        if accion == 'aprobar':
            autorizacion.aprobar(current_user, comentario)
            flash(f'Autorización APROBADA para {autorizacion.solicitante.nombre}.', 'success')
        elif accion == 'rechazar':
            autorizacion.rechazar(current_user, comentario)
            flash(f'Autorización RECHAZADA para {autorizacion.solicitante.nombre}.', 'info')
        else:
            flash('Acción no válida.', 'warning')
            return redirect(url_for('main.autorizaciones'))
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('main.autorizaciones'))


# =============================================================================
# RUTAS DE PAPELETAS (ACTUALIZADAS)
# =============================================================================

@main.route('/papeletas', methods=['GET'])
@login_required
def consulta_papeletas():
    """Muestra la lista de papeletas (filtradas por sucursal si aplica)."""
    if current_user.es_admin():
        # Admin ve todas
        papeletas_list = Papeleta.query.order_by(Papeleta.id.desc()).all()
    elif current_user.es_gerente_o_superior():
        # Gerente ve las de su sucursal
        papeletas_list = Papeleta.query.filter_by(
            sucursal_id=current_user.sucursal_id
        ).order_by(Papeleta.id.desc()).all()
    else:
        # Agente ve solo las suyas
        papeletas_list = Papeleta.query.filter_by(
            usuario_id=current_user.id
        ).order_by(Papeleta.id.desc()).all()
    
    return render_template('consulta_papeletas.html', papeletas_registradas=papeletas_list)


@main.route('/papeletas/nueva', methods=['GET'])
@login_required
def nueva_papeleta_form():
    """Muestra el formulario para crear una nueva papeleta."""
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    tarjetas_list = TarjetaCorporativa.query.filter_by(activa=True).order_by(
        TarjetaCorporativa.nombre_tarjeta
    ).all()
    
    # Preparar info de tarjetas con estado de autorización
    tarjetas_info = []
    for t in tarjetas_list:
        requiere_auth = t.requiere_autorizacion(current_user)
        tiene_auth = False
        
        if requiere_auth:
            auth = Autorizacion.query.filter_by(
                tarjeta_id=t.id,
                solicitante_id=current_user.id,
                estatus='aprobada'
            ).order_by(Autorizacion.fecha_respuesta.desc()).first()
            tiene_auth = auth and auth.esta_vigente(horas=24)
        
        tarjetas_info.append({
            'tarjeta': t,
            'requiere_autorizacion': requiere_auth,
            'tiene_autorizacion': tiene_auth,
            'puede_usar': not requiere_auth or tiene_auth
        })
    
    return render_template(
        'papeletas.html',
        empresas=empresas_list,
        aerolineas=aerolineas_list,
        tarjetas_info=tarjetas_info
    )


@main.route('/papeletas/nueva', methods=['POST'])
@login_required
def nueva_papeleta_post():
    """Recibe los datos del formulario y crea una nueva papeleta."""
    try:
        # 1. Obtener tarjeta (puede ser del dropdown o manual)
        tarjeta_id = request.form.get('tarjeta_id')
        tarjeta_manual = request.form.get('tarjeta_manual', '').strip()
        
        tarjeta_numero = None
        tarjeta_obj = None
        autorizacion_id = None
        
        if tarjeta_id:
            # Usar tarjeta del catálogo
            tarjeta_obj = TarjetaCorporativa.query.get(tarjeta_id)
            if not tarjeta_obj:
                flash('Tarjeta no encontrada.', 'danger')
                return redirect(url_for('main.nueva_papeleta_form'))
            
            tarjeta_numero = tarjeta_obj.numero_tarjeta
            
            # Verificar autorización si es necesaria
            if tarjeta_obj.requiere_autorizacion(current_user):
                auth = Autorizacion.query.filter_by(
                    tarjeta_id=tarjeta_id,
                    solicitante_id=current_user.id,
                    estatus='aprobada'
                ).order_by(Autorizacion.fecha_respuesta.desc()).first()
                
                if not auth or not auth.esta_vigente(horas=24):
                    flash('Necesitas autorización vigente para usar esta tarjeta.', 'danger')
                    return redirect(url_for('main.nueva_papeleta_form'))
                
                autorizacion_id = auth.id
        
        elif tarjeta_manual:
            # Usar tarjeta manual
            if len(tarjeta_manual) != 4 or not tarjeta_manual.isdigit():
                flash('La terminación de tarjeta debe ser de 4 dígitos.', 'warning')
                return redirect(url_for('main.nueva_papeleta_form'))
            tarjeta_numero = tarjeta_manual
        else:
            flash('Debe seleccionar o ingresar una tarjeta.', 'warning')
            return redirect(url_for('main.nueva_papeleta_form'))
        
        # 2. Convertir fecha
        fecha_venta_str = request.form.get('fecha_venta')
        fecha_venta = datetime.strptime(fecha_venta_str, '%Y-%m-%d').date() if fecha_venta_str else None

        # 3. Procesar empresa
        empresa_id_str = request.form.get('facturar_a')
        empresa_id = int(empresa_id_str) if empresa_id_str else None

        # 4. Obtener nombre de empresa
        facturar_a_nombre = ''
        if empresa_id:
            empresa = Empresa.query.get(empresa_id)
            facturar_a_nombre = empresa.nombre_empresa if empresa else ''

        # 5. Procesar aerolínea
        aerolinea_id_str = request.form.get('aerolinea_id')
        aerolinea_id = int(aerolinea_id_str) if aerolinea_id_str else None

        # 6. Generar folio
        folio = request.form.get('folio')
        if not folio:
            # Generar automáticamente si no viene
            ultima = Papeleta.query.filter(
                Papeleta.folio.like(f"{tarjeta_numero}-%")
            ).order_by(Papeleta.id.desc()).first()
            
            if ultima:
                try:
                    num = int(ultima.folio.split('-')[1]) + 1
                except:
                    num = 1
            else:
                num = 1
            folio = f"{tarjeta_numero}-{num:03d}"

        # 7. Crear la papeleta
        nueva = Papeleta(
            folio=folio,
            tarjeta=tarjeta_numero,
            tarjeta_id=int(tarjeta_id) if tarjeta_id else None,
            fecha_venta=fecha_venta,
            total_ticket=float(request.form.get('total_ticket', 0)),
            diez_porciento=float(request.form.get('diez_porciento', 0)),
            cargo=float(request.form.get('cargo', 0)),
            total=float(request.form.get('total', 0)),
            facturar_a=facturar_a_nombre,
            solicito=request.form.get('solicito', ''),
            clave_sabre=request.form.get('clave_sabre', ''),
            forma_pago=request.form.get('forma_pago', ''),
            empresa_id=empresa_id,
            aerolinea_id=aerolinea_id,
            usuario_id=current_user.id,
            autorizacion_id=autorizacion_id,
            sucursal_id=current_user.sucursal_id
        )

        db.session.add(nueva)
        db.session.commit()

        flash(f'Papeleta con folio {nueva.folio} creada con éxito.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la papeleta: {str(e)}', 'danger')

    return redirect(url_for('main.consulta_papeletas'))


# =============================================================================
# RUTAS DE DESGLOSES (Sin cambios significativos)
# =============================================================================

@main.route('/desgloses', methods=['GET'])
@login_required
def desgloses():
    if current_user.es_admin():
        desgloses_list = Desglose.query.order_by(Desglose.folio.desc()).all()
    else:
        desgloses_list = Desglose.query.filter_by(
            usuario_id=current_user.id
        ).order_by(Desglose.folio.desc()).all()
    
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
            usuario_id=current_user.id,
            sucursal_id=current_user.sucursal_id
        )

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
    desglose = Desglose.query.get_or_404(folio)

    if request.method == 'POST':
        try:
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
    desglose_a_eliminar = Desglose.query.get_or_404(folio)

    try:
        db.session.delete(desglose_a_eliminar)
        db.session.commit()
        flash(f'Desglose con folio {folio} eliminado con éxito.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el desglose: {str(e)}', 'danger')

    return redirect(url_for('main.desgloses'))


# =============================================================================
# RUTAS DE EMPRESAS (Sin cambios)
# =============================================================================

@main.route('/empresas', methods=['GET'])
@login_required
def empresas():
    if current_user.rol_relacion.nombre not in ['administrador', 'admin', 'director', 'gerente']:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    lista_empresas = Empresa.query.order_by(Empresa.nombre_empresa).all()
    return render_template('empresas.html', empresas_registradas=lista_empresas)


@main.route('/empresas/nueva', methods=['POST'])
@login_required
def nueva_empresa():
    if current_user.rol_relacion.nombre not in ['administrador', 'admin', 'director']:
        return redirect(url_for('main.dashboard'))

    try:
        nombre = request.form.get('nombre_empresa')
        if not nombre:
            flash('El nombre de la empresa no puede estar vacío.', 'warning')
            return redirect(url_for('main.empresas'))

        nueva = Empresa(
            nombre_empresa=nombre,
            sucursal_id=current_user.sucursal_id
        )
        db.session.add(nueva)
        db.session.flush()

        cargo_facturado = request.form.get('cargoServicioFacturado')
        if cargo_facturado:
            nuevo_cargo_vis = CargoServicio(empresa_id=nueva.id, tipo='visible', monto=float(cargo_facturado))
            db.session.add(nuevo_cargo_vis)
        
        cargo_oculto = request.form.get('cargoServicioOculto')
        if cargo_oculto:
            nuevo_cargo_ocu = CargoServicio(empresa_id=nueva.id, tipo='oculto', monto=float(cargo_oculto))
            db.session.add(nuevo_cargo_ocu)

        monto_descuento = request.form.get('montoDescuento')
        if monto_descuento:
            nuevo_descuento = Descuento(empresa_id=nueva.id, tipo='monto', valor=float(monto_descuento))
            db.session.add(nuevo_descuento)
        
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
    if current_user.rol_relacion.nombre not in ['administrador', 'admin', 'director']:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    empresa = Empresa.query.get_or_404(id)

    if request.method == 'POST':
        try:
            empresa.nombre_empresa = request.form.get('nombre_empresa')

            CargoServicio.query.filter_by(empresa_id=id).delete()
            Descuento.query.filter_by(empresa_id=id).delete()
            TarifaFija.query.filter_by(empresa_id=id).delete()

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
            return redirect(url_for('main.editar_empresa', id=id))
    
    return render_template('empresa_edit.html', empresa=empresa)


@main.route('/empresas/eliminar/<int:id>')
@login_required
def eliminar_empresa(id):
    if current_user.rol_relacion.nombre not in ['administrador', 'admin', 'director']:
        return redirect(url_for('main.dashboard'))

    empresa_a_eliminar = Empresa.query.get_or_404(id)
    db.session.delete(empresa_a_eliminar)
    db.session.commit()
    
    flash(f'La empresa "{empresa_a_eliminar.nombre_empresa}" ha sido eliminada.', 'info')
    return redirect(url_for('main.empresas'))


# =============================================================================
# RUTAS DE SUCURSALES (CRUD)
# =============================================================================

@main.route('/sucursales')
@login_required
def sucursales():
    """Lista de sucursales (solo admin)."""
    if not current_user.es_admin():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    lista = Sucursal.query.order_by(Sucursal.nombre).all()
    return render_template('sucursales.html', sucursales=lista)


@main.route('/sucursales/nueva', methods=['POST'])
@login_required
def nueva_sucursal():
    if not current_user.es_admin():
        return redirect(url_for('main.dashboard'))
    
    try:
        nueva = Sucursal(
            nombre=request.form.get('nombre', '').strip(),
            ciudad=request.form.get('ciudad', '').strip(),
            direccion=request.form.get('direccion', '').strip() or None,
            telefono=request.form.get('telefono', '').strip() or None
        )
        db.session.add(nueva)
        db.session.commit()
        flash(f'Sucursal "{nueva.nombre}" creada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('main.sucursales'))