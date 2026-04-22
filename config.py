import os

class Config:
    #python -c "import secrets; print(secrets.token_hex(16))"
    SECRET_KEY = os.getenv("SECRET_KEY")