import logging
import os

from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base import Base
from .orm.user import User
from .orm.post import Post
from .orm.like import Like
from .orm.comment import Comment

try:
    engine = create_engine(
        f"postgres://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}")
except KeyError:
    engine = create_engine(
        'postgres://drgghtjs:SGBs0eUt9rh9WVEpDDK0rq00uceccJcp@suleiman.db.elephantsql.com:5432/drgghtjs')
    logging.info('Connected to fallback DB')

Session = sessionmaker(bind=engine, autocommit=True)
Base.metadata.create_all(engine)
db_session = Session()

try:
    es = Elasticsearch([{'host': os.environ['ELASTIC_HOST'], 'port': os.environ['ELASTIC_PORT']}])
except:
    logging.info("ElasticSearch not connected")
    es = None

try:
    audio_dir = os.environ['AUDIO_DIR']
    os.makedirs(audio_dir, exist_ok=True)
except:
    logging.info("Audio dir not created")
    audio_dir = None
