from flask import Flask
from flask_cors import CORS
app = Flask(__name__, static_url_path='/Frontend/')
app.config['UPLOAD_FOLDER'] = "../Frontend"
#app.config['CORS_HEADERS'] = 'Content-Type'
from backend import views
