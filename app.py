from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'berli-2026-final-ulrich'
DB = 'berli.db'

USERS = {
    'patron': {'pass': 'berli2024', 'role': 'patron', 'name': 'ULRICH'},
    'caisse': {'pass': 'caisse123', 'role': 'caissier', 'name': 'CAISSE'},
    'stock': {'pass': 'stock123', 'role': 'stock', 'name': 'STOCK'}
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT, client TEXT DEFAULT "")')
    c.execute('CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, client TEXT, total INTEGER, paid INTEGER DEFAULT 0, remaining INTEGER, date TEXT, phone TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, debt_id INTEGER, amount INTEGER, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS movements (id INTEGER PRIMARY KEY, product TEXT, type TEXT, qty REAL, before REAL, after REAL, reason TEXT, date TEXT)')
    # Produits par defaut BERLI
    defaults = [
        ('VODY', 500, 12000, 11000, 9000, 24, 10),
        ('DECA SOFT', 600, 14400, 13000, 10000, 24, 8),
        ('FOCUS', 500, 12000, 11000, 9000, 24, 12)
    ]
    for d in defaults:
        try:
            c.execute('INSERT INTO products (name, pu, pc, pc10, cost_pc, nb, stock) VALUES (?,?,?,?,?,?,?)', d)
        except:
            pass
    conn.commit()
    conn.close()

init_db()

