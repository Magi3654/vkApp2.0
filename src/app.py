 
from flask import Flask, render_template

app = Flask (__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/desgloses')
def desgloses():
    return render_template('desgloses.html')

@app.route('/papeletas')
def papeletas():
    return render_template('papeletas.html')

@app.route('/newclient')
def clients():
    return render_template('registroEmpresas.html')

@app.route('/newuser')
def user():
    return render_template('registroUsuarios.html')

if __name__=='__main__':
    app.run(debug=True)