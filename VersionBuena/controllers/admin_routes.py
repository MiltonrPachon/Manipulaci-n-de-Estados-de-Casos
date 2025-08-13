from flask import Blueprint, render_template, session, request, redirect, url_for
from db import get_connection
from werkzeug.security import generate_password_hash  # Librería para encriptar contraseñas antes de guardarlas en la BD

# Controlador para el rol de administrador
class AdminController:
    def __init__(self):
        """
        Constructor del controlador del administrador.
        Se crea un Blueprint llamado 'admin' con prefijo de URL '/admin'.
        Luego se registran las rutas específicas de este rol.
        """
        self.bp = Blueprint('admin', __name__, url_prefix='/admin')
        self.add_routes()

    def add_routes(self):
        """
        Registra las rutas disponibles para el administrador
        """
        self.bp.route('/dashboard', methods=['GET'])(self.dashboard)
        self.bp.route('/caso/<codigo_caso>')(self.ver_caso)
        self.bp.route('/crear_usuario', methods=['POST'])(self.crear_usuario)
        self.bp.route('/eliminar_usuario', methods=['POST'])(self.eliminar_usuario)

    # Ruta principal del administrador.
    def dashboard(self):
        if 'user' not in session or session['user']['tipo_usuario'] != 'administrador':
            return redirect(url_for('login'))

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Contadores principales
        cursor.execute("SELECT COUNT(*) AS total_usuarios FROM users")
        total_usuarios = cursor.fetchone()['total_usuarios']

        cursor.execute("SELECT COUNT(*) AS total_tecnicos FROM users WHERE tipo_usuario = 'tecnico'")
        total_tecnicos = cursor.fetchone()['total_tecnicos']

        cursor.execute("SELECT COUNT(*) AS total_casos FROM casos")
        total_casos = cursor.fetchone()['total_casos']

        # Búsqueda por nombre o cédula
        query = request.args.get('q')
        usuarios = []
        casos = []

        if query:
            cursor.execute("""
                SELECT u.id_user, u.id_identity, u.tipo_usuario,
                       d.nombre_completo, d.telefono, d.correo,
                       e.nombre_equipo, e.marca, e.modelo, e.serial
                FROM users u
                JOIN datos_personales d ON u.id_datos = d.id_datos
                LEFT JOIN equipos e ON d.id_equipo = e.id_equipo
                WHERE u.id_identity LIKE %s OR d.nombre_completo LIKE %s
            """, (f"%{query}%", f"%{query}%"))
            usuarios = cursor.fetchall()

            if usuarios:
                user_ids = tuple([u['id_user'] for u in usuarios])
                placeholders = ','.join(['%s'] * len(user_ids))
                cursor.execute(f"""
                    SELECT codigo_caso, estado, asunto, id_usuario
                    FROM casos
                    WHERE id_usuario IN ({placeholders})
                """, user_ids)
                casos = cursor.fetchall()

        cursor.execute("""
            SELECT u.id_user, u.id_identity, u.tipo_usuario, 
                   d.nombre_completo, d.correo
            FROM users u
            JOIN datos_personales d ON u.id_datos = d.id_datos
        """)
        todos_usuarios = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('admin/dashboard.html',
                               total_usuarios=total_usuarios,
                               total_tecnicos=total_tecnicos,
                               total_casos=total_casos,
                               query=query,
                               usuarios=usuarios,
                               casos=casos,
                               todos_usuarios=todos_usuarios)

    def ver_caso(self, codigo_caso):
        # Muestra el detalle de un caso específico para que el administrador lo revise.
        if 'user' not in session or session['user']['tipo_usuario'] != 'administrador':
            return redirect(url_for('login'))

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.*, d.nombre_completo, d.telefono, d.correo,
                   e.nombre_equipo, e.marca, e.modelo, e.serial
            FROM casos c
            JOIN users u ON c.id_usuario = u.id_user
            JOIN datos_personales d ON u.id_datos = d.id_datos
            LEFT JOIN equipos e ON d.id_equipo = e.id_equipo
            WHERE c.codigo_caso = %s
        """, (codigo_caso,))
        caso = cursor.fetchone()

        cursor.close()
        conn.close()

        if not caso:
            return "Caso no encontrado", 404

        return render_template('admin/ver_caso.html', caso=caso)

    def crear_usuario(self):
        # Crea un nuevo usuario desde el formulario del administrador.
        data = request.form
        conn = get_connection()
        cursor = conn.cursor()

        # Insertar equipo
        cursor.execute("""
            INSERT INTO equipos (nombre_equipo, marca, modelo, serial)
            VALUES (%s, %s, %s, %s)
        """, (data['nombre_equipo'], data['marca'], data['modelo'], data['serial']))
        id_equipo = cursor.lastrowid

        # Insertar datos personales
        cursor.execute("""
            INSERT INTO datos_personales (cedula, nombre_completo, telefono, correo, id_equipo)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['id_identity'], data['nombre_completo'], data['telefono'], data['correo'], id_equipo))
        id_datos = cursor.lastrowid

        # Encriptar contraseña antes de guardar
        hashed_password = generate_password_hash(data['password'])

        # Insertar usuario con contraseña encriptada
        cursor.execute("""
            INSERT INTO users (id_identity, password, tipo_usuario, id_datos)
            VALUES (%s, %s, %s, %s)
        """, (data['id_identity'], hashed_password, data['tipo_usuario'], id_datos))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin.dashboard'))

    def eliminar_usuario(self):
        # Elimina un usuario con su información personal y su equipo.
        id_identity = request.form['id_identity']
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener IDs relacionados
        cursor.execute("""
            SELECT u.id_user, u.id_datos, d.id_equipo 
            FROM users u
            JOIN datos_personales d ON u.id_datos = d.id_datos
            WHERE u.id_identity = %s
        """, (id_identity,))
        result = cursor.fetchone()

        if result:
            id_user = result['id_user']
            id_datos = result['id_datos']
            id_equipo = result['id_equipo']

            # Eliminar usuario y datos personales.
            cursor.execute("DELETE FROM users WHERE id_user = %s", (id_user,))
            cursor.execute("DELETE FROM datos_personales WHERE id_datos = %s", (id_datos,))

            # Verificar si el equipo está asociado a más personas.
            if id_equipo:
                cursor.execute("SELECT COUNT(*) AS cantidad FROM datos_personales WHERE id_equipo = %s", (id_equipo,))
                if cursor.fetchone()['cantidad'] == 0:
                    cursor.execute("DELETE FROM equipos WHERE id_equipo = %s", (id_equipo,))

            conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('admin.dashboard'))


# Instancia de controlador
admin_controller = AdminController()
admin_bp = admin_controller.bp
