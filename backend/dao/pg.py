import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..base import Base
from ..orm.comment import Comment
from ..orm.like import Like
from ..orm.post import Post
from ..orm.user import User

try:
    engine = create_engine(
        f"postgres://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}")
except KeyError:
    engine = create_engine(
        'postgres://drgghtjs:SGBs0eUt9rh9WVEpDDK0rq00uceccJcp@suleiman.db.elephantsql.com:5432/drgghtjs')
    logging.info('Connected to fallback DB')

Session = sessionmaker(bind=engine, autocommit=True)
Base.metadata.create_all(engine)
db_session = Session()


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


def get_post_likes_count(post_id):
    cnt = db_session.query(Like).filter(Like.post_id == post_id).count()
    return cnt


def get_post_comments_count(post_id):
    cnt = db_session.query(Comment).filter(Comment.post_id == post_id).count()
    return cnt


def post_user_like(post_id, user_id):
    likes = db_session.query(Like) \
        .filter(Like.user_id == user_id, Like.post_id == post_id).all()
    if len(likes) == 0:
        return None
    else:
        return likes[0]


def post_liked_by_user(post_id, user_id):
    like = post_user_like(post_id, user_id)
    if not like:
        return False
    else:
        return True


def user_registration_exists(login):
    ans = db_session.query(User).filter(User.login == login).order_by(User.id.asc()).count()
    return ans > 0


def user_login_exists(login, pwd_hash):
    ans = db_session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).count()
    return ans > 0


def user_login_id(login, pwd_hash):
    ans = db_session.query(User).filter(User.login == login, User.pwd_hash == pwd_hash).order_by(User.id.asc()).one()
    return ans.id
