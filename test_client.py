import json
import os

sample_creds = [{'login': 'test', 'pwd_hash': '1234'},
                {'login': 'test2', 'pwd_hash': '2345'},
                {'login': 'test3', 'pwd_hash': '3456'}]
sample_wrong_creds = [{'login': 'a', 'pwd_hash': 'b'}]
sample_user_data = [{'user_id': 1, 'session_token': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}]
default_title, default_description, default_ranscription = 'Test title', 'Test description', ''
default_comment = 'Test comment'
filedir = '/documents'
filename = 'test_podcast.mp3'


def set_cookies(client, cookies):
    for k, v in cookies.items():
        client.set_cookie('localhost', key=str(k), value=str(v))


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


def add_post(client, title=default_title, description=default_description, transcription=default_ranscription):
    data = {
        'data': json.dumps({
            'title': title,
            'short_description': description,
            'long_description': transcription,
        }),
        'file': (open(os.path.join(filedir, filename), 'rb'), filename)
    }
    return client.post('/api/post', data=data)


def get_post(client, post_id):
    return client.get('/api/post/' + str(post_id))


def get_feed(client, page=None):
    return client.get('/api/feed/' + (str(page) if page is not None else ''))


def get_search(client, query, page):
    return client.post('/api/search/posts/' + str(page), data=json.dumps({'query': query}))


def get_post_likes(client, post_id):
    return client.get('/api/post/likes/' + str(post_id))


def get_post_likes_count(client, post_id):
    return client.get('/api/post/likes/count/' + str(post_id))


def is_post_liked_by_user(client, post_id):
    return client.get('/api/post/is_liked/' + str(post_id))


def like_post(client, post_id):
    return client.post('/api/post/like/' + str(post_id))


def get_comment(client, comment_id):
    return client.get('/api/comment/' + str(comment_id))


def get_post_comments(client, post_id):
    return client.get('/api/post/comments/' + str(post_id))


def get_post_comments_count(client, post_id):
    return client.get('/api/post/comments/count/' + str(post_id))


def add_post_comment(client, post_id, comment=default_comment):
    return client.post('/api/post/comment/' + str(post_id), data=json.dumps({'comment_text': comment}))


def delete_post(client, post_id):
    return client.delete('/api/post/' + str(post_id))


def get_user_posts(client, user_id):
    return client.get('/api/posts/user/' + str(user_id))


def get_user_profile(client, user_id):
    return client.get('/api/profile/' + str(user_id))
