from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'berli_final_100'
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
    # Table finale avec tout ce que tu as demandé  
conn.execute('''CREATE TABLE IF NOT EXISTS products (   
    id INTEGER PRIMARY KEY,      
    name TEXT UNIQUE,      
    pu INTEGER,      
    pc INTEGER,      
    pc10 INTEGER,       
    cost_pc INTEGER,       
    nb INTEGER,       
    stock REAL)''')  
conn.execute('''CREATE TABLE IF NOT EXISTS sales (   
    id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT,     
    pu_final INTEGER, total INTEGER, benefit INTEGER, seller TEXT, date TEXT)''')  
conn.commit()  
conn.close()
init_db()

@app.route('/')
def home():  
    conn=get_db(); prods=conn.execute('SELECT * FROM products ORDER BY name').fetchall(); conn.close()  
    return render_template_string(""" 
    <meta name='viewport' content='width=device-width,initial-scale=1'>  
    <style>body{font-family:sans-serif;margin:0;background:#f5f5f5}.h{background:black;color:white;padding:15px;text-align:center}.g{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px}.c{background:white;padding:10px;border-radius:10px;text-align:center;font-size:13px}.b{background:#25D366;color:white;border:none;padding:7px;border-radius:5px;width:100%}</style>  
    <div class='h'><b>BERLI DISTRIBUTION</b><br>Commande: 92424510</div>   
    <div class='g'>{% for p in prods %}<div class='c'><b>{{p['name']}}</b><br>Unité: {{p['pu']}}F<br>Casier {{p['nb']}}: {{p['pc']}}F<br>10+ : {{p['pc10']}}F<br>Stock: {{p['stock']}} casiers<br><button class='b' onclick="window.open('https://wa.me/22892424510?text=Bonjour Berli, je veux {{p['name']}}','_blank')">Commander</button></div>{% endfor %}</div>  
    {% if not prods %}<p style='text-align:center'>Aucun produit. Connecte-toi en patron pour ajouter.</p>{% endif %}   
    <div style='text-align:center;padding:20px'><a href='/login' style='background:black;color:white;padding:12px 25px;border-radius:20px;text-decoration:none'>Espace Staff</a></div> 
    """, prods=prods)
    
@app.route('/login', methods=['GET','POST'])
def login():   
    if request.method=='POST':    
        u=request.form.get('user','').strip(); pw=request.form.get('pass','').strip()    
        if u in USERS and USERS[u]['pass']==pw:     
            session['user']=u; session['role']=USERS[u]['role']; return redirect('/dashboard')    
            return "Mauvais mot de passe <a href='/login'>Retour</a>"  
            return render_template_string("<h2 style='text-align:center;margin-top:40px'>Connexion BERLI</h2><form method='POST' style='max-width:300px;margin:20px auto'><input name='user' placeholder='patron / caisse / stock' style='width:100%;padding:12px'><br><br><input name='pass' type='password' placeholder='Mot de passe' style='width:100%;padding:12px'><br><br><button style='width:100%;padding:12px;background:black;color:white'>Entrer</button></form>")

@app.route('/dashboard')
def dashboard(): 
    if 'user' not in session: return redirect('/login') 
    conn=get_db(); prods=conn.execute('SELECT * FROM products ORDER BY name').fetchall(); sales=conn.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 50').fetchall()  
    today=datetime.now().strftime('%Y-%m-%d'); ts=conn.execute('SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?', (today+'%',)).fetchone()[0]; tb=conn.execute('SELECT COALESCE(SUM(benefit),0) FROM sales WHERE date LIKE ?', (today+'%',)).fetchone()[0]; conn.close()
    return render_template_string(""" 
    <style>body{font-family:sans-serif;background:#eee;margin:0;font-size:13px}.nav{background:black;color:white;padding:10px;display:flex;justify-content:space-between}.card{background:white;margin:8px;padding:12px;border-radius:8px}table{width:100%;border-collapse:collapse}td,th{border:1px solid #ddd;padding:5px}input,select{padding:7px;margin:2px} .btn{padding:7px 10px;background:black;color:white;border:none;border-radius:4px}</style> 
    <div class='nav'><b>BERLI - {{role}} ({{user}})</b><a href='/logout' style='color:white'>Quitter</a></div> 
    <div class='card'><b>Aujourd'hui:</b> Ventes {{ts}} F | Bénéfice <span style='color:green'>{{tb}} F</span></div>
    
    <div class='card'><h3>1. Vendre</h3>   
    <form method='POST' action='/sell'>  
    <select name='product' required style='width:170px'>{% for p in prods %}<option value='{{p["name"]}}'>{{p['name']}} ({{p['nb']}}/casier)</option>{% endfor %}</select>  
    <select name='type'><option value='unite'>Unité</option><option value='casier'>Casier 1-9</option><option value='casier10'>Casier 10+</option></select>  
    <input type='number' step='0.1' name='qty' value='1' min='0.1' style='width:55px' placeholder='Qte'>   
    <input type='number' name='prix_final' placeholder='Remise? Prix final' style='width:110px'>  
    <button class='btn'>Encaisser</button>  
    </form>   
    <small>Ex: Coca 10 casiers -> Type: Casier 10+ -> Qte 10. Si tu veux faire 5700 au lieu de 5800, tape 5700 dans Remise.</small> 
    </div>
    
    {% if role in ['patron','stock'] %} 
    <div class='card'><h3>2. AJOUTER UN NOUVEL ARTICLE (Toi-même)</h3>
    <form method='POST' action='/add_product' style='display:flex;flex-wrap:wrap;gap:5px'> 
    <input name='name' placeholder='Nom article (ex: Coca)' required style='width:120px'>   
    <input name='pu' type='number' placeholder='Vente unité' required style='width:80px'>  
    <input name='pc' type='number' placeholder='Vente casier 1-9' required style='width:100px'>  
    <input name='pc10' type='number' placeholder='Vente 10+ casiers' required style='width:100px'> 
    <input name='cost_pc' type='number' placeholder='Achat casier' required style='width:90px'>  
    <input name='nb' type='number' placeholder='Nb/b casier (12,20,24)' required style='width:90px'>  
    <input name='stock' type='number' step='0.1' placeholder='Stock casiers' required style='width:80px'>   
    <button class='btn' style='background:green'>+ AJOUTER</button>  
    </form>   
    </div>
    <div class='card'><h3>3. MODIFIER TES PRIX (Clique et change)</h3>  
    <table><tr><th>Article</th><th>Unité</th><th>Casier</th><th>10+</th><th>Achat</th><th>Nb/casier</th><th>Stock</th><th></th></tr>  
    {% for p in prods %}<tr><form method='POST' action='/edit_product'>  
    <td>{{p['name']}}<input type='hidden' name='id' value='{{p["id"]}}'></td> 
    <td><input type='number' name='pu' value='{{p["pu"]}}' style='width:55px'></td>  
    <td><input type='number' name='pc' value='{{p["pc"]}}' style='width:65px'></td>  
    <td><input type='number' name='pc10' value='{{p["pc10"]}}' style='width:65px'></td>   
    <td><input type='number' name='cost_pc' value='{{p["cost_pc"]}}' style='width:65px'></td>  
    <td><input type='number' name='nb' value='{{p["nb"]}}' style='width:45px'></td> 
    <td><input type='number' step='0.1' name='stock' value='{{p["stock"]}}' style='width:50px'></td> 
    <td><button style='background:green;color:white;border:none;padding:5px;border-radius:3px'>Sauver</button> <a href='/delete/{{p["id"]}}' style='color:red;text-decoration:none'> X</a></td>   
    </form></tr>{% endfor %}</table>  
    </div>  
    {% endif %}
    
    <div class='card'><h3>Ventes</h3><table><tr><th>Date</th><th>Art</th><th>Type</th><th>Qte</th><th>P.U</th><th>Total</th><th>Bénéf</th></tr>{% foUse Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
r s in sales %}<tr><td>{{s['date'][5:]}}</td><td>{{s['product']}}</td><td>{{s['type']}}</td><td>{{s['qty']}}</td><td>{{s['pu_final']}}</td><td>{{s['total']}}</td><td style='color:green'>{{s['benefit']}}</td></tr>{% endfor %}</table></div>  
     """, prods=prods, sales=sales, user=session['user'], role=session['role'], ts=ts, tb=tb)
