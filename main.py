from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db
from models import User
from flask_login import LoginManager, login_user, logout_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///infravue.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def home():
        return render_template('upload.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return f"Hello, {current_user.username}! Welcome to your dashboard."

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/projects')
    @login_required
    def projects():
        projects = [
            {'name': 'Project A', 'description': 'Description of Project A'},
            {'name': 'Project B', 'description': 'Description of Project B'}
        ]
        return render_template('projects.html', projects=projects)

    @app.route('/projects/create', methods=['GET', 'POST'])
    @login_required
    def create_project():
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            # Saving to DB if you have Project model
            # new_project = Project(name=name, description=description, owner=current_user)
            # db.session.add(new_project)
            # db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects'))
        return render_template('create_project.html')

    return app
