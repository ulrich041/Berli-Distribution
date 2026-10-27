from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os, json
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'berli-2026-final-fix'
DB = '/data/berli.db' if os.path.exists('/data') else 'berli.db'
USERS = {'patron': {'pass': 'berli2024', 'name': 'Patron Ulrich'}, 'gerant': {'pass': 'gerant2024', 'name': 'Gerant'}, 'caissier': {'pass': 'caisse2024', 'name': 'Caissier'}}
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT, client TEXT DEFAULT "", group_id TEXT DEFAULT "")')
    c.execute('CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, client TEXT, total INTEGER, paid INTEGER DEFAULT 0, remaining INTEGER, date TEXT, phone TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS movements (id INTEGER PRIMARY KEY, product TEXT, type TEXT, qty REAL, before REAL, after REAL, reason TEXT, date TEXT)')
    defaults = [('VODY', 500, 12000, 11000, 9000, 24, 10), ('DECA SOFT', 600, 14400, 13000, 10000, 24, 8), ('FOCUS', 500, 12000, 11000, 9000, 24, 12)]
    for d in defaults:
        try: c.execute('INSERT INTO products (name, pu, pc, pc10, cost_pc, nb, stock) VALUES (?,?,?,?,?,?,?)', d)
        except: pass
    conn.commit(); conn.close()
init_db()
BASE = """<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><style>body{font-family:Arial;background:#f1f5f9;margin:0}.header{background:#0f172a;color:white;padding:15px;display:flex;justify-content:space-between}.card{background:white;padding:15px;margin:10px;border-radius:12px;box-shadow:0 2px 6px #ccc}.btn{background:#0f172a;color:white;padding:10px 15px;border:none;border-radius:8px;cursor:pointer;text-decoration:none;display:inline-block;margin:3px}.btn-green{background:#16a34a}.btn-red{background:#dc2626}.btn-blue{background:#2563eb}.btn-purple{background:#7c3aed}input,select{padding:10px;border-radius:8px;border:1px solid #ccc;width:95%;margin:5px 0}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #eee;text-align:left;font-size:13px}</style></head><body><div class='header'><b>BERLI SOFT - {{USER}}</b><a href='/logout' style='color:white'>Logout</a></div><div style='padding:10px'>{{CONTENT}}</div></body></html>"""
def render_page(content, user=""):
    return render_template_string(BASE.replace("{{USER}}", user).replace("{{CONTENT}}", content))
@app.route('/login', methods=['GET','POST'])
def login():
    err=""
    if request.method=='POST':
        u=request.form.get('username','').lower().strip(); p=request.form.get('password','').strip()
        if u in USERS and USERS[u]['pass']==p:
            session['user']=u; session['name']=USERS[u]['name']; return redirect('/')
        err="Identifiants incorrects"
    return render_page(f"<div class='card' style='max-width:400px;margin:40px auto'><h2>BERLI Login</h2><form method='POST'><input name='username' placeholder='patron / gerant / caissier' required><input name='password' type='password' placeholder='Mot de passe' required><button class='btn' style='width:100%'>Connexion</button></form><p style='color:red'>{err}</p></div>", "LOGIN")
@app.route('/logout')
def logout():
    session.clear(); return redirect('/login')
@app.route('/')
def dash():
    if 'user' not in session: return redirect('/login')
    db=get_db(); today=datetime.now().strftime('%Y-%m-%d')
    st=db.execute('SELECT COALESCE(SUM(total),0) s, COALESCE(SUM(benefit),0) b FROM sales WHERE date LIKE ?', [f'{today}%']).fetchone()
    debt=db.execute('SELECT COALESCE(SUM(remaining),0) r FROM debts').fetchone()
    prods=db.execute('SELECT * FROM products').fetchall(); total=sum([(p['stock'] or 0)*p['pc'] for p in prods]); db.close()
    return render_page(f"<h2>Bonjour {session['name']}</h2><div style='display:flex;flex-wrap:wrap'><div class='card'><h3>Creances</h3><h2>{debt['r']} F</h2></div><div class='card'><h3>Valeur Stock</h3><h2>{total} F</h2></div><div class='card'><h3>Ventes Jour</h3><h2>{st['s']} F</h2><small>Benef {st['b']} F</small></div></div><div class='card'><a href='/sales' class='btn btn-green'>VENTE MULTIPLE</a><a href='/stock' class='btn'>STOCK</a><a href='/entree_stock' class='btn btn-blue'>ENTREE STOCK</a><a href='/products' class='btn btn-green'>AJOUTER ARTICLE</a><a href='/print_stock' class='btn'>IMPRIMER</a></div>", session['name'])
