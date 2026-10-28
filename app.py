import os, json
from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'berli-2026-supabase'
DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_db():
    if DATABASE_URL.startswith('postgres'):
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        import sqlite3
        path = '/data/berli.db' if os.path.exists('/data') else 'berli.db'
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

def query_db(sql, args=(), fetch=False, fetchone=False):
    conn = get_db()
    is_pg = DATABASE_URL.startswith('postgres')
    if is_pg:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql.replace('?', '%s'), args)
    else:
        cur = conn.cursor()
        cur.execute(sql, args)
    result = None
    if fetch: result = cur.fetchall()
    if fetchone: result = cur.fetchone()
    if not fetch and not fetchone:
        conn.commit()
    conn.close()
    return result

def init_db():
    conn = get_db()
    is_pg = DATABASE_URL.startswith('postgres')
    cur = conn.cursor()
    if is_pg:
        cur.execute("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock FLOAT DEFAULT 0)")
        cur.execute("CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, product TEXT, qty FLOAT, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT, client TEXT DEFAULT '', group_id TEXT DEFAULT '')")
    else:
        cur.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock REAL DEFAULT 0)")
        cur.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT, client TEXT DEFAULT '', group_id TEXT DEFAULT '')")
    defaults = [('VODY',500,12000,11000,9000,24,10),('DECA SOFT',600,14400,13000,10000,24,8),('FOCUS',500,12000,11000,9000,24,12)]
    for d in defaults:
        try:
            if is_pg:
                cur.execute("INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (name) DO NOTHING", d)
            else:
                cur.execute("INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (?,?,?,?,?,?,?)", d)
        except: pass
    conn.commit()
    conn.close()

