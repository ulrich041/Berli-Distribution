from flask import Flask, render_template_string, request, redirect, session, Response
import sqlite3, os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'berli_distribution_2026'
DB = 'berli.db'

USERS = {   
  'patron':{'pass':'berli2024','role':'patron','name':'URLICH'},  
  'caisse':{'pass':'caisse123','role':'caissier','name':'CAISSIERE'},   
  'stock':{'pass':'stock123','role':'stock','name':'MAGASINIER'}
}

def get_db():  
  c = sqlite3.connect(DB)  
  c.row_factory = sqlite3.Row  
  return c
  
def init_db():  
  c = get_db()   
  c.execute("""CREATE TABLE IF NOT EXISTS products (    
    id INTEGER PRIMARY KEY, name TEXT UNIQUE, category TEXT,   
    pu INTEGER, pc INTEGER, pc10 INTEGER,      
    cost_pc INTEGER, nb INTEGER, stock REAL DEFAULT 0,   
    alert_stock REAL DEFAULT 2, barcode TEXT, date TEXT)""")   
  c.execute("""CREATE TABLE IF NOT EXISTS sales (      
    id INTEGER PRIMARY KEY, product TEXT, qty REAL, nb INTEGER, type TEXT,     
    pu_base INTEGER, pu_final INTEGER, total INTEGER, cost_total INTEGER, benefit INTEGER,     
    seller TEXT, client TEXT, payment_type TEXT, date TEXT, heure TEXT)""")  
  c.execute("""CREATE TABLE IF NOT EXISTS debts (      
    id INTEGER PRIMARY KEY, client TEXT, phone TEXT, total INTEGER,     
    paid INTEGER DEFAULT 0, remaining INTEGER, date TEXT, status TEXT DEFAULT 'EN COURS')""")  
  c.execute("""CREATE TABLE IF NOT EXISTS payments (     
    id INTEGER PRIMARY KEY, debt_id INTEGER, client TEXT, amount INTEGER, date TEXT, seller TEXT)""")  
  c.execute("""CREATE TABLE IF NOT EXISTS stock_moves (    
    id INTEGER PRIMARY KEY, product TEXT, type TEXT, qty REAL, stock_before REAL, stock_after REAL, reason TEXT, date TEXT)""")   
  c.commit() 
  c.close()

init_db()
BASE_STYLE = """
<meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{font-family:'Segoe UI',Arial;background:#f1f5f9;margin:0;color:#0f172a}
.top{position:sticky;top:0;z-index:10;background:white;padding:14px 18px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;font-weight:bold}
.card{background:white;margin:12px;border-radius:16px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.btn{padding:12px 18px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;font-size:14px}.btn-green{background:#16a34a;color:white}
.btn-orange{background:#f97316;color:white}.btn-dark{background:#0f172a;color:white}.btn-red{background:#ef4444;color:white}
.input{width:100%;padding:13px;border:1px solid #cbd5e1;border-radius:10px;box-sizing:border-box;font-size:14px;margin-top:5px}
.label{font-size:11px;font-weight:800;letter-spacing:0.5px;color:#64748b;margin-top:12px;display:block}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.badge{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:bold}
.badge-green{background:#dcfce7;color:#15803d}.badge-orange{background:#ffedd5;color:#c2410c}.badge-red{background:#fee2e2;color:#b91c1c}
table{width:100%;border-collapse:collapse;font-size:13px} th{font-size:11px;color:#64748b;text-align:left;padding:10px 6px;border-bottom:1px solid #e2e8f0} td{padding:12px 6px;border-bottom:1px solid #f1f5f9}
.search{flex:1;padding:12px 14px;border:1px solid #e2e8f0;border-radius:12px}
</style>
"""

