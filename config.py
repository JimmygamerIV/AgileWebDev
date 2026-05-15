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
    
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True

    MAIL_USERNAME = "unimap2026@gmail.com"
    MAIL_PASSWORD = "kczg bskh smwn mvli"
    MAIL_DEFAULT_SENDER = "unimap2026@gmail.com"