init_db()
USERS = {'patron':{'pass':'berli2024','name':'Patron Ulrich'},'gerant':{'pass':'gerant2024','name':'Gerant'},'caissier':{'pass':'caisse2024','name':'Caissier'}}
BASE = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><style>body{font-family:Arial;background:#f1f5f9;margin:0}.header{background:#0f172a;color:white;padding:15px;display:flex;justify-content:space-between}.card{background:white;padding:15px;margin:10px;border-radius:12px;box-shadow:0 2px 6px #ccc}.btn{background:#0f172a;color:white;padding:10px 15px;border:none;border-radius:8px;cursor:pointer;text-decoration:none;display:inline-block;margin:3px}.btn-green{background:#16a34a}.btn-blue{background:#2563eb}input,select{padding:10px;border-radius:8px;border:1px solid #ccc;width:95%;margin:5px 0}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #eee}</style></head><body><div class='header'><b>BERLI SOFT - {{USER}}</b><a href='/logout' style='color:white'>Logout</a></div><div style='padding:10px'>{{CONTENT}}</div></body></html>"
def render_page(content, user=""):
    return render_template_string(BASE.replace("{{USER}}", user).replace("{{CONTENT}}", content))

@app.route('/login', methods=['GET','POST'])
def login():
    err=""
    if request.method=='POST':
        u=request.form.get('username','').lower().strip()
        p=request.form.get('password','').strip()
        if u in USERS and USERS[u]['pass']==p:
            session['user']=u; session['name']=USERS[u]['name']
            return redirect('/')
        err="Identifiants incorrects"
    return render_page(f"<div class='card' style='max-width:400px;margin:40px auto'><h2>BERLI Login</h2><form method='POST'><input name='username' placeholder='patron / gerant / caissier' required><input name='password' type='password' placeholder='Mot de passe' required><button class='btn' style='width:100%'>Connexion</button></form><p style='color:red'>{err}</p></div>", "LOGIN")

@app.route('/logout')
def logout():
    session.clear(); return redirect('/login')
    @app.route('/')
def dash():
    if 'user' not in session: return redirect('/login')
    is_pg = DATABASE_URL.startswith('postgres')
    if is_pg:
        s = query_db("SELECT COALESCE(SUM(total),0) as s FROM sales WHERE date LIKE %s", [f"{datetime.now().strftime('%Y-%m-%d')}%"], fetchone=True)
        prods = query_db("SELECT * FROM products ORDER BY name", fetch=True)
        total = sum([(p['stock'] or 0)*(p['pc'] or 0) for p in prods]) if prods else 0
        sales_day = s['s'] if s else 0
    else:
        import sqlite3
        conn = get_db(); cur=conn.cursor()
        today=datetime.now().strftime('%Y-%m-%d')
        st=cur.execute('SELECT COALESCE(SUM(total),0) s FROM sales WHERE date LIKE ?', [f'{today}%']).fetchone()
        prods=cur.execute('SELECT * FROM products').fetchall()
        total=sum([(p['stock'] or 0)*p['pc'] for p in prods]); sales_day=st[0]
        conn.close()
    return render_page(f"<h2>Bonjour {session['name']}</h2><div class='card'><b>Ventes Jour:</b> {sales_day} F<br><b>Valeur Stock:</b> {total} F</div><div class='card'><a href='/sales' class='btn btn-green' style='width:95%'>+ VENTE MULTI (CARTON)</a><br><a href='/stock' class='btn'>STOCK</a><a href='/entree_stock' class='btn btn-blue'>ENTREE STOCK</a><a href='/products' class='btn btn-green'>AJOUTER ARTICLE</a><a href='/print_stock' class='btn'>IMPRIMER STOCK</a></div>", session['name'])

@app.route('/stock')
def stock():
    if 'user' not in session: return redirect('/login')
    prods = query_db("SELECT * FROM products ORDER BY name", fetch=True)
    rows="".join([f"<tr><td>{p['name'] if isinstance(p,dict) else p['name']}</td><td>{p['stock']}</td><td>{p['pu']}F</td><td>{p['pc']}F</td></tr>" for p in prods]) if prods else "<tr><td>Aucun</td></tr>"
    return render_page(f"<h2>Stock</h2><a href='/' class='btn'>Dashboard</a><a href='/print_stock' class='btn'>Imprimer</a><div class='card'><table><tr><th>Produit</th><th>Stock</th><th>PU</th><th>PC</th></tr>{rows}</table></div>", session['name'])

@app.route('/entree_stock', methods=['GET','POST'])
def entree_stock():
    if 'user' not in session: return redirect('/login')
    prods = query_db("SELECT * FROM products ORDER BY name", fetch=True)
    if request.method=='POST':
        name=request.form.get('product'); qty=float(request.form.get('qty',0) or 0)
        conn=get_db(); cur=conn.cursor()
        if DATABASE_URL.startswith('postgres'):
            cur.execute("SELECT * FROM products WHERE name=%s", (name,)); pr=cur.fetchone()
            before=pr['stock'] or 0; after=before+qty
            cur.execute("UPDATE products SET stock=%s WHERE name=%s", (after, name))
        else:
            pr=cur.execute('SELECT * FROM products WHERE name=?',[name]).fetchone()
            before=pr['stock']; after=before+qty
            cur.execute('UPDATE products SET stock=? WHERE name=?',[after, name])
        conn.commit(); conn.close()
        return redirect('/stock')
    opts="".join([f"<option>{p['name'] if isinstance(p,dict) else p['name']}</option>" for p in prods]) if prods else ""
    return render_page(f"<h2>Entree Stock</h2><a href='/' class='btn'>Dashboard</a><div class='card'><form method='POST'><select name='product'>{opts}</select><input name='qty' type='number' step='0.5' required placeholder='Quantite'><button class='btn btn-green'>Valider Entree</button></form></div>", session['name'])

@app.route('/products', methods=['GET','POST'])
def products():
    if 'user' not in session: return redirect('/login')
    if request.method=='POST':
        name=request.form.get('name','').strip().upper()
        pu=int(request.form.get('pu') or 0); pc=int(request.form.get('pc') or 0)
        pc10=int(request.form.get('pc10') or pc); cost=int(request.form.get('cost') or 0)
        nb=int(request.form.get('nb') or 24); stock=float(request.form.get('stock') or 0)
        conn=get_db(); cur=conn.cursor()
        try:
            if DATABASE_URL.startswith('postgres'):
                cur.execute("INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (name) DO UPDATE SET pu=EXCLUDED.pu, pc=EXCLUDED.pc", (name,pu,pc,pc10,cost,nb,stock))
            else:
                cur.execute('INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (?,?,?,?,?,?,?)',[name,pu,pc,pc10,cost,nb,stock])
        except:
            if DATABASE_URL.startswith('postgres'):
                cur.execute("UPDATE products SET pu=%s,pc=%s,pc10=%s,cost_pc=%s,nb=%s,stock=%s WHERE name=%s", (pu,pc,pc10,cost,nb,stock,name))
            else:
                cur.execute('UPDATE products SET pu=?,pc=?,pc10=?,cost_pc=?,nb=?,stock=? WHERE name=?',[pu,pc,pc10,cost,nb,stock,name])
        conn.commit(); conn.close()
        return redirect('/products')
    prods=query_db("SELECT * FROM products ORDER BY name", fetch=True)
    rows="".join([f"<tr><td>{p['name'] if isinstance(p,dict) else p[0]}</td><td>{p['stock']}</td></tr>" for p in prods]) if prods else ""
    return render_page(f"<h2>Ajouter Article</h2><a href='/' class='btn'>Dashboard</a><div class='card'><form method='POST'><input name='name' placeholder='NOM (ex: CHAP)' required><input name='pu' type='number' placeholder='PU Bouteille'><input name='pc' type='number' placeholder='PC Casier'><input name='pc10' type='number' placeholder='PC 10+ (option)'><input name='cost' type='number' placeholder='Cout'><input name='nb' type='number' value='24'><input name='stock' type='number' step='0.5' value='0'><button class='btn btn-green'>Ajouter</button></form></div><div class='card'><table>{rows}</table></div>", session['name'])

@app.route('/sales', methods=['GET','POST'])
def sales():
    if 'user' not in session: return redirect('/login')
    prods=query_db("SELECT * FROM products ORDER BY name", fetch=True)
    if request.method=='POST':
        cart_json=request.form.get('cart_json','[]')
        cart=json.loads(cart_json); client=request.form.get('client','')
        group_id=datetime.now().strftime('%Y%m%d%H%M%S%f')
        conn=get_db(); cur=conn.cursor(); sale_ids=[]
        for item in cart:
            product=item['product']; qty=float(item['qty']); type_v=item['type_v']
            if DATABASE_URL.startswith('postgres'):
                cur.execute("SELECT * FROM products WHERE name=%s", (product,)); pr=cur.fetchone()
            else:
                pr=cur.execute('SELECT * FROM products WHERE name=?',[product]).fetchone()
            if not pr: continue
            pu_val=pr['pu'] if isinstance(pr,dict) else pr['pu']; pc_val=pr['pc'] if isinstance(pr,dict) else pr['pc']; pc10_val=pr['pc10'] if isinstance(pr,dict) else pr['pc10']; nb_val=pr['nb'] if isinstance(pr,dict) else pr['nb']
            if type_v=='detail': total=int(qty*pu_val); pu_final=pu_val; ded=qty/(nb_val or 24)
            elif type_v=='casier': total=int(qty*pc_val); pu_final=pc_val; ded=qty
            else: total=int(qty*pc10_val); pu_final=pc10_val; ded=qty
            if DATABASE_URL.startswith('postgres'):
                cur.execute("UPDATE products SET stock=stock-%s WHERE name=%s", (ded, product))
                cur.execute("INSERT INTO sales (product,qty,type,pu_final,total,seller,date,client,group_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id", (product,qty,type_v,pu_final,total,session['name'],datetime.now().strftime('%Y-%m-%d %H:%M'),client,group_id))
                sid=cur.fetchone()['id']; sale_ids.append(sid)
            else:
                cur.execute('UPDATE products SET stock=stock-? WHERE name=?',[ded, product])
                cur.execute('INSERT INTO sales (product,qty,type,pu_final,total,seller,date,client,group_id) VALUES (?,?,?,?,?,?,?, ?,?)',[product,qty,type_v,pu_final,total,session['name'],datetime.now().strftime('%Y-%m-%d %H:%M'),client,group_id])
                sale_ids.append(cur.lastrowid)
        conn.commit(); conn.close()
        if len(sale_ids)==1: return redirect(f'/ticket/{sale_ids[0]}')
        else: return redirect(f"/ticket_multi/{','.join(map(str,sale_ids))}")
    opts="".join([f"<option value='{p['name'] if isinstance(p,dict) else p['name']}' data-pu='{p['pu'] if isinstance(p,dict) else p['pu']}' data-pc='{p['pc'] if isinstance(p,dict) else p['pc']}' data-pc10='{p['pc10'] if isinstance(p,dict) else p['pc10']}'>{p['name'] if isinstance(p,dict) else p['name']} (Stock: {p['stock'] if isinstance(p,dict) else p['stock']})</option>" for p in prods]) if prods else ""
    return render_page(f"<h2>Vente Multi Carton</h2><a href='/' class='btn'>Dashboard</a><div class='card'><div style='display:flex;gap:5px'><select id='prod'>{opts}</select><input id='qty' type='number' value='1' step='0.5' style='width:60px'><select id='type_v'><option value='detail'>Bouteille</option><option value='casier'>Casier</option><option value='casier10'>10+</option></select></div><button onclick='addToCart()' class='btn btn-green' style='width:100%;margin-top:10px'>+ AJOUTER AU PANIER</button><table id='cartTable' style='margin-top:10px'><tr><th>Prod</th><th>Qte</th><th>Type</th><th>Total</th><th>X</th></tr></table><h3>TOTAL: <span id='totalGlobal'>0</span> F</h3><form method='POST' onsubmit='return prepareSubmit()'><input type='hidden' name='cart_json' id='cart_json'><input name='client' placeholder='Client (optionnel)'><button class='btn btn-blue' style='width:100%;padding:15px'>VALIDER & IMPRIMER TICKET GROUPE</button></form></div><script>let cart=[];function addToCart(){{let sel=document.getElementById('prod');let product=sel.value;let qty=parseFloat(document.getElementById('qty').value)||1;let type_v=document.getElementById('type_v').value;let opt=sel.options[sel.selectedIndex];let pu=parseInt(opt.dataset.pu);let pc=parseInt(opt.dataset.pc);let pc10=parseInt(opt.dataset.pc10);let unit=pu;if(type_v=='casier')unit=pc;if(type_v=='casier10')unit=pc10;let total=unit*qty;cart.push({{product,qty,type_v,unit,total}});renderCart();}}function removeItem(i){{cart.splice(i,1);renderCart();}}function renderCart(){{let html='<tr><th>Prod</th><th>Qte</th><th>Type</th><th>Total</th><th>X</th></tr>';let sum=0;cart.forEach((c,i)=>{{html+=`<tr><td>${{c.product}}</td><td>${{c.qty}}</td><td>${{c.type_v}}</td><td>${{c.total}}F</td><td><button type=button onclick=removeItem(${{i}})>X</button></td></tr>`;sum+=c.total;}});document.getElementById('cartTable').innerHTML=html;document.getElementById('totalGlobal').innerText=sum;}}function prepareSubmit(){{if(cart.length==0){{alert('Panier vide');return false;}}document.getElementById('cart_json').value=JSON.stringify(cart);return true;}}</script>", session['name'])

@app.route('/ticket/<int:sid>')
def ticket(sid):
    if 'user' not in session: return redirect('/login')
    sale=query_db("SELECT * FROM sales WHERE id=?", [sid], fetchone=True) if not DATABASE_URL.startswith('postgres') else query_db("SELECT * FROM sales WHERE id=%s", [sid], fetchone=True)
    return f"<html><body style='font-family:monospace;max-width:350px;margin:auto;border:1px dashed black;padding:15px'><h2 style='text-align:center'>BERLI DISTRIBUTION</h2><hr>Date: {sale['date']}<br>Vendeur: {sale['seller']}<hr>Produit: {sale['product']}<br>Qte: {sale['qty']} ({sale['type']})<br>PU: {sale['pu_final']}F<br><b>TOTAL: {sale['total']}F</b><hr><button onclick='window.print()' style='width:100%;padding:12px;background:black;color:white'>IMPRIMER</button><br><a href='/'>Retour</a></body></html>"

@app.route('/ticket_multi/<ids>')
def ticket_multi(ids):
    if 'user' not in session: return redirect('/login')
    id_list=[int(x) for x in ids.split(',') if x.isdigit()]
    conn=get_db(); cur=conn.cursor()
    if DATABASE_URL.startswith('postgres'):
        cur.execute(f"SELECT * FROM sales WHERE id IN ({','.join(['%s']*len(id_list))})", id_list); sales=cur.fetchall()
    else:
        sales=cur.execute(f"SELECT * FROM sales WHERE id IN ({','.join(['?']*len(id_list))})", id_list).fetchall()
    conn.close()
    total=sum([s['total'] for s in sales]); rows="".join([f"<tr><td>{s['product']}</td><td>{s['qty']}</td><td>{s['pu_final']}F</td><td>{s['total']}F</td></tr>" for s in sales])
    return f"<html><body style='font-family:monospace;max-width:400px;margin:auto;border:1px dashed black;padding:15px'><h2 style='text-align:center'>TICKET GROUPE BERLI</h2><table width=100%><tr><th>Prod</th><th>Qte</th><th>PU</th><th>Total</th></tr>{rows}</table><hr><b>TOTAL GENERAL: {total}F</b><br><br><button onclick='window.print()' style='width:100%;padding:12px;background:black;color:white'>IMPRIMER</button><br><a href='/'>Retour Dashboard</a></body></html>"

@app.route('/print_stock')
def print_stock():
    if 'user' not in session: return redirect('/login')
    prods=query_db("SELECT * FROM products ORDER BY name", fetch=True)
    rows="".join([f"<tr><td>{p['name'] if isinstance(p,dict) else p[0]}</td><td>{p['stock']}</td></tr>" for p in prods]) if prods else ""
    return f"<html><body><h2>STOCK BERLI - {datetime.now().strftime('%Y-%m-%d')}</h2><table border=1 width=100%><tr><th>Nom</th><th>Stock</th></tr>{rows}</table><button onclick='window.print()'>IMPRIMER</button></body></html>"

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
