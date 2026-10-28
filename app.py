from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'berli-facture-a4-final'
import sqlite3
def get_db():
    conn = sqlite3.connect('berli.db')
    conn.row_factory = sqlite3.Row
    return conn
def q(sql, args=(), f=False):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, args)
    r = cur.fetchall() if f else None
    if not f:
        conn.commit()
    conn.close()
    return r
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, pu INT, pc INT, stock REAL DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, qty REAL, type TEXT, pu_final INT, total INT, seller TEXT, date TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS operations (id INTEGER PRIMARY KEY, date TEXT, op TEXT, details TEXT, amount INT, user_name TEXT)")
    for d in [('VODY',500,12000,10),('DECA',600,14400,8),('FOCUS',500,12000,12),('CHAP',500,12000,15)]:
        cur.execute("INSERT OR IGNORE INTO products (name,pu,pc,stock) VALUES (?,?,?,?)", d)
    conn.commit()
    conn.close()
init_db()
USERS = {'patron':{'pass':'berli2024','name':'Patron'},'gerant':{'pass':'gerant2024','name':'Gerant'},'caissier':{'pass':'caisse2024','name':'Caissier'}}
HEAD = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'><style>body{background:#f4f6fb}.sidebar{background:#fff;width:240px;position:fixed;top:0;left:0;bottom:0;border-right:1px solid #ddd;padding:20px 10px}.main{margin-left:240px;padding:20px}.grid-card{background:#fff;border-radius:16px;padding:20px;border:1px solid #eee}.card-icon{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff}@media(max-width:768px){.sidebar{display:none}.main{margin-left:0}}</style></head><body><div class='sidebar'><h5><span style='color:#2563eb'>BERLI</span> Soft</h5><a href='/' class='btn btn-light w-100 text-start mb-1'>Accueil</a><a href='/dashboard' class='btn btn-light w-100 text-start mb-1'>Dashboard</a><a href='/caisse' class='btn btn-primary w-100 text-start mb-1'>Caisse Facture</a><a href='/stock' class='btn btn-light w-100 text-start mb-1'>Stock</a><a href='/ventes' class='btn btn-light w-100 text-start mb-1'>Ventes</a><a href='/journal' class='btn btn-light w-100 text-start mb-1'>Journal</a><a href='/stock_faible' class='btn btn-light w-100 text-start mb-1 text-danger'>Stock Faible</a><a href='/logout' class='btn btn-outline-secondary w-100 mt-4'>Logout</a></div><div class='main'>"
FOOT = "</div></body></html>"
def render_page(c):
    return render_template_string(HEAD + c + FOOT)
def log_op(op, details, amount):
    dt = datetime.now().strftime("%d/%m/%Y %H:%M")
    q("INSERT INTO operations (date,op,details,amount,user_name) VALUES (?,?,?,?,?)", (dt,op,details,amount,session.get('name','')))
