import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY            = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                          'mysql+pymysql://root:password@localhost:3306/voting_db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = True
