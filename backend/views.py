import hashlib
from datetime import datetime
import json
import logging
import math
import os
from secrets import token_hex

from elasticsearch import Elasticsearch
from flask import jsonify, abort, request, make_response, send_from_directory, redirect
from flask_cors import CORS, cross_origin
from jinja2.utils import import_string
from sqlalchemy import func
from werkzeug.utils import secure_filename

from backend import app

from .base import Session, Base, engine
from .user import User
from .post import Post
from .like import Like
from .comment import Comment

cors = CORS(app)

Base.metadata.create_all(engine)
db_session = Session()

try:
    es = Elasticsearch([{'host': os.environ['ELASTIC_HOST'], 'port': os.environ['ELASTIC_PORT']}])
except:
    logging.info("ElasticSearch not connected")
    es = None

now = datetime.now

config = {
    'page_size': 5,  # max number of ideas displayed on page
}

user_tokens = {}

uploads_dir = app.config['AUDIO_STORAGE']
os.makedirs(uploads_dir, exist_ok=True)


def user_authenticated():
    user_id = request.cookies.get('user_id')
    session_token = request.cookies.get('session_token')
    if user_id and session_token:
        if user_tokens.get(str(user_id), None) == session_token:
            return True
    return False


def make_clear_token_response(data):
    resp = make_response(data)
    resp.set_cookie('user_id', '', expires=0)
    resp.set_cookie('session_token', '', expires=0)
    return resp


def add_user_token(user_id):
    user_tokens[str(user_id)] = token_hex(16)


def get_user_token(user_id):
    return user_tokens[str(user_id)]


def get_user_by_id(user_id):
    users = db_session.query(User) \
        .filter(User.id == user_id).all()
    if len(users) == 0:
        return None
    return users[0]


def get_post_by_id(post_id):
    posts = db_session.query(Post) \
        .filter(Post.id == post_id).all()
    if len(posts) == 0:
        return None
    return posts[0]


def get_comment_by_id(comment_id):
    comments = db_session.query(Comment) \
        .filter(Comment.id == comment_id).all()
    if len(comments) == 0:
        return None
    return comments[0]


@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(config)


@app.route('/login.html', methods=['GET'])
def login_page():
    return make_clear_token_response(send_from_directory(app.config['UPLOAD_FOLDER'],
                                                         'login.html'))


@app.route('/register.html', methods=['GET'])
def register_page():
    return make_clear_token_response(send_from_directory(app.config['UPLOAD_FOLDER'],
                                                         'register.html'))


@app.route('/', methods=['GET'])
def index():
    return redirect('/index.html')


@app.route('/<path:filename>', methods=['GET'])
def root(filename):
    data = send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

    if not user_authenticated():
        return make_clear_token_response(send_from_directory(app.config['UPLOAD_FOLDER'], filename))
    else:
        return make_response(data)


@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        abort(404)
    return jsonify(user.to_json())


