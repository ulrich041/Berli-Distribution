from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'berli_credit_final_2026'
DB = 'berli.db'
USERS = {'patron':{'pass':'berli2024','role':'patron','name':'URLICH'},'caisse':{'pass':'caisse123','role':'caissier','name':'CAISSE'},'stock':{'pass':'stock123','role':'stock','name':'STOCK'}}

def get_db():  
  c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():  
  c=get_db() 
  c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INTEGER, pc INTEGER, pc10 INTEGER, cost_pc INTEGER, nb INTEGER, stock REAL)')   
  c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT, client TEXT DEFAULT "")')  
  c.execute('CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, client TEXT, total INTEGER, paid INTEGER DEFAULT 0, remaining INTEGER, date TEXT, phone TEXT)')   
  c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, debt_id INTEGER, amount INTEGER, date TEXT)') 
  c.commit(); c.close()
init_db()

LOGIN_HTML = """
<meta name='viewport' content='width=device-width,initial-scale=1'><style>body{margin:0;height:100vh;display:flex;justify-content:center;align-items:center;background:linear-gradient(135deg,#0f172a,#1e3a8a);font-family:Arial}.card{background:#e6e8ec;width:90%;max-width:380px;border-radius:35px;padding:35px 30px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.4)}.inp{width:100%;background:#cbd0d8;border:none;border-radius:25px;padding:16px 20px;font-size:14px;box-sizing:border-box;margin-bottom:12px;outline:none;font-weight:bold}.btn{width:100%;background:#0f172a;color:white;border:none;border-radius:25px;padding:16px;font-weight:bold;cursor:pointer}</style>
<div class='card'><div style='font-size:40px'> </div><h1>Berli Soft</h1><div style='font-size:10px;letter-spacing:3px;color:#666;font-weight:bold;margin-bottom:20px'>AUTHENTIFICATION CHIFFRÉE</div><form method='POST'><input class='inp' name='user' placeholder='NOM D UTILISATEUR' required><input class='inp' type='password' name='pass' placeholder='MOT DE PASSE' required><button class='btn'>ENTRER DANS L'ESPACE ></button></form></div>
"""

@app.route('/')
def home(): return redirect('/login')
@app.route('/login', methods=['GET','POST'])
def login():  
    if request.method=='POST':    
        u=request.form.get('user','').strip().lower(); pw=request.form.get('pass','').strip()     
        if u in USERS and USERS[u]['pass']==pw:       
            session['user']=u; session['name']=USERS[u]['name']; session['cart']=[]; return redirect('/accueil')   
        return render_template_string(LOGIN_HTML+"<p style='color:red'>Erreur</p>")  
       return render_template_string(LOGIN_HTML)

