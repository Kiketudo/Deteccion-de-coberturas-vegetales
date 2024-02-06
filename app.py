from flask import Flask, render_template, request, session,\
                    redirect, url_for, flash, g, send_from_directory, abort, send_file 
from flask_session import Session
from PIL import Image
from datetime import datetime,timedelta
from io import BytesIO
import os
import uuid
import zipfile
import tempfile
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from modelos.U_Net import eval as UnetEval
from modelos.W_Net import eval as WnetEval
from modelos.Clustering import demo
import threading
import time
import shutil
import modelos.U_Net.model
import ortomap
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'sesiones/'
app.config['SESSION_COOKIE_MAX_AGE'] = 1800
app.config['SECRET_KEY'] = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'
app.config['MAX_CONTENT_LENGTH'] = 600 * 1024 * 1024  # 600 MB
MAX_CONTENT = 5 * 1024 * 1024 # 5 MB
app.permanent_session_lifetime = timedelta(minutes=30)
#csrf = CSRFProtect(app)
class ImageUploadForm(FlaskForm):
    imagenes = FileField('Selecciona una imagen', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg', 'tif'],'Solo se permiten archivos de imagen.')])
class orthoUploadForm(FlaskForm):
    ortomap = FileField('Ortomap', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg','tif'])
    ])
@app.route('/', methods=['GET', 'POST'])
def index():
    crea_sesion()
    form = ImageUploadForm()
    uploaded_images = session['uploaded_images'] 
    if form.validate_on_submit():
        imagenes = request.files.getlist('imagenes')
        for imagen in imagenes:
            if imagen.content_length > MAX_CONTENT:
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
    print('vamos a ver tio por que no entra')
    return render_template('index.html', files_and_folders=files_and_folders)

def save_image(file):
# Generación del nombre de la carpeta
    user_id = session.get('user_id')
    folder_name = 'session-{}'.format(user_id)
# Creación de la carpeta
    carpeta =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'uploads')
    carpeta_out =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'outputs')
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
    datos = request.get_json()
    opcion_seleccionada = datos.get('opcionSeleccionada')
    original_image_path = datos.get('imagen')
    print('sdfsdfs')
    print(original_image_path)
    print('opcipon:'+ opcion_seleccionada)
    #original_image_path = request.data.decode('utf-8')
    # Procesar la imagen (en este caso, convertirla a escala de grises)
    #processed_img = UnetEval.evaluar(original_image_path)
    processed_img=select(opcion_seleccionada,original_image_path)
    # Guardar la imagen procesada en el servidor"""
    processed_image_path = original_image_path.replace(os.path.splitext(original_image_path)[1], '_processed.jpg').replace('uploads','outputs')
    processed_img.save(processed_image_path)
    #save_image_output(processed_image_path)
    #actualiza el diccionario de la sesión
    uploaded_images=session.get('uploaded_images')
    uploaded_images[original_image_path]=processed_image_path
    session['uploaded_images']=uploaded_images
    print(uploaded_images)
    print(processed_image_path)
    return processed_image_path

@app.route('/download/sesiones/<sesion>/<state>/<filename>')
def download_processed_image(sesion,filename,state):
    return  send_file(os.path.join(app.config['UPLOAD_FOLDER'],sesion,state,filename), as_attachment=True)

@app.route('/sesiones/<sesion>/<state>/<filename>')
def uploaded_file(sesion,filename,state):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'],sesion,state,filename), as_attachment=True)

@app.route('/descargar',methods=['POST'])
def download_selected_itmes():
    selected_files = request.form.getlist('selected_files')
    if(selected_files):
        for file_path in selected_files:
            # Realiza la operación que desees con cada archivo seleccionado
            print(f"Descargando archivo: {file_path}")
            user_id = session.get('user_id') 
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, 'selected_files.zip')

        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            # Agregar cada archivo seleccionado al archivo zip
            for file_path in selected_files:
                file_name = os.path.basename(file_path)
                file_full_path = os.path.join(app.config['UPLOAD_FOLDER'],'session-{}'.format(user_id),'outputs')
                zip_file.write(file_full_path +'/'+ file_path, arcname=file_name)

        # Enviar el archivo zip como respuesta de descarga
        return send_file(zip_file_path, as_attachment=True, download_name='selected_files.zip')
    else:
        abort(400, 'No se han seleccionado archivos.')

