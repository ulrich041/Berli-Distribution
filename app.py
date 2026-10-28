import os, json
from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'berli-2026'
DATABASE_URL = os.environ.get('DATABASE_URL','')

def get_db():
    if DATABASE_URL.startswith('postgres'):
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        p = '/data/berli.db' if os.path.exists('/data') else 'berli.db'
        c = sqlite3.connect(p)
        c.row_factory = sqlite3.Row
        return c

def q(sql, args=(), f=False, one=False):
    conn = get_db()
    pg = DATABASE_URL.startswith('postgres')
    if pg:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql.replace('?','%s'), args)
    else:
        cur = conn.cursor()
        cur.execute(sql, args)
    r = None
    if f: r = cur.fetchall()
    if one: r = cur.fetchone()
    if not f and not one: conn.commit()
    conn.close()
    return r

def init():
    conn = get_db()
    pg = DATABASE_URL.startswith('postgres')
    cur = conn.cursor()
    if pg:
        cur.execute("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT UNIQUE, pu INT, pc INT, pc10 INT, cost_pc INT, nb INT, stock FLOAT DEFAULT 0)")
        cur.execute("CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, product TEXT, qty FLOAT, type TEXT, pu_final INT, total INT, seller TEXT, date TEXT)")
    else:
        cur.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INT, pc INT, pc10 INT, cost_pc INT, nb INT, stock REAL DEFAULT 0)")
        cur.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INT, total INT, seller TEXT, date TEXT)")
    for d in [('VODY',500,12000,11000,9000,24,10),('DECA',600,14400,13000,10000,24,8),('FOCUS',500,12000,11000,9000,24,12)]:
        try:
            if pg: cur.execute("INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (name) DO NOTHING", d)
            else: cur.execute("INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (?,?,?,?,?,?,?)", d)
        except: pass
    conn.commit(); conn.close()
init()
USERS={'patron':{'pass':'berli2024','name':'Patron'},'gerant':{'pass':'gerant2024','name':'Gerant'},'caissier':{'pass':'caisse2024','name':'Caissier'}}
BASE="<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>body{font-family:Arial;background:#f1f5f9;margin:0}.h{background:#0f172a;color:white;padding:15px;display:flex;justify-content:space-between}.c{background:white;padding:15px;margin:10px;border-radius:12px}.b{background:#0f172a;color:white;padding:10px 15px;border:none;border-radius:8px;text-decoration:none;margin:3px;display:inline-block}.bg{background:#16a34a}input,select{padding:10px;width:95%;margin:5px 0;border-radius:8px;border:1px solid #ccc}</style></head><body><div class='h'><b>BERLI - {{U}}</b><a href='/logout' style='color:white'>Logout</a></div><div style='padding:10px'>{{C}}</div></body></html>"
def rp(c,u=""): return render_template_string(BASE.replace("{{U}}",u).replace("{{C}}",c))
@app.route('/login', methods=['GET','POST'])
def login():
    e=""
    if request.method=='POST':
        u=request.form.get('username','').lower().strip(); p=request.form.get('password','').strip()
        if u in USERS and USERS[u]['pass']==p: session['user']=u; session['name']=USERS[u]['name']; return redirect('/')
        e="Erreur"
    return rp(f"<div class='c' style='max-width:400px;margin:40px auto'><h2>Login BERLI</h2><form method='POST'><input name='username' placeholder='patron/gerant/caissier' required><input name='password' type='password' required><button class='b' style='width:100%'>Connexion</button></form><p style='color:red'>{e}</p></div>","LOGIN")
@app.route('/logout')
def logout(): session.clear(); return redirect('/login')
@app.route('/')
def dash():
    if 'user' not in session: return redirect('/login')
    prods=q("SELECT * FROM products ORDER BY name",f=True)
    tot=sum([(p['stock'] or 0)*(p['pc'] or 0) for p in prods]) if prods else 0
    return rp(f"<h2>Bonjour {session['name']}</h2><div class='c'>Stock: {tot} F</div><div class='c'><a href='/sales' class='b bg' style='width:95%'>+ VENTE</a><br><a href='/stock' class='b'>STOCK</a><a href='/entree_stock' class='b'>ENTREE</a><a href='/products' class='b bg'>+ARTICLE</a></div>",session['name'])
@app.route('/stock')
def stock():
    if 'user' not in session: return redirect('/login')
    prods=q("SELECT * FROM products",f=True)
    rows="".join([f"<tr><td>{p['name']}</td><td>{p['stock']}</td><td>{p['pu']}</td></tr>" for p in prods]) if prods else ""
    return rp(f"<h2>Stock</h2><a href='/' class='b'>Dash</a><div class='c'><table width=100%><tr><th>Nom</th><th>Stock</th><th>PU</th></tr>{rows}</table></div>",session['name'])
