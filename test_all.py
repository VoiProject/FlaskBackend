import json
import logging

import pytest

from backend import app
from backend.dao import Base, engine, db_session, es

# TODO: rename 'pwd_hash' to 'pwd' throughout the project

sample_creds = [{'login': 'test', 'pwd_hash': '1234'},
                {'login': 'test2', 'pwd_hash': '2345'}]


def set_cookies(client, cookies):
    for k, v in cookies.items():
        client.set_cookie('localhost', key=str(k), value=str(v))


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    es.indices.delete(index='posts', ignore=[400, 404])

    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


def simple_response_data_test(client, route):
    response = client.get(route)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0


def test_config(client):
    simple_response_data_test(client, '/api/config')


def test_help(client):
    simple_response_data_test(client, '/api/help')


def register(client, creds):
    return client.post('/api/register', data=json.dumps(creds))


def logout(client, user_data):
    set_cookies(client, user_data)
    return client.post('/api/logout')


@pytest.fixture
def registration_data(client):
    response = register(client, sample_creds[0])
    return json.loads(response.data)


def test_registration(client):
    response = register(client, {'login': 'a', 'pwd_hash': 'b'})
    assert response.status_code == 404

    response = register(client, sample_creds[0])
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user_id' in data and 'session_token' in data
    assert data['user_id'] == 1 and isinstance(data['session_token'], str)

    response = register(client, sample_creds[0])
    assert response.status_code == 409


def test_logout(client, registration_data):
    response = logout(client, registration_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'OK'


def test_empty_feed(client, registration_data):
    response = client.get('/api/feed/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['pages_count'] == 0
    assert len(data['user_feed']) == 0

# def test_add_post(client, registration_data):
