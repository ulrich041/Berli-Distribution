import sqlite3

DB_PATH = "berli.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, telephone TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS credits 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, montant REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS paiements 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, credit_id INTEGER, montant REAL, date TEXT)''')
    conn.commit()
    conn.close(
  from flask import Flask, render_template, request, redirect, url_for, session
from database import get_db, init_db
import os

app = Flask(__name__)
app.secret_key = "berli-2026"
init_db()

@app.route('/')
def dashboard():
    db = get_db()
    total_credits = db.execute("SELECT COALESCE(SUM(montant),0) as t FROM credits").fetchone()['t']
    total_paye = db.execute("SELECT COALESCE(SUM(montant),0) as t FROM paiements").fetchone()['t']
    total_debt = total_credits - total_paye
    total_clients = db.execute("SELECT COUNT(*) as c FROM clients").fetchone()['c']
    db.close()
    return render_template('dashboard.html', total_debt=total_debt, total_credits=total_credits, total_clients=total_clients)

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
