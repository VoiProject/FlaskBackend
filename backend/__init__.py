import os

from flask import Flask

app = Flask(__name__, static_url_path='/Frontend/')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = "../Frontend"

from backend import views
