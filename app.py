from flask import Flask, request, redirect, session, render_template_string, Response
import sqlite3, os, csv, io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'berli-2026-final-complet'
DB = 'berli.db'

USERS = {
    'patron': 'berli2024',   # Toi Ulrich - accès total
    'gerant': 'gerant2024',  # Gérant - peut tout sauf supprimer
    'caissier': 'caisse2024' # Caissier - peut seulement vendre
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT, client TEXT DEFAULT "")')
    c.execute('CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, client TEXT, total INTEGER, paid INTEGER DEFAULT 0, remaining INTEGER, date TEXT, phone TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, debt_id INTEGER, amount INTEGER, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS movements (id INTEGER PRIMARY KEY, product TEXT, type TEXT, qty REAL, before REAL, after REAL, reason TEXT, date TEXT)')
    defaults = [('VODY', 500, 12000, 11000, 9000, 24, 10), ('DECA SOFT', 600, 14400, 13000, 10000, 24, 8), ('FOCUS', 500, 12000, 11000, 9000, 24, 12)]
    for d in defaults:
        try: c.execute('INSERT INTO products (name, pu, pc, pc10, cost_pc, nb, stock) VALUES (?,?,?,?,?,?,?)', d)
        except: pass
    conn.commit(); conn.close()

init_db()

