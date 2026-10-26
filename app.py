from flask import Flask, render_template_string, request, redirect, session, Response
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)app.secret_key = 'berli_distribution_2026'
DB = 'berli.db'

USERS = {  
  'patron': {'pass': 'berli2024', 'role': 'patron', 'name': 'URLICH'}, 
  'caisse': {'pass': 'caisse123', 'role': 'caissier', 'name': 'CAISSIERE'},   
  'stock': {'pass': 'stock123', 'role': 'stock', 'name': 'MAGASINIER'}
}

def get_db():   
  c = sqlite3.connect(DB) 
  c.row_factory = sqlite3.Row   
  return c
def init_db():  
  c = get_db() 
  c.execute('''CREATE TABLE IF NOT EXISTS products (  
  id INTEGER PRIMARY KEY, name TEXT UNIQUE, category TEXT,     
  pu INTEGER, pc INTEGER, pc10 INTEGER,  
  cost_pc INTEGER, nb INTEGER, stock REAL DEFAULT 0,   
  alert_stock REAL DEFAULT 2, barcode TEXT, date TEXT)''')  
  c.execute('''CREATE TABLE IF NOT EXISTS sales (     
  id INTEGER PRIMARY KEY, product TEXT, qty REAL, nb INTEGER, type TEXT,   
  pu_base INTEGER, pu_final INTEGER, total INTEGER, cost_total INTEGER, benefit INTEGER,     
  seller TEXT, client TEXT, payment_type TEXT, date TEXT, heure TEXT)''')  
  c.execute('''CREATE TABLE IF NOT EXISTS debts (      
  id INTEGER PRIMARY KEY, client TEXT, phone TEXT, total INTEGER,   
  paid INTEGER DEFAULT 0, remaining INTEGER, date TEXT, status TEXT DEFAULT 'EN COURS')''') 
  c.execute('''CREATE TABLE IF NOT EXISTS payments (   
  id INTEGER PRIMARY KEY, debt_id INTEGER, client TEXT, amount INTEGER, date TEXT, seller TEXT)''') 
  c.execute('''CREATE TABLE IF NOT EXISTS stock_moves (     
  id INTEGER PRIMARY KEY, product TEXT, type TEXT, qty REAL, stock_before REAL, stock_after REAL, reason TEXT, date TEXT)''')  
  c.commit()  
  c.close()
  
init_db()

BASE_STYLE = """
<meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{font-family:'Segoe UI',Arial;background:#f1f5f9;margin:0;color:#0f172a}
.top{position:sticky;top:0;z-index:10;background:white;padding:14px 18px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;font-weight:bold}
.card{background:white;margin:12px;border-radius:16px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.btn{padding:12px 18px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;font-size:14px}
.btn-green{background:#16a34a;color:white}.btn-orange{background:#f97316;color:white}.btn-dark{background:#0f172a;color:white}.btn-red{background:#ef4444;color:white}
.input{width:100%;padding:13px;border:1px solid #cbd5e1;border-radius:10px;box-sizing:border-box;font-size:14px;margin-top:5px}
.label{font-size:11px;font-weight:800;letter-spacing:0.5px;color:#64748b;margin-top:12px;display:block}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.badge{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:bold}.badge-green{background:#dcfce7;color:#15803d}
.badge-orange{background:#ffedd5;color:#c2410c}.badge-red{background:#fee2e2;color:#b91c1c}
table{width:100%;border-collapse:collapse;font-size:13px} th{font-size:11px;color:#64748b;text-align:left;padding:10px 6px;border-bottom:1px solid #e2e8f0} td{padding:12px 6px;border-bottom:1px solid #f1f5f9}
.search{flex:1;padding:12px 14px;border:1px solid #e2e8f0;border-radius:12px}
</style>
"""