LOGIN_HTML = BASE_STYLE + """
<style>
body{height:100vh;display:flex;justify-content:center;align-items:center;background:linear-gradient(135deg,#0f172a,#1e3a8a)} .login{background:#e6e8ec;width:90%;max-width:380px;border-radius:32px;padding:36px 30px;text-align:center;box-shadow:0 20px 50px rgba(0,0,0,0.3)}</style>
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
  
@app.route('/login', methods=['GET','POST'])
def login():  
  if request.method == 'POST':   
  u = request.form.get('user','').strip().lower()     
  p = request.form.get('pass','').strip()     
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
  <div style='font-size:13px;opacity:0.8'>{{prod_count}} produits • {{ca_today}}F aujourd'hui • {{total_debt}}F à encaisser</div> 
  </div> 
  <div class='grid2'>  
  <a href='/dashboard' style='text-decoration:none'><div class='card' style='text-align:center'><div style='font-size:24px'> </div><b>Dashboard</b><br><small style='color:#64748b'>C.A, Bénéfices, Crédits</small></div></a> 
  <a href='/caisse' style='text-decoration:none'><div class='card' style='text-align:center;border:2px solid #16a34a'><div style='font-size:24px'> </div><b>Caisse</b><br><small style='color:#64748b'>Vente Pu Pc Pc10 + Crédit</small></div></a>  
  <a href='/stock' style='text-decoration:none'><div class='card' style='text-align:center'><div style='font-size:24px'> </div><b>Stock Complet</b><br><small style='color:#64748b'>Entrée, Inventaire, Excel</small></div></a>  
  <a href='/dettes' style='text-decoration:none'><div class='card' style='text-align:center;border:2px solid #f97316'><div style='font-size:24px'> </div><b>Dettes {{total_debt}}F</b><br><small style='color:#64748b'>Gestion des Créances</small></div></a>  
  <a href='/ventes' style='text-decoration:none'><div class='card' style='text-align:center'><div style='font-size:24px'> </div><b>Journal Ventes</b><br><small style='color:#64748b'>Toutes ventes</small></div></a>  
  <a href='/stock_moves' style='text-decoration:none'><div class='card' style='text-align:center'><div style='font-size:24px'> </div><b>Mouvements</b><br><small style='color:#64748b'>Entrées, Sorties, Ajust</small></div></a>  
  </div>  
  {% if low>0 %}<div class='card' style='background:#fef2f2;border:1px solid #fecaca'><b style='color:#b91c1c'> {{low}} produits en stock faible</b> <a href='/stock'>Voir</a></div>{% endif %}  
  """, name=session['name'], total_debt=total_debt, low=low, prod_count=prod_count, ca_today=ca_today)
@app.route('/dashboard')
def dashboard():  
  if 'user' not in session:    
      return redirect('/login')   
  c = get_db()   
  today = datetime.now().strftime('%Y-%m-%d') 
  week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')  
  ca_today = c.execute('SELECT COALESCE(SUM(total),0) FROM sales WHERE date=?', (today,)).fetchone()[0]  
  ben_today = c.execute('SELECT COALESCE(SUM(benefit),0) FROM sales WHERE date=?', (today,)).fetchone()[0]  
  ca_week = c.execute('SELECT COALESCE(SUM(total),0) FROM sales WHERE date>=?', (week,)).fetchone()[0]   
  ben_week = c.execute('SELECT COALESCE(SUM(benefit),0) FROM sales WHERE date>=?', (week,)).fetchone()[0] 
  ca_all = c.execute('SELECT COALESCE(SUM(total),0) FROM sales').fetchone()[0] 
  ben_all = c.execute('SELECT COALESCE(SUM(benefit),0) FROM sales').fetchone()[0]   
  total_debt = c.execute('SELECT COALESCE(SUM(remaining),0) FROM debts WHERE remaining>0').fetchone()[0] 
  total_paid_debt = c.execute('SELECT COALESCE(SUM(paid),0) FROM debts').fetchone()[0]  
  low = c.execute('SELECT COUNT(*) FROM products WHERE stock <= alert_stock').fetchone()[0]  
  top_sales = c.execute('SELECT product, SUM(qty) as q, SUM(total) as t FROM sales GROUP BY product ORDER BY t DESC LIMIT 5').fetchall()   
  c.close()   
  return render_template_string(BASE_STYLE + """ 
  <div class='top'><a href='/accueil' style='text-decoration:none;color:#0f172a'>← Accueil</a> <span>Dashboard</span> <a href='/dettes' style='color:#f97316;text-decoration:none'>{{total_debt}}F crédit</a></div> 
  <div class='card'><b>Berli Distribution - Tableau de Bord</b><br><small style='color:#64748b'>Analyse détaillée</small></div> 
  <div style='padding:0 12px'><div style='font-size:11px;font-weight:800;border-left:4px solid #0ea5e9;padding-left:8px;margin:16px 0 10px'>FOCUS AUJOURD'HUI</div>  
  <div class='grid2'>    <div class='card' style='margin:0;text-align:center'><small style='color:#64748b'>VENTES JOUR</small><div style='font-size:20px;font-weight:800'>{{ca_today}}F</div></div> 
  <div class='card' style='margin:0;text-align:center'><small style='color:#64748b'>BÉNÉF JOUR</small><div style='font-size:20px;font-weight:800;color:#16a34a'>{{ben_today}}F</div></div>  
  <div class='card' style='margin:0;text-align:center;border:2px solid #f97316'><small style='color:#64748b'>CRÉDITS À ENCAISSER</small><div style='font-size:20px;font-weight:800;color:#f97316'>{{total_debt}}F</div></div>   
  <div class='card' style='margin:0;text-align:center'><small style='color:#64748b'>STOCK FAIBLE</small><div style='font-size:20px;font-weight:800;color:#ef4444'>{{low}}</div></div>  
  </div>    <div style='font-size:11px;font-weight:800;border-left:4px solid #16a34a;padding-left:8px;margin:18px 0 10px'>PERFORMANCE</div>  
  <div class='grid2'> 
  <div class='card' style='margin:0'><small>C.A 7 JOURS</small><div style='font-weight:800;font-size:18px'>{{ca_week}}F</div><small style='color:#16a34a'>Bénéf {{ben_week}}F</small></div>  
  <div class='card' style='margin:0'><small>C.A TOTAL</small><div style='font-weight:800;font-size:18px'>{{ca_all}}F</div><small style='color:#16a34a'>Bénéf {{ben_all}}F</small></div> 
  <div class='card' style='margin:0'><small>TOTAL DÉJÀ PAYÉ CRÉDIT</small><div style='font-weight:800;font-size:18px'>{{total_paid_debt}}F</div></div>  
  <div class='card' style='margin:0'><small>RESTE À ENCAISSER</small><div style='font-weight:800;font-size:18px;color:#f97316'>{{total_debt}}F</div><a href='/dettes' style='font-size:11px'>Gérer →</a></div> 
  </div>  
  <div style='font-size:11px;font-weight:800;border-left:4px solid #6366f1;padding-left:8px;margin:18px 0 10px'>TOP PRODUITS</div>  
  {% for p in top_sales %}<div class='card' style='margin:6px 0;padding:10px 14px;display:flex;justify-content:space-between'><span>{{p['product']}} - {{p['q']}} vendus</span><b>{{p['t']}}F</b></div>{% endfor %}    
  </div>   
  """, ca_today=ca_today, ben_today=ben_today, ca_week=ca_week, ben_week=ben_week, ca_all=ca_all, ben_all=ben_all, total_debt=total_debt, total_paid_debt=total_paid_debt, low=low, top_sales=top_sales)

