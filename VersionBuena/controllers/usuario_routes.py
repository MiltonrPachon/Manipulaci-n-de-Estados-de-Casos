from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db import get_connection
from datetime import datetime # Para registrar la fecha actual

class UsuarioController:
    def __init__(self):
        self.bp = Blueprint('usuario', __name__, url_prefix='/usuario')
        self.register_routes()

    def register_routes(self):
        self.bp.route('/formulario', methods=['GET'])(self.formulario)
        self.bp.route('/crear_caso', methods=['POST'])(self.crear_caso)
        self.bp.route('/logout')(self.logout)

    def formulario(self):
        if 'user' not in session:
            return redirect(url_for('login')) # Redirige si no está logueado

        user_id = session['user']['id_user'] # Obtiene ID del usuario autenticado

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Consulta todos los casos del usuario
        cursor.execute("""
            SELECT id_caso, codigo_caso, estado, asunto, descripcion, prioridad, fecha_creacion
            FROM casos
            WHERE id_usuario = %s
            ORDER BY fecha_creacion DESC
        """, (user_id,))
        casos = cursor.fetchall()

        # Para cada caso, traer los comentarios
        for caso in casos:
            cursor.execute("""
                SELECT c.texto, c.fecha_comentario, dp.nombre_completo AS tecnico
                FROM comentarios c
                JOIN datos_personales dp ON c.id_tecnico = dp.id_datos
                WHERE c.id_caso = %s
                ORDER BY c.fecha_comentario DESC
            """, (caso['id_caso'],))
            comentarios = cursor.fetchall()
            caso['comentarios'] = comentarios  # Añadir la lista de comentarios a cada caso

        cursor.close()
        conn.close()

        return render_template('usuario/formulario.html', casos=casos)

    def crear_caso(self):
        if 'user' not in session:
            return redirect(url_for('login'))

        user_id = session['user']['id_user'] # ID del usuario actual
        tipo_caso = request.form.get('tipo_caso') 
        asunto = request.form.get('asunto')
        descripcion = request.form.get('descripcion')
        prioridad = request.form.get('prioridad')

        # Validación: todos los campos son obligatorios
        if not tipo_caso or not asunto or not descripcion or not prioridad:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('usuario.formulario'))

        conn = get_connection()
        cursor = conn.cursor()

        # Insertar nuevo caso con estado inicial 'pendiente' y fecha actual
        cursor.execute("""
            INSERT INTO casos (id_usuario, tipo_caso, estado, asunto, descripcion, prioridad, fecha_creacion)
            VALUES (%s, %s, 'pendiente', %s, %s, %s, %s)
        """, (user_id, tipo_caso, asunto, descripcion, prioridad, datetime.now()))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Caso creado correctamente', 'success')
        return redirect(url_for('usuario.formulario')) # Redirige de nuevo al formulario

    def logout(self):
        session.clear()
        return redirect(url_for('login'))

# Instancia y exportación del blueprint
usuario_controller = UsuarioController()
usuario_bp = usuario_controller.bp
