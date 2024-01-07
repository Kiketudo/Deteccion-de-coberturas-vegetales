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

app.config['UPLOAD_FOLDER'] = 'sesiones/'
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER'] 
app.config['SESSION_COOKIE_MAX_AGE'] = 1800
app.config['SECRET_KEY'] = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
app.permanent_session_lifetime = timedelta(minutes=30)
#csrf = CSRFProtect(app)
class ImageUploadForm(FlaskForm):
    imagenes = FileField('Selecciona una imagen', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg', 'gif'],'Solo se permiten archivos de imagen.')])

@app.route('/', methods=['GET', 'POST'])
def index():
    crea_sesion()
    uploaded_images = {}
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
            uploaded_images = session['uploaded_images'] 
            uploaded_images[original_image_path]=None
            session['uploaded_images'] = uploaded_images
            #print(uploaded_images.keys())
        # Continuar con el procesamiento de la imagen si es necesario

        
    return render_template('main.html', uploaded_images=uploaded_images,os=os,form=form)
@app.route('/archivos')
def archivos():
    user_id = session.get('user_id')
    folder_name = 'session-{}'.format(user_id)+'/'
    # Obtén la lista de archivos y carpetas en el directorio seleccionado
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    # Obtén la lista de archivos y carpetas en el directorio uploads
    files_and_folders = os.listdir(folder_path)
    return render_template('index.html', files_and_folders=files_and_folders)

def save_image(file):
# Generación del nombre de la carpeta
    user_id = session.get('user_id')
    folder_name = 'session-{}'.format(user_id)+'/'
# Creación de la carpeta
    carpeta =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'uploads/')
    carpeta_out =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'outputs/')
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    if not os.path.exists(carpeta_out):
        os.makedirs(carpeta_out)
    # Generar un nombre de archivo seguro
    nombre_seguro = secure_filename(file.filename)

    # Guardar la imagen original en el servidor
    filename = os.path.join(carpeta, nombre_seguro)
    file.save(filename)
    return filename

def save_image_output(file):
    user_id = session.get('user_id') 
# Generación del nombre de la carpeta
    folder_name = 'session-{}'.format(user_id)
    print(folder_name)
# Creación de la carpeta
    carpeta =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'outputs')
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    # Guardar la imagen original en el servidor
    filename = os.path.join(carpeta, file.filename)
    file.save(filename)
    return filename

@app.route('/process/', methods=['POST'])
def process_image():
    # Abrir la imagen con Pillow
    original_image_path = request.data.decode('utf-8')
    img = Image.open(original_image_path)

    # Procesar la imagen (en este caso, convertirla a escala de grises)
    processed_img = img.convert('L')
    # Guardar la imagen procesada en el servidor"""
    processed_image_path = original_image_path.replace(os.path.splitext(original_image_path)[1], '_processed.jpg').replace('uploads','outputs')
    processed_img.save(processed_image_path)
    #save_image_output(processed_image_path)
    #actualiza el diccionario de la sesión
    uploaded_images=session.get('uploaded_images')
    uploaded_images[original_image_path]=processed_image_path
    session['uploaded_images']=uploaded_images
    print(processed_image_path)
    return processed_image_path

@app.route('/download/sesiones/<sesion>/<state>/<filename>')
def download_processed_image(sesion,filename,state):
    return  send_file(os.path.join(app.config['UPLOAD_FOLDER'],sesion,state,filename), as_attachment=True)

@app.route('/sesiones/<sesion>/<state>/<filename>')
def uploaded_file(sesion,filename,state):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'],sesion,state,filename), as_attachment=True)

def delete_session_folder():
    # Obtención del id de la sesión
    session_id = session.id()
    usr_fokder=os.path.join(app.config['UPLOAD_FOLDER'], 'session-{}'.format(session_id))
    if os.path.exists(usr_fokder):
        os.rmdir(usr_fokder)

@app.route('/files/<path:folder_name>')
def show_files(folder_name):
    user_id = session.get('user_id')
    seion_path = 'session-{}'.format(user_id)+'/'
    # Obtén la lista de archivos y carpetas en el directorio seleccionado
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'],seion_path, folder_name)
    print(folder_path)    
    # Verificar si la ruta es un directorio
    if os.path.isdir(folder_path):
        files_and_folders = os.listdir(folder_path)
        return render_template('folders.html', folder_path=folder_name, files_and_folders=files_and_folders)
    else:
        # Si no es un directorio, redirige a la página principal
        return redirect(url_for('index'))

def crea_sesion():
    if session.get('user_id') :
        user_id = str(uuid.uuid4())
        session['user_id'] =user_id
        session['last_activity'] = datetime.now()
        folder_name = 'session-{}'.format(user_id)+'/'
        carpeta =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'uploads/')
        carpeta_out =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'outputs/')
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
        if not os.path.exists(carpeta_out):
            os.makedirs(carpeta_out)

"""@app.teardown_request
def teardown_request(exception = None):
    # Comprobación de si la sesión ha caducado
     print(session['last_activity'])
    #if session.permanent is False and session.last_activity < (datetime.datetime.now() - timedelta(seconds=app.config['SESSION_COOKIE_MAX_AGE'])):
        # Borrado de la carpeta
     delete_session_folder()"""

if __name__ == '__main__':
    app.run(debug=True)