@app.route('/accueil')
def accueil():  
    if 'user' not in session: return redirect('/login')  
    conn=get_db()  
    total_debt=conn.execute('SELECT COALESCE(SUM(remaining),0) FROM debts WHERE remaining>0').fetchone()[0] 
    conn.close()  
    return render_template_string(""" 
    <meta name='viewport' content='width=device-width,initial-scale=1'><style>body{font-family:Arial;background:#f8fafc;margin:0}.top{background:white;padding:15px 20px;font-weight:bold;border-bottom:1px solid #eee}.banner{background:linear-gradient(90deg,#0f172a,#1e293b);color:white;margin:15px;border-radius:18px;padding:20px 25px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 15px 15px}.tile{background:white;border-radius:16px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,0.08);text-decoration:none;color:#111;display:block}.icon{width:42px;height:42px;border-radius:12px;display:flex;justify-content:center;align-items:center;font-size:20px;margin-bottom:10px;color:white}.c1{background:#14b8a6}.c2{background:#22c55e}.c3{background:#38bdf8}.c4{background:#60a5fa}.c5{background:#fb923c}.c6{background:#a78bfa}.c7{background:#34d399}.c8{background:#f87171}</style>  
    <div class='top'>Accueil <span style='float:right'><a href='/logout' style='text-decoration:none'>Déconnexion</a> - {{total_debt}}F à encaisser</span></div>  
    <div class='banner'><small>SYSTÈME INTELLIGENT</small><h2>Bonjour, {{name}}</h2><p>Prêt pour une nouvelle journée chez Berli Soft ?</p></div>  
    <div class='grid'>  
    <a href='/dashboard' class='tile'><div class='icon c1'> </div><b>Dashboard</b><br><small>Vue d'ensemble</small></a>  
    <a href='/caisse' class='tile'><div class='icon c2'> </div><b>Caisse</b><br><small>Vente + Crédit</small></a>  
    <a href='/stock' class='tile'><div class='icon c3'> </div><b>Stock</b><br><small>Nb 12/20/24</small></a> 
    <a href='/ventes' class='tile'><div class='icon c4'> </div><b>Ventes</b><br><small>Historique</small></a>   
    <a href='/dettes' class='tile' style='border:2px solid #fb923c'><div class='icon c5'> </div><b>Dettes - {{total_debt}}F</b><br><small>Gérer les crédits</small></a>   
    <a href='/clients' class='tile'><div class='icon c6'> </div><b>Clients</b><br><small>Base clients crédit</small></a>  
    <a href='/ventes' class='tile'><div class='icon c7'> </div><b>Journal</b><br><small>Financier global</small></a>  
    <a href='/stock' class='tile'><div class='icon c8'> </div><b>Stock Faible</b><br><small>Ruptures</small></a> 
    </div> 
    """, name=session.get('name','URLICH'), total_debt=total_debt)

@app.route('/dashboard')
def dashboard():  
    if 'user' not in session: return redirect('/login')   
    conn=get_db(); today=datetime.now().strftime('%Y-%m-%d')  
    ts_today=conn.execute('SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?',(today+'%',)).fetchone()[0]  
    tb_today=conn.execute('SELECT COALESCE(SUM(benefit),0) FROM sales WHERE date LIKE ?',(today+'%',)).fetchone()[0]  
    ts_all=conn.execute('SELECT COALESCE(SUM(total),0) FROM sales').fetchone()[0] 
    tb_all=conn.execute('SELECT COALESCE(SUM(benefit),0) FROM sales').fetchone()[0]  
    total_debt=conn.execute('SELECT COALESCE(SUM(remaining),0) FROM debts WHERE remaining>0').fetchone()[0]  
    low=conn.execute('SELECT COUNT(*) FROM products WHERE stock < 2').fetchone()[0] 
    prods=conn.execute('SELECT * FROM products').fetchall(); conn.close() 
    return render_template_string("""  
    <meta name='viewport' content='width=device-width,initial-scale=1'><style>body{font-family:Arial;background:#f8fafc;margin:0}.top{background:white;padding:12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;font-weight:bold}.card{background:white;margin:12px;padding:15px;border-radius:12px}.section-title{font-size:12px;font-weight:bold;border-left:4px solid #0ea5e9;padding-left:8px;margin:20px 12px 10px}.focus{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media(min-width:600px){.focus{grid-template-columns:1fr 1fr 1fr 1fr 1fr}}.f-card{background:white;border-radius:12px;padding:12px;text-align:center}.f-icon{width:36px;height:36px;border-radius:8px;display:flex;justify-content:center;align-items:center;margin:0 auto 8px auto;color:white}.perf{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.p-card{background:white;border-radius:12px;padding:15px}</style>   
    <div class='top'><a href='/accueil' style='text-decoration:none'>⬅ Accueil</a> Dashboard <a href='/dettes' style='color:orange'>Dettes {{total_debt}}F</a></div>  
    <div class='card'><b>Tableau de Bord</b><br><small>Aperçu global - Berli Dekon</small></div> 
    <div class='section-title'>FOCUS AUJOURD'HUI</div><div style='padding:0 12px'><div class='focus'>    
    <div class='f-card'><div class='f-icon' style='background:#0f172a'> </div><small style='font-size:10px'>VENTES JOUR</small><div style='font-weight:bold'>{{ts_today}}F
    </div></div>  
    <div class='f-card'><div class='f-icon' style='background:#14b8a6'> </div><small style='font-size:10px'>BÉNÉF JOUR</small><div style='font-weight:bold'>{{tb_today}}F</div></div>   
    <div class='f-card'><div class='f-icon' style='background:#fb923c'> </div><small style='font-size:10px'>CRÉDITS À ENCAISSER</small><div style='font-weight:bold;color:orange'>{{total_debt}}F</div></div>     
    <div class='f-card'><div class='f-icon' style='background:#f87171'> </div><small style='font-size:10px'>STOCK FAIBLE</small><div style='font-weight:bold'>{{low}}</div></div>    
    <div class='f-card'><div class='f-icon' style='background:#334155'> </div><small style='font-size:10px'>PRODUITS</small><div style='font-weight:bold'>{{prods|length}}</div></div>   
    </div></div>  
    <div class='section-title'>PERFORMANCE ANALYTIQUE</div><div style='padding:0 12px'><div class='perf'>  
    <div class='p-card'><small>C.A TOTAL</small><div style='font-weight:bold;font-size:18px'>{{ts_all}}F</div></div>    
    <div class='p-card'><small>BÉNÉFICE TOTAL</small><div style='font-weight:bold;font-size:18px'>{{tb_all}}F</div></div>   
    <div class='p-card' style='border:2px solid orange'><small>CRÉDITS RESTANTS</small><div style='font-weight:bold;font-size:18px;color:orange'>{{total_debt}}F</div><a href='/dettes' style='font-size:12px'>Voir dettes ></a></div>  
    </div></div>    
    """, ts_today=ts_today, tb_today=tb_today, ts_all=ts_all, tb_all=tb_all, total_debt=total_debt, low=low, prods=prods)

