from datetime import datetime, timedelta
import logging
from secrets import token_hex

from flask import Flask, jsonify, abort, request, make_response, \
    after_this_request, send_from_directory, redirect
from jinja2.utils import import_string

from backend import app

from .base import Session, Base, engine
from .user import User
from .post import Post
from .like import Like
import json
from flask_cors import CORS, cross_origin

cors = CORS(app)

Base.metadata.create_all(engine)

db_session = Session()
now = datetime.now

PAGE_SIZE = 10  # max number of ideas displayed on page

user_tokens = {}


def user_authenticated():
    user_id = request.cookies.get('user_id')
    session_token = request.cookies.get('session_token')
    if user_id and session_token:
        if str(user_id) in user_tokens and user_tokens[str(user_id)] == session_token:
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
    print(filename, user_authenticated())

    if not user_authenticated():
        return make_clear_token_response(send_from_directory(app.config['UPLOAD_FOLDER'],
                                                             filename))
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
    return jsonify(post.likes)


@app.route('/api/post/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user_auth = user_authenticated()
    if not user_auth:
        abort(401)
    user_id = request.cookies.get('user_id')

    old_like = post_user_like(post_id, user_id)
    if old_like:
        db_session.delete(old_like)
        db_session.commit()
        return jsonify({'status': 'OK', 'like_state': False})
    else:
        like = Like(user_id, post_id)
        db_session.add(like)
        db_session.commit()

        db_session.refresh(like)

        return jsonify({'status': 'OK', 'like_state': True})


def post_user_like(post_id, user_id):
    likes = db_session.query(Like) \
        .filter(Like.user_id == user_id and Like.post_id == post_id).all()
    if len(likes) == 0:
        return None
    else:
        return likes[0]


@app.route('/api/post/is_liked/<int:post_id>', methods=['GET'])
def is_post_liked_by_user(post_id):
    user_auth = user_authenticated()
    if not user_auth:
        return jsonify({'result': False})
    user_id = request.cookies.get('user_id')
    like = post_user_like(post_id, user_id)
    if not like:
        return jsonify({'result': False})
    else:
        return jsonify({'result': True})


@app.route('/api/posts/user/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    user = get_user_by_id(user_id)
    if not user:
        abort(404)

    user_posts = user.posts
    if len(user_posts) == 0:
        abort(404)
    return jsonify({'user_posts': [p.to_json() for p in user_posts]})


@app.route('/api/feed/', defaults={'page_num': 1, 'user_id': 0}, methods=['GET'])
@app.route('/api/feed/<int:user_id>', defaults={'page_num': 1}, methods=['GET'])
@app.route('/api/feed/<int:user_id>/<int:page_num>', methods=['GET'])
def get_user_feed(user_id, page_num):
    user_auth = user_authenticated()
    print("Feed user auth", user_auth)
    if not user_auth and user_id != 0:
        return redirect('/api/feed/0')
    if user_auth and str(user_id) != request.cookies.get('user_id'):
        return redirect('/api/feed/' + request.cookies.get('user_id'))
    posts = db_session.query(Post) \
        .filter(Post.author_id != user_id) \
        .order_by(Post.post_dt.desc()) \
        .offset(PAGE_SIZE * (page_num - 1)) \
        .limit(PAGE_SIZE).all()
    return jsonify({'user_feed': [p.to_json() for p in posts]})


@app.route('/api/register', methods=['POST'])
def register_user():
    data = json.loads(request.get_data())
    login = data['login']
    pwd_hash = data['pwd_hash']
    logging.info(f'Register user call')

    user_exists = user_login_checker(login, pwd_hash)
    print("User", login, pwd_hash, "exists:", user_exists)

    if not user_exists:
        print("Adding new user")
        db_session.add(User(login, pwd_hash, now()))
        db_session.commit()
        add_user_token(user_login_result(login, pwd_hash))
    else:
        abort(409)

    user_id = user_login_result(login, pwd_hash)

    resp = make_response(jsonify({'user_id': user_id}))
    resp.set_cookie('user_id', str(user_id))
    resp.set_cookie('session_token', str(get_user_token(user_id)))
    return resp


@app.route('/api/login', methods=['POST'])
@cross_origin()
def login_user():
    data = json.loads(request.get_data())
    login = data['login']
    pwd_hash = data['pwd_hash']

    user_exists = user_login_checker(login, pwd_hash)
    print("User", login, pwd_hash, "exists:", user_exists)

    user_id = user_login_result(login, pwd_hash)

    if user_exists and not user_authenticated():
        print("Add user session")
        add_user_token(user_id)

    if not user_exists:
        abort(404)

    resp = make_response(jsonify({'user_id': user_id}))
    resp.set_cookie('user_id', str(user_id))
    resp.set_cookie('session_token', str(get_user_token(user_id)))
    return resp


def user_login_checker(login, pwd_hash):
    ans = db_session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).count()
    return ans > 0


def user_login_result(login, pwd_hash):
    ans = db_session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).one()
    return ans.id


@app.route('/api/post', methods=['POST'])
def add_post():
    data = json.loads(request.get_data())
    user_id = data['user_id']

    if not user_id:
        abort(404)
    if not user_authenticated() or not user_id == request.cookies.get('user_id'):
        abort(404)

    title = data['title']
    short_description = data['short_description']
    long_description = data['long_description']

    post = Post(user_id, now(), title, short_description, long_description)
    db_session.add(post)
    db_session.commit()

    db_session.refresh(post)

    return jsonify({'result': 'OK', 'post_id': post.id})


@app.route('/api/post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    # data = json.loads(request.get_data())
    # post_id = data['post_id']
    user_auth = user_authenticated()
    if not user_auth:
        abort(401)
    post = get_post_by_id(post_id)
    if not post:
        abort(404)
    if str(post.authod_id) != request.cookies.get('user_id'):
        abort(401)
    db_session.delete(post)
    db_session.commit()
    return jsonify({'status': 'OK'})


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

                    methods_repr = ""
                    for m in methods:
                        methods_repr += m + " "

                    routes.append({rule.rule: methods_repr})
        except Exception as exc:
            routes.append({rule.rule:
                               "(%s) INVALID ROUTE DEFINITION!!!" % rule.endpoint})
            route_info = "%s => %s" % (rule.rule, rule.endpoint)
            app.logger.error("Invalid route: %s" % route_info, exc_info=True)
            # func_list[rule.rule] = obj.__doc__

    routes = sorted(routes, key=lambda d: list(d.keys()))
    return jsonify(code=200, data=routes)


@app.route('/api/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return abort(404)

    return jsonify({'user': user.to_json(), 'user_posts': user.posts})
