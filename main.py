from models import db, User
from flask import Flask, render_template, request
import os

app = Flask(__name__)
db.init_app(app)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return 'No image part'

    file = request.files['image']
    if file.filename == '':
        return 'No selected file'

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return render_template('result.html', image_url='/' + filepath)

import json

import json
from datetime import datetime

@app.route('/dashboard')
def dashboard():
    image_folder = 'static/uploads'
    image_files = []
    image_data = {}

    if os.path.exists(image_folder):
        image_files = os.listdir(image_folder)

    if os.path.exists('image_data.json'):
        with open('image_data.json', 'r') as f:
            image_data = json.load(f)

    image_items = []
    for file in image_files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_url = f'/{image_folder}/{file}'
            project_name = image_data.get(file, 'No Project Name')
            image_items.append({'url': image_url, 'project': project_name})

    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template('dashboard.html', images=image_items, last_updated=last_updated)

from flask import request, redirect, url_for

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return 'No image part'

    file = request.files['image']
    if file.filename == '':
        return 'No selected file'

    image_folder = 'static/uploads'
    file.save(os.path.join(image_folder, file.filename))

    return redirect(url_for('dashboard'))

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

from flask import Flask
from flask_login import LoginManager
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

import os
port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


