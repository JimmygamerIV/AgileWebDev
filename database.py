from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from pathlib import Path

BASE_DIR = Path(__file__).parent
engine = create_engine(f"sqlite:///{BASE_DIR}/unimap.db")

Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)