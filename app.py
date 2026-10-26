from flask import Flask, render_template
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
