from flask import Flask, render_template, request, redirect, jsonify
import json, os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = 'data.json'

def load_data(): 
  if os.path.exists(DATA_FILE):  
    with open(DATA_FILE, 'r', encoding='utf-8') as f:   
      return json.load(f)   
  return {"stocks": [], "ventes": [], "depenses": []}
  
def save_data(data): 
  with open(DATA_FILE, 'w', encoding='utf-8') as f:     
    json.dump(data, f, ensure_ascii=False, indent=2)
    
@app.route('/')
def index():  
  data = load_data()  
  return render_template('index.html', data=data)
  
@app.route('/add_stock', methods=['POST'])
def add_stock(): 
  data = load_data()  
  data['stocks'].append({  
    "produit": request.form.get('produit'),     
    "quantite": request.form.get('quantite'),     
    "prix": request.form.get('prix'),       
    "date": datetime.now().strftime("%d/%m/%Y %H:%M")    })  
  save_data(data) 
  return redirect('/')
@app.route('/add_vente', methods=['POST'])
def add_vente():  
  data = load_data()  
  data['ventes'].append({    
    "produit": request.form.get('produit'),    
    "quantite": request.form.get('quantite'),    
    "client": request.form.get('client'),     
    "date": datetime.now().strftime("%d/%m/%Y %H:%M")    }) 
  save_data(data)  
  return redirect('/')
if __name__ == '__main__':
  app.run(debug=True)