@app.route('/proces/', methods=['POST'])
def process_various():
    datos = request.get_json()
    opcion_seleccionada = datos.get('opcionSeleccionada')
    original_image_paths = datos.get('selectedFiles', [])
    user_id=session.get('user_id')
    folder_name = os.path.join(app.config['UPLOAD_FOLDER'],'session-{}'.format(user_id),'uploads')
    folder_out_name=os.path.join(app.config['UPLOAD_FOLDER'],'session-{}'.format(user_id),'outputs')
    for path in original_image_paths:
        print(path)
        original_image_path = os.path.join(folder_name,path)
        processed_img = select(opcion_seleccionada,original_image_path)
        processed_image_path = path.replace(os.path.splitext(path)[1], '_processed.jpg')
        processed_image_path =os.path.join(folder_out_name,processed_image_path)
        processed_img.save(processed_image_path)
    
        #actualiza el diccionario de la sesión
        uploaded_images=session.get('uploaded_images')
        uploaded_images[original_image_path]=processed_image_path
        session['uploaded_images']=uploaded_images
        print(uploaded_images)
    return uploaded_images

@app.route('/ortho', methods=['GET', 'POST'])
def orthomap():
    form = orthoUploadForm()
    user_id=session.get('user_id')
    folder_name = os.path.join(app.config['UPLOAD_FOLDER'],'session-{}'.format(user_id),'Orthomaps')
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        files_and_folders = os.listdir(folder_name)
    else:
       files_and_folders = os.listdir(folder_name)
    if form.validate_on_submit():
        ortomap = form.ortomap.data
        filename = os.path.join(folder_name, ortomap.filename)
        ortomap.save(filename)
        files_and_folders = os.listdir(folder_name)
        return render_template('orthotif.html', form=form,folder_name='Orthomaps',files_and_folders=files_and_folders)

    return render_template('orthotif.html', form=form,folder_name='Orthomaps',files_and_folders=files_and_folders)

@app.route('/procesortho/', methods=['POST'])
def process_ortho():
    datos = request.get_json()
    opcion_seleccionada = datos.get('opcionSeleccionada')
    original_image_paths = datos.get('selectedFiles', [])
    user_id=session.get('user_id')
    folder_name = os.path.join(app.config['UPLOAD_FOLDER'],'session-{}'.format(user_id),'Orthomaps')
    out_name = os.path.join(app.config['UPLOAD_FOLDER'],'session-{}'.format(user_id),'outputs')
    temp_name = os.path.join(app.config['UPLOAD_FOLDER'],'session-{}'.format(user_id),'temp')
    for path in original_image_paths:
        print(path)
        orto=ortomap.orthoseg(temp_folder=temp_name)
        processed_img = orto.pipeline(os.path.join(folder_name,path),opcion_seleccionada)
        processed_image_path = path.replace(os.path.splitext(path)[1], '_ortho_processed.jpg')
        processed_img.save(os.path.join(out_name,processed_image_path))
    files_and_folders = os.listdir(out_name)
    return render_template('folders.html', folder_name='outputs', files_and_folders=files_and_folders)

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
        #if folder_name=='Orthomaps':
        #    return render_template('orthotif.html',folder_name=folder_name, files_and_folders=files_and_folders)
        return render_template('folders.html', folder_name=folder_name, files_and_folders=files_and_folders)
    else:
        # Si no es un directorio, redirige a la página principal
        return redirect(url_for('index'))

def crea_sesion():
    if not session.get('user_id') :
        user_id = str(uuid.uuid4())
        session['user_id'] =user_id
        session['last_activity'] = datetime.now()
        uploaded_images = {}
        session['uploaded_images'] = uploaded_images
        folder_name = 'session-{}'.format(user_id)+'/'
        carpeta =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'uploads/')
        carpeta_out =os.path.join(app.config['UPLOAD_FOLDER'], folder_name,'outputs/')
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
        if not os.path.exists(carpeta_out):
            os.makedirs(carpeta_out)
            
def select(option,route):
    match option:
        case 'opcion1':
            return UnetEval.evaluar(route)
        case 'opcion2':
            return WnetEval.evaluar(route)
        case 'opcion3':
            return demo.main(route)
        
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

def limpiar_directorios():
    while True:
        ruta_base = 'sesiones'

        # Obtener la lista de directorios
        directorios = os.listdir(ruta_base)

        # Obtener la hora actual
        ahora = datetime.now()
        # Duración de inactividad antes de eliminar un directorio (1 hora en este ejemplo)
        duracion_inactividad = app.permanent_session_lifetime
        # Iterar sobre los directorios y eliminar aquellos que han estado inactivos por más de 1 hora
        for directorio in directorios:
            ruta_directorio = os.path.join(ruta_base, directorio)
            tiempo_creacion = datetime.fromtimestamp(os.path.getctime(ruta_directorio))

            # Calcular el tiempo transcurrido desde la creación del directorio
            tiempo_transcurrido = ahora - tiempo_creacion
            if tiempo_transcurrido > duracion_inactividad:
                # Eliminar directorio si ha estado inactivo por más de 1 hora
                shutil.rmtree(ruta_directorio)
                print('Eliminado: '+ ruta_directorio)
        time.sleep(3600)
# Iniciar la tarea en segundo plano
tarea_limpiar_directorios = threading.Thread(target=limpiar_directorios)
tarea_limpiar_directorios.start()
if __name__ == '__main__':
    app.run(debug=True)