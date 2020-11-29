import os

from flask import Flask
from flask_cors import CORS
from flask_elasticsearch import FlaskElasticsearch

app = Flask(__name__, static_url_path='/Frontend/')
es = FlaskElasticsearch(app)

print("Elasticsearch config: ", es)

app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = "../Frontend"
#app.config['CORS_HEADERS'] = 'Content-Type'
from backend import views
