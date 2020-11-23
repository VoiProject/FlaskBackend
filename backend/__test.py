from datetime import datetime

from .base import Session, Base, engine
from .user import User
from .post import Post

Base.metadata.create_all(engine)

session = Session()
now = datetime.now
