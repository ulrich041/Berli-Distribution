from flask import Flask, render_template_string, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = 'berli_secret_2024_togo_secure'

USERS = {
    'patron': {'pass': 'berli2024', 'role': 'patron'},
    'caisse': {'pass': 'caisse123', 'role': 'caissier'},
    'stock': {'pass': 'stock123', 'role': 'stock'}
}

@app.route('/')
def home():
    return render_template_string("<h1 style='text-align:center'>BERLI DISTRIBUTION</h1><p style='text-align:center'>Paiement a la livraison - Lome</p><div style='max-width:400px;margin:auto'><a href='/login' style='display:block;text-align:center;padding:12px;background:black;color:white;text-decoration:none'>Espace staff</a></div>")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('user','').strip()
        p = request.form.get('pass','').strip()
        if u in USERS and USERS[u]['pass'] == p:
            session['user'] = u
            session['role'] = USERS[u]['role']
            return redirect('/dashboard')
        return "Mauvais mot de passe - <a href='/login'>Retour</a>"
    return render_template_string("<h2 style='text-align:center;margin-top:40px'>Connexion Berli</h2><form method='POST' style='max-width:320px;margin:20px auto'><input name='user' placeholder='patron/caisse/stock' style='width:100%;padding:10px'><br><br><input name='pass' type='password' placeholder='pass' style='width:100%;padding:10px'><br><br><button type='submit' style='width:100%;padding:12px;background:black;color:white'>Se connecter</button></form>")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return f"<h1>Bienvenue {session['user']} - {session['role']}</h1><p>Dashboard OK</p><a href='/'>Accueil</a> | <a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
