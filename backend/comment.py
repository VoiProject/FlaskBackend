from sqlalchemy import ForeignKey, Integer, Column, String, DateTime
from sqlalchemy.orm import relationship

from .base import Base


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))
    comment_text = Column(String(512))

    def __init__(self, user_id, post_id, comment_text):
        self.user_id = user_id
        self.post_id = post_id
        self.comment_text = comment_text

    def to_json(self):
        return {'id': self.id,
                'user_id': self.user_id,
                'post_id': self.post_id,
                'comment_text': self.comment_text
                }