@app.route('/caisse')
def caisse():  
  if 'user' not in session: return redirect('/login') 
  conn=get_db(); prods=conn.execute('SELECT * FROM products').fetchall(); conn.close()   
  cart=session.get('cart',[]); tot=sum([c['total'] for c in cart])  
  return render_template_string(""" 
  <meta name='viewport' content='width=device-width,initial-scale=1'><style>body{font-family:Arial;background:#f8fafc;margin:0}.top{background:white;padding:12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between}.card{background:white;margin:12px;padding:15px;border-radius:12px}label{font-weight:bold;font-size:11px;display:block;margin-top:10px}input,select{width:100%;padding:14px;font-size:16px;border-radius:10px;border:1px solid #ccc;margin-top:4px;box-sizing:border-box}.btn{padding:14px;color:white;border:none;border-radius:10px;width:100%;margin-top:10px;font-size:16px}.credit-box{background:#fff7ed;border:2px solid #fb923c;border-radius:10px;padding:12px;margin-top:12px}</style>   
  <div class='top'><a href='/accueil'>⬅ Accueil</a><b>Caisse - Vente</b><a href='/dettes'>Dettes</a></div>  
  <div class='card'><h3>Panier - Pu Pc Pc10 Nb Sto</h3><form method='POST' action='/add_to_cart'><label>Produit</label><select name='product'>{% for p in prods %}<option>{{p['name']}} - {{p['nb']}}/c - Stock:{{p['stock']}}</option>{% endfor %}</select><label>Type</label><select name='type'><option value='unite'>Unité Pu</option><option value='casier'>Casier Pc</option><option value='casier10'>Casier 10+ Pc10</option></select><label>Quantité</label><input type='number' step='0.1' name='qty' value='1'><label>Prix final (vide = normal)</label><input type='number' name='prix_final' placeholder='7000'><button class='btn' style='background:#16a34a'>+ Ajouter au panier</button></form> 
  {% if cart %}<table style='width:100%;margin-top:15px'>{% for c in cart %}<tr><td>{{c['product']}} x{{c['qty']}}</td><td>{{c['total']}}F</td><td><a href='/remove_cart/{{loop.index0}}'>X</a></td></tr>{% endfor %}</table><div style='background:green;color:white;padding:12px;border-radius:8px;text-align:center;font-size:20px;margin-top:10px'>TOTAL {{tot}}F</div>  
  <form method='POST' action='/validate_cart'><div class='credit-box'><label style='font-size:14px'><input type='checkbox' name='is_credit' value='1' onchange='document.getElementById("clientbox").style.display=this.checked?"block":"none"'> VENDRE À CRÉDIT</label><div id='clientbox' style='display:none'><label>Nom du client</label><input name='client_name' placeholder='Ex: Maman Akuwa'><label>Téléphone</label><input name='client_phone' placeholder='90...'><small style='color:#666'>Ce montant ira dans Dettes</small></div></div><button class='btn' style='background:green;margin-top:12px'> VALIDER VENTE</button></form>  
  <form method='POST' action='/validate_cart' style='margin-top:8px'><input type='hidden' name='is_credit' value='0'><button class='btn' style='background:#111'> VENTE COMPTANT</button></form>  
  <a href='/clear_cart' style='color:red'>Vider panier</a>{% endif %}</div>   
  """, prods=prods, cart=cart, tot=tot)

