import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workshop.db')
DB_URL = f'sqlite:///{DB_PATH}'

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