@app.route('/api/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = get_post_by_id(post_id)
    if not post:
        abort(404)
    return jsonify(post.to_json())


@app.route('/api/post/likes/<int:post_id>', methods=['GET'])
def get_post_likes(post_id):
    post = get_post_by_id(post_id)
    if not post:
        abort(404)
    return jsonify([c.to_json() for c in post.likes])


@app.route('/api/post/likes/count/<int:post_id>', methods=['GET'])
def get_post_likes_count_request(post_id):
    post = get_post_by_id(post_id)
    if not post:
        abort(404)
    return jsonify({'count': get_post_likes_count(post_id)})


def get_post_likes_count(post_id):
    cnt = db_session.query(Like).filter(Like.post_id == post_id).count()
    return cnt


@app.route('/api/post/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user_auth = user_authenticated()
    if not user_auth:
        abort(401)
    user_id = request.cookies.get('user_id')

    post = get_post_by_id(post_id)
    if not post:
        abort(404)

    old_like = post_user_like(post_id, user_id)
    if old_like:
        db_session.delete(old_like)
        db_session.commit()
        return jsonify({'status': 'OK', 'like_state': False})
    else:
        like = Like(user_id, post_id)
        db_session.add(like)
        db_session.commit()

        return jsonify({'status': 'OK', 'like_state': True})


def post_user_like(post_id, user_id):
    likes = db_session.query(Like) \
        .filter(Like.user_id == user_id, Like.post_id == post_id).all()
    if len(likes) == 0:
        return None
    else:
        return likes[0]


@app.route('/api/post/is_liked/<int:post_id>', methods=['GET'])
def is_post_liked_by_user_request(post_id):
    return jsonify({'like_state': is_post_liked_by_user(post_id)})


def is_post_liked_by_user(post_id):
    user_auth = user_authenticated()
    if not user_auth:
        return False
    user_id = request.cookies.get('user_id')

    like = post_user_like(post_id, user_id)
    if not like:
        return False
    else:
        return True


@app.route('/api/comment/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    comment = get_comment_by_id(comment_id)
    if not comment:
        abort(404)
    return jsonify(comment.to_json())


@app.route('/api/post/comments/<int:post_id>', methods=['GET'])
def get_post_comments(post_id):
    post = get_post_by_id(post_id)
    if not post:
        abort(404)
    return jsonify([c.to_json() for c in post.comments])


@app.route('/api/post/comments/count/<int:post_id>', methods=['GET'])
def get_post_comments_count_request(post_id):
    post = get_post_by_id(post_id)
    if not post:
        abort(404)
    return jsonify({'count': get_post_comments_count(post_id)})


def get_post_comments_count(post_id):
    cnt = db_session.query(Comment).filter(Comment.post_id == post_id).count()
    return cnt


@app.route('/api/post/comment/<int:post_id>', methods=['POST'])
def add_post_comment(post_id):
    """
    REQUIRE JSON: {'comment_text': <str>}
    """
    user_auth = user_authenticated()
    if not user_auth:
        abort(401)
    user_id = request.cookies.get('user_id')

    post = get_post_by_id(post_id)
    if not post:
        abort(404)

    data = json.loads(request.get_data())
    comment_text = data['comment_text']

    comment = Comment(user_id, post_id, comment_text)
    db_session.add(comment)
    db_session.commit()

    return jsonify({'status': 'OK'})


@app.route('/api/posts/user/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    user = get_user_by_id(user_id)
    if not user:
        abort(404)

    user_posts = user.posts
    if len(user_posts) == 0:
        abort(404)

    return jsonify({'user_posts': [p.to_json() for p in user_posts]})


@app.route('/api/feed/', defaults={'page_num': 1}, methods=['GET'])
@app.route('/api/feed/<int:page_num>', methods=['GET'])
def get_user_feed(page_num):
    user_auth = user_authenticated()
    if not user_auth:
        user_id = 0
    else:
        user_id = request.cookies.get('user_id')

    query = db_session.query(Post) \
        .filter(Post.author_id != user_id) \
        .order_by(Post.post_dt.desc())

    pages_count = math.ceil(query.count() / config['page_size'])
    posts = query \
        .offset(config['page_size'] * (page_num - 1)) \
        .limit(config['page_size']).all()

    return jsonify({'pages_count': pages_count, 'user_feed': [{"post": p.to_json(),
                                                               "likes_count": get_post_likes_count(p.id),
                                                               "liked_by_user": is_post_liked_by_user(p.id),
                                                               "comments_count": get_post_comments_count(p.id),
                                                               "author_login": get_user_by_id(p.author_id).login}
                                                              for p in posts]})


def get_hash(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


@app.route('/api/register', methods=['POST'])
def register_user():
    """
     REQUIRE JSON: {'login': <str>, 'pwd_hash': <str>}
    """
    data = json.loads(request.get_data())
    login = data['login']
    pwd_hash = get_hash(data['pwd_hash'])

    user_exists = user_registration_exists(login)

    if not user_exists:
        db_session.add(User(login, pwd_hash, now()))
        db_session.commit()
        add_user_token(user_login_id(login, pwd_hash))
    else:
        abort(409)

    user_id = user_login_id(login, pwd_hash)

    resp = make_response(jsonify({'user_id': user_id}))
    resp.set_cookie('user_id', str(user_id))
    resp.set_cookie('session_token', str(get_user_token(user_id)))

    return resp


@app.route('/api/login', methods=['POST'])
@cross_origin()
def login_user():
    """
     REQUIRE JSON: {'login': <str>, 'pwd_hash': <str>}
    """

    data = json.loads(request.get_data())
    login = data['login']
    pwd_hash = get_hash(data['pwd_hash'])

    user_exists = user_login_exists(login, pwd_hash)
    if not user_exists:
        abort(404)

    user_id = user_login_id(login, pwd_hash)

    if user_exists and not user_authenticated():
        add_user_token(user_id)

    resp = make_response(jsonify({'user_id': user_id}))
    resp.set_cookie('user_id', str(user_id))
    resp.set_cookie('session_token', str(get_user_token(user_id)))

    return resp


def user_registration_exists(login):
    ans = db_session.query(User).filter(User.login == login).order_by(User.id.asc()).count()
    return ans > 0


def user_login_exists(login, pwd_hash):
    ans = db_session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).count()
    return ans > 0


def user_login_id(login, pwd_hash):
    ans = db_session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).one()
    return ans.id


@app.route('/api/post', methods=['POST'])
def add_post():
    """
    REQUIRE JSON: {'title': <str>, 'short_description': <str>, 'long_description': <str>}
    REQUIRE FILE: file: <audio>
    """
    try:
        print(request.files)
        is_this_file = request.files.get('file')
        print(is_this_file)
        print(is_this_file.filename)
    except AttributeError:
        print("Has no file")
        abort(404)

    data = json.loads(request.form['data'])

    user_auth = user_authenticated()
    if not user_auth:
        abort(401)
    user_id = request.cookies.get('user_id')

    title = data['title']
    short_description = data['short_description']
    long_description = data['long_description']

    file_name = request.files.get('file').filename
    filename, file_extension = os.path.splitext(file_name)
    audio_link = str(hash(db_session.query(func.max(Post.id)).scalar())) + "_" + str(hash(file_name)) + file_extension

    print("Saving ", os.path.join(app.config['AUDIO_STORAGE'], audio_link))
    request.files.get('file').save(os.path.join(uploads_dir, secure_filename(audio_link)))

    dt = now()
    post = Post(user_id, dt, title, short_description, long_description, audio_link)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    if es is not None:
        data_with_user_id = {**data, 'author_id': user_id, 'post_dt': dt}
        es.index('posts', id=post.id, body=data_with_user_id)

    return jsonify({'status': 'OK', 'post_id': post.id})


@app.route('/api/post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    user_auth = user_authenticated()
    if not user_auth:
        abort(401)
    user_id = request.cookies.get('user_id')

    post = get_post_by_id(post_id)

    if not post:
        abort(404)

    if str(post.author_id) != user_id:
        abort(401)

    db_session.delete(post)
    db_session.commit()

    if es is not None:
        es.delete('posts', id=post_id)

    return jsonify({'status': 'OK'})


@app.route('/api/search/posts/<int:page_num>', methods=['POST'])
def search_posts(page_num):
    """
    REQUIRE JSON: {'query': <str>}
    """
    user_auth = user_authenticated()
    if not user_auth:
        user_id = 0
    else:
        user_id = request.cookies.get('user_id')

    data = json.loads(request.get_data())
    body = {
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": data["query"],
                        "fuzziness": "AUTO",
                        "tie_breaker": 0.4,
                        "fields": ["title", "short_description", "long_description"]
                    }
                },
                "must_not": {
                    "match": {
                        "author_id": user_id
                    }
                }
            }
        }
    }
    search_body = {**body,
                   "from": (page_num - 1) * config['page_size'],
                   "size": config['page_size']}

    count_result = es.count(index='posts', body=body)
    pages_count = math.ceil(count_result['count'] / config['page_size'])
    search_result = es.search(index='posts', body=search_body)
    user_feed = [{**hit['_source'], 'id': hit['_id']} for hit in search_result['hits']['hits']]

    return jsonify({'pages_count': pages_count, 'user_feed': [full_post_info_str(p)
                                                              for p in user_feed]})


