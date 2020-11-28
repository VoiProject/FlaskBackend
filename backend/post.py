from sqlalchemy import ForeignKey, Integer, Column, String, DateTime
from sqlalchemy.orm import relationship

from .base import Base


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    post_dt = Column(DateTime)
    title = Column(String(128))
    short_description = Column(String(256))
    long_description = Column(String(1024))
    likes = relationship('Like', cascade="all,delete")
    comments = relationship('Comment', cascade="all,delete")

    def __init__(self, author_id, post_dt, title, short_description, long_description):
        self.author_id = author_id
        self.post_dt = post_dt
        self.title = title
        self.short_description = short_description
        self.long_description = long_description

    def to_json(self):
        return {'id': self.id,
                'author_id': self.author_id,
                'post_dt': self.post_dt,
                'title': self.title,
                'short_description': self.short_description,
                'long_description': self.long_description}
