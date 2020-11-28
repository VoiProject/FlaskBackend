from sqlalchemy import Integer, Column, String, DateTime
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    login = Column(String)
    pwd_hash = Column(String)
    registration_dt = Column(DateTime)
    posts = relationship('Post')
    likes = relationship('Like')

    def __init__(self, login, pwd_hash, registration_dt):
        self.login = login
        self.pwd_hash = pwd_hash
        self.registration_dt = registration_dt

    def to_json(self):
        return {'id': self.id,
                'login': self.login,
                'registration_dt': self.registration_dt}
