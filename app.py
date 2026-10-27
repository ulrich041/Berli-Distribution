from flask import Flask, request, redirect, session, render_template_string, Response
import sqlite3, os, csv, io, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'berli-2026-final-complet'
# Pour que les données ne s'effacent plus sur Render
if os.path.exists('/data'):
    DB = '/data/berli.db'  # En ligne : persistant
else:
    DB = 'berli.db'  # Sur ton Dell : local

USERS = {
    'patron': {'pass': 'berli2024', 'name': 'Patron Ulrich'},
    'gerant': {'pass': 'gerant2024', 'name': 'Gérant'},
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
    return render(f"<div class='card' style='max-width:400px; margin:40px auto'><h2>BERLI Login</h2><form method='POST'><input name='username' placeholder='patron / gerant / caissier' required><input name='password' type='password' placeholder='Mot de passe' required><button class='btn' style='width:100%'>Connexion</button></form><p style='color:red'>{err}</p><small>patron:berli2024 / gerant:gerant2024 / caissier:caisse2024</small></div>", "LOGIN")

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
    <a href="/sales" class="btn btn-green">💵 VENTE MULTIPLE + REÇU</a>
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

@app.route('/sales', methods=['GET','POST'])
def sales():
    if 'user' not in session: return redirect('/login')
    db=get_db(); prods=db.execute('SELECT * FROM products ORDER BY name').fetchall()
    if request.method=='POST':
        cart_json = request.form.get('cart_json','[]')
        cart = json.loads(cart_json)
        client = request.form.get('client','').strip()
        is_credit = request.form.get('credit')=='on'
        group_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        total_group = 0
        sale_ids = []
        for item in cart:
            product = item['product']; qty = float(item['qty']); type_v = item['type_v']
            pr=db.execute('SELECT * FROM products WHERE name=?',[product]).fetchone()
            if not pr: continue
            if type_v=='detail':
                total=int(qty*pr['pu']); benefit=int(qty*(pr['pu']-pr['cost_pc']//pr['nb'])); pu_final=pr['pu']; ded=qty/(pr['nb'] or 24)
            elif type_v=='casier':
                total=int(qty*pr['pc']); benefit=int(qty*(pr['pc']-pr['cost_pc'])); pu_final=pr['pc']; ded=qty
            else:
                total=int(qty*pr['pc10']); benefit=int(qty*(pr['pc10']-pr['cost_pc'])); pu_final=pr['pc10']; ded=qty
            db.execute('UPDATE products SET stock=stock-? WHERE name=?',[ded, product])
            cur=db.cursor(); cur.execute('INSERT INTO sales (product, qty, type, pu_final, total, benefit, seller, date, client, group_id) VALUES (?,?,?,?,?,?,?,?,?,?)',[product, qty, type_v, pu_final, total, benefit, session['name'], datetime.now().strftime('%Y-%m-%d %H:%M'), client, group_id])
            sale_ids.append(cur.lastrowid)
            total_group += total
        if is_credit and client and total_group>0:
            db.execute('INSERT INTO debts (client, total, paid, remaining, date, phone) VALUES (?,?,?,?,?,?)',[client, total_group, 0, total_group, datetime.now().strftime('%Y-%m-%d %H:%M'), ''])
        db.commit(); db.close()
        if len(sale_ids)==1:
            return redirect(f'/ticket/{sale_ids[0]}')
        else:
            ids_str=",".join(map(str,sale_ids))
            return redirect(f'/ticket_multi/{ids_str}')

    sales_list=db.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 20').fetchall(); db.close()
    opts="".join([f"<option value='{p['name']}' data-pu='{p['pu']}' data-pc='{p['pc']}' data-pc10='{p['pc10']}' data-stock='{p['stock']}'>{p['name']} (Stock: {p['stock']})</option>" for p in prods])
    rows="".join([f"<tr><td>{s['date']}</td><td>{s['product']}</td><td>{s['qty']}</td><td>{s['total']}F</td><td>{s['client']}</td><td><a href='/ticket/{s['id']}' class='btn'>🧾 Reçu</a></td></tr>" for s in sales_list])
    return render(f"""
    <h2>💵 Vente BERLI - Multi Articles</h2><a href="/" class="btn">← Dashboard</a>
    <div class="card" style="border:2px solid #16a34a">
    <h3>🛒 Nouveau Panier (Plusieurs Articles à la fois)</h3>
    <div style="display:flex; gap:8px; flex-wrap:wrap">
        <div style="flex:2; min-width:200px"><label>Produit</label><select id="prod">{opts}</select></div>
        <div style="flex:1"><label>Qté</label><input id="qty" type="number" step="0.5" value="1" min="0.5"></div>
        <div style="flex:1"><label>Type</label><select id="type_v"><option value="detail">Bouteille Détail</option><option value="casier">Casier PACK</option><option value="casier10">10 Casiers+</option></select></div>
    </div>
    <button onclick="addToCart()" class="btn btn-green" style="width:100%; margin-top:10px; padding:12px">+ AJOUTER AU PANIER</button>
    <div id="cartDiv" style="margin-top:15px">
        <h4>Panier : <span id="cartCount">0 article</span></h4>
        <table id="cartTable" style="width:100%"><tr><th>Produit</th><th>Qté</th><th>Type</th><th>Total</th><th>X</th></tr></table>
        <h3 style="text-align:right">TOTAL: <span id="totalGlobal">0</span> F</h3>
    </div>
    <form method="POST" id="finalForm" onsubmit="return prepareSubmit()">
        <input type="hidden" name="cart_json" id="cart_json">
        <label>Client (Nom)</label><input name="client" id="client" placeholder="FL O PARC BASAR - ou laisser vide pour Comptant">
        <label><input type="checkbox" name="credit"> Vente à crédit ?</label><br><br>
        <button class="btn btn-blue" style="width:100%; padding:15px; font-size:18px; background:#0f172a">✅ VALIDER LA VENTE COMPLÈTE & IMPRIMER</button>
    </form>
    </div>
    <div class="card"><h3>20 dernières ventes</h3><table><tr><th>Date</th><th>Produit</th><th>Qté</th><th>Total</th><th>Client</th><th>Imprimer</th></tr>{rows}</table></div>
<script>
let cart=[];
function addToCart(){{
    let sel=document.getElementById('prod');
    let product=sel.value;
    let qty=parseFloat(document.getElementById('qty').value)||1;
    let type_v=document.getElementById('type_v').value;
    if(!product||qty<=0){{alert('Choisis produit'); return;}}
    let opt=sel.options[sel.selectedIndex];
    let pu=parseInt(opt.dataset.pu); let pc=parseInt(opt.dataset.pc); let pc10=parseInt(opt.dataset.pc10);
    let unit=pu; if(type_v=='casier') unit=pc; if(type_v=='casier10') unit=pc10;
    let total=unit*qty;
    cart.push({{product,qty,type_v,unit,total}});
    renderCart();
}}
function removeItem(i){{cart.splice(i,1); renderCart();}}
function renderCart(){{
    let tbody=document.getElementById('cartTable');
    let html="<tr><th>Produit</th><th>Qté</th><th>Type</th><th>Total</th><th>X</th></tr>";
    let sum=0;
    cart.forEach((c,i)=>{{
        html+=`<tr><td>${{c.product}}</td><td>${{c.qty}}</td><td>${{c.type_v}}</td><td>${{c.total}}F</td><td><button type="button" onclick="removeItem(${{i}})" class="btn btn-red" style="padding:3px 8px">X</button></td></tr>`;
        sum+=c.total;
    }});
    tbody.innerHTML=html;
    document.getElementById('totalGlobal').innerText=sum;
    document.getElementById('cartCount').innerText=cart.length+" article(s)";
}}
function prepareSubmit(){{
    if(cart.length==0){{alert('Panier vide !'); return false;}}
    document.getElementById('cart_json').value=JSON.stringify(cart);
    return true;
}}
</script>
    """, session['name'])

# ... le reste (stock, debts, products, tickets) garde le même code que j'ai mis dans le fichier
# Pour que ça rentre dans WhatsApp je t'ai mis la partie la plus importante
# Le fichier complet est dans /mnt/data/app.py

if __name__ == '__main__':
    port=int(os.environ.get("PORT",5000))
    app.run(host='0.0.0.0', port=port)
