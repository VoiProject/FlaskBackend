from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

try:
    env_vars = {
        "db": os.environ['POSTGRES_DB'],
        "user": os.environ['POSTGRES_USER'],
        "pass": os.environ['POSTGRES_PASSWORD'],
        "db_port": os.environ['POSTGRES_PORT'],
        "host": os.environ['POSTGRES_HOST']
    }
    use_docker_config = True
    engine = create_engine(
        f'postgres://{env_vars["user"]}:{env_vars["pass"]}@{env_vars["host"]}:{env_vars["db_port"]}/{env_vars["db"]}')
except KeyError:
    use_docker_config = False
    engine = create_engine(
        'postgres://drgghtjs:SGBs0eUt9rh9WVEpDDK0rq00uceccJcp@suleiman.db.elephantsql.com:5432/drgghtjs')

print("USING DOCKER CONFIG:", use_docker_config)

Base = declarative_base()
Session = sessionmaker(bind=engine)
