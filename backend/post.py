from sqlalchemy import ForeignKey, Integer, Column, String, DateTime

from .base import Base


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    post_dt = Column(DateTime)
    title = Column(String)
    short_description = Column(String)
    long_description = Column(String)

    def __init__(self, author_id, post_dt, title, short_description, long_description):
        self.author_id = author_id
        self.post_dt = post_dt
        self.title = title
        self.short_description = short_description
        self.long_description = long_description
