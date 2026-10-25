from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'berli_final_2026'
DB = 'berli.db'

USERS = {
    'patron': {'pass': 'berli2024', 'role': 'patron'},
    'caisse': {'pass': 'caisse123', 'role': 'caissier'},
    'stock': {'pass': 'stock123', 'role': 'stock'}
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
    (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

HTML_HOME = """
<meta name='viewport' content='width=device-width,initial-scale=1'>
<style>body{font-family:sans-serif;margin:0;background:#f5f5f5}.h{background:black;color:white;padding:15px;text-align:center}.g{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px}.c{background:white;padding:10px;border-radius:10px;text-align:center}</style>
<div class='h'><b>BERLI DISTRIBUTION</b><br>92424510</div>
<div class='g'>{% for p in prods %}<div class='c'><b>{{p['name']}}</b><br>U:{{p['pu']}}F<br>C:{{p['pc']}}F<br>10+:{{p['pc10']}}F</div>{% endfor %}</div>
<div style='text-align:center;padding:20px'><a href='/login' style='background:black;color:white;padding:12px 25px;border-radius:20px;text-decoration:none'>Staff</a></div>
"""

@app.route('/')
def home():
    conn=get_db()
    prods=conn.execute('SELECT * FROM products ORDER BY name').fetchall()
    conn.close()
    return render_template_string(HTML_HOME, prods=prods)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form.get('user','').strip()
        pw=request.form.get('pass','').strip()
        if u in USERS and USERS[u]['pass']==pw:
            session['user']=u
            session['role']=USERS[u]['role']
            return redirect('/dashboard')
        return "Erreur <a href='/login'>Retour</a>"
    return "<h2 style='text-align:center;margin-top:40px'>BERLI</h2><form method='POST' style='max-width:300px;margin:auto'><input name='user' placeholder='patron' style='width:100%;padding:12px'><br><br><input name='pass' type='password' style='width:100%;padding:12px'><br><br><button style='width:100%;padding:12px;background:black;color:white'>Entrer</button></form>"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn=get_db()
    prods=conn.execute('SELECT * FROM products ORDER BY name').fetchall()
    sales=conn.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 30').fetchall()
    today=datetime.now().strftime('%Y-%m-%d')
    ts=conn.execute('SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?', (today+'%',)).fetchone()[0]
    tb=conn.execute('SELECT COALESCE(SUM(benefit),0) FROM sales WHERE date LIKE ?', (today+'%',)).fetchone()[0]
    conn.close()
    return render_template_string("""
    <style>body{font-family:sans-serif;background:#eee;margin:0;font-size:13px}.nav{background:black;color:white;padding:10px;display:flex;justify-content:space-between}.card{background:white;margin:8px;padding:12px;border-radius:8px}table{width:100%;border-collapse:collapse}td,th{border:1px solid #ddd;padding:5px}input{padding:6px;margin:2px}.btn{padding:7px;background:black;color:white;border:none}</style>
    <div class='nav'><b>BERLI - {{role}}</b><a href='/logout' style='color:white'>Quitter</a></div>
    <div class='card'>Aujourd'hui: Ventes {{ts}}F | Benef {{tb}}F</div>
    <div class='card'><h3>Vendre</h3><form method='POST' action='/sell'><select name='product'>{% for p in prods %}<option value='{{p["name"]}}'>{{p['name']}} ({{p['nb']}}/casier)</option>{% endfor %}</select><select name='type'><option value='unite'>Unite</option><option value='casier'>Casier</option><option value='casier10'>Casier 10+</option></select><input type='number' step='0.1' name='qty' value='1' style='width:50px'><input type='number' name='prix_final' placeholder='Remise' style='width:80px'><button class='btn'>Vendre</button></form></div>
    <div class='card'><h3>Ajouter Produit</h3><form method='POST' action='/add_product'><input name='name' placeholder='Nom' required><input name='pu' type='number' placeholder='Pu' required style='width:60px'><input name='pc' type='number' placeholder='Pc' required style='width:60px'><input name='pc10' type='number' placeholder='Pc10' required style='width:60px'><input name='cost_pc' type='number' placeholder='Achat' required style='width:60px'><input name='nb' type='number' placeholder='Nb' required style='width:50px'><input name='stock' type='number' placeholder='Stock' required style='width:50px'><button class='btn' style='background:green'>Ajouter</button></form></div>
    <div class='card'><h3>Stock</h3><table><tr><th>Nom</th><th>U</th><th>C</th><th>10+</th><th>Stock</th><th></th></tr>{% for p in prods %}<tr><form method='POST' action='/edit_product'><td>{{p['name']}}<input type='hidden' name='id' value='{{p["id"]}}'></td><td><input type='number' name='pu' value='{{p["pu"]}}' style='width:50px'></td><td><input type='number' name='pc' value='{{p["pc"]}}' style='width:50px'></td><td><input type='number' name='pc10' value='{{p["pc10"]}}' style='width:50px'></td><td><input type='number' name='stock' value='{{p["stock"]}}' style='width:40px'></td><td><button>OK</button></td></form></tr>{% endfor %}</table></div>
    """, prods=prods, role=session['role'], ts=ts, tb=tb)

@app.route('/sell', methods=['POST'])
def sell():
    if 'user' not in session:
        return redirect('/login')
    name=request.form.get('product')
    type_v=request.form.get('type')
    qty=float(request.form.get('qty',1))
    conn=get_db()
    p=conn.execute('SELECT * FROM products WHERE name=?',(name,)).fetchone()
    if p:
        base=p['pu'] if type_v=='unite' else (p['pc'] if type_v=='casier' else p['pc10'])
        pu_final=int(request.form.get('prix_final') or base)
        total=int(pu_final*qty)
        if type_v=='unite':
            benefit=(pu_final - p['cost_pc']/p['nb'])*qty
        else:
            benefit=(pu_final - p['cost_pc'])*qty
        deduit=qty/p['nb'] if type_v=='unite' else qty
        conn.execute('UPDATE products SET stock=stock-? WHERE name=?',(deduit,name))
        conn.execute('INSERT INTO sales (product,qty,type,pu_final,total,benefit,seller,date) VALUES (?,?,?,?,?,?,?,?)',(name,qty,type_v,pu_final,total,int(benefit),session['user'],datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/add_product', methods=['POST'])
def add_product():
    conn=get_db()
    try:
        conn.execute('INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (?,?,?,?,?,?,?)',(request.form.get('name').strip(), int(request.form.get('pu',0)), int(request.form.get('pc',0)), int(request.form.get('pc10',0)), int(request.form.get('cost_pc',0)), int(request.form.get('nb',24)), float(request.form.get('stock',0))))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect('/dashboard')

@app.route('/edit_product', methods=['POST'])
def edit_product():
    conn=get_db()
    conn.execute('UPDATE products SET pu=?, pc=?, pc10=?, stock=? WHERE id=?',(int(request.form.get('pu',0)), int(request.form.get('pc',0)), int(request.form.get('pc10',0)), float(request.form.get('stock',0)), request.form.get('id')))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
