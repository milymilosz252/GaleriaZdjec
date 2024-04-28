from flask import Flask, request, render_template, send_file, redirect, url_for, send_from_directory, abort
import zipfile
from werkzeug.utils import secure_filename
from PIL import Image
import os

app = Flask(__name__)
app.config['DEBUG'] = True  # Włączamy tryb debugowania

UPLOAD_FOLDER = 'zdjecia'
WEBP_FOLDER = 'WebP'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['WEBP_FOLDER'] = WEBP_FOLDER

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def compress_images(folder):
    file_paths = [os.path.join(folder, filename) for filename in os.listdir(folder)]
    with zipfile.ZipFile(f'{folder}.zip', 'w') as zip_file:
        for file_path in file_paths:
            zip_file.write(file_path, os.path.basename(file_path))

def convert_to_webp(input_path, output_path, quality=24):
    try:
        im = Image.open(input_path)
        im.save(output_path, quality=quality, lossless=False)
        return True
    except Exception as e:
        print(f"Conversion failed for {input_path}: {str(e)}")
        return False

def save_image_names(folder):
    with open('img.names', 'w') as f:
        for filename in os.listdir(folder):
            f.write(f"{filename}\n")

def get_file_name(filename):
    return os.path.splitext(filename)[0]

app.jinja_env.filters['get_file_name'] = get_file_name

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'Brak pliku w formularzu!'
    
    files = request.files.getlist('file')

    for file in files:
        if file.filename == '':
            return 'Brak wybranego pliku!'
        
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Konwersja do WebP
            webp_filename = secure_filename(os.path.splitext(filename)[0] + '.webp')
            webp_path = os.path.join(app.config['WEBP_FOLDER'], webp_filename)
            convert_to_webp(file_path, webp_path)
        else:
            return 'Niedozwolone rozszerzenie pliku!'
    
    # Po zakończeniu przesyłania, kompresujemy przesłane pliki
    compress_images(UPLOAD_FOLDER)
    # Zapisujemy nazwy plików do pliku img.names
    save_image_names(UPLOAD_FOLDER)
    
    # Przekierowanie użytkownika na stronę główną po przesłaniu plików
    return redirect(url_for('gallery'))

@app.route('/')
def gallery():
    webp_images = os.listdir(app.config['WEBP_FOLDER'])
    return render_template('gallery.html', webp_images=webp_images)

@app.route('/webp_images/<path:path>')
def send_webp_image(path):
    return send_from_directory(app.config['WEBP_FOLDER'], path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
