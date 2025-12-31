# routes.py - Kinessia Hub v2.0
# Rutas actualizadas con sistema de tarjetas corporativas, autorizaciones y gestión de usuarios

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .models import (
    db, Usuario, Rol, Papeleta, Desglose, Empresa, Aerolinea, EmpresaBooking, 
    CargoServicio, Descuento, TarifaFija, Sucursal, TarjetaCorporativa, Autorizacion,
    TarjetaUsuario, AuditLog
)
from datetime import datetime, timedelta
from sqlalchemy import func
from collections import OrderedDict

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
    ultimo_folio = db.session.query(func.max(Desglose.folio)).scalar()
    siguiente = (ultimo_folio or 0) + 1
    return jsonify({'folio': siguiente})


@main.route('/api/siguiente-folio-papeleta')
@login_required
def siguiente_folio_papeleta():
    tarjeta = request.args.get('tarjeta', '')
    tarjeta_id = request.args.get('tarjeta_id', '')

    if tarjeta_id:
        tarjeta_obj = TarjetaCorporativa.query.get(tarjeta_id)
        if tarjeta_obj:
            tarjeta = tarjeta_obj.numero_tarjeta

    if not tarjeta or len(tarjeta) < 2:
        return jsonify({'error': 'Tarjeta inválida'}), 400

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
    empresa = Empresa.query.get_or_404(empresa_id)
    cargo_visible = None
    cargo_oculto = None

    for cargo in empresa.cargos_servicio:
        if cargo.tipo == 'visible':
            cargo_visible = float(cargo.monto)
        elif cargo.tipo == 'oculto':
            cargo_oculto = float(cargo.monto)

    return jsonify({'cargo_visible': cargo_visible, 'cargo_oculto': cargo_oculto})


@main.route('/api/papeleta/<int:id>')
@login_required
def api_papeleta_detalle(id):
    """API para obtener el detalle de una papeleta."""
    papeleta = Papeleta.query.get(id)
    if not papeleta:
        return jsonify({'error': 'Papeleta no encontrada'}), 404
    
    tarjeta_nombre = papeleta.tarjeta_rel.nombre_tarjeta if papeleta.tarjeta_rel else ''
    aerolinea_nombre = papeleta.aerolinea.nombre if papeleta.aerolinea else ''
    
    papeleta_relacionada_folio = ''
    if papeleta.papeleta_relacionada_id:
        pap_rel = Papeleta.query.get(papeleta.papeleta_relacionada_id)
        if pap_rel:
            papeleta_relacionada_folio = pap_rel.folio
    
    return jsonify({
        'id': papeleta.id,
        'folio': papeleta.folio,
        'tarjeta': papeleta.tarjeta,
        'tarjeta_nombre': tarjeta_nombre,
        'fecha_venta': papeleta.fecha_venta.strftime('%d/%m/%Y') if papeleta.fecha_venta else '',
        'total_ticket': float(papeleta.total_ticket or 0),
        'diez_porciento': float(papeleta.diez_porciento or 0),
        'cargo': float(papeleta.cargo or 0),
        'total': float(papeleta.total or 0),
        'facturar_a': papeleta.facturar_a or '',
        'solicito': papeleta.solicito or '',
        'clave_sabre': papeleta.clave_sabre or '',
        'forma_pago': papeleta.forma_pago or '',
        'aerolinea': aerolinea_nombre,
        'proveedor': papeleta.proveedor or '',
        'tipo_cargo': papeleta.tipo_cargo or '',
        'extemporanea': papeleta.extemporanea or False,
        'fecha_cargo_real': papeleta.fecha_cargo_real.strftime('%d/%m/%Y') if papeleta.fecha_cargo_real else '',
        'motivo_extemporanea': papeleta.motivo_extemporanea or '',
        'tiene_reembolso': papeleta.tiene_reembolso or False,
        'estatus_reembolso': papeleta.estatus_reembolso or '',
        'motivo_reembolso': papeleta.motivo_reembolso or '',
        'monto_reembolso': float(papeleta.monto_reembolso) if papeleta.monto_reembolso else None,
        'fecha_solicitud_reembolso': papeleta.fecha_solicitud_reembolso.strftime('%d/%m/%Y') if papeleta.fecha_solicitud_reembolso else '',
        'referencia_reembolso': papeleta.referencia_reembolso or '',
        'papeleta_relacionada': papeleta_relacionada_folio,
        'usuario': papeleta.usuario.nombre if papeleta.usuario else '',
        'created_at': papeleta.created_at.strftime('%d/%m/%Y %H:%M') if papeleta.created_at else ''
    })


@main.route('/api/verificar-tarjeta/<int:tarjeta_id>')
@login_required
def verificar_tarjeta(tarjeta_id):
    tarjeta = TarjetaCorporativa.query.get_or_404(tarjeta_id)
    requiere_autorizacion = tarjeta.requiere_autorizacion(current_user)
    tiene_autorizacion = False
    autorizacion_id = None
    tiempo_restante = None
    fecha_expiracion = None
    
    if requiere_autorizacion:
        autorizacion = Autorizacion.query.filter_by(
            tarjeta_id=tarjeta_id,
            solicitante_id=current_user.id,
            estatus='aprobada'
        ).order_by(Autorizacion.fecha_respuesta.desc()).first()
        
        if autorizacion and autorizacion.esta_vigente(horas=24):
            tiene_autorizacion = True
            autorizacion_id = autorizacion.id
            fecha_resp = autorizacion.fecha_respuesta
            if fecha_resp.tzinfo is not None:
                fecha_resp = fecha_resp.replace(tzinfo=None)
            expira = fecha_resp + timedelta(hours=24)
            fecha_expiracion = expira.strftime('%d/%m/%Y %H:%M')
            diferencia = expira - datetime.utcnow()
            horas_restantes = diferencia.total_seconds() / 3600
            if horas_restantes > 1:
                tiempo_restante = f"{int(horas_restantes)} hora{'s' if int(horas_restantes) > 1 else ''}"
            else:
                tiempo_restante = f"{int(horas_restantes * 60)} minuto{'s' if int(horas_restantes * 60) > 1 else ''}"
    
    return jsonify({
        'tarjeta_id': tarjeta_id,
        'numero_tarjeta': tarjeta.numero_tarjeta,
        'nombre_tarjeta': tarjeta.nombre_tarjeta,
        'sucursal': tarjeta.sucursal.nombre if tarjeta.sucursal else 'Sin asignar',
        'requiere_autorizacion': requiere_autorizacion,
        'tiene_autorizacion': tiene_autorizacion,
        'autorizacion_id': autorizacion_id,
        'puede_usar': not requiere_autorizacion or tiene_autorizacion,
        'tiempo_restante': tiempo_restante,
        'fecha_expiracion': fecha_expiracion
    })


