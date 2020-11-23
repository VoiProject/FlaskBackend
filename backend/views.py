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

PAGE_SIZE = 10  # max number of ideas displayed on page


@app.route('/', methods=['GET'])
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
    return jsonify({'user': users[0].to_json()})


@app.route('/api/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    posts = session.query(Post) \
        .filter(Post.id == post_id).all()
    if len(posts) == 0:
        abort(404)
    return jsonify({'post': posts[0].to_json()})


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


@app.route('/api/feed/<int:user_id>', defaults={'page_num': 1}, methods=['GET'])
@app.route('/api/feed/<int:user_id>/<int:page_num>', methods=['GET'])
def get_user_feed(user_id, page_num):
    posts = session.query(Post) \
        .filter(Post.author_id != user_id) \
        .order_by(Post.post_dt.desc()) \
        .offset(PAGE_SIZE * (page_num - 1)) \
        .limit(PAGE_SIZE).all()
    return jsonify({'user_feed': [p.to_json() for p in posts]})
