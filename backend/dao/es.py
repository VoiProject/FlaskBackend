import logging
import os

from elasticsearch import Elasticsearch


try:
    es = Elasticsearch([{'host': os.environ['ELASTIC_HOST'], 'port': os.environ['ELASTIC_PORT']}])
except:
    logging.info("ElasticSearch not connected")
    es = None


def get_es_size():
    return es.count(index='posts', body={"query": {"match_all": {}}})['count']
