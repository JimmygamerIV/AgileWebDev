import secrets
import os


secret_key = secrets.token_hex(32)

with open('.env', 'w') as f:
    f.write(f'SECRET_KEY={secret_key}\n')