@app.route('/dettes')
def dettes():
  if 'user' not in session: return redirect('/login') 
  conn=get_db(); debts=conn.execute('SELECT * FROM debts ORDER BY remaining DESC').fetchall(); conn.close()   
  return render_template_string("""  
  <meta name='viewport' content='width=device-width,initial-scale=1'><style>body{font-family:Arial;background:#f8fafc;margin:0}.top{background:white;padding:12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between}.card{background:white;margin:12px;padding:15px;border-radius:12px}input{padding:12px;border-radius:8px;border:1px solid #ccc;width:70%}.btn{padding:10px 14px;background:#fb923c;color:white;border:none;border-radius:8px}</style> 
  <div class='top'><a href='/accueil'>⬅ Accueil</a><b>Dettes - Règlement Crédit</b><a href='/caisse'>Caisse</a></div>
  {% for d in debts %}{% if d['remaining']>0 %}<div class='card' style='border-left:5px solid {% if d["remaining"]>0 %}orange{% else %}green{% endif %}'><b>{{d['client']}}</b> - {{d['phone']}}<br><small>{{d['date']}}</small><br><br>Total: <b>{{d['total']}}F</b> | Payé: {{d['paid']}}F | <b style='color:orange'>Reste: {{d['remaining']}}F</b><br><br><form method='POST'       action='/pay_debt/{{d["id"]}}' style='display:flex;gap:8px'><input type='number' name='amount' placeholder='Montant payé' max='{{d["remaining"]}}' required><button class='btn'> Régler</button></form>{% if d['remaining']==0 %}<span style='color:green;font-weight:bold'> SOLDÉ</span>{% endif %}</div>{% endif %}{% endfor %}  
  {% if not debts %}<div class='card'>Aucune dette</div>{% endif %}   
  <div class='card'><h4>Toutes les dettes (même soldées)</h4>{% for d in debts %}{{d['client']}} - {{d['total']}}F - Reste {{d['remaining']}}F - {{d['date']}}<br>{% endfor %}</div>    
  """, debts=debts)

@app.route('/pay_debt/<int:debt_id>', methods=['POST'])
def pay_debt(debt_id):  
  if 'user' not in session: return redirect('/login')  
  amount=int(request.form.get('amount',0))  
  conn=get_db()  
  d=conn.execute('SELECT * FROM debts WHERE id=?',(debt_id,)).fetchone()   
  if d and amount>0 and amount<=d['remaining']:     
     new_paid=d['paid']+amount; new_rem=d['remaining']-amount     
     conn.execute('UPDATE debts SET paid=?, remaining=? WHERE id=?',(new_paid,new_rem,debt_id))   
     conn.execute('INSERT INTO payments (debt_id,amount,date) VALUES (?,?,?)',(debt_id,amount,datetime.now().strftime('%Y-%m-%d %H:%M')))   
     conn.commit()  
   conn.close(); return redirect('/dettes')