@main.route('/api/tarjetas-disponibles')
@login_required
def tarjetas_disponibles():
    tarjetas = TarjetaCorporativa.query.filter_by(activa=True).all()
    resultado = []
    for t in tarjetas:
        requiere_auth = t.requiere_autorizacion(current_user)
        tiene_auth = False
        if requiere_auth:
            auth = Autorizacion.query.filter_by(
                tarjeta_id=t.id, solicitante_id=current_user.id, estatus='aprobada'
            ).order_by(Autorizacion.fecha_respuesta.desc()).first()
            tiene_auth = auth and auth.esta_vigente(horas=24)
        resultado.append({
            'id': t.id, 'numero_tarjeta': t.numero_tarjeta, 'nombre_tarjeta': t.nombre_tarjeta,
            'banco': t.banco, 'sucursal': t.sucursal.nombre if t.sucursal else None,
            'requiere_autorizacion': requiere_auth, 'tiene_autorizacion': tiene_auth,
            'puede_usar': not requiere_auth or tiene_auth
        })
    resultado.sort(key=lambda x: (not x['puede_usar'], x['nombre_tarjeta']))
    return jsonify(resultado)


@main.route('/api/usuario/<int:id>')
@login_required
def api_usuario_detalle(id):
    """API para obtener el detalle de un usuario."""
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    tarjetas = []
    for asignacion in usuario.tarjetas_asignadas:
        if asignacion.activo and asignacion.tarjeta:
            tarjetas.append({
                'id': asignacion.tarjeta.id,
                'nombre': asignacion.tarjeta.nombre_tarjeta,
                'numero': asignacion.tarjeta.numero_tarjeta
            })
    
    return jsonify({
        'id': usuario.id, 'nombre': usuario.nombre, 'correo': usuario.correo,
        'telefono': usuario.telefono, 'rol': usuario.rol, 'rol_id': usuario.rol_id,
        'sucursal': usuario.sucursal.nombre if usuario.sucursal else None,
        'sucursal_id': usuario.sucursal_id, 'tipo_agente': usuario.tipo_agente,
        'activo': usuario.activo, 'tarjetas': tarjetas, 'tarjetas_count': len(tarjetas),
        'created_at': usuario.created_at.strftime('%d/%m/%Y %H:%M') if usuario.created_at else '',
        'updated_at': usuario.updated_at.strftime('%d/%m/%Y %H:%M') if usuario.updated_at else ''
    })


@main.route('/api/usuario/<int:id>/tarjetas')
@login_required
def api_usuario_tarjetas(id):
    """API para obtener las tarjetas asignadas a un usuario."""
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    tarjetas_ids = [asig.tarjeta_id for asig in usuario.tarjetas_asignadas if asig.activo]
    return jsonify({'tarjetas': tarjetas_ids})


# =============================================================================
# RUTAS DE USUARIOS
# =============================================================================

