from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'berli_secret_2024_togo'
DB = 'berli.db'

USERS = {
  'patron': {'pass':'berli2024','role':'patron'},
  'caisse': {'pass':'caisse123','role':'caissier'},
  'stock':{'pass':'stock123','role':'stock'}
}
  
def init_db(): 
  con = sqlite3.connect(DB)   
  c = con.cursor()   
  c.execute('''CREATE TABLE IF NOT EXISTS produits    
         (id INTEGER PRIMARY KEY, nom TEXT UNIQUE, stock INTEGER, prix_achat INTEGER, prix_detail INTEGER, prix_gros INTEGER, qte_gros INTEGER)''')
  c.execute('''CREATE TABLE IF NOT EXISTS ventes            
         (id INTEGER PRIMARY KEY, date TEXT, produit TEXT, qte INTEGER, type_vente TEXT, total INTEGER, benefice INTEGER, client TEXT, type_paiement TEXT, reste INTEGER, remise INTEGER, vendeur TEXT)''')  
  c.execute('SELECT COUNT(*) FROM produits')  
  if c.fetchone()[0] == 0:  
    base = [      
      ('Coca 33cl', 120, 300, 500, 5500, 12),   
      ('Youki', 120, 200, 350, 3800, 12),        
      ('Beaufort 65cl', 60, 400, 600, 6800, 12),     
      ('Eau Vive 1.5L', 48, 150, 300, 3200, 12),     
    ]      
    c.executemany('INSERT INTO produits (nom,stock,prix_achat,prix_detail,prix_gros,qte_gros) VALUES (?,?,?,?,?,?)', base)  
  con.commit()  
  con.close()
  
init_db()

def login_required(f):  
  @wraps(f)  
  def dec(*args, **kwargs):    
    if 'user' not in session:   
      return redirect('/login')   
     return f(*args, **kwargs)  
    return dec
    
@app.route('/login', methods=['GET', 'POST'])
def login():  
  if request.method == 'POST': 
    u = request.form['user']     
    p = request.form['pass']
    if u in USERS and USERS[u]['pass'] == p: 
      session['user'] = u      
      session['role'] = USERS[u]['role']  
      return redirect('/admin')    
    return 'Mauvais identifiant'   
  return '''<html><body style="font-family:Arial;padding:30px;background:#f0f2f5">   
    <div style="background:#fff;padding:20px;border-radius:10px;max-width:350px;margin:auto;text-align:center">        
    <h2>BERLI DISTRIBUTION</h2><p>Connexion</p>      
    <form method="post"><input name="user" placeholder="Utilisateur" style="width:100%;padding:12px;margin:5px 0">     
    <input name="pass" type="password" placeholder="Mot de passe" style="width:100%;padding:12px;margin:5px 0">        
    <button style="width:100%;padding:12px;background:#0071bc;color:#fff;border:none;border-radius:8px">Entrer</button></form>  
    <p style="font-size:12px;margin-top:15px">patron / berli2024<br>caisse / caisse123<br>stock / stock123</p></div></body></html>'''
    
@app.route('/logout')
def logout():   
  session.clear() 
  return redirect('/login')
  
@app.route('/')
def home(): 
  return render_template('index.html')
  
@app.route('/admin')
@login_required
def admin(): 
  return render_template('admin.html', role=session['role'], user=session['user'])
  
@app.route('/api/me')
def me():  
  return jsonify({'user': session.get('user'), 'role': session.get('role')})
  
@app.route('/api/produits')
@login_required
def get_produits():   
  con = sqlite3.connect(DB)   
  con.row_factory = sqlite3.Row   
  rows = [dict(r) for r in con.execute('SELECT * FROM produits').fetchall()]   
  con.close()  
  if session['role'] == 'caissier':   
    for r in rows:       
      r['prix_achat'] = 0    
  return jsonify(rows)
  
@app.route('/api/ajout_stock', methods=['POST'])
@login_required
def ajout_stock():  
  if session['role'] not in ['patron', 'stock']:   
    return jsonify({'error': 'Non autorise'}), 403  
    d = request.json  
    con = sqlite3.connect(DB)  
    c = con.cursor() 
    c.execute('UPDATE produits SET stock=stock+? WHERE nom=?', (int(d['qte']), d['produit']))   
    con.commit()  
    con.close()  
    return jsonify({'ok': True})
@app.route('/api/vendre', methods=['POST'])
@login_required
def vendre():  
  if session['role'] not in ['patron', 'caissier']:  
    return jsonify({'error': 'Non autorise'}), 403   
  d = request.json  
  nom = d['produit']  
  qte = int(d['qte'])  
  type_v = d.get('type_vente', 'Detail') 
  remise = int(d.get('remise', 0))  
  client = d.get('client', 'Client')   
  type_p = d.get('type', 'Cash')   
  con = sqlite3.connect(DB)  
  c = con.cursor()  
  c.execute('SELECT stock,prix_achat,prix_detail,prix_gros,qte_gros FROM produits WHERE nom=?', (nom,)) 
  row = c.fetchone() 
  if not row:   
    return jsonify({'error': 'Produit inconnu'}), 400  
  stock, pa, pd, pg, qg = row 
  besoin = qte * qg if type_v == 'Gros' else qte  
  prix_u = pg if type_v == 'Gros' else pd   
  cout = pa * besoin  
  if stock < besoin:    
     return jsonify({'error': f'Stock insuffisant {stock}'}), 400 
  total_brut = prix_u * qte 
  total = total_brut - remise 
  benef = total - cout 
  reste = total if type_p == 'Credit' else 0  
  c.execute('UPDATE produits SET stock=stock-? WHERE nom=?', (besoin, nom))  
  c.execute('INSERT INTO ventes (date,produit,qte,type_vente,total,benefice,client,type_paiement,reste,remise,vendeur) VALUES (?,?,?,?,?,?,?,?,?,?,?)',    
        (datetime.now().strftime('%Y-%m-%d %H:%M'), f"{nom} {type_v} x{qte}", qte, type_v, total, benef, client, type_p, reste, remise, session['user']))  
  con.commit()  
  con.close() 
  return jsonify({'total': total, 'benefice': benef, 'ticket': f"BERLI - {nom} {type_v} x{qte} = {total}F - {client} par {session['user']}"})
  
@app.route('/api/dashboard')
@login_required
def dashboard(): 
  con = sqlite3.connect(DB)  
  c = con.cursor()   
  today = datetime.now().strftime('%Y-%m-%d') 
  c.execute("SELECT SUM(total), SUM(benefice) FROM ventes WHERE date LIKE ?", (f'{today}%',)) 
  j = c.fetchone() 
  c.execute("SELECT SUM(total), SUM(benefice) FROM ventes") 
  t = c.fetchone()   
  c.execute("SELECT client, SUM(reste) FROM ventes WHERE reste>0 GROUP BY client")  
  credits = c.fetchall()    
  c.execute("SELECT vendeur, SUM(total) FROM ventes GROUP BY vendeur") 
  par_vendeur = c.fetchall()  
  con.close()  
  if session['role'] != 'patron':    
     return jsonify({'jour_ca': j[0] or 0, 'jour_benef': 0, 'total_ca': t[0] or 0, 'total_benef': 0, 'credits': credits, 'par_vendeur': par_vendeur})  
  return jsonify({'jour_ca': j[0] or 0, 'jour_benef': j[1] or 0, 'total_ca': t[0] or 0, 'total_benef': t[1] or 0, 'credits': credits, 'par_vendeur': par_vendeur})
  
if __name__ == '__main__': 
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