@app.route('/clients')
def clients():  
  if 'user' not in session: return redirect('/login')   
  conn=get_db(); clients=conn.execute('SELECT client, SUM(total) as total, SUM(remaining) as reste, phone FROM debts GROUP BY client ORDER BY reste DESC').fetchall(); conn.close()   
  return render_template_string(""" 
  <meta name='viewport' content='width=device-width,initial-scale=1'><div style='padding:15px;font-family:Arial'><a href='/accueil'>⬅ Accueil</a> | <a href='/dettes'>Dettes</a><h3>Clients à crédit</h3>{% for c in clients %}<div style='background:white;padding:12px;border-radius:10px;margin-bottom:8px'><b>{{c['client']}}</b> {{c['phone']}}<br>Total crédits: {{c['total']}}F | Reste à payer: <b style='color:orange'>{{c['reste']}}F</b></div>{% endfor %}</div>   
  """, clients=clients)

@app.route('/stock')
def stock_page():  
    if 'user' not in session: return redirect('/login')   
    conn=get_db(); prods=conn.execute('SELECT * FROM products').fetchall(); conn.close()   
    return render_template_string("""   
    <meta name='viewport' content='width=device-width,initial-scale=1'><style>body{font-family:Arial;background:#f8fafc;margin:0}.top{background:white;padding:12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between}.card{background:white;margin:12px;padding:15px;border-radius:12px}label{font-size:11px;font-weight:bold;display:block;margin-top:8px}input{width:100%;padding:12px;border-radius:8px;border:1px solid #ccc;box-sizing:border-box;margin-top:3px}.row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}.btn{padding:12px;background:#111;color:white;border:none;border-radius:8px;width:100%;margin-top:10px}</style>   
    <div class='top'><a href='/accueil'>⬅</a><b>Stock</b><a href='/dashboard'>Dash</a></div>  
    <div class='card'><form method='POST' action='/add_product'><label>Nom Produit</label><input name='name' required><div class='row'><div><label>Pu Prix Bouteille</label><input name='pu' type='number' required></div><div><label>Pc Prix Casier</label><input name='pc' type='number' required></div><div><label>Pc10 Prix Gros</label><input name='pc10' type='number' required></div></div><div class='row'><div><label>Achat Prix Achat Casier</label><input name='cost_pc' type='number' required></div><div><label>Nb / Casier</label><input name='nb' type='number' value='24' required></div><div><label>Sto Stock</label><input name='stock' type='number' step='0.1' required></div></div><button class='btn'>Ajouter</button></form></div>   
    """, prods=prods)

@app.route('/ventes')
def ventes():   
  if 'user' not in session: return redirect('/login')  
  conn=get_db(); sales=conn.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 100').fetchall(); conn.close()
  return render_template_string("<meta name='viewport' content='width=device-width,initial-scale=1'><div style='padding:15px;font-family:Arial'><a href='/accueil'>⬅ Accueil</a> | <a href='/dashboard'>Dashboard</a><h3>Journal - Historique Financier Global</h3>{% for s in sales %}{{s['date']}} - {{s['product']}} {{s['qty']}} {{s['type']}} - {{s['total']}}F {% if s['client'] %} - Client: {{s['client']}} (Crédit){% endif %}<br>{% endfor %}</div>", sales=sales)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():   
  if 'user' not in session: return redirect('/login')   
  raw=request.form.get('product',''); name=raw.split(' - ')[0].strip()  
  type_v=request.form.get('type'); qty=float(request.form.get('qty',1))  
  conn=get_db(); p=conn.execute('SELECT * FROM products WHERE name=?',(name ,)).fetchone(); conn.close()  
  if p:   
     base=p['pu'] if type_v=='unite' else (p['pc'] if type_v=='casier' else p['pc10'])     
     pu_final=int(request.form.get('prix_final') or base); total=int(pu_final*qty)     
     cart=session.get('cart',[]); cart.append({'product':name,'qty':qty,'type':type_v,'pu_final':pu_final,'total':total,'nb':p['nb'],'cost_pc':p['cost_pc']}); session['cart']=cart  
      return redirect('/caisse')
