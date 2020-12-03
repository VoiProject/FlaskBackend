import os
from datetime import datetime

from elasticsearch import Elasticsearch
from flask import Flask
from flask_cors import CORS

app = Flask(__name__, static_url_path='/Frontend/')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = "../Frontend"
app.config['AUDIO_STORAGE'] = "/audio_data"

# app.config['CORS_HEADERS'] = 'Content-Type'
from backend import views