@app.route('/login', methods=['GET','POST'])
def login():
    err = ""
    if request.method == 'POST':
        u = request.form.get('username','').lower().strip()
        p = request.form.get('password','').strip()
        if u in USERS and USERS[u]['pass'] == p:
            session['user'] = u
            session['name'] = USERS[u]['name']
            return redirect('/')
        err = "Erreur identifiants"
    return "<html><head><link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'></head><body style='background:#f4f6fb'><div style='max-width:400px;margin:80px auto'><div class='card p-4 shadow'><h3>BERLI Soft</h3><form method='POST'><input name='username' class='form-control mb-2' placeholder='patron' required><input name='password' type='password' class='form-control mb-2' required><button class='btn btn-dark w-100'>Connexion</button></form><p class='text-danger'>"+err+"</p><small>patron:berli2024</small></div></div></body></html>"
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/')
def accueil():
    if 'user' not in session:
        return redirect('/login')
    html = "<h4>Accueil - Comme DECA Soft</h4><p>Facture A4 + Vente Multiple</p><div class='row g-3'><div class='col-6 col-md-3'><a href='/caisse' style='text-decoration:none'><div class='grid-card' style='border:2px solid #2563eb'><div class='card-icon' style='background:#16a34a'>C</div><h6>Caisse Facture A4</h6></div></a></div><div class='col-6 col-md-3'><a href='/dashboard' style='text-decoration:none'><div class='grid-card'><div class='card-icon' style='background:#22c55e'>D</div><h6>Dashboard</h6></div></a></div><div class='col-6 col-md-3'><a href='/journal' style='text-decoration:none'><div class='grid-card'><div class='card-icon' style='background:#a855f7'>J</div><h6>Journal</h6></div></a></div><div class='col-6 col-md-3'><a href='/stock' style='text-decoration:none'><div class='grid-card'><div class='card-icon' style='background:#3b82f6'>S</div><h6>Stock</h6></div></a></div></div>"
    return render_page(html)
    @app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    sales = q("SELECT * FROM sales", f=True) or []
    total = sum([s['total'] or 0 for s in sales])
    return render_page(f"<h4>Dashboard - Comme DECA</h4><div class='card p-3 mb-3'><small>TOTAL ENTREES</small><h4 class='text-success'>{total:,} F</h4></div><div class='card p-3'><h6>FOCUS AUJOURD'HUI</h6><p>CA Aujourd'hui: {total:,} F</p></div>")

@app.route('/stock')
def stock():
    if 'user' not in session:
        return redirect('/login')
    prods = q("SELECT * FROM products ORDER BY name", f=True) or []
    rows = ""
    for p in prods:
        rows += f"<tr><td><b>{p['name']}</b></td><td>{p['stock']}</td><td>{p['pu']} F</td><td>{p['pc']} F</td></tr>"
    return render_page(f"<h4>Stock</h4><div class='card p-3'><table class='table'><tr><th>Nom</th><th>Stock</th><th>PU</th><th>PC</th></tr>{rows}</table></div>")

@app.route('/stock_faible')
def stock_faible():
    if 'user' not in session:
        return redirect('/login')
    prods = q("SELECT * FROM products WHERE stock < 5", f=True) or []
    rows = ""
    for p in prods:
        rows += f"<tr><td>{p['name']}</td><td class='text-danger fw-bold'>{p['stock']}</td></tr>"
    if not rows:
        rows = "<tr><td colspan=2>Aucun stock faible</td></tr>"
    return render_page(f"<h4 class='text-danger'>Stock Faible</h4><div class='card p-3'><table class='table'><tr><th>Produit</th><th>Stock</th></tr>{rows}</table></div>")

@app.route('/entree_stock', methods=['GET','POST'])
def entree():
    if 'user' not in session:
        return redirect('/login')
    prods = q("SELECT * FROM products", f=True) or []
    if request.method == 'POST':
        n = request.form.get('product')
        qty = float(request.form.get('qty') or 0)
        q("UPDATE products SET stock=stock+? WHERE name=?", (qty,n))
        log_op("Entree stock", f"{qty} {n}", 0)
        return redirect('/stock')
    opts = ""
    for p in prods:
        opts += f"<option>{p['name']}</option>"
    return render_page(f"<h4>Entree Stock</h4><div class='card p-3' style='max-width:400px'><form method='POST'><select name='product' class='form-control mb-2'>{opts}</select><input name='qty' type='number' step='0.5' class='form-control mb-2' required><button class='btn btn-success w-100'>Valider</button></form></div>")