BASE = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial; background:#f1f5f9; margin:0} .header{background:#0f172a; color:white; padding:15px; display:flex; justify-content:space-between}
.card{background:white; padding:15px; margin:10px; border-radius:12px; box-shadow:0 2px 6px #ccc}
.btn{background:#0f172a; color:white; padding:10px 15px; border:none; border-radius:8px; cursor:pointer; text-decoration:none; display:inline-block; margin:3px}
.btn-green{background:#16a34a} .btn-red{background:#dc2626} .btn-blue{background:#2563eb} .btn-purple{background:#7c3aed}
input,select{padding:10px; border-radius:8px; border:1px solid #ccc; width:95%; margin:5px 0}
table{width:100%; border-collapse:collapse} td,th{padding:8px; border-bottom:1px solid #eee; text-align:left; font-size:13px}
@media print{.no-print{display:none}}
</style></head><body>
<div class="header"><b>BERLI SOFT - {{USER}}</b><a href="/logout" style="color:white">Logout</a></div>
<div style="padding:10px">{{CONTENT}}</div></body></html>"""

def render(content, user=""):
    return render_template_string(BASE.replace("{{USER}}", user).replace("{{CONTENT}}", content))

@app.route('/login', methods=['GET','POST'])
def login():
    err=""
    if request.method=='POST':
        u=request.form.get('username','').lower(); p=request.form.get('password','')
        if u in USERS and USERS[u]['pass']==p:
            session['user']=u; session['name']=USERS[u]['name']; return redirect('/')
        err="Identifiants incorrects"
    return render(f"<div class='card' style='max-width:400px; margin:40px auto'><h2>BERLI Login</h2><form method='POST'><input name='username' placeholder='patron / caisse / stock' required><input name='password' type='password' placeholder='Mot de passe' required><button class='btn' style='width:100%'>Connexion</button></form><p style='color:red'>{err}</p></div>", "LOGIN")

@app.route('/logout')
def logout():
    session.clear(); return redirect('/login')

@app.route('/')
def dash():
    if 'user' not in session: return redirect('/login')
    db=get_db()
    today=datetime.now().strftime('%Y-%m-%d')
    st=db.execute('SELECT COALESCE(SUM(total),0) s, COALESCE(SUM(benefit),0) b FROM sales WHERE date LIKE ?', [f'{today}%']).fetchone()
    debt=db.execute('SELECT COALESCE(SUM(remaining),0) r FROM debts').fetchone()['r']
    prods=db.execute('SELECT * FROM products').fetchall()
    total=sum([(p['stock'] or 0)*p['pc'] for p in prods]); db.close()
    return render(f"""
    <h2>Bonjour {session['name']} 👋</h2>
    <div style="display:flex; flex-wrap:wrap">
    <div class="card"><h3>💰 Créances</h3><h2>{debt} F</h2></div>
    <div class="card"><h3>📦 Valeur Stock</h3><h2>{total} F</h2></div>
    <div class="card"><h3>📊 Ventes Jour</h3><h2>{st['s']} F</h2><small>Bénéf {st['b']} F</small></div>
    </div>
    <div class="card">
    <a href="/sales" class="btn btn-green">💵 VENTE + REÇU</a>
    <a href="/stock" class="btn">📦 STOCK</a>
    <a href="/add_stock" class="btn btn-blue">📥 ENTRÉE STOCK</a>
    <a href="/inventaire" class="btn btn-purple">⚖️ INVENTAIRE</a>
    <a href="/movements" class="btn">📈 MOUVEMENTS</a>
    <a href="/debts" class="btn btn-red">📒 DETTES</a>
    <a href="/products" class="btn btn-green">➕ AJOUTER ARTICLE</a>
    <a href="/print_stock" class="btn">🖨️ IMPRIMER STOCK</a>
    <a href="/export_stock" class="btn btn-blue">📥 EXPORT EXCEL</a>
    </div>
    """, session['name'])

# --- STOCK ---
@app.route('/stock')
def stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    rows="".join([f"<tr><td><b>{p['name']}</b></td><td>{p['stock']}</td><td>{p['pu']}F</td><td>{p['pc']}F</td><td>{p['pc10']}F</td><td>{p['stock']*p['pc']}F</td></tr>" for p in prods])
    return render(f"""
    <h2>Stock Existant BERLI</h2>
    <div class="no-print"><a href="/" class="btn">← Dashboard</a><a href="/print_stock" class="btn">🖨️ Imprimer Stock</a><a href="/export_stock" class="btn btn-blue">Export Excel</a></div>
    <div class="card"><table><tr><th>Produit</th><th>Stock Casiers</th><th>PU</th><th>PC</th><th>PC10</th><th>Valeur</th></tr>{rows}</table></div>
    """, session['name'])

@app.route('/print_stock')
def print_stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    date=datetime.now().strftime('%Y-%m-%d %H:%M')
    rows="".join([f"<tr><td>{p['name']}</td><td>{p['stock']}</td><td>{p['pu']}</td><td>{p['pc']}</td><td>{p['pc']}</td><td>{p['cost_pc']}</td><td>{p['stock']*p['pc']}</td><td>{p['stock']*p['nb']}</td></tr>" for p in prods])
    total=sum([p['stock']*p['pc'] for p in prods])
    return render_template_string(f"""
    <html><head><meta charset="utf-8"><title>Stock BERLI</title>
    <style>body{{font-family:Arial; max-width:900px; margin:20px auto; padding:20px}} table{{width:100%; border-collapse:collapse}} th,td{{border:1px solid black; padding:6px; font-size:12px}} th{{background:#eee}} @media print{{.no-print{{display:none}}}}</style>
    </head><body>
    <h2 style="text-align:center">BERLI DISTRIBUTION - INVENTAIRE STOCK</h2>
    <p>Date: {date} | Responsable: {session['name']}<br>Valeur totale stock: <b>{total} F CFA</b></p>
    <table><tr><th>Produit</th><th>Casiers</th><th>PU</th><th>PC</th><th>PC10</th><th>Coût</th><th>Valeur</th><th>Btls Total</th></tr>{rows}
    <tr><td colspan="6" style="text-align:right"><b>TOTAL</b></td><td><b>{total} F</b></td><td></td></tr></table>
    <p><br>Signature Responsable: ___________________ <br><br>Signature Patron: ___________________</p>
    <button onclick="window.print()" class="no-print" style="padding:15px; width:100%; background:black; color:white; border:none; border-radius:8px">🖨️ IMPRIMER STOCK</button>
    <a href="/stock" class="no-print">← Retour</a>
    </body></html>
    """)

@app.route('/export_stock')
def export_stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products').fetchall(); db.close()
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(['Nom','PU','PC','PC10','Cout_Casier','Nb_Btls','Stock_Casiers','Stock_Bouteilles','Valeur_Stock','Benefice_Unitaire','Benefice_Casier'])
    for p in prods:
        writer.writerow([p['name'], p['pu'], p['pc'], p['pc10'], p['cost_pc'], p['nb'], p['stock'], p['stock']*p['nb'], p['stock']*p['pc'], p['pu']-p['cost_pc']//p['nb'], p['pc']-p['cost_pc']])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=BERLI_Stock_'+datetime.now().strftime('%Y%m%d')+'.csv'})

# --- ENTREE STOCK ---
@app.route('/add_stock', methods=['GET','POST'])
def add_stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products').fetchall()
    if request.method=='POST':
        name=request.form.get('product'); qty=float(request.form.get('qty',0)); reason=request.form.get('reason','Livraison fournisseur')
        p=db.execute('SELECT * FROM products WHERE name=?',[name]).fetchone()
        before=p['stock']; after=before+qty
        db.execute('UPDATE products SET stock=? WHERE name=?',[after, name])
        db.execute('INSERT INTO movements (product, type, qty, before, after, reason, date) VALUES (?,?,?,?,?,?,?)',[name,'ENTREE',qty,before,after,reason,datetime.now().strftime('%Y-%m-%d %H:%M')])
        db.commit(); db.close(); return redirect('/stock')
    opts="".join([f"<option>{p['name']}</option>" for p in prods]); db.close()
    return render(f"""
    <h2>📥 Entrée Stock - Livraison Fournisseur</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card"><form method="POST"><label>Produit</label><select name="product">{opts}</select>
    <label>Qté Casiers Livrés</label><input name="qty" type="number" step="0.5" required>
    <label>Raison</label><select name="reason"><option>Livraison fournisseur</option><option>Retour client</option><option>Ajustement</option></select>
    <button class="btn btn-green">Valider Entrée Stock</button></form></div>
    """, session['name'])

# --- INVENTAIRE ---
@app.route('/inventaire', methods=['GET','POST'])
def inventaire():
    if 'user' not in session: return redirect('/login')
    db=get_db()
    if request.method=='POST':
        for k in request.form:
            if k.startswith('count_'):
                pid=int(k.split('_')[1]); counted=float(request.form.get(k,0) or 0)
                p=db.execute('SELECT * FROM products WHERE id=?',[pid]).fetchone()
                if p:
                    before=p['stock'] or 0; diff=counted-before
                    if diff!=0:
                        db.execute('UPDATE products SET stock=? WHERE id=?',[counted, pid])
                        db.execute('INSERT INTO movements (product, type, qty, before, after, reason, date) VALUES (?,?,?,?,?,?,?)',[p['name'],'INVENTAIRE',diff,before,counted,f"Inventaire - Ecart {diff:+}",datetime.now().strftime('%Y-%m-%d %H:%M')])
        db.commit(); db.close(); return redirect('/print_stock?inventaire=1')
    prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    rows="".join([f"<tr><td><b>{p['name']}</b><br><small>Théo: {p['stock']}</small></td><td><input name='count_{p['id']}' type='number' step='0.5' value='{p['stock']}' style='width:90px' required></td></tr>" for p in prods])
    return render(f"""
    <h2>⚖️ Session Inventaire - Comptage Physique</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card"><p>Compte tes casiers réels, note, puis valide. Le stock sera mis à jour et imprimable.</p>
    <form method="POST"><table><tr><th>Produit</th><th>Compté Réel</th></tr>{rows}</table>
    <button class="btn btn-purple" style="width:100%; padding:15px">✅ Valider Inventaire & Imprimer Rapport</button></form></div>
    """, session['name'])

# --- MOUVEMENTS ---
@app.route('/movements')
def movements():
    if 'user' not in session: return redirect('/login')
    db=get_db(); moves=db.execute('SELECT * FROM movements ORDER BY id DESC LIMIT 100').fetchall(); db.close()
    rows="".join([f"<tr><td>{m['date']}</td><td>{m['product']}</td><td>{m['type']}</td><td style='color:{'green' if m['qty']>0 else 'red'}'>{m['qty']:+}</td><td>{m['before']}→{m['after']}</td><td>{m['reason']}</td></tr>" for m in moves])
    return render(f"""
    <h2>📈 Mouvements Stock</h2><a href="/" class="btn">← Dashboard</a><a href="/export_stock" class="btn btn-blue">Export Excel</a>
    <div class="card"><table><tr><th>Date</th><th>Produit</th><th>Type</th><th>Qté</th><th>Avant→Après</th><th>Raison</th></tr>{rows if rows else '<tr><td colspan=6>Aucun mouvement</td></tr>'}</table></div>
    """, session['name'])

# --- VENTES + TICKET + FACTURE ---
@app.route('/sales', methods=['GET','POST'])
def sales():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products').fetchall()
    if request.method=='POST':
        product=request.form.get('product'); qty=float(request.form.get('qty',1)); type_v=request.form.get('type_v','detail'); client=request.form.get('client','')
        pr=db.execute('SELECT * FROM products WHERE name=?',[product]).fetchone()
        if type_v=='detail':
            total=int(qty*pr['pu']); benefit=int(qty*(pr['pu']-pr['cost_pc']//pr['nb'])); pu_final=pr['pu']; ded=qty/(pr['nb'] or 24)
        elif type_v=='casier':
            total=int(qty*pr['pc']); benefit=int(qty*(pr['pc']-pr['cost_pc'])); pu_final=pr['pc']; ded=qty
        else:
            total=int(qty*pr['pc10']); benefit=int(qty*(pr['pc10']-pr['cost_pc'])); pu_final=pr['pc10']; ded=qty
        db.execute('UPDATE products SET stock=stock-? WHERE name=?',[ded, product])
        cur=db.cursor(); cur.execute('INSERT INTO sales (product, qty, type, pu_final, total, benefit, seller, date, client) VALUES (?,?,?,?,?,?,?,?,?)',[product, qty, type_v, pu_final, total, benefit, session['name'], datetime.now().strftime('%Y-%m-%d %H:%M'), client])
        sid=cur.lastrowid
        if request.form.get('credit')=='on' and client:
            db.execute('INSERT INTO debts (client, total, paid, remaining, date, phone) VALUES (?,?,?,?,?,?)',[client, total, 0, total, datetime.now().strftime('%Y-%m-%d %H:%M'), ''])
        db.commit(); db.close(); return redirect(f'/ticket/{sid}')
    sales_list=db.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 20').fetchall(); db.close()
    opts="".join([f"<option>{p['name']}</option>" for p in prods])
    rows="".join([f"<tr><td>{s['date']}</td><td>{s['product']}</td><td>{s['qty']}</td><td>{s['total']}F</td><td>{s['client']}</td><td><a href='/ticket/{s['id']}' class='btn'>🧾 Reçu</a><a href='/facture/{s['id']}' class='btn btn-blue'>Facture</a></td></tr>" for s in sales_list])
    return render(f"""
    <h2>Vente BERLI</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card"><form method="POST"><label>Produit</label><select name="product">{opts}</select>
    <label>Qté</label><input name="qty" type="number" step="0.5" value="1" required>
    <label>Type</label><select name="type_v"><option value="detail">Bouteille Détail</option><option value="casier">Casier PACK</option><option value="casier10">10 Casiers+</option></select>
    <label>Client</label><input name="client" placeholder="FL O PARC BASAR">
    <label><input type="checkbox" name="credit"> Vente à crédit ?</label><br>
    <button class="btn btn-green">Vendre & Imprimer</button></form></div>
    <div class="card"><table><tr><th>Date</th><th>Produit</th><th>Qté</th><th>Total</th><th>Client</th><th>Imprimer</th></tr>{rows}</table></div>
    """, session['name'])

@app.route('/ticket/<int:sid>')
def ticket(sid):
    if 'user' not in session: return redirect('/login')
    db=get_db(); s=db.execute('SELECT * FROM sales WHERE id=?',[sid]).fetchone(); db.close()
    if not s: return "Ticket introuvable"
    return render_template_string(f"""
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{font-family:monospace; max-width:350px; margin:10px auto; background:white; padding:15px; border:1px dashed black}}
    h2{{text-align:center}} .line{{border-top:1px dashed black; margin:8px 0}} .big{{font-size:18px; font-weight:bold}}
    .btn{{padding:12px; width:100%; background:black; color:white; border:none; border-radius:6px; margin-top:8px}} @media print{{.no-print{{display:none}} body{{border:none}}}}
    </style></head><body>
    <h2>BERLI DISTRIBUTION</h2><div style="text-align:center">Lomé - TOGO<br>Distribution Boissons</div><div class="line"></div>
    <div>Reçu N°: {s['id']:05d}<br>Date: {s['date']}<br>Vendeur: {s['seller']}<br>Client: {s['client'] or 'Comptant'}</div><div class="line"></div>
    <div>Produit: {s['product']}<br>Qté: {s['qty']} ({s['type']})<br>PU: {s['pu_final']} F<br><span class="big">TOTAL: {s['total']} F CFA</span></div><div class="line"></div>
    <div style="text-align:center">Merci pour votre confiance !</div>
    <button onclick="window.print()" class="btn no-print">🖨️ IMPRIMER REÇU</button>
    <a href="/facture/{s['id']}" class="no-print" style="display:block; text-align:center; margin-top:8px; background:#2563eb; color:white; padding:12px; border-radius:6px; text-decoration:none">📄 IMPRIMER FACTURE</a>
    <a href="/sales" class="no-print" style="display:block; text-align:center; margin-top:8px">← Retour</a>
    </body></html>
    """)

@app.route('/facture/<int:sid>')
def facture(sid):
    if 'user' not in session: return redirect('/login')
    db=get_db(); s=db.execute('SELECT * FROM sales WHERE id=?',[sid]).fetchone(); db.close()
    if not s: return "Facture introuvable"
    tva=int(s['total']*0.18); ht=s['total']-tva
    return render_template_string(f"""
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{font-family:Arial; max-width:700px; margin:20px auto; padding:20px}} .line{{border-top:2px solid black; margin:15px 0}}
    table{{width:100%; border-collapse:collapse}} th,td{{border:1px solid #ccc; padding:8px}} th{{background:#eee}} .right{{text-align:right}}
    .btn{{padding:12px; width:100%; background:black; color:white; border:none; border-radius:6px; margin-top:15px}} @media print{{.no-print{{display:none}}}}
    </style></head><body>
    <div style="display:flex; justify-content:space-between"><div><h2>BERLI DISTRIBUTION</h2>Lomé - TOGO<br>Tel: +228 XX XX XX</div><div><h3>FACTURE</h3>N°: FAC-{s['id']:05d}<br>Date: {s['date']}<br>Client: <b>{s['client'] or 'Comptant'}</b></div></div>
    <div class="line"></div>
    <table><tr><th>Désignation</th><th>Qté</th><th>PU</th><th>Total HT</th></tr>
    <tr><td>{s['product']} ({s['type']})</td><td>{s['qty']}</td><td>{s['pu_final']} F</td><td>{ht} F</td></tr>
    <tr><td colspan="3" class="right">TVA 18%</td><td>{tva} F</td></tr>
    <tr><td colspan="3" class="right"><b>TOTAL TTC</b></td><td><b>{s['total']} F CFA</b></td></tr></table>
    <p>Arrêtée à <b>{s['total']} F CFA</b> - Vendeur: {s['seller']}</p>
    <button onclick="window.print()" class="btn no-print">🖨️ IMPRIMER FACTURE VENTE</button>
    <a href="/ticket/{s['id']}" class="no-print" style="display:block; text-align:center; margin-top:8px">← Reçu</a>
    </body></html>
    """)

@app.route('/debts')
def debts():
    if 'user' not in session: return redirect('/login')
    db=get_db(); ds=db.execute('SELECT * FROM debts ORDER BY id DESC').fetchall(); db.close()
    rows="".join([f"<tr><td>{d['client']}</td><td>{d['total']}F</td><td>{d['remaining']}F</td><td>{d['date']}</td><td><a href='/pay/{d['id']}' class='btn btn-green'>Payer</a></td></tr>" for d in ds])
    return render(f"<h2>Dettes</h2><a href='/' class='btn'>← Dashboard</a><div class='card'><table><tr><th>Client</th><th>Total</th><th>Reste</th><th>Date</th><th>Action</th></tr>{rows if rows else '<tr><td colspan=5>Aucune dette</td></tr>'}</table></div>", session['name'])

@app.route('/pay/<int:did>', methods=['GET','POST'])
def pay(did):
    if 'user' not in session: return redirect('/login')
    db=get_db(); debt=db.execute('SELECT * FROM debts WHERE id=?',[did]).fetchone()
    if request.method=='POST':
        amount=int(request.form.get('amount',0)); new_paid=debt['paid']+amount; new_rem=debt['total']-new_paid
        db.execute('UPDATE debts SET paid=?, remaining=? WHERE id=?',[new_paid, new_rem, did])
        db.execute('INSERT INTO payments (debt_id, amount, date) VALUES (?,?,?)',[did, amount, datetime.now().strftime('%Y-%m-%d %H:%M')])
        db.commit(); db.close(); return redirect('/debts')
    db.close()
    return render(f"<h2>Paiement {debt['client']} - Reste {debt['remaining']}F</h2><div class='card'><form method='POST'><input name='amount' type='number' required><button class='btn btn-green'>Payer</button></form></div>", session['name'])

@app.route('/products', methods=['GET','POST'])
def manage_products():
    if 'user' not in session:
        return redirect('/login')
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name','').strip().upper()
        pu = int(request.form.get('pu') or 0)
        pc = int(request.form.get('pc') or 0)
        pc10 = int(request.form.get('pc10') or pc)
        cost = int(request.form.get('cost') or 0)
        nb = int(request.form.get('nb') or 24)
        stock = float(request.form.get('stock') or 0)
        if name:
            try:
                db.execute('INSERT INTO products (name, pu, pc, pc10, cost_pc, nb, stock) VALUES (?,?,?,?,?,?,?)',
                           [name, pu, pc, pc10, cost, nb, stock])
                db.commit()
            except:
                db.execute('UPDATE products SET pu=?, pc=?, pc10=?, cost_pc=?, nb=?, stock=? WHERE name=?',
                           [pu, pc, pc10, cost, nb, stock, name])
                db.commit()
        db.close()
        return redirect('/products')
    
    prods = db.execute('SELECT * FROM products ORDER BY name').fetchall()
    db.close()
    rows = "".join([f"<tr><td>{p['name']}</td><td>{p['pu']}F</td><td>{p['pc']}F</td><td>{p['stock']}</td><td><a href='/delete_product/{p['id']}' class='btn btn-red' onclick='return confirm(\"Supprimer {p['name']} ?\")'>🗑️</a></td></tr>" for p in prods])
    
    return render(f"""
    <h2>📦 Gestion des Articles - Ajout Facile</h2>
    <a href="/" class="btn">← Dashboard</a> <a href="/stock" class="btn">Stock</a>
    
    <div class="card" style="border:2px solid #16a34a">
    <h3>➕ Ajouter un Nouvel Article (toi-même)</h3>
    <form method="POST">
    <label>Nom Article * (ex: CHAPMAN 33CL)</label><input name="name" placeholder="Nom en MAJUSCULE" required>
    <div style="display:flex; gap:10px">
    <div style="flex:1"><label>PU Détail (1 bouteille)</label><input name="pu" type="number" placeholder="500" required></div>
    <div style="flex:1"><label>PC Casier (1 casier)</label><input name="pc" type="number" placeholder="12000" required></div>
    <div style="flex:1"><label>PC10 (10 casiers+)</label><input name="pc10" type="number" placeholder="11000"></div>
    </div>
    <div style="display:flex; gap:10px">
    <div style="flex:1"><label>Coût Achat Casier</label><input name="cost" type="number" placeholder="9000"></div>
    <div style="flex:1"><label>Nb Btls / Casier</label><input name="nb" type="number" value="24"></div>
    <div style="flex:1"><label>Stock Départ Casiers</label><input name="stock" type="number" step="0.5" value="0"></div>
    </div>
    <button class="btn btn-green" style="width:100%; padding:15px; font-size:16px">✅ Ajouter l'Article</button>
    </form>
    <p style="font-size:12px; color:gray">Astuce: Si l'article existe déjà, ça met à jour ses prix.</p>
    </div>

    <div class="card">
    <h3>Liste de tes Articles ({len(prods)} articles)</h3>
    <table><tr><th>Nom</th><th>PU</th><th>PC</th><th>Stock</th><th>Action</th></tr>{rows}</table>
    </div>
    """, session['name'])

@app.route('/delete_product/<int:pid>')
def delete_product(pid):
    if 'user' not in session:
        return redirect('/login')
    if session.get('user') != 'patron':
        return "Seul le patron peut supprimer"
    db = get_db()
    db.execute('DELETE FROM products WHERE id=?', [pid])
    db.commit()
    db.close()
    return redirect('/products')
if __name__ == '__main__':
    port=int(os.environ.get("PORT",5000))
    app.run(host='0.0.0.0', port=port)
