from flask import Flask, request, redirect, session, render_template_string, Response
import sqlite3, os, csv, io, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'berli-2026-final-complet'
DB = '/data/berli.db' if os.path.exists('/data') else 'berli.db'

USERS = {
    'patron': {'pass': 'berli2024', 'name': 'Patron Ulrich'},
    'gerant': {'pass': 'gerant2024', 'name': 'Gerant'},
    'caissier': {'pass': 'caisse2024', 'name': 'Caissier'}
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock REAL DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT, client TEXT DEFAULT "", group_id TEXT DEFAULT "")')
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
        u=request.form.get('username','').lower().strip(); p=request.form.get('password','').strip()
        if u in USERS and USERS[u]['pass']==p:
            session['user']=u; session['name']=USERS[u]['name']; return redirect('/')
        err="Identifiants incorrects"
    return render(f"<div class='card' style='max-width:400px; margin:40px auto'><h2>BERLI Login</h2><form method='POST'><input name='username' placeholder='patron / gerant / caissier' required><input name='password' type='password' placeholder='Mot de passe' required><button class='btn' style='width:100%'>Connexion</button></form><p style='color:red'>{err}</p></div>", "LOGIN")

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
    <a href="/sales" class="btn btn-green">💵 VENTE MULTIPLE</a>
    <a href="/stock" class="btn">📦 STOCK</a>
    <a href="/entree_stock" class="btn btn-blue">📥 ENTRÉE STOCK</a>
    <a href="/inventaire" class="btn btn-purple">⚖️ INVENTAIRE</a>
    <a href="/movements" class="btn">📈 MOUVEMENTS</a>
    <a href="/debts" class="btn btn-red">📒 DETTES</a>
    <a href="/products" class="btn btn-green">➕ AJOUTER ARTICLE</a>
    <a href="/print_stock" class="btn">🖨️ IMPRIMER STOCK</a>
    </div>
    """, session['name'])

@app.route('/stock')
def stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    rows="".join([f"<tr><td><b>{p['name']}</b></td><td>{p['stock']}</td><td>{p['pu']}F</td><td>{p['pc']}F</td><td>{p['pc10']}F</td><td>{p['stock']*p['pc']}F</td></tr>" for p in prods])
    return render(f"""
    <h2>Stock Existant BERLI</h2>
    <div class="no-print"><a href="/" class="btn">← Dashboard</a><a href="/print_stock" class="btn">🖨️ Imprimer Stock</a></div>
    <div class="card"><table><tr><th>Produit</th><th>Stock</th><th>PU</th><th>PC</th><th>PC10</th><th>Valeur</th></tr>{rows}</table></div>
    """, session['name'])
    @app.route('/print_stock')
def print_stock():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    date=datetime.now().strftime('%Y-%m-%d %H:%M')
    rows="".join([f"<tr><td>{p['name']}</td><td>{p['stock']}</td><td>{p['pu']}</td><td>{p['pc']}</td><td>{p['pc10']}</td><td>{p['cost_pc']}</td><td>{p['stock']*p['pc']}</td></tr>" for p in prods])
    total=sum([p['stock']*p['pc'] for p in prods])
    return render_template_string(f"""
    <html><head><meta charset="utf-8"><title>Stock</title>
    <style>body{{font-family:Arial; max-width:900px; margin:20px auto; padding:20px}} table{{width:100%; border-collapse:collapse}} th,td{{border:1px solid black; padding:6px; font-size:12px}} th{{background:#eee}}</style>
    </head><body>
    <h2 style="text-align:center">BERLI DISTRIBUTION - STOCK</h2>
    <p>Date: {date} | {total} F</p>
    <table><tr><th>Produit</th><th>Casiers</th><th>PU</th><th>PC</th><th>PC10</th><th>Cout</th><th>Valeur</th></tr>{rows}
    <tr><td colspan="6"><b>TOTAL</b></td><td><b>{total} F</b></td></tr></table>
    <button onclick="window.print()" style="padding:15px; width:100%; background:black; color:white">🖨️ IMPRIMER</button>
    <a href="/stock">← Retour</a>
    </body></html>
    """)

@app.route('/entree_stock', methods=['GET','POST'])
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
    <h2>📥 Entrée Stock - CORRIGÉ</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card"><form method="POST"><label>Produit</label><select name="product">{opts}</select>
    <label>Qté Casiers</label><input name="qty" type="number" step="0.5" required>
    <label>Raison</label><select name="reason"><option>Livraison fournisseur</option><option>Retour client</option><option>Ajustement</option></select>
    <button class="btn btn-green">Valider Entrée Stock</button></form></div>
    """, session['name'])

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
                        db.execute('INSERT INTO movements (product, type, qty, before, after, reason, date) VALUES (?,?,?,?,?,?,?)',[p['name'],'INVENTAIRE',diff,before,counted,f"Inventaire {diff:+}",datetime.now().strftime('%Y-%m-%d %H:%M')])
        db.commit(); db.close(); return redirect('/print_stock')
    prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    rows="".join([f"<tr><td><b>{p['name']}</b><br><small>Theo: {p['stock']}</small></td><td><input name='count_{p['id']}' type='number' step='0.5' value='{p['stock']}' style='width:90px' required></td></tr>" for p in prods])
    return render(f"""
    <h2>⚖️ Inventaire</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card"><form method="POST"><table><tr><th>Produit</th><th>Compté</th></tr>{rows}</table>
    <button class="btn btn-purple" style="width:100%; padding:15px">✅ Valider Inventaire</button></form></div>
    """, session['name'])

@app.route('/movements')
def movements():
    if 'user' not in session: return redirect('/login')
    db=get_db(); moves=db.execute('SELECT * FROM movements ORDER BY id DESC LIMIT 100').fetchall(); db.close()
    rows="".join([f"<tr><td>{m['date']}</td><td>{m['product']}</td><td>{m['type']}</td><td>{m['qty']:+}</td><td>{m['before']}→{m['after']}</td><td>{m['reason']}</td></tr>" for m in moves])
    return render(f"""<h2>📈 Mouvements</h2><a href="/" class="btn">← Dashboard</a><div class="card"><table><tr><th>Date</th><th>Produit</th><th>Type</th><th>Qté</th><th>Avant→Après</th><th>Raison</th></tr>{rows if rows else '<tr><td colspan=6>Aucun</td></tr>'}</table></div>""", session['name'])

@app.route('/sales', methods=['GET','POST'])
def sales():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall()
    if request.method=='POST':
        cart_json = request.form.get('cart_json','[]')
        cart = json.loads(cart_json)
        client = request.form.get('client','').strip()
        group_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        total_group = 0
        sale_ids = []
        for item in cart:
            product = item['product']; qty = float(item['qty']); type_v = item['type_v']
            pr=db.execute('SELECT * FROM products WHERE name=?',[product]).fetchone()
            if not pr: continue
            if type_v=='detail':
                total=int(qty*pr['pu']); pu_final=pr['pu']; ded=qty/(pr['nb'] or 24)
            elif type_v=='casier':
                total=int(qty*pr['pc']); pu_final=pr['pc']; ded=qty
            else:
                total=int(qty*pr['pc10']); pu_final=pr['pc10']; ded=qty
            db.execute('UPDATE products SET stock=stock-? WHERE name=?',[ded, product])
            cur=db.cursor(); cur.execute('INSERT INTO sales (product, qty, type, pu_final, total, benefit, seller, date, client, group_id) VALUES (?,?,?,?,?,?,?,?,?,?)',[product, qty, type_v, pu_final, total, pr['pc']-pr['cost_pc'], session['name'], datetime.now().strftime('%Y-%m-%d %H:%M'), client, group_id])
            sale_ids.append(cur.lastrowid)
            total_group += total
        db.commit(); db.close()
        if len(sale_ids)==1:
            return redirect(f'/ticket/{sale_ids[0]}')
        else:
            return redirect(f'/ticket_multi/{",".join(map(str,sale_ids))}')
    opts="".join([f"<option value='{p['name']}' data-pu='{p['pu']}' data-pc='{p['pc']}' data-pc10='{p['pc10']}'>{p['name']} (Stock: {p['stock']})</option>" for p in prods])
    sales_list=db.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 15').fetchall(); db.close()
    return render(f"""
    <h2>💵 Vente Multi Articles - OK</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card" style="border:2px solid #16a34a">
    <div style="display:flex; gap:8px; flex-wrap:wrap">
        <div style="flex:2"><label>Produit</label><select id="prod">{opts}</select></div>
        <div style="flex:1"><label>Qté</label><input id="qty" type="number" step="0.5" value="1"></div>
        <div style="flex:1"><label>Type</label><select id="type_v"><option value="detail">Bouteille</option><option value="casier">Casier</option><option value="casier10">10 Casiers+</option></select></div>
    </div>
    <button onclick="addToCart()" class="btn btn-green" style="width:100%; margin-top:10px">+ AJOUTER AU PANIER</button>
    <table id="cartTable" style="margin-top:10px"><tr><th>Produit</th><th>Qté</th><th>Type</th><th>Total</th><th>X</th></tr></table>
    <h3 style="text-align:right">TOTAL: <span id="totalGlobal">0</span> F</h3>
    <form method="POST" onsubmit="return prepareSubmit()">
        <input type="hidden" name="cart_json" id="cart_json">
        <label>Client</label><input name="client" placeholder="Nom client">
        <button class="btn btn-blue" style="width:100%; padding:15px">✅ VALIDER & IMPRIMER REÇU GROUPÉ</button>
    </form>
    </div>
<script>
let cart=[];
function addToCart(){{
    let sel=document.getElementById('prod'); let product=sel.value; let qty=parseFloat(document.getElementById('qty').value)||1; let type_v=document.getElementById('type_v').value;
    let opt=sel.options[sel.selectedIndex]; let pu=parseInt(opt.dataset.pu); let pc=parseInt(opt.dataset.pc); let pc10=parseInt(opt.dataset.pc10);
    let unit=pu; if(type_v=='casier') unit=pc; if(type_v=='casier10') unit=pc10; let total=unit*qty;
    cart.push({{product,qty,type_v,unit,total}}); renderCart();
}}
function removeItem(i){{cart.splice(i,1); renderCart();}}
function renderCart(){{
    let html="<tr><th>Produit</th><th>Qté</th><th>Type</th><th>Total</th><th>X</th></tr>"; let sum=0;
    cart.forEach((c,i)=>{{html+=`<tr><td>${{c.product}}</td><td>${{c.qty}}</td><td>${{c.type_v}}</td><td>${{c.total}}F</td><td><button type="button" onclick="removeItem(${{i}})" class="btn btn-red">X</button></td></tr>`; sum+=c.total;}});
    document.getElementById('cartTable').innerHTML=html; document.getElementById('totalGlobal').innerText=sum;
}}
function prepareSubmit(){{if(cart.length==0){{alert('Panier vide'); return false;}} document.getElementById('cart_json').value=JSON.stringify(cart); return true;}}
</script>
    """, session['name'])

@app.route('/ticket/<int:sid>')
def ticket(sid):
    if 'user' not in session: return redirect('/login')
    db=get_db(); s=db.execute('SELECT * FROM sales WHERE id=?',[sid]).fetchone(); db.close()
    if not s: return "Ticket introuvable"
    return render_template_string(f"""
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{font-family:monospace; max-width:350px; margin:10px auto; background:white; padding:15px; border:1px dashed black}}
    .btn{{padding:12px; width:100%; background:black; color:white; border:none; border-radius:6px; margin-top:8px}} @media print{{.no-print{{display:none}}}}</style></head><body>
    <h2 style="text-align:center">BERLI DISTRIBUTION</h2><div style="text-align:center">Hedzranawoé - Lomé</div><hr>
    <div>Reçu N°: {s['id']:05d}<br>Date: {s['date']}<br>Vendeur: {s['seller']}<br>Client: {s['client'] or 'Comptant'}</div><hr>
    <div>Produit: {s['product']}<br>Qté: {s['qty']} ({s['type']})<br>PU: {s['pu_final']}F<br><b>TOTAL: {s['total']}F</b></div><hr>
    <button onclick="window.print()" class="btn no-print">🖨️ IMPRIMER</button>
    <a href="/sales" class="no-print">← Retour</a></body></html>
    """)

@app.route('/ticket_multi/<ids>')
def ticket_multi(ids):
    if 'user' not in session: return redirect('/login')
    id_list=[int(x) for x in ids.split(',') if x.isdigit()]
    db=get_db(); placeholders=','.join('?'*len(id_list))
    sales=db.execute(f'SELECT * FROM sales WHERE id IN ({placeholders})', id_list).fetchall(); db.close()
    total=sum([s['total'] for s in sales]); date=sales[0]['date']; seller=sales[0]['seller']; client=sales[0]['client'] or 'Comptant'
    rows="".join([f"<tr><td>{s['product']}</td><td>{s['qty']}</td><td>{s['pu_final']}F</td><td>{s['total']}F</td></tr>" for s in sales])
    return render_template_string(f"""<html><head><meta charset="utf-8"></head><body style="font-family:monospace; max-width:400px; margin:auto; border:1px dashed black; padding:15px">
    <h2 style="text-align:center">REÇU GROUPÉ</h2><hr><div>Date: {date}<br>Vendeur: {seller}<br>Client: {client}</div><hr>
    <table style="width:100%"><tr><th>Prod</th><th>Qté</th><th>PU</th><th>Total</th></tr>{rows}
    <tr><td colspan="3" style="text-align:right; border-top:2px dashed black"><b>TOTAL</b></td><td style="border-top:2px dashed black"><b>{total}F</b></td></tr></table><hr>
    <div style="text-align:center"><b>TOTAL: {total} F CFA</b></div>
    <button onclick="window.print()" style="width:100%; padding:12px; background:black; color:white">🖨️ IMPRIMER GROUPÉ</button>
    <a href="/sales">← Nouvelle Vente</a></body></html>""")

@app.route('/products', methods=['GET','POST'])
def manage_products():
    if 'user' not in session: return redirect('/login')
    db=get_db()
    if request.method=='POST':
        name=request.form.get('name','').strip().upper(); pu=int(request.form.get('pu') or 0); pc=int(request.form.get('pc') or 0)
        pc10=int(request.form.get('pc10') or pc); cost=int(request.form.get('cost') or 0); nb=int(request.form.get('nb') or 24); stock=float(request.form.get('stock') or 0)
        try: db.execute('INSERT INTO products (name, pu, pc, pc10, cost_pc, nb, stock) VALUES (?,?,?,?,?,?,?)',[name, pu, pc, pc10, cost, nb, stock])
        except: db.execute('UPDATE products SET pu=?, pc=?, pc10=?, cost_pc=?, nb=?, stock=? WHERE name=?',[pu, pc, pc10, cost, nb, stock, name])
        db.commit(); db.close(); return redirect('/products')
    prods=db.execute('SELECT * FROM products ORDER BY name').fetchall(); db.close()
    rows="".join([f"<tr><td>{p['name']}</td><td>{p['pu']}F</td><td>{p['pc']}F</td><td>{p['stock']}</td></tr>" for p in prods])
    return render(f"""
    <h2>📦 Gestion Articles</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card"><form method="POST"><input name="name" placeholder="NOM MAJUSCULE" required>
    <div style="display:flex; gap:5px"><input name="pu" type="number" placeholder="PU"><input name="pc" type="number" placeholder="PC"><input name="pc10" type="number" placeholder="PC10"></div>
    <div style="display:flex; gap:5px"><input name="cost" type="number" placeholder="Cout"><input name="nb" type="number" value="24"><input name="stock" type="number" step="0.5" value="0"></div>
    <button class="btn btn-green" style="width:100%">Ajouter Article</button></form></div>
    <div class="card"><table><tr><th>Nom</th><th>PU</th><th>PC</th><th>Stock</th></tr>{rows}</table></div>
    """, session['name'])

@app.route('/debts')
def debts():
    if 'user' not in session: return redirect('/login')
    db=get_db(); ds=db.execute('SELECT * FROM debts ORDER BY id DESC').fetchall(); db.close()
    rows="".join([f"<tr><td>{d['client']}</td><td>{d['total']}F</td><td>{d['remaining']}F</td></tr>" for d in ds])
    return render(f"<h2>Dettes</h2><a href='/' class='btn'>← Dashboard</a><div class='card'><table><tr><th>Client</th><th>Total</th><th>Reste</th></tr>{rows}</table></div>", session['name'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