@app.route('/remove_cart/<int:i>')
def remove_cart(i):  
   cart=session.get('cart',[]); 
   if 0 <= i < len(cart): cart.pop(i); session['cart']=cart  
   return redirect('/caisse')
@app.route('/clear_cart')
def clear_cart(): session['cart']=[]; return redirect('/caisse')
    
@app.route('/validate_cart', methods=['POST'])
def validate_cart():  
  if 'user' not in session: return redirect('/login')  
  cart=session.get('cart',[]); 
  if not cart: return redirect('/caisse')   
  is_credit=request.form.get('is_credit')=='1' 
  client_name=request.form.get('client_name','').strip().upper()   
  client_phone=request.form.get('client_phone','').strip() 
  total_cart=sum([c['total'] for c in cart]) 
  conn=get_db()  
  if is_credit and client_name:    
    conn.execute('INSERT INTO debts (client,total,paid,remaining,date,phone) VALUES (?,?,?,?,?,?)',(client_name,total_cart,0,total_cart,datetime.now().strftime('%Y-%m-%d %H:%M'),client_phone))   
    for c in cart:        
      benefit=(c['pu_final']-c['cost_pc']/c['nb'])*c['qty'] if c['type']=='unite' else (c['pu_final']-c['cost_pc'])*c['qty']      
      deduit=c['qty']/c['nb'] if c['type']=='unite' else c['qty']      
      conn.execute('UPDATE products SET stock=stock-? WHERE name=?',(deduit,c['product']))   
      conn.execute('INSERT INTO sales (product,qty,type,pu_final,total,benefit,seller,date,client) VALUES (?,?,?,?,?,?,?,?,?)',(c['product'],c['qty'],c['type'],c['pu_final'],c['total'],int(benefit),session['user'],datetime.now().strftime('%Y-%m-%d %H:%M'),client_name)) 
else:     
for c in cart:      
  benefit=(c['pu_final']-c['cost_pc']/c['nb'])*c['qty'] if c['type']=='unite' else (c['pu_final']-c['cost_pc'])*c['qty']       
  deduit=c['qty']/c['nb'] if c['type']=='unite' else c['qty']        
  conn.execute('UPDATE products SET stock=stock-? WHERE name=?',(deduit,c['product']))      
  conn.execute('INSERT INTO sales (product,qty,type,pu_final,total,benefit,seller,date) VALUES (?,?,?,?,?,?,?,?)',(c['product'],c['qty'],c['type'],c['pu_final'],c['total'],int(benefit),session['user'],datetime.now().strftime('%Y-%m-%d %H:%M')))  
conn.commit(); conn.close(); session['cart']=[]; 
return redirect('/dettes' if is_credit else '/dashboard')

@app.route('/add_product', methods=['POST'])
def add_product():  
  conn=get_db()
  try: conn.execute('INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (?,?,?,?,?,?,?)',(request.form.get('name').strip(),int(request.form.get('pu',0)),int(request.form.get('pc',0)),int(request.form.get('pc10',0)),int(request.form.get('cost_pc',0)),int(request.form.get('nb',24)),float(request.form.get('stock',0)))); conn.commit()  
  except: pass  
  conn.close(); return redirect('/stock')
@app.route('/logout')
def logout(): session.clear(); return redirect('/login')
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
