import os
from datetime import datetime

from elasticsearch import Elasticsearch
from flask import Flask
from flask_cors import CORS

app = Flask(__name__, static_url_path='/Frontend/')
try:
    es = Elasticsearch([{'host': os.environ['ELASTIC_HOST'], 'port': os.environ['ELASTIC_PORT']}])

    print("Elasticsearch config: ", es)

    doc = {
        'author': 'kimchy',
        'text': 'Elasticsearch: cool. bonsai cool.',
        'timestamp': datetime.now(),
    }
    res = es.index(index="test-index", id=1, body=doc)
    print(res['result'])

    res = es.get(index="test-index", id=1)
    print(res['_source'])

    es.indices.refresh(index="test-index")

    res = es.search(index="test-index", body={"query": {"match_all": {}}})
    print(res)
except KeyError:
    print("Elastic not defined in env")


app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = "../Frontend"
#app.config['CORS_HEADERS'] = 'Content-Type'
from backend import views
