from flask import Flask, render_template, request, jsonify
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
DB = 'berli.db'
def init_db():
  con = sqlite3.connect(DB) 
  c = con.cursor()  
  c.execute('''CREATE TABLE IF NOT EXISTS produits      
         (id INTEGER PRIMARY KEY, nom TEXT UNIQUE, stock INTEGER, prix_achat INTEGER, prix_vente INTEGER)''') 
  c.execute('''CREATE TABLE IF NOT EXISTS ventes        
         (id INTEGER PRIMARY KEY, date TEXT, produit TEXT, qte INTEGER, total INTEGER, benefice INTEGER, client TEXT, type_paiement TEXT, reste INTEGER)''')  
  # Produits boissons exemple si vide  
  c.execute('SELECT COUNT(*) FROM produits')  
  if c.fetchone()[0]==0:     
    base = [('Coca 33cl', 100, 300, 500), ('Youki', 100, 200, 350), ('Beaufort', 50, 400, 600), ('Eau Vive', 100, 150, 250)]   
    c.executemany('INSERT INTO produits (nom,stock,prix_achat,prix_vente) VALUES (?,?,?,?,?)' if False else 'INSERT INTO produits (nom,stock,prix_achat,prix_vente) VALUES (?,?,?,?)', base) 
    con.commit() 
    con.close()
    
init_db()

@app.route('/')
def home(): 
  return render_template('index.html')
  
@app.route('/admin')
def admin():  
  return render_template('admin.html')
  
@app.route('/api/produits')
def get_produits():  
  con = sqlite3.connect(DB) 
  con.row_factory = sqlite3.Row  
  produits = [dict(r) for r in con.execute('SELECT * FROM produits').fetchall()]  
  con.close()  
  return jsonify(produits)
  
@app.route('/api/vendre', methods=['POST'])
def vendre():  
  d = request.json   
  nom = d['produit']  
  qte = int(d['qte'])  
  client = d.get('client','Client')  
  type_p = d.get('type','Cash')    
  con = sqlite3.connect(DB)  
  c = con.cursor()  
  c.execute('SELECT stock,prix_achat,prix_vente FROM produits WHERE nom=?', (nom,)) 
  row = c.fetchone() 
  if not row or row[0] < qte:    
    return jsonify({'error':'Stock insuffisant'}), 400  
    
    stock, pa, pv = row  
    total = pv * qte 
    benef = (pv - pa) * qte 
    reste = total if type_p=='Credit' else 0   
    c.execute('UPDATE produits SET stock=stock-? WHERE nom=?', (qte, nom))  
    c.execute('INSERT INTO ventes (date,produit,qte,total,benefice,client,type_paiement,reste) VALUES (?,?,?,?,?,?,?,?)',  
          (datetime.now().strftime('%Y-%m-%d %H:%M'), nom, qte, total, benef, client, type_p, reste))
    con.commit()  
    con.close() 
    return jsonify({'total':total,'benefice':benef,'ticket':f"BERLI - {nom} x{qte} = {total}F - Client: {client}"})
@app.route('/api/dashboard')
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
  con.close() 
  return jsonify({   
    'jour_ca': j[0] or 0, 'jour_benef': j[1] or 0,  
    'total_ca': t[0] or 0, 'total_benef': t[1] or 0,   
    'credits': credits  
  })
if __name__ == '__main__':  
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