LOGIN_HTML = BASE_STYLE + """
<style>body{height:100vh;display:flex;justify-content:center;align-items:center;background:linear-gradient(135deg,#0f172a,#1e3a8a)} .login{background:#e6e8ec;width:90%;max-width:380px;border-radius:32px;padding:36px 30px;text-align:center;box-shadow:0 20px 50px rgba(0,0,0,0.3)}</style>
<div class='login'>
<div style='font-size:42px'> </div>
<h1 style='margin:8px 0 0 0'>Berli Distribution</h1>
<div style='font-size:10px;letter-spacing:3px;color:#64748b;font-weight:800;margin:6px 0 22px 0'>LOGICIEL DE GESTION</div>
<form method='POST'>
<input class='input' style='background:#cbd0d8;border:none;border-radius:24px;padding:16px 20px;margin-bottom:12px;font-weight:bold' name='user' placeholder='UTILISATEUR' required>
<input class='input' style='background:#cbd0d8;border:none;border-radius:24px;padding:16px 20px;margin-bottom:16px;font-weight:bold' type='password' name='pass' placeholder='MOT DE PASSE' required>
<button class='btn btn-dark' style='width:100%;border-radius:24px;padding:16px'>ENTRER ></button>
</form>
<div style='margin-top:18px;font-size:11px;color:#64748b'>patron / berli2024</div>
</div>
"""

@app.route('/')
def home():  
  return redirect('/login')
  
@app.route('/login', methods=['GET', 'POST'])
def login(): 
  if request.method == 'POST':     
    u = request.form.get('user', '').strip().lower()  
    p = request.form.get('pass', '').strip()    
    if u in USERS and USERS[u]['pass'] == p:      
      session['user'] = u     
      session['role'] = USERS[u]['role']     
      session['name'] = USERS[u]['name']       
      session['cart'] = []        
      return redirect('/accueil')     
      return render_template_string(LOGIN_HTML + "<p style='color:red;font-size:12px'>Identifiant incorrect</p>")  
      return render_template_string(LOGIN_HTML)
      