@app.route('/caisse')
def caisse():
  if 'user' not in session: 
    return redirect('/login') 
  c = get_db()  
  prods = c.execute('SELECT * FROM products ORDER BY name').fetchall()  
  c.close() 
  cart = session.get('cart', []) 
  tot = sum([x['total'] for x in cart])  
  ben = sum([x['benefit'] for x in cart])  
  return render_template_string(BASE_STYLE + """ 
  <div class='top'><a href='/accueil' style='text-decoration:none'>←</a><b>Caisse - Berli Distribution</b><a href='/dettes' style='text-decoration:none;color:#f97316'>Dettes</a></div>  
  <div class='card'>  
  <form method='POST' action='/add_to_cart'>   
  <label class='label'>PRODUIT (Pu Pc Pc10 Nb Sto)</label>   
  <select name='product' class='input' style='font-weight:bold'>   
  {% for p in prods %}<option>{{p['name']}} | Pu:{{p['pu']}} Pc:{{p['pc']}} Pc10:{{p['pc10']}} | Nb:{{p['nb']}} Sto:{{p['stock']}} | Coût:{{p['cost_pc']}}</option>{% endfor %}  
  </select>  
  <div class='grid3'>  
  <div><label class='label'>TYPE VENTE</label><select name='type' class='input'><option value='unite'>Unité (Pu)</option><option value='casier'>Casier (Pc)</option><option value='casier10'>Casier 10+ (Pc10)</option></select></div> 
  <div><label class='label'>QUANTITÉ</label><input name='qty' type='number' step='0.1' value='1' class='input'></div>  
  <div><label class='label'>PRIX FINAL (si promo)</label><input name='prix_final' type='number' placeholder='Vide=normal' class='input'></div>
  </div>  
  <button class='btn btn-green' style='width:100%;margin-top:12px'>+ Ajouter au panier</button>   
  </form>   
  {% if cart %}   
  <div style='margin-top:16px'>   
  <table><tr><th>Produit</th><th>Qté/Type</th><th>Pu final</th><th>Total</th><th>Bénéf</th><th></th></tr>  
  {% for item in cart %}<tr><td><b>{{item['product']}}</b></td><td>{{item['qty']}} {{item['type']}}</td><td>{{item['pu_final']}}F</td><td>{{item['total']}}F</td><td style='color:green'>{{item['benefit']}}F</td><td><a href='/remove_cart/{{loop.index0}}' style='color:red'>X</a></td></tr>{% endfor %}   
  </table>  
  <div style='background:#16a34a;color:white;padding:14px;border-radius:12px;text-align:center;margin-top:12px'>  
  <div style='font-size:12px'>TOTAL VENTE</div><div style='font-size:26px;font-weight:800'>{{tot}}F</div><div style='font-size:11px'>Bénéfice: {{ben}}F</div>  
  </div>  
  <form method='POST' action='/validate_cart' style='margin-top:12px'>  
  <div style='background:#fff7ed;border:2px solid #fb923c;border-radius:12px;padding:12px'>  
  <label style='font-weight:800'><input type='checkbox' name='is_credit' value='1' onchange='document.getElementById("clientbox").style.display=this.checked?"block":"none"'> VENDRE À CRÉDIT (ira dans Dettes)</label>  
  <div id='clientbox' style='display:none;margin-top:10px'> 
  <label class='label'>NOM CLIENT (ex: FL O PARC BASAR)</label><input name='client_name' class='input' placeholder='Nom complet'>  
  <label class='label'>TÉLÉPHONE</label><input name='client_phone' class='input' placeholder='90...'>  
  </div> 
  </div>  
  <div style='display:flex;gap:8px;margin-top:10px'><button class='btn btn-green' style='flex:1'> VALIDER VENTE</button><a href='/clear_cart' class='btn btn-red' style='flex:1;text-align:center;text-decoration:none'>Vider</a></div>  
  </form>  
  </div> 
  {% endif %}   
  </div>   
  """, prods=prods, cart=cart, tot=tot, ben=ben)
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():  
  if 'user' not in session:  
    return redirect('/login')  
  raw = request.form.get('product','') 
  name = raw.split('|')[0].strip() 
  typ = request.form.get('type')  
  qty = float(request.form.get('qty',1))  
  c = get_db()  
  p = c.execute('SELECT * FROM products WHERE name=?', (name,)).fetchone()  
  c.close()  
  if p:    
     base = p['pu'] if typ=='unite' else (p['pc'] if typ=='casier' else p['pc10'])    
     cost_unit = p['cost_pc']/p['nb'] if typ=='unite' else p['cost_pc']     
     pf_raw = request.form.get('prix_final','').strip()    
     pu_final = int(pf_raw) if pf_raw else base      
     total = int(pu_final * qty)   
     benefit = int((pu_final - cost_unit) * qty) 
     cart = session.get('cart', [])     
     cart.append({'product':name,'qty':qty,'type':typ,'nb':p['nb'],'pu_base':base,'pu_final':pu_final,'total':total,'cost_unit':cost_unit,'benefit':benefit})     
     session['cart'] = cart  
   return redirect('/caisse')

