import sqlite3
from flask import Flask
import os

DB_PATH = "berli.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, telephone TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS credits (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, montant REAL, date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS paiements (id INTEGER PRIMARY KEY AUTOINCREMENT, credit_id INTEGER, montant REAL, date TEXT)")
    conn.commit()
    conn.close()

app = Flask(__name__)
init_db()

@app.route('/')
def dashboard():
    try:
        db = get_db()
        total_credits = db.execute("SELECT COALESCE(SUM(montant),0) as t FROM credits").fetchone()['t']
        total_paye = db.execute("SELECT COALESCE(SUM(montant),0) as t FROM paiements").fetchone()['t']
        total_debt = total_credits - total_paye
        total_clients = db.execute("SELECT COUNT(*) as c FROM clients").fetchone()['c']
        db.close()
        
        return f"""
        <html><head><style>
        body{{font-family:Arial; background:#f4f4f4; padding:20px}}
        .card{{background:white; padding:20px; border-radius:10px; margin:10px; display:inline-block; min-width:200px; box-shadow:0 2px 5px #ccc}}
        h1{{color:#2c3e50}}
        </style></head><body>
        <h1>BERLI Distribution - LIVE ✅</h1>
        <div class="card"><h3>Total Dettes</h3><h2>{total_debt} FCFA</h2></div>
        <div class="card"><h3>Total Crédits</h3><h2>{total_credits} FCFA</h2></div>
        <div class="card"><h3>Clients</h3><h2>{total_clients}</h2></div>
        <p style="margin-top:20px">Félicitations Ulrich ! Ton app marche !</p>
        </body></html>
        """
    except Exception as e:
        return f"<h1>Erreur: {e}</h1>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
