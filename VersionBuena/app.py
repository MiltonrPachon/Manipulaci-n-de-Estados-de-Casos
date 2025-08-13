from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Importación de Blueprints personalizados para organizar rutas por roles
from controllers.admin_routes import admin_bp
from controllers.tecnico_routes import tecnico_bp
from controllers.usuario_routes import usuario_bp
from db import get_connection


# CLASE PRINCIPAL DE LA APLICACIÓN
class MyApp:
    """
    Esta clase encapsula toda la configuración y ejecución de la aplicación Flask.
    Se utiliza Programación Orientada a Objetos para mantener una estructura clara,
    escalable y reutilizable.
    """
    def __init__(self):
        """
        Constructor de la clase. Aquí se inicializa la aplicación Flask y se configura la clave secreta para sesiones, 
        las rutas principales, los Blueprints (rutas organizadas por roles) y los encabezados de control de caché.
        """
        self.app = Flask(__name__)
        self.app.secret_key = 'tu_clave_secreta' 
        self.register_routes()
        self.register_blueprints()
        self.set_headers()


    # Método que define las rutas principales:
    def register_routes(self):
        @self.app.route('/')
        def login():
            return render_template('login.html') #Muestra el formulario de login

        @self.app.route('/login', methods=['POST'])
        def login_post():
            """
            Recibe los datos de inicio de sesión enviados por JavaScript (JSON).
            Verifica en la base de datos si el usuario y la contraseña son válidos.
            Si son válidos, se redirige según el tipo de usuario
            """
            data = request.get_json() # Recibe los datos en formato JSON desde el frontend

            if not data:
                return jsonify({'message': 'Datos inválidos'}), 400 # Error si no llegaron datos

            username = data.get('username')
            password = data.get('password')

            # Conexión a base de datos y validación del usuario
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id_identity = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                tipo = user['tipo_usuario']
                session['user'] = user # Se guardan los datos del usuario en la sesión

                # Redirección según el tipo de usuario
                if tipo == 'administrador':
                    return jsonify({'redirect_url': url_for('admin.dashboard')})
                elif tipo == 'tecnico':
                    return jsonify({'redirect_url': url_for('tecnico.dashboard')})
                elif tipo == 'usuario':
                    return jsonify({'redirect_url': url_for('usuario.formulario')})
                else:
                    return jsonify({'message': 'Tipo de usuario inválido'}), 403
            else:
                return jsonify({'message': 'Usuario o contraseña incorrecta'}), 401

        @self.app.route('/logout')
        def logout():
            #Cierra la sesión del usuario y lo redirige al login.
            session.clear() # Elimina todos los datos de la sesión.
            return redirect(url_for('login'))

    def set_headers(self):
        """
        Este método configura los encabezados HTTP de las respuestas para deshabilitar la caché del navegador.
        Esto es para que el navegador no muestre páginas antiguas cuando se navega con el botón "Atrás".
        """
        @self.app.after_request
        def add_header(response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    def register_blueprints(self):
        """
        Registra los Blueprints del sistema.
        Los Blueprints permiten modularizar el código, separando las rutas y lógica
        de cada tipo de usuario.
        """
        self.app.register_blueprint(admin_bp)
        self.app.register_blueprint(tecnico_bp)
        self.app.register_blueprint(usuario_bp)

    def run(self):
        """
        Ejecuta la aplicación en modo debug.
        Este modo muestra errores detallados en el navegador y reinicia el servidor
        automáticamente si detecta cambios en el código.
        """
        self.app.run(debug=True)

if __name__ == '__main__':
    # Se crea una instancia de la clase MyApp y se ejecuta la aplicación
    app_instance = MyApp()
    app_instance.run()