@app.route('/remove_cart/<int:i>')
def remove_cart(i): 
  cart = session.get('cart', [])  
  if 0 <= i < len(cart):   
    cart.pop(i)     
    session['cart'] = cart  
  return redirect('/caisse')

@app.route('/clear_cart')
def clear_cart():   
  session['cart'] = []  
  return redirect('/caisse')

@app.route('/validate_cart', methods=['POST'])
def validate_cart(): 
  if 'user' not in session: 
      return redirect('/login')   
  cart = session.get('cart', []) 
  if not cart:       
    return redirect('/caisse')  
  is_credit = request.form.get('is_credit') == '1' 
  client = request.form.get('client_name','').strip().upper()  
  phone = request.form.get('client_phone','').strip() 
  total = sum([x['total'] for x in cart])  
  now_date = datetime.now().strftime('%Y-%m-%d')  
  now_heure = datetime.now().strftime('%H:%M')  
  c = get_db()  
  if is_credit and client:  
    c.execute('INSERT INTO debts (client,phone,total,paid,remaining,date,status) VALUES (?,?,?,?,?,?,?)', (client,phone,total,0,total,now_date+' '+now_heure,'EN COURS'))   
    for it in cart:      
      deduit = it['qty']/it['nb'] if it['type']=='unite' else it['qty']   
      before = c.execute('SELECT stock FROM products WHERE name=?', (it['product'],)).fetchone()[0]   
      c.execute('UPDATE products SET stock=stock-? WHERE name=?', (deduit, it['product']))     
      after = before - deduit     
      c.execute('INSERT INTO stock_moves (product,type,qty,stock_before,stock_after,reason,date) VALUES (?,?,?,?,?,?,?)', (it['product'],'SORTIE',deduit,before,after,f'Vente credit {client}',now_date))     
      c.execute('INSERT INTO sales (product,qty,nb,type,pu_base,pu_final,total,cost_total,benefit,seller,client,payment_type,date,heure) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',        
           (it['product'],it['qty'],it['nb'],it['type'],it['pu_base'],it['pu_final'],it['total'],int(it['cost_unit']*it['qty']),it['benefit'],session['user'],client,'CREDIT',now_date,now_heure))  
  else:    
    for it in cart:      
      deduit = it['qty']/it['nb'] if it['type']=='unite' else it['qty']   
      before = c.execute('SELECT stock FROM products WHERE name=?', (it['product'],)).fetchone()[0]        
      c.execute('UPDATE products SET stock=stock-? WHERE name=?', (deduit, it['product']))      
      after = before - deduit     
      c.execute('INSERT INTO stock_moves (product,type,qty,stock_before,stock_after,reason,date) VALUES (?,?,?,?,?,?,?)', (it['product'],'SORTIE',deduit,before,after,'Vente cash',now_date))      
      c.execute('INSERT INTO sales (product,qty,nb,type,pu_base,pu_final,total,cost_total,benefit,seller,client,payment_type,date,heure) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',      
            (it['product'],it['qty'],it['nb'],it['type'],it['pu_base'],it['pu_final'],it['total'],int(it['cost_unit']*it['qty']),it['benefit'],session['user'],'','CASH',now_date,now_heure))  
   c.commit()  
   c.close()  
   session['cart'] = []    
      return redirect('/dettes' if is_credit else '/dashboard')
