import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:

    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(BASE_DIR / 'unimap.db')
    

    TIMETABLES_DIR = BASE_DIR / "timetables"
    

    WTF_CSRF_ENABLED = True
    BUILDINGS_JSON = BASE_DIR / "buildings.json"
    POIS_JSON = BASE_DIR / "pois.json"
