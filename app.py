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
