from flask import Flask, render_template_string, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = 'berli_secret_2024_togo'

USERS = {   
  'patron': {'pass': 'berli2024', 'role': 'patron'},   
  'caisse': {'pass': 'caisse123', 'role': 'caissier'},   
  'stock': {'pass': 'stock123', 'role': 'stock'}
}

# PAGE CLIENT (celle que tu as déjà)
@app.route('/')
def home():  
  return render_template_string("""  
  <h1 style='text-align:center'>BERLI DISTRIBUTION</h1> 
  <p style='text-align:center'>Commandez vos produits - Paiement a la livraison a Lome</p>  
  <div style='max-width:400px;margin:auto'> 
  <input placeholder='Votre nom' style='width:100%;padding:10px;margin:5px'><br> 
  <input placeholder='Votre numero WhatsApp' style='width:100%;padding:10px;margin:5px'><br>  
  <input placeholder='Produit voulu' style='width:100%;padding:10px;margin:5px'><br>  
  <button style='width:100%;padding:12px;background:green;color:white;border:none'>Commander sur WhatsApp</button> 
  <br><br><a href='/login'>Espace staff (patron/caisse/stock)</a>  
  </div>   
  """)
  
# PAGE LOGIN
@app.route('/login', methods=['GET','POST'])
def login():  
  if request.method == 'POST':  
    u = request.form.get('user')     
    p = request.form.get('pass')    
    if u in USERS and USERS[u]['pass'] == p:  
      session['user'] = u       
      session['role'] = USERS[u]['role']    
      return redirect('/dashboard')    
      return 'Mot de passe incorrect <a href=/login>retour</a>' 
      return render_template_string("""  
      <h2 style='text-align:center'>Connexion Berli</h2>  
      <form method='POST' style='max-width:350px;margin:auto'>  
      <input name='user' placeholder='patron / caisse / stock' style='width:100%;padding:10px;margin:5px'><br>  
      <input name='pass' type='password' placeholder='mot de passe' style='width:100%;padding:10px;margin:5px'><br> 
      <button style='width:100%;padding:12px;background:black;color:white'>Se connecter</button> 
      </form>   
      """)
      
@app.route('/dashboard')
def dashboard():   
  if 'user' not in session:   
    return redirect('/login')   
    return f"""   
    <h1>Bienvenue {session['user']} - Role: {session['role']}</h1> 
    <p>Tableau de bord Berli - Stock / Ventes / Benefice</p>  
    <a href='/logout'>Deconnexion</a> | <a href='/'>Voir site client</a>   
    """
    
@app.route('/logout')
def logout(): 
  session.clear() 
  return redirect('/login')
  
if __name__ == '__main__':   
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
