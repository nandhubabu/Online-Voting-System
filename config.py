import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

db_url = os.environ.get('DATABASE_URL', 'sqlite:///voting.db')

# Automatically normalize production database connection strings
if db_url.startswith('mysql://'):
    db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
elif db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_DATABASE_URI = db_url
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = True
