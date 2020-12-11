import pytest

from backend import app
from backend.dao import Base, engine, db_session, es
from test_client import *


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    es.indices.delete(index='posts', ignore=[400, 404])

    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


def unwrap(response):
    assert response.status_code == 200
    return json.loads(response.data)


def simple_response_data_test(client, route):
    data = unwrap(client.get(route))
    assert len(data) > 0


def test_config(client):
    simple_response_data_test(client, '/api/config')


def test_help(client):
    simple_response_data_test(client, '/api/help')


@pytest.fixture
def registration_data(client):
    return enter_correct(register, client, sample_creds[0])


def test_registration(client):
    response = register(client, sample_wrong_creds[0])
    assert response.status_code == 404

    # 4.1.1.2
    response = register(client, sample_creds[0])
    data = unwrap(response)
    assert 'user_id' in data and 'session_token' in data
    assert isinstance(data['user_id'], int) and isinstance(data['session_token'], str)

    # 4.1.1.5
    response = register(client, sample_creds[0])
    assert response.status_code == 409


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
    data = unwrap(response)
    assert 'user_id' in data and 'session_token' in data
    assert isinstance(data['user_id'], int) and isinstance(data['session_token'], str)


def test_logout(client, registration_data):
    response = logout(client)
    data = unwrap(response)
    assert data['status'] == 'OK'

    response = logout(client)
    assert response.status_code == 401


def test_add_post(client, registration_data):
    # 4.1.2
    response = add_post(client)
    data = unwrap(response)
    post_id = data['post_id']
    assert post_id == 1

    data = unwrap(get_post(client, post_id))
    assert data['author_id'] == registration_data['user_id']
    assert data['title'] == default_title


def test_user_feed(client):
    # 4.1.4

    def get_feed_correct(page=None):
        return unwrap(get_feed(client, page))

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


def test_search(client):
    def get_search_correct(query, page):
        return unwrap(get_search(client, query, page))

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


def test_likes(client):
    user_data = enter_correct(register, client, sample_creds[0])
    user_id = user_data['user_id']

    response = add_post(client)
    data = unwrap(response)
    post_id = data['post_id']

    assert unwrap(get_post_likes(client, post_id)) == []
    assert unwrap(get_post_likes_count(client, post_id))['count'] == 0
    assert not unwrap(is_post_liked_by_user(client, post_id))['like_state']

    response = like_post(client, post_id)
    data = unwrap(response)
    assert data['like_state']

    assert unwrap(get_post_likes(client, post_id)) == [{'user_id': user_id, 'post_id': post_id}]
    assert unwrap(get_post_likes_count(client, post_id))['count'] == 1
    assert unwrap(is_post_liked_by_user(client, post_id))['like_state']

    response = like_post(client, post_id)
    data = unwrap(response)
    assert not data['like_state']

    assert unwrap(get_post_likes(client, post_id)) == []
    assert unwrap(get_post_likes_count(client, post_id))['count'] == 0
    assert not unwrap(is_post_liked_by_user(client, post_id))['like_state']


def test_comments(client):
    user_data = enter_correct(register, client, sample_creds[0])
    user_id = user_data['user_id']

    data = unwrap(add_post(client))
    post_id = data['post_id']

    assert unwrap(get_post_comments(client, post_id)) == []
    assert unwrap(get_post_comments_count(client, post_id))['count'] == 0

    response = add_post_comment(client, post_id)
    data = unwrap(response)
    comment_id = data['comment_id']

    data_maybe = {
        'id': comment_id,
        'user_id': user_id,
        'post_id': post_id,
        'comment_text': default_comment
    }
    data = unwrap(get_comment(client, comment_id))
    assert data == data_maybe
    assert unwrap(get_post_comments(client, post_id)) == [data_maybe]
    assert unwrap(get_post_comments_count(client, post_id))['count'] == 1