@app.route('/dettes')
def dettes(): 
  if 'user' not in session:   
    return redirect('/login')  
    q = request.args.get('q','').strip().upper() 
    c = get_db()   
    if q:      
       debts = c.execute('SELECT * FROM debts WHERE client LIKE ? ORDER BY remaining DESC', ('%'+q+'%',)).fetchall() 
    else:     
      debts = c.execute('SELECT * FROM debts WHERE remaining>0 ORDER BY id DESC').fetchall() 
      total = c.execute('SELECT COALESCE(SUM(remaining),0) FROM debts WHERE remaining>0').fetchone()[0]   
      total_paid = c.execute('SELECT COALESCE(SUM(paid),0) FROM debts').fetchone()[0] 
      c.close()    
      return render_template_string(BASE_STYLE + """   
      <div class='top'><a href='/accueil' style='text-decoration:none;color:#0f172a'>←</a><div><div>Dettes</div><div style='font-size:10px;color:#64748b;font-weight:400'>Gestion des Créances - {{total}}F à encaisser</div></div><div style='font-size:11px'>{{name}}</div></div>
      <div style='padding:12px'>  
      <div class='card' style='margin:0'><b>Gestion des Créances</b><div style='font-size:12px;color:#64748b;margin-top:4px'>Suivi des paiements dus par vos clients - Total: <b style='color:#f97316'>{{total}}F</b> | Déjà payé: {{total_paid}}F</div>  
      <form style='display:flex;gap:8px;margin-top:12px' method='GET'><input name='q' value='{{q}}' class='search' placeholder='Rechercher un client endetté... (ex: FL O PARC)'><button class='btn btn-dark'>Rechercher</button></form>  
      </div>   
      {% for d in debts %} 
      <div class='card' style='margin:12px 0 0 0'>  
      <div style='display:flex;justify-content:space-between;align-items:center'>  
      <div style='display:flex;align-items:center;gap:12px'><div style='width:38px;height:38px;background:#eef2ff;border-radius:50%;display:flex;justify-content:center;align-items:center;font-weight:800;color:#6366f1'>{{d['client'][0]}}</div><div><b style='font-size:13px'>{{d['client']}}</b><br><small style='color:#64748b'>{{d['date']}} • {{d['phone']}} • Total {{d['total']}}F</small></div></div> 
      <div style='text-align:right'><b style='color:#f97316'>{{d['remaining']}}F</b><br><small style='color:#64748b'>Reste / Payé {{d['paid']}}F</small><br><span class='badge badge-orange'>{{d['status']}}</span></div>  
      </div>   
      <form method='POST' action='/pay_debt/{{d["id"]}}' style='display:flex;gap:8px;margin-top:12px;background:#fff7ed;padding:10px;border-radius:10px;border:1px solid #fed7aa'> 
      <input name='amount' type='number' class='input' style='margin:0' placeholder='Montant payé' max='{{d["remaining"]}}' required>  
      <button class='btn btn-orange'>Régler</button>  
      </form>  
      </div>   
      {% endfor %}  
      {% if not debts %}<div class='card' style='text-align:center;padding:30px;color:#64748b'>Aucune dette {% if q %}pour "{{q}}"{% endif %}<br><small>Toutes les créances sont réglées !</small></div>{% endif %} 
      </div> 
      """, debts=debts, total=total, total_paid=total_paid, q=q, name=session.get('name'))
      
