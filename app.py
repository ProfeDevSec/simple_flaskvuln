# app.py — Aplicación Flask VULNERABLE (solo para fines educativos)
from flask import Flask, request, render_template_string
import sqlite3, pickle, os

app = Flask(__name__)

# VULN-1: XSS Reflejado — entrada de usuario sin escapar
@app.route('/hello')
def hello():
    name = request.args.get('name', 'Mundo')
    return render_template_string(f'<h1>Hola, {name}!</h1>')

# VULN-2: SQL Injection — consulta sin parametrizar
@app.route('/user')
def get_user():
    user_id = request.args.get('id', '1')
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM users WHERE id = {user_id}')
    return str(cur.fetchall())

# VULN-3: RCE — ejecución de comandos del sistema
@app.route('/ping')
def ping():
    host = request.args.get('host', '127.0.0.1')
    return os.popen(f'ping -c 1 {host}').read()

# VULN-4: Deserialización insegura
@app.route('/load', methods=['POST'])
def load_data():
    data = request.get_data()
    return str(pickle.loads(data))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