@app.route('/entree_stock', methods=['GET','POST'])
def entree():
    if 'user' not in session: return redirect('/login')
    prods=q("SELECT * FROM products",f=True)
    if request.method=='POST':
        n=request.form.get('product'); qty=float(request.form.get('qty') or 0)
        conn=get_db(); cur=conn.cursor()
        if DATABASE_URL.startswith('postgres'): cur.execute("UPDATE products SET stock=stock+%s WHERE name=%s",(qty,n))
        else: cur.execute("UPDATE products SET stock=stock+? WHERE name=?",(qty,n))
        conn.commit(); conn.close(); return redirect('/stock')
    opts="".join([f"<option>{p['name']}</option>" for p in prods]) if prods else ""
    return rp(f"<h2>Entree</h2><a href='/' class='b'>Dash</a><div class='c'><form method='POST'><select name='product'>{opts}</select><input name='qty' type='number' step='0.5' required><button class='b bg'>Valider</button></form></div>",session['name'])
@app.route('/products', methods=['GET','POST'])
def prod():
    if 'user' not in session: return redirect('/login')
    if request.method=='POST':
        n=request.form.get('name','').strip().upper(); pu=int(request.form.get('pu') or 0); pc=int(request.form.get('pc') or 0); nb=int(request.form.get('nb') or 24); st=float(request.form.get('stock') or 0)
        conn=get_db(); cur=conn.cursor()
        try:
            if DATABASE_URL.startswith('postgres'): cur.execute("INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (name) DO UPDATE SET pu=EXCLUDED.pu, pc=EXCLUDED.pc, stock=EXCLUDED.stock",(n,pu,pc,pc,0,nb,st))
            else: cur.execute("INSERT OR REPLACE INTO products (name,pu,pc,nb,stock) VALUES (?,?,?,?,?)",(n,pu,pc,nb,st))
        except: pass
        conn.commit(); conn.close(); return redirect('/stock')
    return rp("<h2>Ajouter</h2><a href='/' class='b'>Dash</a><div class='c'><form method='POST'><input name='name' placeholder='NOM' required><input name='pu' placeholder='PU'><input name='pc' placeholder='PC'><input name='nb' value='24'><input name='stock' value='0'><button class='b bg'>Ajouter</button></form></div>",session['name'])
@app.route('/sales', methods=['GET','POST'])
def sales():
    if 'user' not in session: return redirect('/login')
    prods=q("SELECT * FROM products",f=True)
    if request.method=='POST':
        p=request.form.get('product'); qty=float(request.form.get('qty') or 1); t=request.form.get('type_v')
        conn=get_db(); cur=conn.cursor()
        if DATABASE_URL.startswith('postgres'): cur.execute("SELECT * FROM products WHERE name=%s",(p,)); pr=cur.fetchone()
        else: pr=cur.execute("SELECT * FROM products WHERE name=?",(p,)).fetchone()
        if not pr: return redirect('/sales')
        pu=pr['pu']; pc=pr['pc']; nb=pr['nb']
        if t=='detail': tot=int(qty*pu); pu_f=pu; ded=qty/(nb or 24)
        else: tot=int(qty*pc); pu_f=pc; ded=qty
        if DATABASE_URL.startswith('postgres'):
            cur.execute("UPDATE products SET stock=stock-%s WHERE name=%s",(ded,p)); cur.execute("INSERT INTO sales (product,qty,type,pu_final,total,seller,date) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",(p,qty,t,pu_f,tot,session['name'],datetime.now().strftime('%Y-%m-%d %H:%M'))); sid=cur.fetchone()['id']
        else:
            cur.execute("UPDATE products SET stock=stock-? WHERE name=?",(ded,p)); cur.execute("INSERT INTO sales (product,qty,type,pu_final,total,seller,date) VALUES (?,?,?,?,?,?,?)",(p,qty,t,pu_f,tot,session['name'],datetime.now().strftime('%Y-%m-%d %H:%M'))); sid=cur.lastrowid
        conn.commit(); conn.close(); return redirect(f'/ticket/{sid}')
    opts="".join([f"<option value='{p['name']}'>{p['name']} (Stk {p['stock']})</option>" for p in prods]) if prods else ""
    return rp(f"<h2>Vente</h2><a href='/' class='b'>Dash</a><div class='c'><form method='POST'><select name='product'>{opts}</select><input name='qty' type='number' value='1' step='0.5'><select name='type_v'><option value='detail'>Bouteille</option><option value='casier'>Casier</option></select><button class='b bg' style='width:100%'>VENDRE & TICKET</button></form></div>",session['name'])
@app.route('/ticket/<int:sid>')
def ticket(sid):
    if 'user' not in session: return redirect('/login')
    s=q("SELECT * FROM sales WHERE id=%s" if DATABASE_URL.startswith('postgres') else "SELECT * FROM sales WHERE id=?",[sid],one=True)
    return f"<body style='font-family:monospace;max-width:350px;margin:auto'><h2>BERLI</h2>Date: {s['date']}<br>Prod: {s['product']}<br>Qte: {s['qty']}<br>Total: {s['total']}F<br><button onclick='window.print()' style='width:100%;padding:12px;background:black;color:white'>IMPRIMER</button><br><a href='/'>Retour</a></body>"
@app.route('/print_stock')
def ps():
    prods=q("SELECT * FROM products",f=True)
    rows="".join([f"<tr><td>{p['name']}</td><td>{p['stock']}</td></tr>" for p in prods]) if prods else ""
    return f"<h2>STOCK</h2><table border=1 width=100%><tr><th>Nom</th><th>Stock</th></tr>{rows}</table><button onclick='window.print()'>IMPRIMER</button>"
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