@app.route('/pay_debt/<int:debt_id>', methods=['POST'])
def pay_debt(debt_id):   
  if 'user' not in session:   
    return redirect('/login') 
  amount = int(request.form.get('amount',0))  
  c = get_db()  
  d = c.execute('SELECT * FROM debts WHERE id=?', (debt_id,)).fetchone() 
  if d and amount>0 and amount<=d['remaining']:     
    new_paid = d['paid']+amount   
    new_rem = d['remaining']-amount   
    status = 'SOLDE' if new_rem==0 else 'EN COURS'    
    c.execute('UPDATE debts SET paid=?, remaining=?, status=? WHERE id=?', (new_paid,new_rem,status,debt_id))    
    c.execute('INSERT INTO payments (debt_id,client,amount,date,seller) VALUES (?,?,?,?,?)', (debt_id,d['client'],amount,datetime.now().strftime('%Y-%m-%d %H:%M'),session['user']))    
    c.commit()  
  c.close() 
  return redirect('/dettes')
    
@app.route('/stock')
def stock_page():  
  if 'user' not in session:    
      return redirect('/login')  
  c = get_db()   
  prods = c.execute('SELECT * FROM products ORDER BY name').fetchall()  
  c.close()  
  return render_template_string(BASE_STYLE + """  
  <div class='top'><a href='/accueil' style='text-decoration:none'>← Accueil</a><b>Berli Distribution - Stock</b><div style='display:flex;gap:6px'><a href='/stock_moves' style='text-decoration:none;font-size:11px' class='btn btn-dark'>Mouvements</a><a href='/export_stock' style='text-decoration:none;font-size:11px' class='btn btn-green'> Excel</a></div></div> 
  <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px'>  
  <div class='card' style='margin:0;border:2px solid #16a34a'><b style='color:#16a34a'> ENTRÉE STOCK</b><br><small style='color:#64748b'>Livraison fournisseur</small> 
  <form method='POST' action='/stock_entry' style='margin-top:10px'> 
  <select name='entry_product' class='input' required>{% for p in prods %}<option>{{p['name']}} - Actuel: {{p['stock']}} casiers</option>{% endfor %}</select>  
  <div style='display:flex;gap:6px;margin-top:8px'><input name='entry_qty' type='number' step='0.1' placeholder='Qté casiers' class='input' style='margin:0' required><input name='entry_reason' class='input' style='margin:0' value='Livraison fournisseur'></div>  
  <button class='btn btn-green' style='width:100%;margin-top:8px'>Ajouter Entrée</button>  
  </form></div>  
  <div class='card' style='margin:0;border:2px solid #f97316'><b style='color:#f97316'> INVENTAIRE / AJUSTEMENT</b><br><small style='color:#64748b'>Casse, perte, inventaire réel</small>  
  <form method='POST' action='/stock_adjust' style='margin-top:10px'>  
  <select name='adj_product' class='input' required>{% for p in prods %}<option>{{p['name']}} - Actuel: {{p['stock']}}</option>{% endfor %}</select>
  <div style='display:flex;gap:6px;margin-top:8px'><input name='adj_stock' type='number' step='0.1' placeholder='Nouveau stock réel' class='input' style='margin:0' required><input name='adj_reason' class='input' style='margin:0' value='Inventaire'></div>   
  <button class='btn btn-orange' style='width:100%;margin-top:8px'>Ajuster Stock</button> 
  </form></div>  
  </div>   
  <div class='card'> 
  <b>Ajouter / Modifier Produit</b><br><small style='color:#64748b'>Tous les paramètres de vente</small> 
  <form method='POST' action='/add_product'>  
  <div class='grid2'> 
  <div><label class='label'>NOM PRODUIT</label><input name='name' class='input' placeholder='Ex: Castel Pils' required></div>  
  <div><label class='label'>CATÉGORIE</label><select name='category' class='input'><option>Bières</option><option>Boissons gazeuses</option><option>Eaux</option><option>Vins</option><option>Autres</option></select></div>  
  </div>   
  <div class='grid3'>  
  <div><label class='label'>PU (Prix Unité)</label><input name='pu' type='number' class='input' required></div>  
  <div><label class='label'>PC (Prix Casier)</label><input name='pc' type='number' class='input' required></div>  
  <div><label class='label'>PC10 (Prix 10+ Casiers)</label><input name='pc10' type='number' class='input' required></div> 
  </div>    
  <div class='grid3'>    
  <div><label class='label'>COÛT ACHAT CASIER</label><input name='cost_pc' type='number' class='input' required></div> 
  <div><label class='label'>NB / CASIER (12/20/24)</label><input name='nb' type='number' value='24' class='input' required></div> 
  <div><label class='label'>STOCK (en casiers)</label><input name='stock' type='number' step='0.1' class='input' required></div>   
  </div>   
  <div class='grid2'>  
  <div><label class='label'>ALERTE STOCK FAIBLE</label><input name='alert' type='number' step='0.1' value='2' class='input'></div>  
  <div><label class='label'>CODE BARRE</label><input name='barcode' class='input'></div> 
  </div> 
  <button class='btn btn-dark' style='width:100%;margin-top:14px'> ENREGISTRER PRODUIT</button>   
  </form>  
  </div>  
  <div class='card'>
  <b>Inventaire Complet</b> - {{prods|length}} produits  
  <div style='overflow-x:auto;margin-top:10px'>  
  <table><tr><th>Produit</th><th>Cat</th><th>Pu/Pc/Pc10</th><th>Coût</th><th>Nb</th><th>Sto</th><th>Bénéf</th><th>Statut</th></tr> 
  {% for p in prods %}  
  <tr><td><b>{{p['name']}}</b></td><td>{{p['category']}}</td><td>{{p['pu']}}/{{p['pc']}}/{{p['pc10']}}</td><td>{{p['cost_pc']}}F</td><td>{{p['nb']}}</td><td><b>{{p['stock']}}</b><br><small>{{(p['stock']*p['nb'])|int}} b</small></td><td style='color:green'>{{p['pu'] - (p['cost_pc']/p['nb'])|int}}F<br>{{p['pc']-p['cost_pc']}}F</td><td>{% if p['stock']<=p['alert_stock'] %}<span class='badge badge-red'>FAIBLE</span>{% else %}<span class='badge badge-green'>OK</span>{% endif %}</td></tr>  
  {% endfor %}   
  </table></div></div> 
  """, prods=prods)
  