@app.route('/accueil')
def accueil():  
  if 'user' not in session: 
    return redirect('/login')  
    c = get_db()  
    total_debt = c.execute('SELECT COALESCE(SUM(remaining),0) FROM debts WHERE remaining>0').fetchone()[0] 
    low = c.execute('SELECT COUNT(*) FROM products WHERE stock <= alert_stock').fetchone()[0]  
    prod_count = c.execute('SELECT COUNT(*) FROM products').fetchone()[0]  
    today = datetime.now().strftime('%Y-%m-%d') 
    ca_today = c.execute('SELECT COALESCE(SUM(total),0) FROM sales WHERE date=?', (today,)).fetchone()[0]  
    c.close()  
    return render_template_string(BASE_STYLE + """  
    <div class='top'>Berli Distribution <span style='font-size:12px'><a href='/logout' style='text-decoration:none;color:#ef4444'>Deconnexion</a></span></div>
    <div style='margin:12px;background:linear-gradient(90deg,#0f172a,#1e293b);color:white;border-radius:20px;padding:22px'>   
    <div style='font-size:10px;letter-spacing:2px;opacity:0.7'>SYSTEME INTELLIGENT</div> 
    <div style='font-size:22px;font-weight:800;margin:6px 0'>Bonjour, {{name}} </div>  
    <div style='font-size:13px;opacity:0.8'>{{prod_count}} produits - {{ca_today}}F aujourd'hui - {{total_debt}}F a encaisser</div>  
    </div>  
    <div class='grid2'>  
    <a href='/dashboard' style='text-decoration:none'><div class='card' style='text-align:center'><div style='font-size:24px'> </div><b>Dashboard</b><br><small style='color:#64748b'>C.A, Benefices, Credits</small></div></a>  
    <a href='/caisse' style='text-decoration:none'><div class='card' style='text-align:center;border:2px solid #16a34a'><div style='font-size:24px'> </div><b>Caisse</b><br><small style='color:#64748b'>Vente Pu Pc Pc10 + Credit</small></div></a> 
<a href='/stock' style='text-decoration:none'><div class='card' style='text-align:center'><div style='font-size:24px'> </div><b>Stock Complet

    @app.route('/add_to_cart', methods=['POST'])
    def add_to_cart(): 
    if 'user' not in session:    
    return redirect('/login')  
    raw = request.form.get('product', '') 
    name = raw.split('|')[0].strip() 
    typ = request.form.get('type') 
    qty = float(request.form.get('qty', 1)) 
    c = get_db()  
    p = c.execute('SELECT * FROM products WHERE name=?', (name,)).fetchone()  
    c.close()  
    if p:     
    base = p['pu'] if typ == 'unite' else (p['pc'] if typ == 'casier' else p['pc10'])  
    cost_unit = p['cost_pc'] / p['nb'] if typ == 'unite' else p['cost_pc']     
    pf_raw = request.form.get('prix_final', '').strip()    
    pu_final = int(pf_raw) if pf_raw else base   
    total = int(pu_final * qty)    
    benefit = int((pu_final - cost_unit) * qty)        cart = session.get('cart', [])        cart.append({'product': name, 'qty': qty, 'type': typ, 'nb': p['nb'], 'pu_base': base, 'pu_final': pu_final, 'total': total, 'cost_unit': cost_unit, 'benefit': benefit})        session['cart'] = cart    return redirect('/caisse')
@app.route('/remove_cart/<int:i>')def remove_cart(i):    cart = session.get('cart', [])    if 0 <= i < len(cart):        cart.pop(i)        session['cart'] = cart    return redirect('/caisse')
@app.route('/clear_cart')def clear_cart():    session['cart'] = []    return redirect('/caisse')
@app.route('/validate_cart', methods=['POST'])def validate_cart():    if 'user' not in session:        return redirect('/login')    cart = session.get('cart', [])    if not cart:        return redirect('/caisse')    is_credit = request.form.get('is_credit') == '1'    client = request.form.get('client_name', '').strip().upper()    phone = request.form.get('client_phone', '').strip()    total = sum([x['total'] for x in cart])    now_date = datetime.now().strftime('%Y-%m-%d')    now_heure = datetime.now().strftime('%H:%M')    c = get_db()    if is_credit and client:        c.execute('INSERT INTO debts (client,phone,total,paid,remaining,date,status) VALUES (?,?,?,?,?,?,?)', (client, phone, total, 0, total, now_date + ' ' + now_heure, 'EN COURS'))        for it in cart:            deduit = it['qty'] / it['nb'] if it['type'] == 'unite' else it['qty']            before = c.execute('SELECT stock FROM products WHERE name=?', (it['product'],)).fetchone()[0]            c.execute('UPDATE products SET stock=stock-? WHERE name=?', (deduit, it['product']))            after = before - deduit            c.execute('INSERT INTO stock_moves (product,type,qty,stock_before,stock_after,reason,date) VALUES (?,?,?,?,?,?,?)', (it['product'], 'SORTIE', deduit, before, after, f'Vente credit {client}', now_date))            c.execute('INSERT INTO sales (product,qty,nb,type,pu_base,pu_final,total,cost_total,benefit,seller,client,payment_type,date,heure) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (it['product'], it['qty'], it['nb'], it['type'], it['pu_base'], it['pu_final'], it['total'], int(it['cost_unit'] * it['qty']), it['benefit'], session['user'], client, 'CREDIT', now_date, now_heure))    else:        for it in cart:            deduit = it['qty'] / it['nb'] if it['type'] == 'unite' else it['qty']            before = c.execute('SELECT stock FROM products WHERE name=?', (it['product'],)).fetchone()[0]            c.execute('UPDATE products SET stock=stock-? WHERE name=?', (deduit, it['product']))            after = before - deduit            c.execute('INSERT INTO stock_moves (product,type,qty,stock_before,stock_after,reason,date) VALUES (?,?,?,?,?,?,?)', (it['product'], 'SORTIE', deduit, before, after, 'Vente cash', now_date))            c.execute('INSERT INTO sales (product,qty,nb,type,pu_base,pu_final,total,cost_total,benefit,seller,client,payment_type,date,heure) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (it['product'], it['qty'], it['nb'], it['type'], it['pu_base'], it['pu_final'], it['total'], int(it['cost_unit'] * it['qty']), it['benefit'], session['user'], '', 'CASH', now_date, now_heure))    c.commit()    c.close()    session['cart'] = []    return redirect('/dettes' if is_credit else '/dashboard')
@app.route('/dettes')def dettes():    if 'user' not in session:        return redirect('/login')    q = request.args.get('q', '').strip().upper()    c = get_db()    if q:        debts = c.execute('SELECT * FROM debts WHERE client LIKE ? ORDER BY remaining DESC', ('%' + q + '%',)).fetchall()    else:        debts = c.execute('SELECT * FROM debts WHERE remaining>0 ORDER BY id DESC').fetchall()    total = c.execute('SELECT COALESCE(SUM(remaining),0) FROM debts WHERE remaining>0').fetchone()[0]    total_paid = c.execute('SELECT COALESCE(SUM(paid),0) FROM debts').fetchone()[0]    c.close()    return render_template_string(BASE_STYLE + """    <div class='top'><a href='/accueil' style='text-decoration:none;color:#0f172a'>Accueil</a><div>Dettes - {{total}}F</div><div style='font-size:11px'>{{name}}</div></div>    <div style='padding:12px'>    <div class='card' style='margin:0'><b>Gestion des Creances</b><div style='font-size:12px;color:#64748b;margin-top:4px'>Total: <b style='color:#f97316'>{{total}}F</b> | Deja paye: {{total_paid}}F</div>    <form style='display:flex;gap:8px;margin-top:12px' method='GET'><input name='q' value='{{q}}' class='search' placeholder='Rechercher client...'><button class='btn btn-dark'>Rechercher</button></form>    </div>    {% for d in debts %}    <div class='card' style='margin:12px 0 0 0'>    <div style='display:flex;justify-content:space-between;align-items:center'>    <div style='display:flex;align-items:center;gap:12px'><div style='width:38px;height:38px;background:#eef2ff;border-radius:50%;display:flex;justify-content:center;align-items:center;font-weight:800;color:#6366f1'>{{d['client'][0]}}</div><div><b style='font-size:13px'>{{d['client']}}</b><br><small style='color:#64748b'>{{d['date']}} - {{d['phone']}} - Total {{d['total']}}F</small></div></div>    <div style='text-align:right'><b style='color:#f97316'>{{d['remaining']}}F</b><br><small style='color:#64748b'>Reste / Paye {{d['paid']}}F</small><br><span class='badge badge-orange'>{{d['status']}}</span></div>    </div>    <form method='POST' action='/pay_debt/{{d["id"]}}' style='display:flex;gap:8px;margin-top:12px;background:#fff7ed;padding:10px;border-radius:10px;border:1px solid #fed7aa'>    <input name='amount' type='number' class='input' style='margin:0' placeholder='Montant paye' max='{{d["remaining"]}}' required>    <button class='btn btn-orange'>Regler</button>    </form>    </div>    {% endfor %}    {% if not debts %}<div class='card' style='text-align:center;padding:30px;color:#64748b'>Aucune dette - Toutes les creances sont reglees !</div>{% endif %}    </div>    """, debts=debts, total=total, total_paid=total_paid, q=q, name=session.get('name'))
@app.route('/pay_debt/<int:debt_id>', methods=['POST'])def pay_debt(debt_id):    if 'user' not in session:        return redirect('/login')    amount = int(request.form.get('amount', 0))    c = get_db()    d = c.execute('SELECT * FROM debts WHERE id=?', (debt_id,)).fetchone()    if d and amount > 0 and amount <= d['remaining']:        new_paid = d['paid'] + amount        new_rem = d['remaining'] - amount        status = 'SOLDE' if new_rem == 0 else 'EN COURS'        c.execute('UPDATE debts SET paid=?, remaining=?, status=? WHERE id=?', (new_paid, new_rem, status, debt_id))        c.execute('INSERT INTO payments (debt_id,client,amount,date,seller) VALUES (?,?,?,?,?)', (debt_id, d['client'], amount, datetime.now().strftime('%Y-%m-%d %H:%M'), session['user']))        c.commit()    c.close()    return redirect('/dettes')
@app.route('/stock')def stock_page():    if 'user' not in session:        return redirect('/login')    c = get_db()    prods = c.execute('SELECT * FROM products ORDER BY name').fetchall()    c.close()    return render_template_string(BASE_STYLE + """    <div class='top'><a href='/accueil' style='text-decoration:none'>Accueil</a><b>Berli Distribution - Stock</b><div style='display:flex;gap:6px'><a href='/stock_moves' style='text-decoration:none;font-size:11px' class='btn btn-dark'>Mouvements</a><a href='/export_stock' style='text-decoration:none;font-size:11px' class='btn btn-green'>Excel</a></div></div>    <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px'>    <div class='card' style='margin:0;border:2px solid #16a34a'><b style='color:#16a34a'>ENTREE STOCK</b><br><small style='color:#64748b'>Livraison fournisseur</small>    <form method='POST' action='/stock_entry' style='margin-top:10px'>    <select name='entry_product' class='input' required>{% for p in prods %}<option>{{p['name']}} - Actuel: {{p['stock']}} casiers</option>{% endfor %}</select>    <div style='display:flex;gap:6px;margin-top:8px'><input name='entry_qty' type='number' step='0.1' placeholder='Qte casiers' class='input' style='margin:0' required><input name='entry_reason' class='input' style='margin:0' value='Livraison fournisseur'></div>    <button class='btn btn-green' style='width:100%;margin-top:8px'>Ajouter Entree</button>    </form></div>    <div class='card' style='margin:0;border:2px solid #f97316'><b style='color:#f97316'>INVENTAIRE / AJUSTEMENT</b><br><small style='color:#64748b'>Casse, perte, inventaire reel</small>    <form method='POST' action='/stock_adjust' style='margin-top:10px'>    <select name='adj_product' class='input' required>{% for p in prods %}<option>{{p['name']}} - Actuel: {{p['stock']}}</option>{% endfor %}</select>    <div style='display:flex;gap:6px;margin-top:8px'><input name='adj_stock' type='number' step='0.1' placeholder='Nouveau stock reel' class='input' style='margin:0' required><input name='adj_reason' class='input' style='margin:0' value='Inventaire'></div>    <button class='btn btn-orange' style='width:100%;margin-top:8px'>Ajuster Stock</button>    </form></div>    </div>    <div class='card'>    <b>Ajouter / Modifier Produit</b>    <form method='POST' action='/add_product'>    <div class='grid2'>    <div><label class='label'>NOM PRODUIT</label><input name='name' class='input' placeholder='Ex: Castel Pils' required></div>    <div><label class='label'>CATEGORIE</label><select name='category' class='input'><option>Bieres</option><option>Boissons gazeuses</option><option>Eaux</option><option>Vins</option><option>Autres</option></select></div>    </div>    <div class='grid3'>    <div><label class='label'>PU (Prix Unite)</label><input name='pu' type='number' class='input' required></div>    <div><label class='label'>PC (Prix Casier)</label><input name='pc' type='number' class='input' required></div>    <div><label class='label'>PC10 (Prix 10+ Casiers)</label><input name='pc10' type='number' class='input' required></div>    </div>    <div class='grid3'>    <div><label class='label'>COUT ACHAT CASIER</label><input name='cost_pc' type='number' class='input' required></div>    <div><label class='label'>NB / CASIER (12/20/24)</label><input name='nb' type='number' value='24' class='input' required></div>    <div><label class='label'>STOCK (en casiers)</label><input name='stock' type='number' step='0.1' class='input' required></div>    </div>    <div class='grid2'>    <div><label class='label'>ALERTE STOCK FAIBLE</label><input name='alert' type='number' step='0.1' value='2' class='input'></div>    <div><label class='label'>CODE BARRE</label><input name='barcode' class='input'></div>    </div>    <button class='btn btn-dark' style='width:100%;margin-top:14px'>ENREGISTRER PRODUIT</button>    </form>    </div>    <div class='card'>    <b>Inventaire Complet</b> - {{prods|length}} produits    <div style='overflow-x:auto;margin-top:10px'>    <table><tr><th>Produit</th><th>Cat</th><th>Pu/Pc/Pc10</th><th>Cout</th><th>Nb</th><th>Sto</th><th>Benef</th><th>Statut</th></tr>    {% for p in prods %}    <tr><td><b>{{p['name']}}</b></td><td>{{p['category']}}</td><td>{{p['pu']}}/{{p['pc']}}/{{p['pc10']}}</td><td>{{p['cost_pc']}}F</td><td>{{p['nb']}}</td><td><b>{{p['stock']}}</b><br><small>{{(p['stock']*p['nb'])|int}} b</small></td><td style='color:green'>{{p['pu'] - (p['cost_pc']/p['nb'])|int}}F<br>{{p['pc']-p['cost_pc']}}F</td><td>{% if p['stock']<=p['alert_stock'] %}<span class='badge badge-red'>FAIBLE</span>{% else %}<span class='badge badge-green'>OK</span>{% endif %}</td></tr>    {% endfor %}    </table></div></div>    """, prods=prods)
@app.route('/add_product', methods=['POST'])def add_product():    c = get_db()    try:        name = request.form.get('name', '').strip()        c.execute('INSERT OR REPLACE INTO products (name,category,pu,pc,pc10,cost_pc,nb,stock,alert_stock,barcode,date) VALUES (?,?,?,?,?,?,?,?,?,?,?)',                  (name, request.form.get('category', 'Bieres'), int(request.form.get('pu', 0)), int(request.form.get('pc', 0)), int(request.form.get('pc10', 0)),                   int(request.form.get('cost_pc', 0)), int(request.form.get('nb', 24)), float(request.form.get('stock', 0)), float(request.form.get('alert', 2)), request.form.get('barcode', ''), datetime.now().strftime('%Y-%m-%d')))        c.commit()    except Exception as e:        print(e)    c.close()    return redirect('/stock')
@app.route
