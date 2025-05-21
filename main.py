import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from ultralytics import YOLO

# App and config
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# YOLO Model
model = YOLO("models/yolov8n.pt")

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

# Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    images = Image.query.all()
    return render_template('dashboard.html', user=current_user, projects=projects, images=images)

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image_for_dashboard():
    project_id = request.form['project_id']
    file = request.files['image']
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, filename)
        file.save(file_path)
        image = Image(filename=filename, project_id=project_id)
        db.session.add(image)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/rename/<int:image_id>', methods=['POST'])
@login_required
def rename_image(image_id):
    image = Image.query.get_or_404(image_id)
    new_name = secure_filename(request.form['new_name'])
    old_path = os.path.join(app.config['UPLOAD_FOLDER'], str(image.project_id), image.filename)
    new_path = os.path.join(app.config['UPLOAD_FOLDER'], str(image.project_id), new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        image.filename = new_name
        db.session.commit()
        flash("Image renamed successfully!")
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], str(image.project_id), image.filename)
    if os.path.exists(image_path):
        os.remove(image_path)
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted successfully!")
    return redirect(url_for('dashboard'))

@app.route('/process/<int:image_id>', methods=['POST'])
@login_required
def process_image_ai(image_id):
    image = Image.query.get_or_404(image_id)
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], str(image.project_id), image.filename)

    # Output path
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], str(image.project_id), f"processed_{image.filename}")

    results = model(img_path)
    results[0].save(filename=output_path)

    flash("AI processing complete!")
    return redirect(url_for('dashboard'))

@app.template_filter('file_exists')
def file_exists_filter(filepath):
    return os.path.exists(os.path.join(app.static_folder, filepath))

@app.route('/run_ai/<int:image_id>', methods=['POST'])
@login_required
def run_ai(image_id):
    image = Image.query.get_or_404(image_id)

    # Define input/output paths
    input_path = os.path.join(app.static_folder, 'uploads', str(image.project_id), image.filename)
    output_filename = f"processed_{image.filename}"
    output_path = os.path.join(app.static_folder, 'uploads', str(image.project_id), output_filename)

    try:
        model = YOLO("yolov8n.pt")  # or yolov8s.pt, etc.
        results = model(input_path)
        results[0].save(filename=output_path)
        flash("AI processing complete!", "success")
    except Exception as e:
        flash(f"AI processing failed: {str(e)}", "danger")

    return redirect(url_for('dashboard'))

# Run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
