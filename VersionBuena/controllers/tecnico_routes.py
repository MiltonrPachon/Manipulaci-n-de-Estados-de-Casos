from flask import Blueprint, render_template, session, request, redirect, url_for
from db import get_connection
import io # Para manipular imágenes en memoria y codificarlas
import base64 # Para manipular imágenes en memoria y codificarlas
import pandas as pd # Análisis de datos
import matplotlib.pyplot as plt  # Generar gráficos visuales

class TecnicoController:
    def __init__(self):
        self.bp = Blueprint('tecnico', __name__, url_prefix='/tecnico') # Define el blueprint para este módulo
        self.register_routes() # Asocia rutas del técnico a funciones

    def register_routes(self):

        # Mapea las rutas a las funciones correspondientes del técnico.
        self.bp.route('/dashboard', methods=['GET'])(self.dashboard)
        self.bp.route('/logout')(self.logout)
        self.bp.route('/pendientes')(self.pendientes)
        self.bp.route('/proceso')(self.proceso)
        self.bp.route('/resueltos')(self.resueltos)
        self.bp.route('/caso/<string:codigo_caso>', methods=['GET', 'POST'])(self.ver_caso)
        self.bp.route('/caso/proceso/<string:codigo_caso>', methods=['GET', 'POST'])(self.ver_caso_proceso)
        self.bp.route('/caso/resuelto/<string:codigo_caso>', methods=['GET', 'POST'])(self.ver_caso_resuelto)

    def create_base64_plot(self, fig):
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight') # Guardar la figura en memoria
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode() # Convertir a base64 para enviar al navegador

    def dashboard(self):
        if 'user' not in session:
            return redirect(url_for('login'))

        # Consultar datos para estadísticas
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Casos por estado
        cursor.execute("SELECT estado, COUNT(*) AS cantidad FROM casos GROUP BY estado")
        estado_data = cursor.fetchall()
        df_estado = pd.DataFrame(estado_data)

        # Tendencia de casos por tiempo
        cursor.execute("SELECT id_caso, fecha_creacion FROM casos ORDER BY fecha_creacion")
        tendencia_data = cursor.fetchall()
        df_tendencia = pd.DataFrame(tendencia_data)
        df_tendencia['conteo'] = range(1, len(df_tendencia) + 1)

        fig1, ax1 = plt.subplots()
        ax1.pie(df_estado['cantidad'], labels=df_estado['estado'], autopct='%1.1f%%', startangle=140)
        ax1.set_title("Distribución de Casos")
        piechart = self.create_base64_plot(fig1)
        plt.close(fig1)

        fig2, ax2 = plt.subplots()
        ax2.bar(df_estado['estado'], df_estado['cantidad'], color='skyblue')
        ax2.set_title("Casos por Estado")
        barchart = self.create_base64_plot(fig2)
        plt.close(fig2)

        fig3, ax3 = plt.subplots()
        ax3.plot(df_tendencia['id_caso'], df_tendencia['conteo'], marker='o', linestyle='-', color='green')
        ax3.set_title("Tendencia de Casos")
        ax3.set_xlabel("ID del Caso")
        ax3.set_ylabel("Cantidad Acumulada")
        linechart = self.create_base64_plot(fig3)
        plt.close(fig3)

        # Obtener cantidades individuales por estado
        pendientes = df_estado[df_estado['estado'] == 'pendiente']['cantidad'].values[0] if 'pendiente' in df_estado['estado'].values else 0
        proceso = df_estado[df_estado['estado'] == 'proceso']['cantidad'].values[0] if 'proceso' in df_estado['estado'].values else 0
        resueltos = df_estado[df_estado['estado'] == 'resuelto']['cantidad'].values[0] if 'resuelto' in df_estado['estado'].values else 0

        query = request.args.get('q')
        usuarios, casos = [], []

        if query:
            cursor.execute("""
                SELECT u.id_identity, u.tipo_usuario, 
                       d.nombre_completo, d.telefono, d.correo,
                       e.nombre_equipo, e.marca, e.modelo, e.serial
                FROM users u
                JOIN datos_personales d ON u.id_datos = d.id_datos
                LEFT JOIN equipos e ON d.id_equipo = e.id_equipo
                WHERE d.nombre_completo LIKE %s
            """, (f"%{query}%",))
            usuarios = cursor.fetchall()

            cursor.execute("""
                SELECT codigo_caso, estado, asunto
                FROM casos
                WHERE codigo_caso LIKE %s
            """, (f"%{query}%",))
            casos = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('tecnico/dashboard.html',
                               pendientes=pendientes,
                               proceso=proceso,
                               resueltos=resueltos,
                               query=query,
                               usuarios=usuarios,
                               casos=casos,
                               piechart=piechart,
                               barchart=barchart,
                               linechart=linechart)

    def logout(self):
        session.clear()
        return redirect(url_for('login'))

    def pendientes(self):
        if 'user' not in session:
            return redirect(url_for('login'))

        prioridad = request.args.get('prioridad', 'alta')
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT codigo_caso, estado, asunto, descripcion, prioridad, fecha_creacion, tipo_caso
            FROM casos
            WHERE estado = 'pendiente' AND prioridad = %s
            ORDER BY fecha_creacion DESC
        """, (prioridad,))
        casos = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('tecnico/pendientes.html', casos=casos, prioridad=prioridad)

    def proceso(self):
        if 'user' not in session:
            return redirect(url_for('login'))

        prioridad = request.args.get('prioridad', 'alta')
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT codigo_caso, estado, asunto, descripcion, prioridad, fecha_creacion, tipo_caso
            FROM casos
            WHERE estado = 'proceso' AND prioridad = %s
            ORDER BY fecha_creacion DESC
        """, (prioridad,))
        casos = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('tecnico/proceso.html', casos=casos, prioridad=prioridad)

    def resueltos(self):
        if 'user' not in session:
            return redirect(url_for('login'))

        prioridad = request.args.get('prioridad', 'alta')
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT codigo_caso, estado, asunto, descripcion, prioridad, fecha_creacion, tipo_caso
            FROM casos
            WHERE estado = 'resuelto' AND prioridad = %s
            ORDER BY fecha_creacion DESC
        """, (prioridad,))
        casos = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('tecnico/resueltos.html', casos=casos, prioridad=prioridad)

    def ver_caso(self, codigo_caso):
        return self._ver_caso_generico(codigo_caso, 'tecnico.ver_caso')

    def ver_caso_proceso(self, codigo_caso):
        return self._ver_caso_generico(codigo_caso, 'tecnico.ver_caso_proceso')

    def ver_caso_resuelto(self, codigo_caso):
        return self._ver_caso_generico(codigo_caso, 'tecnico.ver_caso_resuelto')

    def _ver_caso_generico(self, codigo_caso, redirect_endpoint):
        if 'user' not in session:
            return redirect(url_for('login'))

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_caso, codigo_caso, id_usuario, estado, asunto, descripcion, prioridad, fecha_creacion, tipo_caso
            FROM casos
            WHERE codigo_caso = %s
        """, (codigo_caso,))
        caso = cursor.fetchone()

        if not caso:
            cursor.close()
            conn.close()
            return "Caso no encontrado", 404

        if request.method == 'POST':
            accion = request.form.get('accion')
            comentario = request.form.get('comentario')
            id_tecnico = session['user']['id_datos']

            if accion == 'comentar' and comentario:
                cursor.execute("""
                    INSERT INTO comentarios (id_caso, id_tecnico, texto, fecha_comentario)
                    VALUES (%s, %s, %s, NOW())
                """, (caso['id_caso'], id_tecnico, comentario))

            elif accion in ['pendiente', 'proceso', 'resuelto']:
                cursor.execute("""
                    UPDATE casos SET estado = %s WHERE id_caso = %s
                """, (accion, caso['id_caso']))

                if comentario:
                    cursor.execute("""
                        INSERT INTO comentarios (id_caso, id_tecnico, texto, fecha_comentario)
                        VALUES (%s, %s, %s, NOW())
                    """, (caso['id_caso'], id_tecnico, comentario))

            conn.commit()
            return redirect(url_for(redirect_endpoint, codigo_caso=caso['codigo_caso']))

        cursor.execute("""
            SELECT d.*, u.tipo_usuario, u.id_identity, e.nombre_equipo, e.marca, e.modelo, e.serial
            FROM users u
            JOIN datos_personales d ON u.id_datos = d.id_datos
            LEFT JOIN equipos e ON d.id_equipo = e.id_equipo
            WHERE u.id_user = %s
        """, (caso['id_usuario'],))
        usuario = cursor.fetchone()

        if not usuario:
            cursor.close()
            conn.close()
            return "Usuario no encontrado", 404

        cursor.execute("""
            SELECT c.texto, c.fecha_comentario, dp.nombre_completo AS tecnico
            FROM comentarios c
            JOIN datos_personales dp ON c.id_tecnico = dp.id_datos
            WHERE c.id_caso = %s
            ORDER BY c.fecha_comentario DESC
        """, (caso['id_caso'],))
        comentarios = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('tecnico/ver_caso.html',
                               caso=caso,
                               usuario=usuario,
                               comentarios=comentarios)

# Exportar el blueprint
tecnico_controller = TecnicoController()
tecnico_bp = tecnico_controller.bp
