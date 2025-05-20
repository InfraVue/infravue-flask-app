# --- main.py ---
from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db
from models import User, Project, Image
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///infravue.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def home():
        return redirect(url_for('dashboard'))

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
                flash('Invalid username or password.', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_projects = Project.query.filter_by(user_id=current_user.id).all()
        project_ids = [p.id for p in user_projects]
        images = Image.query.filter(Image.project_id.in_(project_ids)).all()
        return render_template('dashboard.html', user=current_user, projects=user_projects, images=images)

    @app.route('/projects/create', methods=['POST'])
    @login_required
    def create_project():
        name = request.form.get('name')
        description = request.form.get('description')
        new_project = Project(name=name, description=description, user_id=current_user.id)
        db.session.add(new_project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/dashboard/upload', methods=['POST'])
    @login_required
    def upload_image_for_dashboard():
        project_id = request.form.get('project_id')
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
        if 'image' in request.files:
            image_file = request.files['image']
            filename = secure_filename(image_file.filename)
            folder = os.path.join(app.root_path, 'static', 'uploads', str(project.id))
            os.makedirs(folder, exist_ok=True)
            image_path = os.path.join(folder, filename)
            image_file.save(image_path)

            new_image = Image(filename=filename, project_id=project.id)
            db.session.add(new_image)
            db.session.commit()
            flash('Image uploaded successfully!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/images/<int:image_id>/rename', methods=['POST'])
    @login_required
    def rename_image(image_id):
        image = Image.query.get_or_404(image_id)
        new_name = request.form.get('new_name')
        if new_name:
            _, ext = os.path.splitext(image.filename)
            new_filename = new_name.strip() + ext
            old_path = os.path.join(app.root_path, 'static', 'uploads', str(image.project_id), image.filename)
            new_path = os.path.join(app.root_path, 'static', 'uploads', str(image.project_id), new_filename)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                image.filename = new_filename
                db.session.commit()
                flash('Image renamed successfully!', 'success')
            else:
                flash('File not found on server.', 'danger')
        return redirect(url_for('dashboard'))

    @app.route('/images/<int:image_id>/delete', methods=['POST'])
    @login_required
    def delete_image(image_id):
        image = Image.query.get_or_404(image_id)
        file_path = os.path.join(app.root_path, 'static', 'uploads', str(image.project_id), image.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(image)
        db.session.commit()
        flash('Image deleted successfully.', 'success')
        return redirect(url_for('dashboard'))

    return app