@app.route('/add_product', methods=['POST'])
def add_product(): 
  c = get_db()  
  try:      
     name = request.form.get('name','').strip()    
     c.execute('INSERT OR REPLACE INTO products (name,category,pu,pc,pc10,cost_pc,nb,stock,alert_stock,barcode,date) VALUES (?,?,?,?,?,?,?,?,?,?,?)',    
          (name, request.form.get('category','Bières'), int(request.form.get('pu',0)), int(request.form.get('pc',0)), int(request.form.get('pc10',0)),    
          int(request.form.get('cost_pc',0)), int(request.form.get('nb',24)), float(request.form.get('stock',0)), float(request.form.get('alert',2)), request.form.get('barcode',''), datetime.now().strftime('%Y-%m-%d')))      
     c.commit()  
   except Exception as e:    
      print(e)  
   c.close()  
   return redirect('/stock')

@app.route('/stock_entry', methods=['POST'])
def stock_entry():  
if 'user' not in session:    
return redirect('/login')  
name = request.form.get('entry_product','').split(' - ')[0].strip() 
qty = float(request.form.get('entry_qty',0))  
reason = request.form.get('entry_reason','Livraison fournisseur')  
c = get_db()  
before = c.execute('SELECT stock FROM products WHERE name=?', (name,)).fetchone()  
if before:    
   before_val = before[0]    
   after_val = before_val + qty   
   c.execute('UPDATE products SET stock=? WHERE name=?', (after_val, name))  
   c.execute('INSERT INTO stock_moves (product,type,qty,stock_before,stock_after,reason,date) VALUES (?,?,?,?,?,?,?)',          
        (name,'ENTREE',qty,before_val,after_val,reason,datetime.now().strftime('%Y-%m-%d %H:%M'))) 
   c.commit()  
c.close()  
return redirect('/stock')

