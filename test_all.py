import json
import logging
import os

import pytest

from backend import app
from backend.dao import Base, engine, db_session, es

# TODO: rename 'pwd_hash' to 'pwd' throughout the project

sample_creds = [{'login': 'test', 'pwd_hash': '1234'},
                {'login': 'test2', 'pwd_hash': '2345'},
                {'login': 'test3', 'pwd_hash': '3456'}]
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


def login(client, creds):
    return client.post('/api/login', data=json.dumps(creds))


def logout(client):
    return client.post('/api/logout')


def enter_correct(method, client, creds):
    response = method(client, creds)
    user_data = json.loads(response.data)
    set_cookies(client, user_data)
    return user_data


@pytest.fixture
def registration_data(client):
    return enter_correct(register, client, sample_creds[0])


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


def add_post(client, title='Test title', description='Test description', transcription=''):
    filedir = '/documents'
    filename = 'test_podcast.mp3'
    data = {
        'data': json.dumps({
            'title': title,
            'short_description': description,
            'long_description': transcription,
        }),
        'file': (open(os.path.join(filedir, filename), 'rb'), filename)
    }
    return client.post('/api/post', data=data)


def test_add_post(client, registration_data):
    # 4.1.2
    response = add_post(client)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'OK' and data['post_id'] == 1


def get_feed(client, page=None):
    return client.get('/api/feed/' + (str(page) if page is not None else ''))


def test_user_feed(client):
    # 4.1.4

    def get_feed_correct(page=None):
        response = get_feed(client, page)
        assert response.status_code == 200
        return json.loads(response.data)

    enter_correct(register, client, sample_creds[0])
    add_post(client, 'Title A')
    data = get_feed_correct()
    assert data['pages_count'] == 0
    assert len(data['user_feed']) == 0

    enter_correct(register, client, sample_creds[1])
    add_post(client, 'Title B')
    data = get_feed_correct()
    assert data['pages_count'] == 1
    assert len(data['user_feed']) == 1
    assert data['user_feed'][0]['post']['title'] == 'Title A'
    del data['user_feed'][0]['post']
    assert data['user_feed'][0] == {"likes_count": 0,
                                    "liked_by_user": False,
                                    "comments_count": 0,
                                    "author_login": sample_creds[0]['login']}

    enter_correct(register, client, sample_creds[2])
    for i in range(10):
        add_post(client, f'Title C{i}')

    data = get_feed_correct()
    assert data['pages_count'] == 1
    assert len(data['user_feed']) == 2

    enter_correct(login, client, sample_creds[0])
    data = get_feed_correct(2)
    assert data['pages_count'] == 3
    assert len(data['user_feed']) == 5

    data = get_feed_correct(3)
    assert data['pages_count'] == 3
    assert len(data['user_feed']) == 1


def get_search(client, query, page):
    return client.post('/api/search/posts/' + str(page), data=json.dumps({'query': query}))


def test_search(client):
    def get_search_correct(query, page):
        response = get_search(client, query, page)
        assert response.status_code == 200
        return json.loads(response.data)

    enter_correct(register, client, sample_creds[0])
    for i, title in enumerate(['Apple pie'] * 3 + ['Orange juice'] * 11):
        add_post(client, title)

    enter_correct(register, client, sample_creds[1])
    data = get_search_correct('pie', 1)
    assert data['pages_count'] == 1
    assert len(data['user_feed']) == 3

    data = get_search_correct('orange', 2)
    assert data['pages_count'] == 3
    assert len(data['user_feed']) == 5

    data = get_search_correct('Orange', 3)
    assert data['pages_count'] == 3
    assert len(data['user_feed']) == 1
