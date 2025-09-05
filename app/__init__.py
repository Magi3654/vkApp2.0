from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Creamos las instancias de las extensiones aquí, pero sin inicializarlas todavía.
# Esto nos permite importarlas en otros archivos (como models.py) de forma segura.
db = SQLAlchemy()
login_manager = LoginManager()

# Le decimos a Flask-Login a qué página redirigir a los usuarios que intenten
# acceder a una página protegida sin haber iniciado sesión.
login_manager.login_view = 'auth.login'


def create_app():
    """
    Esta es la función 'fábrica' que construye y configura la aplicación.
    """
    app = Flask(__name__)

    # 1. Cargar la configuración desde el archivo config.py
    app.config.from_object(Config)

    # 2. Conectar las extensiones (como la base de datos) con la aplicación
    db.init_app(app)
    login_manager.init_app(app)

    # 3. Configurar el cargador de usuarios para Flask-Login
    # Esto le dice a Flask-Login cómo encontrar un usuario específico por su ID.
    from .models import Usuario 
    @login_manager.user_loader
    def load_user(user_id):
        # SQLAlchemy devuelve el usuario correspondiente a ese ID.
        return Usuario.query.get(int(user_id))

    # 4. Registrar los Blueprints (nuestras colecciones de rutas)
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    # Todas las rutas en auth.py tendrán el prefijo /auth (ej: /auth/login)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # 5. Contexto de la aplicación
    with app.app_context():
        # ¡IMPORTANTE! Comentamos o eliminamos la siguiente línea porque tus tablas
        # de la base de datos ya fueron creadas manualmente. Si la dejamos,
        # podría intentar sobreescribirlas o causar errores.
        # db.create_all()
        pass

    return app

