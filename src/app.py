from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Usuario, Rol  # Asegúrate de que estos modelos estén definidos
from werkzeug.security import generate_password_hash  # Para el hashing de contraseñas
from flask_migrate import Migrate
from config import Config

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS

#Inicializacoion de base de datos y migraciones
db.init_app(app)
migrate = Migrate(app, db)

#Definicion de rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/header')
def header():
    return render_template('header.html')

@app.route('/dashboard')
def dashboard():
    print('Accediendo a DASHBOARD')
    return render_template('dashboard.html')

@app.route('/desgloses')
def desgloses():
    return render_template('desgloses.html')

@app.route('/papeletas')
def papeletas():
    return render_template('papeletas.html')

@app.route('/registroEmpresas')
def registroEmpresas():
    return render_template('registroEmpresas.html')

@app.route('/registroUsuarios')
def registroUsuarios():
    return render_template('registroUsuarios.html')

if __name__ == '__main__':
    app.run(debug=True)