def get_es_size():
    return es.count(index='posts', body={"query": {"match_all": {}}})['count']


@app.route('/api/sync/postgresql_to_elasticsearch', methods=['GET'])
def sync_postgresql_to_elasticsearch():
    es_size_old = get_es_size()
    posts = db_session.query(Post).all()

    for post in posts:
        post_json = post.to_json()
        del post_json['id']
        es.index('posts', id=post.id, body=post_json)

    es.indices.refresh(index="posts")
    es_size_new = get_es_size()
    return jsonify(
        {'status': 'OK', 'es_size_old': es_size_old, 'es_size_new': es_size_new, 'postgres_size': len(posts)})


@app.route('/api/', methods=['GET'])
@app.route('/api/help', methods=['GET'])
def routes_info():
    routes = []
    for rule in app.url_map.iter_rules():
        try:
            if rule.endpoint != 'static':
                if hasattr(app.view_functions[rule.endpoint], 'import_name'):
                    import_name = app.view_functions[rule.endpoint].import_name
                    obj = import_string(import_name)
                    routes.append({rule.rule: "%s\n%s" % (",".join(list(rule.methods)), obj.__doc__)})
                else:
                    methods = list(filter(lambda x: x in ['GET', 'POST', 'DELETE', 'PUT', 'PATCH'], list(rule.methods)))

                    methods_repr = []
                    for m in methods:
                        methods_repr.append(m)

                    endpoint_doc = app.view_functions[rule.endpoint].__doc__
                    if endpoint_doc:
                        methods_repr.append(list(str(endpoint_doc).split('\n'))[1:-1])

                    routes.append({rule.rule: methods_repr})
        except Exception as exc:
            routes.append({rule.rule:
                               "(%s) INVALID ROUTE DEFINITION!!!" % rule.endpoint})
            route_info = "%s => %s" % (rule.rule, rule.endpoint)
            app.logger.error("Invalid route: %s" % route_info, exc_info=True)

    routes = sorted(routes, key=lambda d: list(d.keys()))
    return jsonify(code=200, data=routes)


@app.route('/api/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return abort(404)

    return jsonify({'user': user.to_json(), 'user_posts': [full_post_info(x) for x in user.posts]})


@app.route('/api/audio/<path:audio_link>', methods=['GET'])
def get_audio(audio_link):
    data = send_from_directory(app.config['AUDIO_STORAGE'],
                               audio_link)

    if not user_authenticated():
        return make_clear_token_response(send_from_directory(os.path.join(uploads_dir), audio_link))
    else:
        return make_response(data)


def full_post_info_str(post):
    return {"post": post,
            "likes_count": get_post_likes_count(post['id']),
            "liked_by_user": is_post_liked_by_user(post['id']),
            "comments_count": get_post_comments_count(post['id']),
            "author_login": get_user_by_id(post['author_id']).login}


def full_post_info(p):
    return {"post": p.to_json(),
            "likes_count": get_post_likes_count(p.id),
            "liked_by_user": is_post_liked_by_user(p.id),
            "comments_count": get_post_comments_count(p.id),
            "author_login": get_user_by_id(p.author_id).login}
