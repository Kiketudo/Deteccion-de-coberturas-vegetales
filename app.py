from flask import Flask, render_template, request, session,\
                    redirect, url_for, flash, g, send_from_directory, abort, send_file 
from flask_session import Session
from PIL import Image
from datetime import datetime,timedelta
from io import BytesIO
import os
import uuid
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'sesiones/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_COOKIE_MAX_AGE'] = 1800
app.config['SECRET_KEY'] = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
app.permanent_session_lifetime = timedelta(minutes=30)
#csrf = CSRFProtect(app)
class ImageUploadForm(FlaskForm):
    imagenes = FileField('Selecciona una imagen', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg', 'gif'],'Solo se permiten archivos de imagen.')])

@app.route('/', methods=['GET', 'POST'])
def index():
    uploaded_images = []
    form = ImageUploadForm()

    if form.validate_on_submit():
        imagenes = request.files.getlist('imagenes')
        for imagen in imagenes:
            if imagen.content_length > app.config['MAX_CONTENT_LENGTH']:
                return "El tamaño del archivo excede el límite permitido (5 MB)."

        # Almacenar la imagen en el servidor
            original_image_path = save_image(imagen)
            # Procesar la imagen (en este caso, convertirla a escala de grises)
        #processed_image_path = process_image(original_image_path)
            uploaded_images.append({
                'original_image': original_image_path,
                'processed_image': None
            })
            print(uploaded_images[0]['original_image'])
        # Continuar con el procesamiento de la imagen si es necesario

        
    return render_template('main.html', uploaded_images=uploaded_images,os=os,form=form)

""" @app.route('/',methods=['GET', 'POST'])
def index():
    uploaded_images = []
    if request.method == 'POST':
        images = request.files.getlist('file')
        
        for file in images:
            if file.filename == '':
                continue
            if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                return "El tamaño del archivo excede el límite permitido (5 MB)."
            # Guardar la imagen original en el servidor
            original_image_path = save_image(file)

            # Procesar la imagen (en este caso, convertirla a escala de grises)
            processed_image_path = process_image(original_image_path)

            uploaded_images.append({
                'original_image': original_image_path,
                'processed_image': processed_image_path
            })

        # Retornar las rutas de las imágenes y la biblioteca os para ser manejadas por JavaScript
    return render_template('main.html', uploaded_images=uploaded_images,os=os)      
   """

@app.route('/resultados', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        # Guardar la imagen original en el servidor
        original_image_path = save_image(file)

        # Procesar la imagen (en este caso, convertirla a escala de grises)
        processed_image_path = process_image(original_image_path)

        return render_template('result.html', original_image=file.filename, processed_image=processed_image_path)

def save_image(file):
    user_id = session.get('user_id') or str(uuid.uuid4())
    session['user_id'] = user_id
# Generación del nombre de la carpeta
    folder_name = 'session-{}'.format(user_id)
    print(folder_name)
# Creación de la carpeta
    carpeta =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'uploads')
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    # Generar un nombre de archivo seguro
    nombre_seguro = secure_filename(file.filename)

    # Guardar la imagen original en el servidor
    filename = os.path.join(carpeta, nombre_seguro)
    file.save(filename)
    return filename
@app.route('/process/', methods=['POST'])
def process_image():
    # Abrir la imagen con Pillow
    original_image_path = request.data.decode('utf-8')
    print(original_image_path)
    img = Image.open(original_image_path)

    # Procesar la imagen (en este caso, convertirla a escala de grises)
    processed_img = img.convert('L')
    # Guardar la imagen procesada en el servidor
    processed_image_path = original_image_path.replace(os.path.splitext(original_image_path)[1], '_processed.jpg')
    processed_img.save(processed_image_path)
    return processed_image_path

@app.route('/download/<filename>')
def download_processed_image(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

"""@app.route('/sesiones/<filename>')
def uploaded_file(filename):
    print(filename)
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'],session.get('user_id'),filename), as_attachment=True)"""
def delete_session_folder():
    # Obtención del id de la sesión
    session_id = session.id()
    usr_fokder=os.path.join(app.config['UPLOAD_FOLDER'], 'session-{}'.format(session_id))
    if os.path.exists(usr_fokder):
        os.rmdir(usr_fokder)
"""@app.teardown_request
def teardown_request(exception = None):
    # Comprobación de si la sesión ha caducado
    if session.permanent is False and session.last_activity < (datetime.datetime.now() - timedelta(seconds=app.config['SESSION_COOKIE_MAX_AGE'])):
        # Borrado de la carpeta
     delete_session_folder()"""

if __name__ == '__main__':
    app.run(debug=True)