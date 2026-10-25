from flask import Flask, render_template, request
import json
import os

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
  
if __name__ == '__main__':
  app.run(debug=True)