@main.route('/usuarios')
@login_required
def usuarios():
    """Lista de usuarios del sistema."""
    if not current_user.es_admin():
        flash('Acceso no autorizado. Solo administradores pueden gestionar usuarios.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    usuarios_list = Usuario.query.order_by(Usuario.nombre).all()
    roles_list = Rol.query.order_by(Rol.nombre).all()
    sucursales_list = Sucursal.query.filter_by(activa=True).order_by(Sucursal.nombre).all()
    tarjetas_list = TarjetaCorporativa.query.filter_by(activa=True).order_by(TarjetaCorporativa.nombre_tarjeta).all()
    
    return render_template('usuarios.html', 
                           usuarios=usuarios_list, roles=roles_list,
                           sucursales=sucursales_list, tarjetas=tarjetas_list)


@main.route('/usuarios/nuevo', methods=['POST'])
@login_required
def nuevo_usuario():
    """Crea un nuevo usuario."""
    if not current_user.es_admin():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        contrasena = request.form.get('contrasena', '')
        telefono = request.form.get('telefono', '').strip() or None
        rol_id = request.form.get('rol_id')
        sucursal_id = request.form.get('sucursal_id')
        tipo_agente = request.form.get('tipo_agente', '').strip() or None
        
        if not nombre or not correo or not contrasena:
            flash('Nombre, correo y contraseña son obligatorios.', 'warning')
            return redirect(url_for('main.usuarios'))
        
        if len(contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
            return redirect(url_for('main.usuarios'))
        
        if Usuario.query.filter_by(correo=correo).first():
            flash('Ya existe un usuario con ese correo electrónico.', 'warning')
            return redirect(url_for('main.usuarios'))
        
        rol = Rol.query.get(rol_id)
        if not rol:
            flash('Rol no válido.', 'warning')
            return redirect(url_for('main.usuarios'))
        
        nuevo = Usuario(
            nombre=nombre, correo=correo, telefono=telefono, rol=rol.nombre,
            rol_id=int(rol_id), sucursal_id=int(sucursal_id) if sucursal_id else None,
            tipo_agente=tipo_agente, activo=True
        )
        nuevo.set_password(contrasena)
        db.session.add(nuevo)
        db.session.commit()
        
        audit = AuditLog(
            tabla_nombre='usuarios', registro_id=str(nuevo.id), accion='INSERT',
            datos_nuevos={'nombre': nombre, 'correo': correo, 'rol': rol.nombre, 'sucursal_id': sucursal_id},
            usuario_id=current_user.id, usuario_email=current_user.correo, sucursal_id=current_user.sucursal_id
        )
        db.session.add(audit)
        db.session.commit()
        flash(f'Usuario "{nombre}" creado exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear usuario: {str(e)}', 'danger')
    
    return redirect(url_for('main.usuarios'))


@main.route('/usuarios/editar/<int:id>', methods=['POST'])
@login_required
def editar_usuario(id):
    """Edita un usuario existente."""
    if not current_user.es_admin():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    usuario = Usuario.query.get_or_404(id)
    
    try:
        datos_anteriores = {
            'nombre': usuario.nombre, 'correo': usuario.correo,
            'rol': usuario.rol, 'sucursal_id': usuario.sucursal_id
        }
        
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        telefono = request.form.get('telefono', '').strip() or None
        rol_id = request.form.get('rol_id')
        sucursal_id = request.form.get('sucursal_id')
        tipo_agente = request.form.get('tipo_agente', '').strip() or None
        contrasena = request.form.get('contrasena', '').strip()
        
        if not nombre or not correo:
            flash('Nombre y correo son obligatorios.', 'warning')
            return redirect(url_for('main.usuarios'))
        
        usuario_existente = Usuario.query.filter(Usuario.correo == correo, Usuario.id != id).first()
        if usuario_existente:
            flash('Ya existe otro usuario con ese correo electrónico.', 'warning')
            return redirect(url_for('main.usuarios'))
        
        rol = Rol.query.get(rol_id)
        if not rol:
            flash('Rol no válido.', 'warning')
            return redirect(url_for('main.usuarios'))
        
        usuario.nombre = nombre
        usuario.correo = correo
        usuario.telefono = telefono
        usuario.rol = rol.nombre
        usuario.rol_id = int(rol_id)
        usuario.sucursal_id = int(sucursal_id) if sucursal_id else None
        usuario.tipo_agente = tipo_agente
        
        if contrasena:
            if len(contrasena) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
                return redirect(url_for('main.usuarios'))
            usuario.set_password(contrasena)
        
        audit = AuditLog(
            tabla_nombre='usuarios', registro_id=str(usuario.id), accion='UPDATE',
            datos_anteriores=datos_anteriores,
            datos_nuevos={'nombre': nombre, 'correo': correo, 'rol': rol.nombre, 
                         'sucursal_id': sucursal_id, 'contrasena_cambiada': bool(contrasena)},
            usuario_id=current_user.id, usuario_email=current_user.correo, sucursal_id=current_user.sucursal_id
        )
        db.session.add(audit)
        db.session.commit()
        flash(f'Usuario "{nombre}" actualizado exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar usuario: {str(e)}', 'danger')
    
    return redirect(url_for('main.usuarios'))


@main.route('/usuarios/<int:id>/toggle-estatus', methods=['POST'])
@login_required
def toggle_estatus_usuario(id):
    """Activa o desactiva un usuario."""
    if not current_user.es_admin():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'warning')
        return redirect(url_for('main.usuarios'))
    
    usuario = Usuario.query.get_or_404(id)
    
    try:
        accion = request.form.get('accion')
        motivo = request.form.get('motivo', '').strip()
        
        if not motivo or len(motivo) < 10:
            flash('Debe proporcionar un motivo (mínimo 10 caracteres).', 'warning')
            return redirect(url_for('main.usuarios'))
        
        estado_anterior = usuario.activo
        usuario.activo = not usuario.activo
        
        audit = AuditLog(
            tabla_nombre='usuarios', registro_id=str(usuario.id), accion='UPDATE',
            datos_anteriores={'activo': estado_anterior},
            datos_nuevos={'activo': usuario.activo, 'motivo': motivo, 'accion': accion},
            usuario_id=current_user.id, usuario_email=current_user.correo, sucursal_id=current_user.sucursal_id
        )
        db.session.add(audit)
        db.session.commit()
        
        estado = "activado" if usuario.activo else "desactivado"
        flash(f'Usuario "{usuario.nombre}" ha sido {estado}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('main.usuarios'))


@main.route('/usuarios/<int:id>/tarjetas', methods=['POST'])
@login_required
def asignar_tarjetas_usuario(id):
    """Asigna tarjetas a un usuario."""
    if not current_user.es_admin():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    usuario = Usuario.query.get_or_404(id)
    
    try:
        tarjetas_ids = request.form.getlist('tarjetas[]')
        TarjetaUsuario.query.filter_by(usuario_id=id).update({'activo': False})
        
        for tarjeta_id in tarjetas_ids:
            asignacion = TarjetaUsuario.query.filter_by(tarjeta_id=int(tarjeta_id), usuario_id=id).first()
            if asignacion:
                asignacion.activo = True
            else:
                nueva_asignacion = TarjetaUsuario(
                    tarjeta_id=int(tarjeta_id), usuario_id=id,
                    asignado_por=current_user.id, activo=True
                )
                db.session.add(nueva_asignacion)
        
        audit = AuditLog(
            tabla_nombre='tarjetas_usuarios', registro_id=str(id), accion='UPDATE',
            datos_nuevos={'usuario_id': id, 'tarjetas_asignadas': tarjetas_ids, 'asignado_por': current_user.nombre},
            usuario_id=current_user.id, usuario_email=current_user.correo, sucursal_id=current_user.sucursal_id
        )
        db.session.add(audit)
        db.session.commit()
        flash(f'Tarjetas asignadas a "{usuario.nombre}" exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al asignar tarjetas: {str(e)}', 'danger')
    
    return redirect(url_for('main.usuarios'))


# =============================================================================
# RUTAS DE TARJETAS CORPORATIVAS
# =============================================================================

@main.route('/tarjetas')
@login_required
def tarjetas():
    if not current_user.es_gerente_o_superior():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    tarjetas_list = TarjetaCorporativa.query.order_by(TarjetaCorporativa.nombre_tarjeta).all()
    sucursales = Sucursal.query.filter_by(activa=True).all()
    return render_template('tarjetas.html', tarjetas=tarjetas_list, sucursales=sucursales)


@main.route('/tarjetas/nueva', methods=['POST'])
@login_required
def nueva_tarjeta():
    if not current_user.es_gerente_o_superior():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        numero = request.form.get('numero_tarjeta', '').strip()
        nombre = request.form.get('nombre_tarjeta', '').strip()
        
        if not numero or not nombre:
            flash('El número y nombre de la tarjeta son obligatorios.', 'warning')
            return redirect(url_for('main.tarjetas'))
        
        if TarjetaCorporativa.query.filter_by(numero_tarjeta=numero).first():
            flash(f'Ya existe una tarjeta con el número {numero}.', 'warning')
            return redirect(url_for('main.tarjetas'))
        
        sucursal_id = request.form.get('sucursal_id')
        nueva = TarjetaCorporativa(
            numero_tarjeta=numero, nombre_tarjeta=nombre,
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
    if not current_user.es_gerente_o_superior():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    tarjeta = TarjetaCorporativa.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            tarjeta.numero_tarjeta = request.form.get('numero_tarjeta', '').strip()
            tarjeta.nombre_tarjeta = request.form.get('nombre_tarjeta', '').strip()
            tarjeta.banco = request.form.get('banco', '').strip() or None
            tarjeta.titular = request.form.get('titular', '').strip() or None
            sucursal_id = request.form.get('sucursal_id')
            tarjeta.sucursal_id = int(sucursal_id) if sucursal_id else None
            tarjeta.activa = request.form.get('activa') == 'on'
            
            agentes_ids = [int(aid) for aid in request.form.getlist('agentes_ids') if aid]
            TarjetaUsuario.query.filter_by(tarjeta_id=tarjeta.id).delete()
            
            for usuario_id in agentes_ids:
                nueva_asignacion = TarjetaUsuario(
                    tarjeta_id=tarjeta.id, usuario_id=usuario_id,
                    asignado_por=current_user.id, activo=True
                )
                db.session.add(nueva_asignacion)
            
            db.session.commit()
            flash(f'Tarjeta "{tarjeta.nombre_tarjeta}" actualizada.', 'success')
            return redirect(url_for('main.tarjetas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    sucursales = Sucursal.query.filter_by(activa=True).all()
    usuarios = Usuario.query.order_by(Usuario.nombre).all()
    usuarios_asignados_ids = [asig.usuario_id for asig in TarjetaUsuario.query.filter_by(tarjeta_id=tarjeta.id, activo=True).all()]
    
    return render_template('tarjeta_edit.html', tarjeta=tarjeta, sucursales=sucursales,
                           usuarios=usuarios, usuarios_asignados_ids=usuarios_asignados_ids)


@main.route('/tarjetas/eliminar/<int:id>')
@login_required
def eliminar_tarjeta(id):
    if not current_user.es_admin():
        flash('Solo los administradores pueden eliminar tarjetas.', 'danger')
        return redirect(url_for('main.tarjetas'))
    
    tarjeta = TarjetaCorporativa.query.get_or_404(id)
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
    if current_user.rol in ['director', 'administrador', 'admin']:
        lista = Autorizacion.query.filter_by(estatus='pendiente').order_by(Autorizacion.fecha_solicitud.asc()).all()
        es_director = True
    else:
        lista = Autorizacion.query.filter_by(solicitante_id=current_user.id).order_by(Autorizacion.fecha_solicitud.desc()).all()
        es_director = False
    return render_template('autorizaciones.html', autorizaciones=lista, es_director=es_director)


@main.route('/autorizaciones/solicitar', methods=['POST'])
@login_required
def solicitar_autorizacion():
    try:
        tarjeta_id = request.form.get('tarjeta_id')
        motivo = request.form.get('motivo', '').strip()
        
        if not tarjeta_id or not motivo:
            flash('Debe seleccionar una tarjeta y proporcionar un motivo.', 'warning')
            return redirect(url_for('main.nueva_papeleta_form'))
        
        tarjeta = TarjetaCorporativa.query.get_or_404(tarjeta_id)
        existente = Autorizacion.query.filter_by(tarjeta_id=tarjeta_id, solicitante_id=current_user.id, estatus='pendiente').first()
        
        if existente:
            flash('Ya tienes una solicitud pendiente para esta tarjeta.', 'warning')
            return redirect(url_for('main.autorizaciones'))
        
        nueva_auth = Autorizacion(
            tipo='uso_tarjeta', solicitante_id=current_user.id,
            tarjeta_id=tarjeta_id, motivo=motivo,
            sucursal_id=current_user.sucursal_id or 1
        )
        db.session.add(nueva_auth)
        db.session.commit()
        flash(f'Solicitud de autorización enviada para tarjeta {tarjeta.nombre_tarjeta}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al solicitar autorización: {str(e)}', 'danger')
    
    return redirect(url_for('main.autorizaciones'))


@main.route('/autorizaciones/responder/<int:id>', methods=['POST'])
@login_required
def responder_autorizacion(id):
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
# RUTAS DE PAPELETAS
# =============================================================================

@main.route('/papeletas', methods=['GET'])
@login_required
def consulta_papeletas():
    """Muestra la lista de papeletas agrupadas por tarjeta."""
    if current_user.es_admin():
        papeletas_list = Papeleta.query.order_by(Papeleta.tarjeta, Papeleta.fecha_venta.desc()).all()
    elif current_user.es_gerente_o_superior():
        papeletas_list = Papeleta.query.filter_by(sucursal_id=current_user.sucursal_id).order_by(Papeleta.tarjeta, Papeleta.fecha_venta.desc()).all()
    else:
        papeletas_list = Papeleta.query.filter_by(usuario_id=current_user.id).order_by(Papeleta.tarjeta, Papeleta.fecha_venta.desc()).all()
    
    papeletas_por_tarjeta = OrderedDict()
    
    for papeleta in papeletas_list:
        tarjeta_numero = papeleta.tarjeta
        tarjeta_info = None
        if papeleta.tarjeta_id:
            tarjeta_obj = TarjetaCorporativa.query.get(papeleta.tarjeta_id)
            if tarjeta_obj:
                tarjeta_info = {'numero': tarjeta_obj.numero_tarjeta, 'nombre': tarjeta_obj.nombre_tarjeta, 'banco': tarjeta_obj.banco}
        
        if not tarjeta_info:
            tarjeta_info = {'numero': tarjeta_numero, 'nombre': None, 'banco': None}
        
        class TarjetaKey:
            def __init__(self, numero, nombre, banco):
                self.numero = numero
                self.nombre = nombre
                self.banco = banco
            def __hash__(self):
                return hash(self.numero)
            def __eq__(self, other):
                return self.numero == other.numero
        
        tarjeta_key = TarjetaKey(tarjeta_info['numero'], tarjeta_info['nombre'], tarjeta_info['banco'])
        if tarjeta_key not in papeletas_por_tarjeta:
            papeletas_por_tarjeta[tarjeta_key] = []
        papeletas_por_tarjeta[tarjeta_key].append(papeleta)
    
    return render_template('consulta_papeletas.html', papeletas_por_tarjeta=papeletas_por_tarjeta)


@main.route('/papeletas/nueva', methods=['GET'])
@login_required
def nueva_papeleta_form():
    """Muestra el formulario para crear una nueva papeleta."""
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    tarjetas_list = TarjetaCorporativa.query.filter_by(activa=True).order_by(TarjetaCorporativa.nombre_tarjeta).all()
    
    tarjetas_info = []
    for t in tarjetas_list:
        requiere_auth = t.requiere_autorizacion(current_user)
        tiene_auth = False
        tiempo_restante = None
        fecha_expiracion = None
        
        if requiere_auth:
            auth = Autorizacion.query.filter_by(tarjeta_id=t.id, solicitante_id=current_user.id, estatus='aprobada').order_by(Autorizacion.fecha_respuesta.desc()).first()
            if auth and auth.esta_vigente(horas=24):
                tiene_auth = True
                fecha_resp = auth.fecha_respuesta
                if fecha_resp.tzinfo is not None:
                    fecha_resp = fecha_resp.replace(tzinfo=None)
                expira = fecha_resp + timedelta(hours=24)
                fecha_expiracion = expira.strftime('%d/%m/%Y %H:%M')
                diferencia = expira - datetime.utcnow()
                horas_restantes = diferencia.total_seconds() / 3600
                tiempo_restante = f"{int(horas_restantes)}h" if horas_restantes > 1 else f"{int(horas_restantes * 60)}min"
        
        usuarios_asignados = [asig.usuario.nombre for asig in TarjetaUsuario.query.filter_by(tarjeta_id=t.id, activo=True).all() if asig.usuario]
        
        tarjetas_info.append({
            'tarjeta': t, 'requiere_autorizacion': requiere_auth, 'tiene_autorizacion': tiene_auth,
            'puede_usar': not requiere_auth or tiene_auth, 'usuarios_asignados': usuarios_asignados,
            'tiempo_restante': tiempo_restante, 'fecha_expiracion': fecha_expiracion
        })
    
    return render_template('papeletas.html', empresas=empresas_list, aerolineas=aerolineas_list, tarjetas_info=tarjetas_info)


@main.route('/papeletas/nueva', methods=['POST'])
@login_required
def nueva_papeleta_post():
    """Recibe los datos del formulario y crea una nueva papeleta."""
    try:
        tarjeta_id = request.form.get('tarjeta_id')
        tarjeta_manual = request.form.get('tarjeta_manual', '').strip()
        es_extemporanea = request.form.get('extemporanea') == '1'
        
        tarjeta_numero = None
        tarjeta_obj = None
        autorizacion_id = None
        
        if tarjeta_id:
            tarjeta_obj = TarjetaCorporativa.query.get(tarjeta_id)
            if not tarjeta_obj:
                flash('Tarjeta no encontrada.', 'danger')
                return redirect(url_for('main.nueva_papeleta_form'))
            tarjeta_numero = tarjeta_obj.numero_tarjeta
            
            if not es_extemporanea and tarjeta_obj.requiere_autorizacion(current_user):
                auth = Autorizacion.query.filter_by(tarjeta_id=tarjeta_id, solicitante_id=current_user.id, estatus='aprobada').order_by(Autorizacion.fecha_respuesta.desc()).first()
                if not auth or not auth.esta_vigente(horas=24):
                    flash('Necesitas autorización vigente para usar esta tarjeta.', 'danger')
                    return redirect(url_for('main.nueva_papeleta_form'))
                autorizacion_id = auth.id
        elif tarjeta_manual:
            if len(tarjeta_manual) != 4 or not tarjeta_manual.isdigit():
                flash('La terminación de tarjeta debe ser de 4 dígitos.', 'warning')
                return redirect(url_for('main.nueva_papeleta_form'))
            tarjeta_numero = tarjeta_manual
        else:
            flash('Debe seleccionar o ingresar una tarjeta.', 'warning')
            return redirect(url_for('main.nueva_papeleta_form'))
        
        fecha_cargo_real = None
        motivo_extemporanea = None
        if es_extemporanea:
            fecha_cargo_real_str = request.form.get('fecha_cargo_real')
            if not fecha_cargo_real_str:
                flash('Debe ingresar la fecha real del cargo para papeletas extemporáneas.', 'warning')
                return redirect(url_for('main.nueva_papeleta_form'))
            fecha_cargo_real = datetime.strptime(fecha_cargo_real_str, '%Y-%m-%d').date()
            motivo_extemporanea = request.form.get('motivo_extemporanea', '').strip()
            if not motivo_extemporanea:
                flash('Debe ingresar el motivo del registro tardío.', 'warning')
                return redirect(url_for('main.nueva_papeleta_form'))
        
        fecha_venta_str = request.form.get('fecha_venta')
        fecha_venta = datetime.strptime(fecha_venta_str, '%Y-%m-%d').date() if fecha_venta_str else None
        empresa_id_str = request.form.get('facturar_a')
        empresa_id = int(empresa_id_str) if empresa_id_str else None
        facturar_a_nombre = ''
        if empresa_id:
            empresa = Empresa.query.get(empresa_id)
            facturar_a_nombre = empresa.nombre_empresa if empresa else ''
        aerolinea_id_str = request.form.get('aerolinea_id')
        aerolinea_id = int(aerolinea_id_str) if aerolinea_id_str else None

        folio = request.form.get('folio')
        if not folio:
            ultima = Papeleta.query.filter(Papeleta.folio.like(f"{tarjeta_numero}-%")).order_by(Papeleta.id.desc()).first()
            num = int(ultima.folio.split('-')[1]) + 1 if ultima else 1
            folio = f"{tarjeta_numero}-{num:03d}"

        tiene_reembolso = request.form.get('tiene_reembolso') == '1'
        motivo_reembolso = None
        monto_reembolso = None
        estatus_reembolso = None
        fecha_solicitud_reembolso = None
        referencia_reembolso = None
        papeleta_relacionada_id = None
        
        if tiene_reembolso:
            motivo_reembolso = request.form.get('motivo_reembolso', '')
            if motivo_reembolso == 'otro':
                motivo_reembolso = request.form.get('motivo_reembolso_otro', '').strip()
            monto_str = request.form.get('monto_reembolso', '').strip()
            monto_reembolso = float(monto_str) if monto_str else None
            estatus_reembolso = request.form.get('estatus_reembolso', 'pendiente')
            fecha_sol_str = request.form.get('fecha_solicitud_reembolso', '').strip()
            if fecha_sol_str:
                fecha_solicitud_reembolso = datetime.strptime(fecha_sol_str, '%Y-%m-%d').date()
            referencia_reembolso = request.form.get('referencia_reembolso', '').strip() or None
            folio_relacionado = request.form.get('papeleta_relacionada_folio', '').strip()
            if folio_relacionado:
                pap_rel = Papeleta.query.filter_by(folio=folio_relacionado).first()
                if pap_rel:
                    papeleta_relacionada_id = pap_rel.id
        
        nueva = Papeleta(
            folio=folio, tarjeta=tarjeta_numero, tarjeta_id=int(tarjeta_id) if tarjeta_id else None,
            fecha_venta=fecha_venta, total_ticket=float(request.form.get('total_ticket', 0)),
            diez_porciento=float(request.form.get('diez_porciento', 0)), cargo=float(request.form.get('cargo', 0)),
            total=float(request.form.get('total', 0)), facturar_a=facturar_a_nombre,
            solicito=request.form.get('solicito', ''), clave_sabre=request.form.get('clave_sabre', ''),
            forma_pago=request.form.get('forma_pago', ''), empresa_id=empresa_id, aerolinea_id=aerolinea_id,
            usuario_id=current_user.id, autorizacion_id=autorizacion_id, sucursal_id=current_user.sucursal_id,
            tipo_cargo=request.form.get('tipo_cargo', ''), proveedor=request.form.get('proveedor', ''),
            extemporanea=es_extemporanea, fecha_cargo_real=fecha_cargo_real, motivo_extemporanea=motivo_extemporanea,
            tiene_reembolso=tiene_reembolso, motivo_reembolso=motivo_reembolso, monto_reembolso=monto_reembolso,
            estatus_reembolso=estatus_reembolso, fecha_solicitud_reembolso=fecha_solicitud_reembolso,
            referencia_reembolso=referencia_reembolso, papeleta_relacionada_id=papeleta_relacionada_id
        )
        db.session.add(nueva)
        db.session.commit()

        if tiene_reembolso:
            flash(f'Papeleta {nueva.folio} registrada con reembolso {estatus_reembolso}.', 'success')
        elif es_extemporanea:
            flash(f'Papeleta extemporánea {nueva.folio} registrada.', 'success')
        else:
            flash(f'Papeleta {nueva.folio} creada con éxito.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la papeleta: {str(e)}', 'danger')

    return redirect(url_for('main.consulta_papeletas'))


@main.route('/papeletas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_papeleta(id):
    """Edita una papeleta existente. Solo administración puede editar."""
    if not current_user.es_admin():
        flash('Solo administración puede editar papeletas.', 'danger')
        return redirect(url_for('main.consulta_papeletas'))
    
    papeleta = Papeleta.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            motivo_edicion = request.form.get('motivo_edicion', '').strip()
            if not motivo_edicion or len(motivo_edicion) < 10:
                flash('Debe proporcionar un motivo de edición (mínimo 10 caracteres).', 'warning')
                return redirect(url_for('main.consulta_papeletas'))
            
            datos_anteriores = {
                'fecha_venta': str(papeleta.fecha_venta), 'total_ticket': float(papeleta.total_ticket),
                'total': float(papeleta.total), 'facturar_a': papeleta.facturar_a,
                'solicito': papeleta.solicito, 'clave_sabre': papeleta.clave_sabre
            }
            
            papeleta.fecha_venta = datetime.strptime(request.form.get('fecha_venta'), '%Y-%m-%d').date()
            papeleta.total_ticket = float(request.form.get('total_ticket', 0))
            papeleta.diez_porciento = float(request.form.get('diez_porciento', 0))
            papeleta.cargo = float(request.form.get('cargo', 0))
            papeleta.total = float(request.form.get('total', 0))
            papeleta.solicito = request.form.get('solicito', '')
            papeleta.clave_sabre = request.form.get('clave_sabre', '')
            papeleta.forma_pago = request.form.get('forma_pago', '')
            
            empresa_id = request.form.get('facturar_a')
            if empresa_id:
                papeleta.empresa_id = int(empresa_id)
                empresa = Empresa.query.get(empresa_id)
                papeleta.facturar_a = empresa.nombre_empresa if empresa else ''
            
            aerolinea_id = request.form.get('aerolinea_id')
            papeleta.aerolinea_id = int(aerolinea_id) if aerolinea_id else None
            
            audit = AuditLog(
                tabla_nombre='papeletas', registro_id=str(papeleta.id), accion='UPDATE',
                datos_anteriores=datos_anteriores,
                datos_nuevos={'fecha_venta': str(papeleta.fecha_venta), 'total_ticket': float(papeleta.total_ticket),
                             'total': float(papeleta.total), 'facturar_a': papeleta.facturar_a, 'motivo_edicion': motivo_edicion},
                usuario_id=current_user.id, usuario_email=current_user.correo, sucursal_id=current_user.sucursal_id
            )
            db.session.add(audit)
            db.session.commit()
            flash(f'Papeleta {papeleta.folio} actualizada con éxito.', 'success')
            return redirect(url_for('main.consulta_papeletas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    return render_template('papeleta_edit.html', papeleta=papeleta, empresas=empresas_list, aerolineas=aerolineas_list)


@main.route('/papeletas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_papeleta(id):
    """Elimina una papeleta. Solo administración puede eliminar con motivo."""
    if not current_user.es_admin():
        flash('Solo administración puede eliminar papeletas.', 'danger')
        return redirect(url_for('main.consulta_papeletas'))
    
    papeleta = Papeleta.query.get_or_404(id)
    motivo_tipo = request.form.get('motivo_eliminacion_tipo', '').strip()
    motivo_detalle = request.form.get('motivo_eliminacion_detalle', '').strip()
    
    if not motivo_tipo:
        flash('Debe seleccionar un tipo de motivo para eliminar.', 'warning')
        return redirect(url_for('main.consulta_papeletas'))
    
    if not motivo_detalle or len(motivo_detalle) < 10:
        flash('Debe proporcionar detalle del motivo (mínimo 10 caracteres).', 'warning')
        return redirect(url_for('main.consulta_papeletas'))
    
    try:
        folio = papeleta.folio
        audit = AuditLog(
            tabla_nombre='papeletas', registro_id=str(papeleta.id), accion='DELETE',
            datos_anteriores={
                'folio': papeleta.folio, 'tarjeta': papeleta.tarjeta, 'fecha_venta': str(papeleta.fecha_venta),
                'total_ticket': float(papeleta.total_ticket), 'total': float(papeleta.total),
                'facturar_a': papeleta.facturar_a, 'solicito': papeleta.solicito,
                'clave_sabre': papeleta.clave_sabre, 'usuario_id': papeleta.usuario_id
            },
            datos_nuevos={'motivo_tipo': motivo_tipo, 'motivo_detalle': motivo_detalle, 'eliminado_por': current_user.nombre},
            usuario_id=current_user.id, usuario_email=current_user.correo, sucursal_id=current_user.sucursal_id
        )
        db.session.add(audit)
        db.session.delete(papeleta)
        db.session.commit()
        flash(f'Papeleta {folio} eliminada. Motivo: {motivo_tipo}', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('main.consulta_papeletas'))


# =============================================================================
# RUTAS DE DESGLOSES
# =============================================================================

@main.route('/desgloses', methods=['GET'])
@login_required
def desgloses():
    if current_user.es_admin():
        desgloses_list = Desglose.query.order_by(Desglose.folio.desc()).all()
    else:
        desgloses_list = Desglose.query.filter_by(usuario_id=current_user.id).order_by(Desglose.folio.desc()).all()
    return render_template('consulta_desgloses.html', desgloses_registrados=desgloses_list)


@main.route('/desgloses/nuevo', methods=['GET'])
@login_required
def nuevo_desglose_form():
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    empresas_booking_list = EmpresaBooking.query.order_by(EmpresaBooking.nombre).all()
    return render_template('desgloses.html', empresas=empresas_list, aerolineas=aerolineas_list, empresas_booking=empresas_booking_list)


@main.route('/desgloses/nuevo', methods=['POST'])
@login_required
def nuevo_desglose_post():
    try:
        nuevo = Desglose(
            folio=int(request.form.get('folio')), empresa_id=int(request.form.get('empresa_id')),
            aerolinea_id=int(request.form.get('aerolinea_id')), empresa_booking_id=int(request.form.get('empresa_booking_id')),
            tarifa_base=float(request.form.get('tarifa_base')), iva=float(request.form.get('iva')),
            tua=float(request.form.get('tua')), yr=float(request.form.get('yr')),
            otros_cargos=float(request.form.get('otros_cargos')), cargo_por_servicio=float(request.form.get('cargo_por_servicio')),
            total=float(request.form.get('total')), clave_reserva=request.form.get('clave_reserva'),
            usuario_id=current_user.id, sucursal_id=current_user.sucursal_id
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
            flash(f'Desglose {desglose.folio} actualizado con éxito.', 'success')
            return redirect(url_for('main.desgloses'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    empresas_list = Empresa.query.order_by(Empresa.nombre_empresa).all()
    aerolineas_list = Aerolinea.query.order_by(Aerolinea.nombre).all()
    empresas_booking_list = EmpresaBooking.query.order_by(EmpresaBooking.nombre).all()
    return render_template('desglose_edit.html', desglose=desglose, empresas=empresas_list, aerolineas=aerolineas_list, empresas_booking=empresas_booking_list)


@main.route('/desgloses/eliminar/<int:folio>')
@login_required
def eliminar_desglose(folio):
    desglose_a_eliminar = Desglose.query.get_or_404(folio)
    try:
        db.session.delete(desglose_a_eliminar)
        db.session.commit()
        flash(f'Desglose {folio} eliminado.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    return redirect(url_for('main.desgloses'))


# =============================================================================
# RUTAS DE EMPRESAS
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
        
        nueva = Empresa(nombre_empresa=nombre, sucursal_id=current_user.sucursal_id)
        db.session.add(nueva)
        db.session.flush()

        cargo_facturado = request.form.get('cargoServicioFacturado')
        if cargo_facturado:
            db.session.add(CargoServicio(empresa_id=nueva.id, tipo='visible', monto=float(cargo_facturado)))
        cargo_oculto = request.form.get('cargoServicioOculto')
        if cargo_oculto:
            db.session.add(CargoServicio(empresa_id=nueva.id, tipo='oculto', monto=float(cargo_oculto)))
        monto_descuento = request.form.get('montoDescuento')
        if monto_descuento:
            db.session.add(Descuento(empresa_id=nueva.id, tipo='monto', valor=float(monto_descuento)))
        tarifa_fija = request.form.get('tarifaFija')
        if tarifa_fija:
            db.session.add(TarifaFija(empresa_id=nueva.id, monto=float(tarifa_fija)))

        db.session.commit()
        flash(f'Empresa "{nombre}" registrada con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar empresa: {str(e)}', 'danger')
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
                db.session.add(CargoServicio(empresa_id=id, tipo='visible', monto=float(cargo_facturado)))
            cargo_oculto = request.form.get('cargoServicioOculto')
            if cargo_oculto:
                db.session.add(CargoServicio(empresa_id=id, tipo='oculto', monto=float(cargo_oculto)))
            monto_descuento = request.form.get('montoDescuento')
            if monto_descuento:
                db.session.add(Descuento(empresa_id=id, tipo='monto', valor=float(monto_descuento)))
            tarifa_fija = request.form.get('tarifaFija')
            if tarifa_fija:
                db.session.add(TarifaFija(empresa_id=id, monto=float(tarifa_fija)))

            db.session.commit()
            flash(f'Empresa "{empresa.nombre_empresa}" actualizada.', 'success')
            return redirect(url_for('main.empresas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    return render_template('empresa_edit.html', empresa=empresa)


@main.route('/empresas/eliminar/<int:id>')
@login_required
def eliminar_empresa(id):
    if current_user.rol_relacion.nombre not in ['administrador', 'admin', 'director']:
        return redirect(url_for('main.dashboard'))
    empresa_a_eliminar = Empresa.query.get_or_404(id)
    db.session.delete(empresa_a_eliminar)
    db.session.commit()
    flash(f'Empresa "{empresa_a_eliminar.nombre_empresa}" eliminada.', 'info')
    return redirect(url_for('main.empresas'))


# =============================================================================
# RUTAS DE SUCURSALES
# =============================================================================

@main.route('/sucursales')
@login_required
def sucursales():
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


@main.route('/sucursales/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_sucursal(id):
    if not current_user.es_admin():
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))
    sucursal = Sucursal.query.get_or_404(id)
    if request.method == 'POST':
        try:
            sucursal.nombre = request.form.get('nombre', '').strip()
            sucursal.ciudad = request.form.get('ciudad', '').strip()
            sucursal.direccion = request.form.get('direccion', '').strip() or None
            sucursal.telefono = request.form.get('telefono', '').strip() or None
            sucursal.activa = request.form.get('activa') == 'on'
            db.session.commit()
            flash(f'Sucursal "{sucursal.nombre}" actualizada.', 'success')
            return redirect(url_for('main.sucursales'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('sucursal_edit.html', sucursal=sucursal)


@main.route('/sucursales/eliminar/<int:id>')
@login_required
def eliminar_sucursal(id):
    if not current_user.es_admin():
        return redirect(url_for('main.dashboard'))
    sucursal = Sucursal.query.get_or_404(id)
    if Usuario.query.filter_by(sucursal_id=id).count() > 0:
        flash('No se puede eliminar: la sucursal tiene usuarios asignados.', 'warning')
        return redirect(url_for('main.sucursales'))
    nombre = sucursal.nombre
    db.session.delete(sucursal)
    db.session.commit()
    flash(f'Sucursal "{nombre}" eliminada.', 'info')
    return redirect(url_for('main.sucursales'))