BASE_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial; background:#f1f5f9; margin:0; padding:0}
.header{background:#0f172a; color:white; padding:15px; display:flex; justify-content:space-between}
.card{background:white; padding:15px; margin:10px; border-radius:12px; box-shadow:0 2px 6px #ccc}
.btn{background:#0f172a; color:white; padding:10px 15px; border:none; border-radius:8px; cursor:pointer; text-decoration:none; display:inline-block; margin:5px}
.btn-green{background:#16a34a} .btn-red{background:#dc2626} .btn-blue{background:#2563eb}
input,select{padding:10px; border-radius:8px; border:1px solid #ccc; width:95%; margin:5px 0}
table{width:100%; border-collapse:collapse} td,th{padding:8px; border-bottom:1px solid #eee; text-align:left}
</style></head><body>
<div class="header"><b>BERLI SOFT - {{user}}</b><span><a href="/logout" style="color:white">Logout</a></span></div>
<div style="padding:10px">
{{content|safe}}
</div></body></html>
"""

LOGIN_HTML = """
<div style="max-width:400px; margin:50px auto" class="card">
<h2>BERLI Distribution - Login</h2>
<form method="POST">
<input name="username" placeholder="Utilisateur: patron / caisse / stock" required>
<input name="password" type="password" placeholder="Mot de passe" required>
<button class="btn" style="width:100%">Connexion</button>
</form>
<p style="font-size:12px; color:gray">patron: berli2024 | caisse: caisse123 | stock: stock123</p>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
</div>
"""

@app.route('/login', methods=['GET','POST'])
def login():
    error = ""
    if request.method == 'POST':
        u = request.form.get('username','').lower()
        p = request.form.get('password','')
        if u in USERS and USERS[u]['pass'] == p:
            session['user'] = u
            session['name'] = USERS[u]['name']
            session['role'] = USERS[u]['role']
            return redirect('/')
        else:
            error = "Identifiants incorrects"
    return render_template_string(BASE_HTML.replace("{{content|safe}}", LOGIN_HTML).replace("{{user}}","LOGIN"), error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    total_stock_val = 0
    products = db.execute('SELECT * FROM products').fetchall()
    for pr in products:
        total_stock_val += (pr['stock'] or 0) * pr['pc']
    
    today = datetime.now().strftime('%Y-%m-%d')
    sales_today = db.execute('SELECT COALESCE(SUM(total),0) as s, COALESCE(SUM(benefit),0) as b FROM sales WHERE date LIKE ?',[f'{today}%']).fetchone()
    debts_total = db.execute('SELECT COALESCE(SUM(remaining),0) as r FROM debts').fetchone()['r']
    low_stock = db.execute('SELECT * FROM products WHERE stock < 3').fetchall()
    db.close()

    content = f"""
    <h2>Bonjour {session['name']} 👋</h2>
    <div class="card"><b>Focus Aujourd'hui ({today})</b><br>
    Ventes: {sales_today['s']} FCFA | Benefice: {sales_today['b']} FCFA</div>
    <div style="display:flex; flex-wrap:wrap">
    <div class="card"><h3>💰 Creances</h3><h2>{debts_total} F</h2><a href="/debts" class="btn">Voir Dettes</a></div>
    <div class="card"><h3>📦 Valeur Stock</h3><h2>{total_stock_val} F</h2><a href="/stock" class="btn">Stock</a></div>
    <div class="card"><h3>📊 Ventes Jour</h3><h2>{sales_today['s']} F</h2><a href="/sales" class="btn btn-blue">Vendre</a></div>
    </div>
    <div class="card"><h3>⚠️ Alerte Stock < 3 casiers</h3>
    {"<br>".join([f"{p['name']}: {p['stock']} casiers" for p in low_stock]) if low_stock else "Aucune alerte"}
    </div>
    <a href="/stock" class="btn">📦 STOCK</a>
    <a href="/sales" class="btn btn-green">💵 VENTE</a>
    <a href="/debts" class="btn btn-red">📒 DETTES</a>
    <a href="/products" class="btn btn-blue">➕ PRODUITS</a>
    """
    return render_template_string(BASE_HTML.replace("{{user}}", session['name']).replace("{{content|safe}}", content))

@app.route('/stock')
def stock_view():
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    prods = db.execute('SELECT * FROM products ORDER BY name').fetchall()
    db.close()
    rows = ""
    for p in prods:
        rows += f"<tr><td>{p['name']}</td><td>{p['stock']}</td><td>{p['pu']}F</td><td>{p['pc']}F</td><td>{p['pc10']}F</td><td><a href='/add_stock/{p['id']}' class='btn btn-green'>+ Stock</a></td></tr>"
    content = f"""
    <h2>Stock BERLI</h2>
    <a href="/" class="btn">← Dashboard</a>
    <div class="card"><table><tr><th>Produit</th><th>Stock Casiers</th><th>PU</th><th>PC</th><th>PC10</th><th>Action</th></tr>{rows}</table></div>
    """
    return render_template_string(BASE_HTML.replace("{{user}}", session['name']).replace("{{content|safe}}", content))

@app.route('/add_stock/<int:pid>', methods=['GET','POST'])
def add_stock(pid):
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    prod = db.execute('SELECT * FROM products WHERE id=?',[pid]).fetchone()
    if request.method == 'POST':
        qty = float(request.form.get('qty',0))
        reason = request.form.get('reason','Livraison fournisseur')
        before = prod['stock']
        after = before + qty
        db.execute('UPDATE products SET stock=? WHERE id=?',[after, pid])
        db.execute('INSERT INTO movements (product, type, qty, before, after, reason, date) VALUES (?,?,?,?,?,?,?)',[prod['name'],'ENTREE',qty,before,after,reason,datetime.now().strftime('%Y-%m-%d %H:%M')])
        db.commit()
        db.close()
        return redirect('/stock')
    db.close()
    content = f"""
    <h2>Entrée Stock - {prod['name']}</h2>
    <div class="card">
    <p>Stock actuel: {prod['stock']} casiers</p>
    <form method="POST">
    <label>Qté casiers livrés</label><input name="qty" type="number" step="0.5" required>
    <label>Raison</label><select name="reason"><option>Livraison fournisseur</option><option>Inventaire</option><option>Casse</option><option>Retour client</option></select>
    <button class="btn btn-green">Valider Entrée</button>
    </form></div>
    """
    return render_template_string(BASE_HTML.replace("{{user}}", session['name']).replace("{{content|safe}}", content))

@app.route('/sales', methods=['GET','POST'])
def sales():
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    prods = db.execute('SELECT * FROM products').fetchall()
    if request.method == 'POST':
        product = request.form.get('product')
        qty = float(request.form.get('qty',1))
        type_v = request.form.get('type_v','detail')
        client = request.form.get('client','')
        credit = request.form.get('credit') == 'on'
        pr = db.execute('SELECT * FROM products WHERE name=?',[product]).fetchone()
        if type_v == 'detail':
            pu = pr['pu']
        elif type_v == 'pack':
            pu = pr['pc'] // pr['nb'] if pr['nb'] else pr['pu']
            qty = qty * pr['nb']  # qty en packs converti en bouteilles pour calcul stock? Simplifie
            qty = float(request.form.get('qty',1))  # garde simple
            pu = pr['pc']
            type_v = 'casier'
        else:
            pu = pr['pc10'] // pr['nb'] if pr['nb'] else pr['pu']
        
        total = int(qty * (pr['pu'] if type_v=='detail' else (pr['pc'] if type_v=='casier' else pr['pc10']) //1))
        # calcul simple
        if type_v == 'detail':
            total = int(qty * pr['pu'])
            benefit = int(qty * (pr['pu'] - (pr['cost_pc']//pr['nb'] if pr['nb'] else 0)))
        elif type_v == 'casier':
            total = int(qty * pr['pc'])
            benefit = int(qty * (pr['pc'] - pr['cost_pc']))
        else:
            total = int(qty * pr['pc10'])
            benefit = int(qty * (pr['pc10'] - pr['cost_pc']))
        
        # Retire stock (1 casier = nb bouteilles mais on stocke en casiers)
        stock_deduction = qty if type_v != 'detail' else qty / (pr['nb'] or 24)
        db.execute('UPDATE products SET stock = stock - ? WHERE name=?',[stock_deduction, product])
        db.execute('INSERT INTO sales (product, qty, type, pu_final, total, benefit, seller, date, client) VALUES (?,?,?,?,?,?,?,?,?)',[product, qty, type_v, pu, total, benefit, session['name'], datetime.now().strftime('%Y-%m-%d %H:%M'), client])
        if credit and client:
            db.execute('INSERT INTO debts (client, total, paid, remaining, date, phone) VALUES (?,?,?,?,?,?)',[client, total, 0, total, datetime.now().strftime('%Y-%m-%d %H:%M'), ''])
        db.commit()
        db.close()
        return redirect('/')
    
    sales_list = db.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 20').fetchall()
    db.close()
    opts = "".join([f"<option>{p['name']}</option>" for p in prods])
    rows = "".join([f"<tr><td>{s['date']}</td><td>{s['product']}</td><td>{s['qty']}</td><td>{s['total']}F</td><td>{s['client']}</td></tr>" for s in sales_list])
    content = f"""
    <h2>Vente BERLI</h2>
    <a href="/" class="btn">← Dashboard</a>
    <div class="card">
    <form method="POST">
    <label>Produit</label><select name="product">{opts}</select>
    <label>Qté</label><input name="qty" type="number" step="0.5" value="1" required>
    <label>Type</label><select name="type_v"><option value="detail">1 Bouteille (detail)</option><option value="casier">1 Casier (PACK)</option><option value="casier10">10 Casiers+</option></select>
    <label>Client (si credit)</label><input name="client" placeholder="Ex: FL O PARC BASAR">
    <label><input type="checkbox" name="credit"> Vente à crédit ?</label><br>
    <button class="btn btn-green">Vendre</button>
    </form></div>
    <div class="card"><h3>Dernières ventes</h3><table><tr><th>Date</th><th>Produit</th><th>Qté</th><th>Total</th><th>Client</th></tr>{rows}</table></div>
    """
    return render_template_string(BASE_HTML.replace("{{user}}", session['name']).replace("{{content|safe}}", content))

@app.route('/debts')
def debts():
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    ds = db.execute('SELECT * FROM debts ORDER BY id DESC').fetchall()
    db.close()
    rows = ""
    for d in ds:
        rows += f"<tr><td>{d['client']}</td><td>{d['total']}F</td><td>{d['paid']}F</td><td><b>{d['remaining']}F</b></td><td>{d['date']}</td><td><a href='/pay/{d['id']}' class='btn btn-green'>Payer</a></td></tr>"
    content = f"""
    <h2>Gestion des Créances</h2>
    <a href="/" class="btn">← Dashboard</a>
    <div class="card"><table><tr><th>Client</th><th>Total</th><th>Payé</th><th>Reste</th><th>Date</th><th>Action</th></tr>{rows if rows else "<tr><td colspan=6>Aucune dette - Ex: FL O PARC BASAR 22.000F apparaitra ici</td></tr>"}</table></div>
    """
    return render_template_string(BASE_HTML.replace("{{user}}", session['name']).replace("{{content|safe}}", content))

@app.route('/pay/<int:did>', methods=['GET','POST'])
def pay(did):
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    debt = db.execute('SELECT * FROM debts WHERE id=?',[did]).fetchone()
    if request.method == 'POST':
        amount = int(request.form.get('amount',0))
        new_paid = debt['paid'] + amount
        new_rem = debt['total'] - new_paid
        db.execute('UPDATE debts SET paid=?, remaining=? WHERE id=?',[new_paid, new_rem, did])
        db.execute('INSERT INTO payments (debt_id, amount, date) VALUES (?,?,?)',[did, amount, datetime.now().strftime('%Y-%m-%d %H:%M')])
        db.commit()
        db.close()
        return redirect('/debts')
    db.close()
    content = f"""
    <h2>Règlement - {debt['client']}</h2>
    <div class="card">
    <p>Total: {debt['total']}F | Déjà payé: {debt['paid']}F | Reste: {debt['remaining']}F</p>
    <form method="POST">
    <label>Montant payé maintenant</label><input name="amount" type="number" required>
    <button class="btn btn-green">Valider Paiement</button>
    </form></div>
    """
    return render_template_string(BASE_HTML.replace("{{user}}", session['name']).replace("{{content|safe}}", content))

@app.route('/products', methods=['GET','POST'])
def products():
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name','').upper()
        pu = int(request.form.get('pu',0))
        pc = int(request.form.get('pc',0))
        pc10 = int(request.form.get('pc10',0))
        cost = int(request.form.get('cost',0))
        nb = int(request.form.get('nb',24))
        stock = float(request.form.get('stock',0))
        try:
            db.execute('INSERT INTO products (name, pu, pc, pc10, cost_pc, nb, stock) VALUES (?,?,?,?,?,?,?)',[name, pu, pc, pc10, cost, nb, stock])
            db.commit()
        except:
            pass
    db.close()
    return redirect('/stock')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
