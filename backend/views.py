from datetime import datetime
import logging

from flask import Flask, jsonify, abort
from backend import app

from .base import Session, Base, engine
from .user import User
from .post import Post

Base.metadata.create_all(engine)

session = Session()
now = datetime.now


@app.route('/', methods=['GET'])
def site_map():
    res = str(app.url_map)
    return res


@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    users = session.query(User).filter(User.id == user_id).all()
    logging.info(f'Found {len(users)} with id={user_id}')
    if len(users) == 0:
        abort(404)
    return jsonify({'user': users[0]})


@app.route('/api/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = list(filter(lambda u: u['id'] == post_id, posts))
    if len(post) == 0:
        abort(404)
    return jsonify({'post': post[0]})


@app.route('/api/posts/user/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    user = list(filter(lambda u: u['id'] == user_id, users))
    if len(user) == 0:
        abort(404)
    user = user[0]
    user_posts = user['posts']

    user_posts = list(filter(lambda p: p['id'] in user_posts, posts))
    if len(user_posts) == 0:
        abort(404)
    return jsonify({'user_posts': user_posts})


@app.route('/api/feed/<int:user_id>', methods=['GET'])
def get_user_feed(user_id):
    user = list(filter(lambda u: u['id'] == user_id, users))
    if len(user) == 0:
        abort(404)
    user = user[0]
    user_posts = user['posts']

    user_feed = list(filter(lambda p: p['id'] not in user_posts, posts))
    return jsonify({'user_feed': user_feed})
