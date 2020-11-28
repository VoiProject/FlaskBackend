from datetime import datetime, timedelta
import logging

from flask import Flask, jsonify, abort, request, make_response, after_this_request, send_from_directory, redirect

from backend import app

from .base import Session, Base, engine
from .user import User
from .post import Post
import json
from flask_cors import CORS, cross_origin

cors = CORS(app)

Base.metadata.create_all(engine)

session = Session()
now = datetime.now

PAGE_SIZE = 10  # max number of ideas displayed on page


@app.route('/', methods=['GET'])
def index():
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               'index.html')


@app.route('/<path:filename>', methods=['GET'])
def root(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/api/', methods=['GET'])
def site_map():
    res = str(app.url_map)
    return res


@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    users = session.query(User) \
        .filter(User.id == user_id).all()
    logging.info(f'Found {len(users)} with id={user_id}')
    if len(users) == 0:
        abort(404)
    return jsonify(users[0].to_json())


@app.route('/api/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    posts = session.query(Post) \
        .filter(Post.id == post_id).all()
    if len(posts) == 0:
        abort(404)
    return jsonify(posts[0].to_json())


@app.route('/api/posts/user/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    users = session.query(User) \
        .filter(User.id == user_id).all()
    if len(users) == 0:
        abort(404)
    user = users[0]
    user_posts = user.posts
    if len(user_posts) == 0:
        abort(404)
    return jsonify({'user_posts': [p.to_json() for p in user_posts]})


@app.route('/api/feed/', defaults={'page_num': 1, 'user_id': -1}, methods=['GET'])
@app.route('/api/feed/<int:user_id>', defaults={'page_num': 1}, methods=['GET'])
@app.route('/api/feed/<int:user_id>/<int:page_num>', methods=['GET'])
def get_user_feed(user_id, page_num):
    print("getting feed")
    posts = session.query(Post) \
        .filter(Post.author_id != user_id) \
        .order_by(Post.post_dt.desc()) \
        .offset(PAGE_SIZE * (page_num - 1)) \
        .limit(PAGE_SIZE).all()
    return jsonify({'user_feed': [p.to_json() for p in posts]})


@app.route('/api/register', methods=['POST'])
def register_user():
    login = request.args.get('login', type=str)
    pwd_hash = request.args.get('pwd_hash', type=str)
    logging.info(f'Register user call')

    user_exists = user_login_checker(login, pwd_hash)
    print("User", login, pwd_hash, "exists:", user_exists)

    if not user_exists:
        print("Adding new user")
        session.add(User(login, pwd_hash, now()))
        session.commit()
    else:
        abort(404)

    return jsonify({'user_id': user_login_result(login, pwd_hash)})

    # res = make_response("Register response")
    # res.set_cookie('user_id', user_login_result(login, pwd_hash))
    # return res


@app.route('/api/login', methods=['POST'])
@cross_origin()
def login_user():
    data = json.loads(request.get_data())
    login = data['login']
    pwd_hash = data['pwd_hash']

    user_exists = user_login_checker(login, pwd_hash)
    print("User", login, pwd_hash, "exists:", user_exists)

    if not user_exists:
        abort(404)

    return jsonify({'user_id': user_login_result(login, pwd_hash)})


def user_login_checker(login, pwd_hash):
    ans = session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).count()
    return ans > 0


def user_login_result(login, pwd_hash):
    ans = session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).one()
    return ans.id


@app.route('/api/post', methods=['POST'])
def add_post():
    data = json.loads(request.get_data())
    user_id = data['user_id']
    if not user_id:
        abort(404)

    title = data['title']
    short_description = data['short_description']
    long_description = data['long_description']

    post = Post(user_id, now(), title, short_description, long_description)
    session.add(post)
    session.commit()

    session.refresh(post)

    return jsonify({'result': 'OK', 'post_id': post.id})
