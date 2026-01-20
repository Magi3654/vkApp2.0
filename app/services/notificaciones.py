# app/services/notificaciones.py
# Servicio de notificaciones para Kinessia Hub

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import current_app, url_for
import os

class NotificacionService:
    """Servicio para enviar notificaciones por email y sistema"""
    
    # Configuración de email
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'ilse@viajeskinessia.com')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
    
    # Destinatario para autorizaciones
    EMAIL_DIRECTOR = os.environ.get('EMAIL_DIRECTOR', 'gabycl61@hotmail.com')
    
    # URL base del sistema (cambiar en producción)
    BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
    
    @classmethod
    def enviar_email(cls, destinatario, asunto, cuerpo_html, cuerpo_texto=None):
        """Envia un email"""
        if not cls.EMAIL_PASSWORD:
            return False, "EMAIL_PASSWORD no configurado"
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = asunto
            msg['From'] = cls.EMAIL_SENDER
            msg['To'] = destinatario
            
            if cuerpo_texto:
                part1 = MIMEText(cuerpo_texto, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(cuerpo_html, 'html', 'utf-8')
            msg.attach(part2)
            
            with smtplib.SMTP(cls.SMTP_SERVER, cls.SMTP_PORT) as server:
                server.starttls()
                server.login(cls.EMAIL_SENDER, cls.EMAIL_PASSWORD)
                server.sendmail(cls.EMAIL_SENDER, destinatario, msg.as_string())
            
            return True, "Email enviado correctamente"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Error de autenticacion SMTP - Verifica EMAIL_PASSWORD"
        except smtplib.SMTPException as e:
            return False, f"Error SMTP: {str(e)}"
        except Exception as e:
            return False, f"Error al enviar email: {str(e)}"
    
    @classmethod
    def notificar_autorizacion_solicitada(cls, autorizacion, db, Notificacion):
        """Notifica al director sobre una nueva solicitud de autorizacion"""
        resultado = {
            'sistema': False,
            'email': False,
            'errores': []
        }
        
        # Generar token si no existe
        if not autorizacion.token:
            autorizacion.token = autorizacion.generar_token()
            db.session.commit()
        
        # 1. Crear notificacion en sistema
        try:
            notif = Notificacion(
                tipo='autorizacion_solicitada',
                destinatario=cls.EMAIL_DIRECTOR,
                canal='sistema',
                titulo='Nueva solicitud de autorizacion',
                mensaje=f'{autorizacion.solicitante.nombre} solicita autorizacion para usar tarjeta {autorizacion.tarjeta.nombre_tarjeta}. Motivo: {autorizacion.motivo}',
                autorizacion_id=autorizacion.id,
                sucursal_id=autorizacion.sucursal_id,
                estatus='pendiente'
            )
            db.session.add(notif)
            db.session.commit()
            resultado['sistema'] = True
        except Exception as e:
            resultado['errores'].append(f"Error notificacion sistema: {str(e)}")
        
        # 2. Enviar email con botones
        try:
            asunto = f"Nueva Solicitud de Autorizacion - {autorizacion.solicitante.nombre}"
            
            numero_tarjeta = autorizacion.tarjeta.numero_tarjeta or 'N/A'
            
            # URLs para aprobar/rechazar
            url_aprobar = f"{cls.BASE_URL}/autorizacion/aprobar/{autorizacion.token}"
            url_rechazar = f"{cls.BASE_URL}/autorizacion/rechazar/{autorizacion.token}"
            
            cuerpo_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #990100 0%, #b90504 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 25px; border: 1px solid #e0e0e0; }}
                    .info-box {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #990100; }}
                    .label {{ font-weight: bold; color: #666; font-size: 12px; text-transform: uppercase; }}
                    .value {{ font-size: 16px; color: #333; margin-top: 5px; }}
                    .buttons {{ margin-top: 25px; text-align: center; }}
                    .btn {{ display: inline-block; padding: 14px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; margin: 0 10px; }}
                    .btn-aprobar {{ background: #198754; color: white; }}
                    .btn-rechazar {{ background: #dc3545; color: white; }}
                    .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #888; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2 style="margin:0;">Nueva Solicitud de Autorizacion</h2>
                        <p style="margin:5px 0 0 0; opacity: 0.9;">Kinessia Trip Hub</p>
                    </div>
                    <div class="content">
                        <p>Se ha recibido una nueva solicitud de autorizacion:</p>
                        
                        <div class="info-box">
                            <div class="label">Solicitante</div>
                            <div class="value">{autorizacion.solicitante.nombre}</div>
                        </div>
                        
                        <div class="info-box">
                            <div class="label">Tarjeta</div>
                            <div class="value">{autorizacion.tarjeta.nombre_tarjeta} ({numero_tarjeta})</div>
                        </div>
                        
                        <div class="info-box">
                            <div class="label">Motivo</div>
                            <div class="value">{autorizacion.motivo}</div>
                        </div>
                        
                        <div class="info-box">
                            <div class="label">Fecha de solicitud</div>
                            <div class="value">{autorizacion.fecha_solicitud.strftime('%d/%m/%Y %H:%M')}</div>
                        </div>
                        
                        <div class="buttons">
                            <a href="{url_aprobar}" class="btn btn-aprobar">✓ APROBAR</a>
                            <a href="{url_rechazar}" class="btn btn-rechazar">✗ RECHAZAR</a>
                        </div>
                        
                        <p style="text-align: center; margin-top: 20px; font-size: 12px; color: #888;">
                            Al hacer clic en los botones, la decision se registrara automaticamente.
                        </p>
                    </div>
                    <div class="footer">
                        <p>Este es un mensaje automatico del sistema Kinessia Trip Hub.<br>
                        Por favor no responda a este correo.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            cuerpo_texto = f"""
            Nueva Solicitud de Autorizacion - Kinessia Trip Hub
            
            Solicitante: {autorizacion.solicitante.nombre}
            Tarjeta: {autorizacion.tarjeta.nombre_tarjeta} ({numero_tarjeta})
            Motivo: {autorizacion.motivo}
            Fecha: {autorizacion.fecha_solicitud.strftime('%d/%m/%Y %H:%M')}
            
            Para APROBAR: {url_aprobar}
            Para RECHAZAR: {url_rechazar}
            """
            
            exito, mensaje = cls.enviar_email(cls.EMAIL_DIRECTOR, asunto, cuerpo_html, cuerpo_texto)
            resultado['email'] = exito
            if not exito:
                resultado['errores'].append(mensaje)
                
        except Exception as e:
            resultado['errores'].append(f"Error enviando email: {str(e)}")
        
        return resultado
    
    @classmethod
    def notificar_autorizacion_respondida(cls, autorizacion, db, Notificacion):
        """Notifica al agente que su autorizacion fue respondida"""
        resultado = {
            'sistema': False,
            'email': False,
            'errores': []
        }
        
        estatus_texto = "APROBADA" if autorizacion.estatus == 'aprobada' else "RECHAZADA"
        
        # 1. Notificacion en sistema
        try:
            notif = Notificacion(
                tipo='autorizacion_respondida',
                destinatario=autorizacion.solicitante.correo,
                canal='sistema',
                titulo=f'Autorizacion {estatus_texto}',
                mensaje=f'Tu solicitud de autorizacion para {autorizacion.tarjeta.nombre_tarjeta} fue {estatus_texto}. {autorizacion.comentario_respuesta or ""}',
                autorizacion_id=autorizacion.id,
                sucursal_id=autorizacion.sucursal_id,
                estatus='pendiente'
            )
            db.session.add(notif)
            db.session.commit()
            resultado['sistema'] = True
        except Exception as e:
            resultado['errores'].append(f"Error notificacion sistema: {str(e)}")
        
        # 2. Email al solicitante
        if autorizacion.solicitante.correo:
            try:
                asunto = f"Autorizacion {estatus_texto} - {autorizacion.tarjeta.nombre_tarjeta}"
                
                color = "#198754" if autorizacion.estatus == 'aprobada' else "#dc3545"
                icono = "✓" if autorizacion.estatus == 'aprobada' else "✗"
                numero_tarjeta = autorizacion.tarjeta.numero_tarjeta or 'N/A'
                
                cuerpo_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: {color}; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                        .content {{ background: #f9f9f9; padding: 25px; border: 1px solid #e0e0e0; }}
                        .info-box {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #888; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2 style="margin:0;">{icono} Autorizacion {estatus_texto}</h2>
                        </div>
                        <div class="content">
                            <p>Hola {autorizacion.solicitante.nombre},</p>
                            <p>Tu solicitud de autorizacion ha sido <strong>{estatus_texto}</strong>.</p>
                            
                            <div class="info-box">
                                <strong>Tarjeta:</strong> {autorizacion.tarjeta.nombre_tarjeta} ({numero_tarjeta})<br>
                                <strong>Fecha:</strong> {autorizacion.fecha_respuesta.strftime('%d/%m/%Y %H:%M') if autorizacion.fecha_respuesta else 'N/A'}
                            </div>
                            
                            {f'<div class="info-box"><strong>Comentario:</strong> {autorizacion.comentario_respuesta}</div>' if autorizacion.comentario_respuesta else ''}
                            
                            {'<p><strong>Ya puedes usar la tarjeta para tu operacion.</strong></p>' if autorizacion.estatus == 'aprobada' else ''}
                        </div>
                        <div class="footer">
                            <p>Kinessia Trip Hub - Sistema de Gestion</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                exito, mensaje = cls.enviar_email(autorizacion.solicitante.correo, asunto, cuerpo_html)
                resultado['email'] = exito
                if not exito:
                    resultado['errores'].append(mensaje)
                    
            except Exception as e:
                resultado['errores'].append(f"Error enviando email: {str(e)}")
        
        return resultado


def obtener_notificaciones_pendientes(usuario, Notificacion, Autorizacion):
    """Obtiene el conteo de notificaciones pendientes para el usuario"""
    resultado = {
        'autorizaciones_pendientes': 0,
        'notificaciones_no_leidas': 0,
        'total': 0
    }
    
    if usuario.rol in ['director', 'administrador', 'admin']:
        resultado['autorizaciones_pendientes'] = Autorizacion.query.filter_by(
            estatus='pendiente'
        ).count()
    
    resultado['notificaciones_no_leidas'] = Notificacion.query.filter_by(
        destinatario=usuario.correo,
        estatus='pendiente'
    ).count()
    
    resultado['total'] = resultado['autorizaciones_pendientes'] + resultado['notificaciones_no_leidas']
    
    return resultado