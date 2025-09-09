from flask import Flask
from config import Config
from .models import db, Usuario 
from flask_login import LoginManager

# NO importes los blueprints aquí arriba.

def create_app():
    """
    Fábrica de la aplicación que construye y configura la instancia de Flask.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Inicializa las extensiones con la instancia de la aplicación.
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # Redirige aquí si se necesita login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # Flask-Login usa esta función para recargar el objeto de usuario desde el ID de usuario almacenado en la sesión.
        return Usuario.query.get(int(user_id))

    # 2. Importa y registra los Blueprints DESPUÉS de inicializar las extensiones.
    #    Esta es la parte crucial de la solución.
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    with app.app_context():
        # Comentamos esta línea porque las tablas ya existen en tu base de datos.
        # Si estuvieras empezando de cero, la necesitarías.
        # db.create_all() 
        pass

    return app

