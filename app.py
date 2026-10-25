from flask import Flask, render_template
import json, os
app = Flask(__name__)
DATA_FILE= 'data.json'
def load_data():
    if os.path.exsits(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"stocks":[]}
def save_data(data):
  with open(DATA_FILE, 'w') as f:
    json.dump(data, f, indent=2)
@app.route('/')
def index():
  data = load_data()
  return render_template('index.html', data=data)
if _name_ == '_main_':
  app.run()
    
