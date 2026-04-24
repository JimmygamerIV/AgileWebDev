import secrets
import os

def generate_env():
    if not os.path.exists('.env'):
        secret_key = secrets.token_hex(32)
        with open('.env', 'w') as f:
            f.write(f'SECRET_KEY={secret_key}\n')
            f.write(f"DATABASE_URL = sqlite:///unimap.db")