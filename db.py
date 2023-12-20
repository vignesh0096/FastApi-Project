from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQL_DATABASE_URL = "mysql+mysqlconnector://root:Vrdella!6@localhost/jwt"

engine = create_engine(SQL_DATABASE_URL)

Session_local = sessionmaker(autoflush=False,autocommit=False,bind=engine)

Base = declarative_base()


def get_db():
    try:
        db = Session_local()
        yield db
    finally:
        db.close()