@app.route('/stock')
def stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    rows="".join([f"<tr><td><b>{p['name']}</b></td><td>{p['stock']}</td><td>{p['pu']}F</td><td>{p['pc']}F</td><td>{p['pc10']}F</td><td>{p['stock']*p['pc']}F</td></tr>" for p in prods])
    return render_page(f"<h2>Stock</h2><a href='/' class='btn'>Dashboard</a><a href='/print_stock' class='btn'>Imprimer</a><div class='card'><table><tr><th>Produit</th><th>Stock</th><th>PU</th><th>PC</th><th>PC10</th><th>Valeur</th></tr>{rows}</table></div>", session['name'])
@app.route('/print_stock')
def print_stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    date=datetime.now().strftime('%Y-%m-%d %H:%M'); rows="".join([f"<tr><td>{p['name']}</td><td>{p['stock']}</td><td>{p['pu']}</td><td>{p['pc']}</td><td>{p['pc10']}</td><td>{p['stock']*p['pc']}</td></tr>" for p in prods]); total=sum([p['stock']*p['pc'] for p in prods])
    @app.route('/entree_stock', methods=['GET','POST'])
def entree_stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products').fetchall()
    if request.method=='POST':
        name=request.form.get('product'); qty=float(request.form.get('qty',0)); reason=request.form.get('reason','Livraison')
        p=db.execute('SELECT * FROM products WHERE name=?',[name]).fetchone()
        before=p['stock']; after=before+qty
        db.execute('UPDATE products SET stock=? WHERE name=?',[after, name])
        db.execute('INSERT INTO movements (product, type, qty, before, after, reason, date) VALUES (?,?,?,?,?,?,?)',[name,'ENTREE',qty,before,after,reason,datetime.now().strftime('%Y-%m-%d %H:%M')])
        db.commit(); db.close(); return redirect('/stock')
    opts="".join([f"<option>{p['name']}</option>" for p in prods]); db.close()
    return render_page(f"<h2>Entree Stock</h2><a href='/' class='btn'>Dashboard</a><div class='card'><form method='POST'><select name='product'>{opts}</select><input name='qty' type='number' step='0.5' required placeholder='Qte'><select name='reason'><option>Livraison</option><option>Retour</option></select><button class='btn btn-green'>Valider</button></form></div>", session['name'])

@app.route('/products', methods=['GET','POST'])
def products():
    if 'user' not in session: return redirect('/login')
    db=get_db()
    if request.method=='POST':
        name=request.form.get('name','').strip().upper(); pu=int(request.form.get('pu') or 0); pc=int(request.form.get('pc') or 0); pc10=int(request.form.get('pc10') or pc); cost=int(request.form.get('cost') or 0); nb=int(request.form.get('nb') or 24); stock=float(request.form.get('stock') or 0)
        try: db.execute('INSERT INTO products (name, pu, pc, pc10, cost_pc, nb, stock) VALUES (?,?,?,?,?,?,?)',[name, pu, pc, pc10, cost, nb, stock])
        except: db.execute('UPDATE products SET pu=?, pc=?, pc10=?, cost_pc=?, nb=?, stock=? WHERE name=?',[pu, pc, pc10, cost, nb, stock, name])
        db.commit(); db.close(); return
    return render_template_string(f"<html><head><meta charset='utf-8'></head><body><h2>BERLI STOCK {date} - {total}F</h2><table border=1 width=100%><tr><th>Produit</th><th>Stock</th><th>PU</th><th>PC</th><th>PC10</th><th>Valeur</th></tr>{rows}</table><button onclick='window.print()'>IMPRIMER</button></body></html>")