@app.route('/stock_adjust', methods=['POST'])
def stock_adjust(): 
if 'user' not in session: 
return redirect('/login')  
name = request.form.get('adj_product','').split(' - ')[0].strip() 
new_stock = float(request.form.get('adj_stock',0))  
reason = request.form.get('adj_reason','Inventaire')  
c = get_db()  
before = c.execute('SELECT stock FROM products WHERE name=?', (name,)).fetchone()  
if before:    
before_val = before[0]    
c.execute('UPDATE products SET stock=? WHERE name=?', (new_stock, name))    
c.execute('INSERT INTO stock_moves (product,type,qty,stock_before,stock_after,reason,date) VALUES (?,?,?,?,?,?,?)',  
(name,'AJUSTEMENT',new_stock-before_val,before_val,new_stock,reason,datetime.now().strftime('%Y-%m-%d %H:%M')))    
c.commit()  
c.close()   
return redirect('/stock')

@app.route('/export_stock')
def export_stock():  
  if 'user' not in session:  
return redirect('/login')  
c = get_db() 
prods = c.execute('SELECT * FROM products ORDER BY name').fetchall()  
c.close()  
csv_content = "Nom,Categorie,Pu,Pc,Pc10,Cout_Casier,Nb,Stock_Casiers,Stock_Bouteilles,Valeur_Stock,Benef_Unite,Benef_Casier,Alert,Barcode\n"  
for p in prods:      
stock_bout = int(p['stock']*p['nb'])     
val_stock = int(p['stock']*p['cost_pc'])     
ben_u = int(p['pu'] - p['cost_pc']/p['nb'])   
ben_c = p['pc'] - p['cost_pc']      
csv_content += f"{p['name']},{p['category']},{p['pu']},{p['pc']},{p['pc10']},{p['cost_pc']},{p['nb']},{p['stock']},{stock_bout},{val_stock},{ben_u},{ben_c},{p['alert_stock']},{p['barcode']}\n" 
return Response(csv_content, mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=stock_berli_distribution_'+datetime.now().strftime('%Y%m%d')+'.csv'})

@app.route('/stock_moves')
def stock_moves():  
if 'user' not in session:   
return redirect('/login') 
c = get_db() 
moves = c.execute('SELECT * FROM stock_moves ORDER BY id DESC LIMIT 200').fetchall()  
c.close()  
return render_template_string(BASE_STYLE + '''  
<div class='top'><a href='/stock'>← Stock</a><b>Mouvements Stock</b><a href='/export_stock' style='text-decoration:none' class='btn btn-green' > Export Excel</a></div>  
<div class='card'><table><tr><th>Date</th><th>Produit</th><th>Type</th><th>Qté</th><th>Avant</th><th>Après</th><th>Raison</th></tr>
{% for m in moves %}<tr><td>{{m['date']}}</td><td><b>{{m['product']}}</b></td><td>{% if m['type']=='ENTREE' %}<span class='badge badge-green'>ENTRÉE</span>{% elif m['type']=='SORTIE' %}<span class='badge badge-red'>SORTIE</span>{% else %}<span class='badge badge-orange'>AJUST</span>{% endif %}</td><td>{{m['qty']}}</td><td>{{m['stock_before']}}</td><td>{{m['stock_after']}}</td><td>{{m['reason']}}</td></tr>{% endfor %} 
</table></div>  
''', moves=moves)
    
@app.route('/ventes')
def ventes(): 
  if 'user' not in session:    
    return redirect('/login')   
    c = get_db()  
    sales = c.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 150').fetchall()  
    c.close()  
    return render_template_string(BASE_STYLE + """  
    <div class='top'><a href='/accueil'>← Accueil</a><b>Journal Ventes</b><a href='/dashboard'>Dashboard</a></div>  
    <div class='card'><table><tr><th>Date</th><th>Produit Qté Type</th><th>Pu base/final</th><th>Total</th><th>Bénéf</th><th>Client/Paiement</th><th>Vendeur</th></tr>   
    {% for s in sales %}<tr><td><small>{{s['date']}} {{s['heure']}}</small></td><td><b>{{s['product']}}</b><br>{{s['qty']}} x {{s['nb']}}/c {{s['type']}}</td><td>{{s['pu_base']}} → <b>{{s['pu_final']}}</b></td><td><b>{{s['total']}}F</b></td><td style='color:green'>{{s['benefit']}}F</td><td>{% if s['client'] %}{{s['client']}}<br><span class='badge badge-orange'>{{s['payment_type']}}</span>{% else %}<span class='badge badge-green'>CASH</span>{% endif %}</td><td>{{s['seller']}}</td></tr>{% endfor %} 
    </table></div>    
    """, sales=sales)
@app.route('/logout')
def logout():  
  session.clear() 
return redirect('/login')
if __name__ == '__main__':  
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