@app.route('/caisse', methods=['GET','POST'])
def caisse():
    if 'user' not in session:
        return redirect('/login')
    prods = q("SELECT * FROM products", f=True) or []
    if 'cart' not in session:
        session['cart'] = []
    if request.method == 'POST':
        act = request.form.get('action')
        if act == 'add':
            prod = request.form.get('product')
            qty = float(request.form.get('qty') or 1)
            typ = request.form.get('type_v')
            p = next((x for x in prods if x['name'] == prod), None)
            if p:
                total = int(qty*p['pu']) if typ == 'detail' else int(qty*p['pc'])
                pu_f = p['pu'] if typ == 'detail' else p['pc']
                session['cart'].append({'product':prod,'qty':qty,'type':typ,'pu':pu_f,'total':total})
                session.modified = True
        elif act == 'clear':
            session['cart'] = []
            session.modified = True
        elif act == 'validate':
            cart = session.get('cart', [])
            if cart:
                grand = sum([c['total'] for c in cart])
                client = request.form.get('client') or 'Client de passage'
                for c in cart:
                    ded = c['qty']/24 if c['type'] == 'detail' else c['qty']
                    q("UPDATE products SET stock=stock-? WHERE name=?", (ded,c['product']))
                    q("INSERT INTO sales (product,qty,type,pu_final,total,seller,date) VALUES (?,?,?,?,?,?,?)", (c['product'],c['qty'],c['type'],c['pu'],c['total'],session['name'],datetime.now().strftime("%d/%m/%Y %H:%M")))
                log_op("Vente de produits", f"{len(cart)} article(s) - {client}", grand)
                session['last_ticket'] = cart
                session['last_total'] = grand
                session['client_name'] = client
                session['cart'] = []
                session.modified = True
                return redirect('/facture')
        return redirect('/caisse')
    opts = ""
    for p in prods:
        opts += f"<option value='{p['name']}'>{p['name']} (Stock {p['stock']})</option>"
    cart = session.get('cart', [])
    cart_rows = ""
    for c in cart:
        cart_rows += f"<tr><td>{c['product']}</td><td>{c['qty']} {c['type']}</td><td>{c['pu']} F</td><td>{c['total']} F</td></tr>"
    if not cart_rows:
        cart_rows = "<tr><td colspan=4>Panier vide</td></tr>"
    cart_total = sum([c['total'] for c in cart])
    html = f"<h4>Caisse - Facture A4 (Vente Multiple)</h4><div class='row'><div class='col-md-5'><div class='card p-3'><h6>Ajouter Produit</h6><form method='POST'><input type='hidden' name='action' value='add'><select name='product' class='form-control mb-2'>{opts}</select><div class='row'><div class='col-6'><input name='qty' type='number' value='1' step='0.5' class='form-control mb-2'></div><div class='col-6'><select name='type_v' class='form-control mb-2'><option value='casier'>Casier</option><option value='detail'>Bouteille</option></select></div></div><button class='btn btn-primary w-100'>+ Ajouter au Panier</button></form></div></div><div class='col-md-7'><div class='card p-3'><h6>Panier ({len(cart)} article(s)) <form method='POST' style='display:inline'><input type='hidden' name='action' value='clear'><button class='btn btn-sm btn-outline-danger float-end'>Vider</button></form></h6><table class='table table-sm'><tr><th>Produit</th><th>Qte</th><th>PU</th><th>Total</th></tr>{cart_rows}</table><h5 class='text-end'>Total: {cart_total:,} F</h5><form method='POST'><input type='hidden' name='action' value='validate'><input name='client' class='form-control mb-2' placeholder='Nom Client'><button class='btn btn-success w-100 btn-lg'>VALIDER & FACTURE A4</button></form></div></div></div>"
    return render_page(html)

