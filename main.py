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

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Setup login manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ----- Routes -----

    # Home redirects to dashboard
    @app.route('/')
    def home():
        return redirect(url_for('dashboard'))

    # Login
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

    # Logout
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    # Dashboard showing all user images
    @app.route('/dashboard')
    @login_required
    def dashboard():
        projects = Project.query.filter_by(user_id=current_user.id).all()
        project_ids = [p.id for p in projects]
        images = Image.query.filter(Image.project_id.in_(project_ids)).all()
        return render_template('dashboard.html', user=current_user, projects=projects, images=images)

    # Inline create project from dashboard
    @app.route('/dashboard/create_project', methods=['POST'])
    @login_required
    def create_project_inline():
        name = request.form.get('name')
        description = request.form.get('description')
        new_project = Project(name=name, description=description, user_id=current_user.id)
        db.session.add(new_project)
        db.session.commit()
        flash(f'Project "{name}" created!', 'success')
        return redirect(url_for('dashboard'))

    # Upload image from dashboard (select project)
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

    # Edit image filename
    @app.route('/dashboard/edit_image/<int:image_id>', methods=['POST'])
    @login_required
    def edit_image(image_id):
        image = Image.query.get_or_404(image_id)
        project = Project.query.get_or_404(image.project_id)
        if project.user_id != current_user.id:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('dashboard'))

        new_filename = secure_filename(request.form.get('new_filename'))
        old_path = os.path.join(app.root_path, 'static', 'uploads', str(project.id), image.filename)
        new_path = os.path.join(app.root_path, 'static', 'uploads', str(project.id), new_filename)

        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            image.filename = new_filename
            db.session.commit()
            flash('Image renamed successfully!', 'success')
        else:
            flash('Original file not found.', 'danger')

        return redirect(url_for('dashboard'))

    # Delete image
    @app.route('/dashboard/delete_image/<int:image_id>', methods=['POST'])
    @login_required
    def delete_image(image_id):
        image = Image.query.get_or_404(image_id)
        project = Project.query.get_or_404(image.project_id)
        if project.user_id != current_user.id:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('dashboard'))

        image_path = os.path.join(app.root_path, 'static', 'uploads', str(project.id), image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)

        db.session.delete(image)
        db.session.commit()
        flash('Image deleted successfully.', 'success')

        return redirect(url_for('dashboard'))

    # Project list
    @app.route('/projects')
    @login_required
    def projects():
        projects = Project.query.filter_by(user_id=current_user.id).all()
        return render_template('projects.html', projects=projects)

    # Create project from projects page
    @app.route('/projects/create', methods=['GET', 'POST'])
    @login_required
    def create_project():
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            new_project = Project(name=name, description=description, user_id=current_user.id)
            db.session.add(new_project)
            db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects'))
        return render_template('create_project.html')

    # Project dashboard
    @app.route('/projects/<int:project_id>')
    @login_required
    def project_dashboard(project_id):
        project = Project.query.get_or_404(project_id)
        if project.user_id != current_user.id:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('dashboard'))
        images = Image.query.filter_by(project_id=project.id).all()
        return render_template('project_dashboard.html', project=project, images=images)

    # Upload image directly to project
    @app.route('/projects/<int:project_id>/upload', methods=['GET', 'POST'])
    @login_required
    def upload_image(project_id):
        project = Project.query.get_or_404(project_id)
        if project.user_id != current_user.id:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('dashboard'))

        if request.method == 'POST' and 'image' in request.files:
            image_file = request.files['image']
            filename = secure_filename(image_file.filename)
            folder = os.path.join(app.root_path, 'static', 'uploads', str(project.id))
            os.makedirs(folder, exist_ok=True)
            image_path = os.path.join(folder, filename)
            image_file.save(image_path)

            new_image = Image(filename=filename, project_id=project.id)
            db.session.add(new_image)
            db.session.commit()

            flash('Image uploaded!', 'success')
            return redirect(url_for('project_dashboard', project_id=project.id))

        return render_template('upload_image.html', project=project)

    return app
