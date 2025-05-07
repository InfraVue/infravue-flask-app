from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db
from models import User, Project, Image  # Assuming you have Project and Image models
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///infravue.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from flask_migrate import Migrate
    migrate = Migrate(app, db)

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
        projects = Project.query.all()  # replace with dummy list if Project model missing
        return render_template('projects.html', projects=projects)

    @app.route('/projects/create', methods=['GET', 'POST'])
    @login_required
    def create_project():
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            new_project = Project(name=name, description=description, owner_id=current_user.id)
            db.session.add(new_project)
            db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects'))
        return render_template('create_project.html')

    @app.route('/projects/<int:project_id>')
    @login_required
    def project_dashboard(project_id):
        project = Project.query.get_or_404(project_id)
        images = Image.query.filter_by(project_id=project.id).all()
        return render_template('project_dashboard.html', project=project, images=images)

    @app.route('/projects/<int:project_id>/upload', methods=['GET', 'POST'])
    @login_required
    def upload_image(project_id):
        project = Project.query.get_or_404(project_id)
        if request.method == 'POST':
            if 'image' in request.files:
                image_file = request.files['image']
                filename = secure_filename(image_file.filename)
                folder = os.path.join(app.root_path, 'static', 'uploads', str(project_id))
                os.makedirs(folder, exist_ok=True)
                image_path = os.path.join(folder, filename)
                image_file.save(image_path)

                new_image = Image(filename=filename, project_id=project.id)
                db.session.add(new_image)
                db.session.commit()

                flash('Image uploaded!', 'success')
                return redirect(url_for('project_dashboard', project_id=project_id))
        return render_template('upload_image.html', project=project)

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        if request.method == 'POST':
            if 'image' in request.files:
                image_file = request.files['image']
                filename = secure_filename(image_file.filename)
                folder = os.path.join('static/uploads')
                os.makedirs(folder, exist_ok=True)
                image_path = os.path.join(folder, filename)
                image_file.save(image_path)
                flash('Image uploaded!', 'success')
                return redirect(url_for('dashboard'))
        return render_template('upload.html')

    return app
