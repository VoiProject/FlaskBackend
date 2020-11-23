from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('postgres://jkemxbmo:Y8Ympw1YUisZplQZJuwmRah9ODa8n6vV@rogue.db.elephantsql.com:5432/jkemxbmo')

Base = declarative_base()
Session = sessionmaker(bind=engine)
