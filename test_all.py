import json
import logging
import os

import pytest

from backend import app
from backend.dao import Base, engine, db_session, es

# TODO: rename 'pwd_hash' to 'pwd' throughout the project

sample_creds = [{'login': 'test', 'pwd_hash': '1234'},
                {'login': 'test2', 'pwd_hash': '2345'}]
sample_wrong_creds = [{'login': 'a', 'pwd_hash': 'b'}]
sample_user_data = [{'user_id': 1, 'session_token': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}]


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


def logout(client):
    return client.post('/api/logout')


def login(client, creds):
    return client.post('/api/login', data=json.dumps(creds))


@pytest.fixture
def registration_data(client):
    response = register(client, sample_creds[0])
    user_data = json.loads(response.data)
    set_cookies(client, user_data)
    return user_data


def test_registration(client):
    response = register(client, sample_wrong_creds[0])
    assert response.status_code == 404

    # 4.1.1.2
    response = register(client, sample_creds[0])
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user_id' in data and 'session_token' in data
    assert data['user_id'] == 1 and isinstance(data['session_token'], str)

    # 4.1.1.5
    response = register(client, sample_creds[0])
    assert response.status_code == 409


def test_logout(client, registration_data):
    response = logout(client)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'OK'

    response = logout(client)
    assert response.status_code == 401


def test_login(client, registration_data):
    logout(client)

    # 4.1.1.3
    response = login(client, sample_creds[1])
    assert response.status_code == 404

    # 4.1.1.4
    response = login(client, {'login': sample_creds[0]['login'],
                              'pwd_hash': sample_creds[1]['pwd_hash']})
    assert response.status_code == 404

    # 4.1.1.1
    response = login(client, sample_creds[0])
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user_id' in data and 'session_token' in data
    assert data['user_id'] == 1 and isinstance(data['session_token'], str)


def test_add_post(client, registration_data):
    filedir = '/documents'
    filename = 'test_podcast.mp3'
    set_cookies(client, registration_data)

    data = {
        'data': json.dumps({
            'title': 'Test',
            'short_description': 'Test audio upload',
            'long_description': ''
        }),
        'file': (open(os.path.join(filedir, filename), 'rb'), filename)
    }

    response = client.post('/api/post', data=data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'OK' and data['post_id'] == 1


def test_empty_feed(client, registration_data):
    response = client.get('/api/feed/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['pages_count'] == 0
    assert len(data['user_feed']) == 0

# def test_add_post(client, registration_data):
