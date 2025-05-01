from flask import Flask, render_template, request
import os

app = Flask(__name__)
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

import os
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
