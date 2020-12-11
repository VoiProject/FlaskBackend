from sqlalchemy import ForeignKey, Integer, Column, String, DateTime
from sqlalchemy.orm import relationship

from ..base import Base


class Like(Base):
    __tablename__ = 'likes'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), primary_key=True)

    def __init__(self, user_id, post_id):
        self.user_id = user_id
        self.post_id = post_id

    def to_json(self):
        return {'user_id': self.user_id,
                'post_id': self.post_id
                }
