"""
init_db.py — Database initialization script.
Run this script to create tables and ensure the default Admin account exists.
"""

from app import app
from extensions import db
from models import ChiefElectionOfficer

def init_database():
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Ensure default Admin (CEO) exists
        admin_email = 'admin@election.gov.in'
        ceo = ChiefElectionOfficer.query.filter_by(email=admin_email).first()
        if not ceo:
            ceo = ChiefElectionOfficer(
                name='Chief Election Officer',
                email=admin_email
            )
            ceo.set_password('Admin@123')
            db.session.add(ceo)
            db.session.commit()
            print(f"Default CEO admin account created: {admin_email} / Admin@123")
        else:
            print(f"CEO admin account already exists: {admin_email}")

if __name__ == '__main__':
    init_database()