@app.route('/sell', methods=['POST'])
def sell():  
    if 'user' not in session: return redirect('/login') 
    name=request.form.get('product'); type_v=request.form.get('type'); qty=float(request.form.get('qty',1))
    prix_final_raw=request.form.get('prix_final')  
    conn=get_db(); p=conn.execute('SELECT * FROM products WHERE name=?',(name,)).fetchone() 
    if p:   
        base = p['pu'] if type_v=='unite' else (p['pc'] if type_v=='casier' else p['pc10'])    
        pu_final=int(prix_final_raw) if prix_final_raw else base  
        total=int(pu_final*qty)    
        # Bénéfice     
        if type_v=='unite': benefit = (pu_final - p['cost_pc']/p['nb'])*qty   
        else: benefit = (pu_final - p['cost_pc'])*qty   
        # Stock: si unité, on retire fraction de casier     
        if type_v=='unite': deduit = qty / p['nb']     
        else: deduit = qty    
        conn.execute('UPDATE products SET stock=stock-? WHERE name=?',(deduit,name))    
        conn.execute('INSERT INTO sales (product,qty,type,pu_final,total,benefit,seller,date) VALUES (?,?,?,?,?,?,?,?)',(name,qty,type_v,pu_final,total,int(benefit),session['user'],datetime.now().strftime('%Y-%m-%d %H:%M')))    
        conn.commit()  
    conn.close(); return redirect('/dashboard')

@app.route('/add_product', methods=['POST'])
def add_product():  
    if 'user' not in session or session['role'] not in ['patron','stock']: return redirect('/login') 
    conn=get_db()   
    try:    
        conn.execute('INSERT INTO products (name,pu,pc,pc10,cost_pc,nb,stock) VALUES (?,?,?,?,?,?,?)',  
        (request.form.get('name').strip(), int(request.form.get('pu',0)), int(request.form.get('pc',0)), int(request.form.get('pc10',0)), int(request.form.get('cost_pc',0)), int(request.form.get('nb',24)), float(request.form.get('stock',0))))   
        conn.commit()  
    except Exception as e: print(e)  
    conn.close(); return redirect('/dashboard')
@app.route('/edit_product', methods=['POST'])
def edit_product():  
    if 'user' not in session: return redirect('/login') 
    conn=get_db()   
    conn.execute('UPDATE products SET pu=?, pc=?, pc10=?, cost_pc=?, nb=?, stock=? WHERE id=?',  
    (int(request.form.get('pu',0)), int(request.form.get('pc',0)), int(request.form.get('pc10',0)), int(request.form.get('cost_pc',0)), int(request.form.get('nb',24)), float(request.form.get('stock',0)), request.form.get('id')))  
    conn.commit(); conn.close(); return redirect('/dashboard')
    
@app.route('/delete/<int:pid>')
def delete(pid):  
    if 'user' not in session or session['role']!='patron': return redirect('/login')  
    conn=get_db(); conn.execute('DELETE FROM products WHERE id=?',(pid,)); conn.commit(); conn.close(); return redirect('/dashboard')
    
@app.route('/logout')
def logout(): 
    session.clear(); return redirect('/login')
    
if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
