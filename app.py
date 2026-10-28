from flask import Flask, request, redirect, session
from datetime import datetime
import sqlite3
app=Flask(__name__)
app.secret_key='berli'
def get_db():
 con=sqlite3.connect('berli.db')
 con.row_factory=sqlite3.Row
 return con
def q(sql,args=(),f=False):
 con=get_db()
 cur=con.cursor()
 cur.execute(sql,args)
 r=cur.fetchall() if f else None
 if not f:
  con.commit()
 con.close()
 return r
def init():
 con=get_db()
 c=con.cursor()
 c.execute("CREATE TABLE IF NOT EXISTS products (name TEXT PRIMARY KEY, pu INT, pc INT, stock REAL)")
 c.execute("CREATE TABLE IF NOT EXISTS sales (product TEXT, qty REAL, type TEXT, total INT, date TEXT)")
 for d in [('VODY',500,12000,10),('DECA',600,14400,8)]:
  c.execute("INSERT OR IGNORE INTO products VALUES (?,?,?,?)",d)
 con.commit()
 con.close()
init()
@app.route('/')
def home():
 return "<h2>BERLI</h2><a href='/caisse'>Caisse Facture A4</a> | <a href='/stock'>Stock</a>"
@app.route('/caisse',methods=['GET','POST'])
def caisse():
 p=q("SELECT * FROM products",f=True) or []
 if 'cart' not in session:
  session['cart']=[]
 if request.method=='POST':
  a=request.form.get('action')
  if a=='add':
   pr=request.form.get('product')
   qty=float(request.form.get('qty') or 1)
   ty=request.form.get('type_v')
   prd=next((x for x in p if x['name']==pr),None)
   if prd:
    tot=int(qty*prd['pu']) if ty=='detail' else int(qty*prd['pc'])
    pu=prd['pu'] if ty=='detail' else prd['pc']
    session['cart'].append({'product':pr,'qty':qty,'type':ty,'pu':pu,'total':tot})
    session.modified=True
  elif a=='clear':
   session['cart']=[]
   session.modified=True
  elif a=='val':
   session['last']=session.get('cart',[])
   session['ltot']=sum(c['total'] for c in session['last'])
   session['cart']=[]
   session.modified=True
   return redirect('/facture')
  return redirect('/caisse')
 cart=session.get('cart',[])
 opts="".join([f"<option>{x['name']}</option>" for x in p])
 rows="".join([f"<tr><td>{c['product']}</td><td>{c['qty']}</td><td>{c['total']}F</td></tr>" for c in cart]) or "<tr><td>Vide</td></tr>"
 tot=sum(c['total'] for c in cart)
 return f"<h3>Panier {len(cart)} - {tot}F</h3><form method=POST><input type=hidden name=action value=add><select name=product>{opts}</select><input name=qty value=1 type=number><select name=type_v><option value=casier>Casier</option><option value=detail>Bouteille</option></select><button>Ajouter</button></form><table border=1>{rows}</table><form method=POST><input type=hidden name=action value=val><button>VALIDER FACTURE A4</button></form><form method=POST><input type=hidden name=action value=clear><button>Vider</button></form>"
@app.route('/facture')
def facture():
 cart=session.get('last',[])
 tot=session.get('ltot',0)
 if not cart:
  return redirect('/caisse')
 num=datetime.now().strftime("FAC-%Y%m%d-%H%M%S")
 rows="".join([f"<tr><td>{c['product']}</td><td>{c['qty']} {c['type']}</td><td>{c['pu']}F</td><td>{c['total']}F</td></tr>" for c in cart])
 return f"<h2 style=color:blue>BERLI DISTRIBUTION</h2><h3>FACTURE {num}</h3><table border=1><tr><th>Produit</th><th>Qte</th><th>PU</th><th>Total</th></tr>{rows}</table><h2>NET A PAYER: {tot} F CFA</h2><button onclick=window.print()>IMPRIMER A4</button><br><a href=/caisse>Nouvelle vente</a>"
@app.route('/stock')
def stock():
 p=q("SELECT * FROM products",f=True) or []
 h="<h3>Stock</h3>"
 for r in p:
  h+=f"{r['name']} - {r['stock']} - {r['pu']}F<br>"
 return h
if __name__=='__main__':
 app.run(host='0.0.0.0',port=5000)