@app.route('/facture')
def facture():
    if 'user' not in session:
        return redirect('/login')
    cart = session.get('last_ticket', [])
    total = session.get('last_total', 0)
    if not cart:
        return redirect('/caisse')
    num = datetime.now().strftime("FAC-%Y%m%d-%H%M%S")
    date_str = datetime.now().strftime("%d/%m/%
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    rows = ""
    for i,c in enumerate(cart):
        rows += f"<tr><td style='padding:8px;border:1px solid #ddd'>{i+1}</td><td style='padding:8px;border:1px solid #ddd'><b>{c['product']}</b></td><td style='padding:8px;border:1px solid #ddd'>{c['qty']} {c['type']}</td><td style='padding:8px;border:1px solid #ddd'>{c['pu']} F</td><td style='padding:8px;border:1px solid #ddd;text-align:right'>{c['total']} F</td></tr>"
    client = session.get('client_name','Client')
    html = "<html><head><meta charset='utf-8'><title>Facture "+num+"</title><style>body{font-family:Arial;background:#f5f5f5;padding:20px} .facture{background:white;max-width:800px;margin:0 auto;padding:40px} table{width:100%;border-collapse:collapse} @media print{.no-print{display:none}}</style></head><body><div class='facture'><div style='display:flex;justify-content:space-between;border-bottom:3px solid #2563eb;padding-bottom:20px'><div><div style='font-size:28px;font-weight:bold;color:#2563eb'>BERLI DISTRIBUTION</div><div>Lome - Togo</div></div><div style='text-align:right'><h2 style='color:#2563eb'>FACTURE</h2><div>N: "+num+"</div><div>Date: "+date_str+"</div><div>Vendeur: "+session['name']+"</div></div></div><div style='margin-top:15px'><b>Client:</b> "+client+"</div><table style='margin-top:15px'><tr style='background:#2563eb;color:white'><th style='padding:10px;border:1px solid #ddd'>N</th><th style='padding:10px;border:1px solid #ddd'>DESIGNATION</th><th style='padding:10px;border:1px solid #ddd'>QTE</th><th style='padding:10px;border:1px solid #ddd'>P.U</th><th style='padding:10px;border:1px solid #ddd'>MONTANT</th></tr>"+rows+"</table><div style='text-align:right;font-size:22px;font-weight:bold;color:#2563eb;border-top:2px solid #2563eb;margin-top:15px;padding-top:10px'>NET A PAYER: "+str(total)+" F CFA</div><div class='no-print' style='margin-top:30px;text-align:center'><button onclick='window.print()' style='padding:12px 30px;background:#2563eb;color:white;border:none;border-radius:8px'>IMPRIMER FACTURE A4</button><br><br><a href='/caisse' style='padding:10px 20px;background:#16a34a;color:white;text-decoration:none;border-radius:8px'>Nouvelle Vente</a> <a href='/' style='padding:10px 20px;background:gray;color:white;text-decoration:none;border-radius:8px'>Accueil</a></div></div></body></html>"
    return html

@app.route('/ventes')
def ventes():
    if 'user' not in session:
        return redirect('/login')
    sales = q("SELECT * FROM sales ORDER BY id DESC LIMIT 100", f=True) or []
    rows = ""
    for s in sales:
        rows += f"<tr><td>{s['date']}</td><td>{s['product']}</td><td>{s['qty']} {s['type']}</td><td>{s['total']} F</td><td>{s['seller']}</td></tr>"
    return render_page(f"<h4>Ventes</h4><div class='card p-3'><table class='table table-sm'><tr><th>Date</th><th>Produit</th><th>Qte</th><th>Total</th><th>Vendeur</th></tr>{rows}</table></div>")

@app.route('/journal')
def journal():
    if 'user' not in session:
        return redirect('/login')
    ops = q("SELECT * FROM operations ORDER BY id DESC LIMIT 100", f=True) or []
    total = sum([o['amount'] or 0 for o in ops if 'Vente' in o['op']])
    rows = ""
    for o in ops:
        rows += f"<tr><td><small>{o['date']}</small></td><td>{o['op']}</td><td>{o['details']}</td><td>{o['amount'] or 0} F</td></tr>"
    return render_page(f"<h4>Journal des Operations</h4><div class='card p-3'><small>TOTAL ENTREES: {total:,} F</small><table class='table mt-2'><tr><th>DATE</th><th>OPERATION</th><th>DETAILS</th><th>MONTANT</th></tr>{rows}</table></div>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
