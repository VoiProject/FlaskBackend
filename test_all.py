import json
import logging

import pytest

from backend import app
from backend.dao import Base, engine, db_session, es

LOGIN = 'test'
PASSWORD = '1234'


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    es.indices.delete(index='posts', ignore=[400, 404])

    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


def register(client):
    response = client.post('/api/register', data=json.dumps({'login': LOGIN,
                                                             'pwd_hash': PASSWORD}))
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user_id' in data and 'session_token' in data
    return data


def test_registration(client):
    data = register(client)
    assert data['user_id'] == 1 and isinstance(data['session_token'], str)


@pytest.fixture
def registration_data(client):
    return register(client)


def test_config(client):
    response = client.get('/api/config')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0


def test_empty_feed(client, registration_data):
    response = client.get('/api/feed/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['pages_count'] == 0
    assert len(data['user_feed']) == 0
