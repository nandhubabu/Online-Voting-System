"""
seed_data.py — Populates the database with demo data.

Run:  python seed_data.py

Default credentials created:
  CEO:      admin@election.gov.in / Admin@123
  Officer1: officer1@election.gov.in / Officer@123  (Chennai North)
  Officer2: officer2@election.gov.in / Officer@123  (Mumbai South)

Voter registry entries (use these to register voter accounts):
  Voter ID: TN00001  DOB: 1990-05-15  (Chennai North)
  Voter ID: TN00002  DOB: 1985-08-22  (Chennai North)
  Voter ID: TN00003  DOB: 1992-03-10  (Chennai North)
  Voter ID: MH00001  DOB: 1988-11-30  (Mumbai South)
  Voter ID: MH00002  DOB: 1995-07-14  (Mumbai South)
"""

from datetime import date, datetime
from app import app
from extensions import db
from models import (
    Constituency, Party, VoterRegistry,
    ChiefElectionOfficer, ElectionOfficer, Election
)


def seed():
    with app.app_context():
        db.create_all()

        # ── Constituencies ─────────────────────────────────────────
        constituencies = [
            Constituency(name='Chennai North',    district='Chennai',  state='Tamil Nadu'),
            Constituency(name='Chennai South',    district='Chennai',  state='Tamil Nadu'),
            Constituency(name='Mumbai South',     district='Mumbai',   state='Maharashtra'),
            Constituency(name='Delhi Central',    district='Delhi',    state='Delhi'),
            Constituency(name='Bengaluru North',  district='Bengaluru', state='Karnataka'),
        ]
        for c in constituencies:
            if not Constituency.query.filter_by(name=c.name).first():
                db.session.add(c)
        db.session.commit()
        print('✓ Constituencies seeded')

        cn = Constituency.query.filter_by(name='Chennai North').first()
        ms = Constituency.query.filter_by(name='Mumbai South').first()

        # ── Political Parties ──────────────────────────────────────
        parties = [
            Party(party_name='Indian National Congress', symbol='INC', description='Grand Old Party of India'),
            Party(party_name='Bharatiya Janata Party',   symbol='BJP', description='Nationalist party'),
            Party(party_name='Aam Aadmi Party',          symbol='AAP', description='Common Man Party'),
            Party(party_name='Dravida Munnetra Kazhagam', symbol='DMK', description='Tamil regional party'),
            Party(party_name='All India Anna DMK',       symbol='AIADMK', description='Tamil regional party'),
        ]
        for p in parties:
            if not Party.query.filter_by(party_name=p.party_name).first():
                db.session.add(p)
        db.session.commit()
        print('✓ Parties seeded')

        # ── Chief Election Officer ─────────────────────────────────
        if not ChiefElectionOfficer.query.filter_by(email='admin@election.gov.in').first():
            ceo = ChiefElectionOfficer(name='Rajesh Kumar', email='admin@election.gov.in')
            ceo.set_password('Admin@123')
            db.session.add(ceo)
            db.session.commit()
            print('✓ CEO seeded')

        # ── Election Officers ──────────────────────────────────────
        officers = [
            {'name': 'Priya Sharma',  'email': 'officer1@election.gov.in', 'cid': cn.id},
            {'name': 'Arjun Mehta',   'email': 'officer2@election.gov.in', 'cid': ms.id},
        ]
        for o in officers:
            if not ElectionOfficer.query.filter_by(email=o['email']).first():
                off = ElectionOfficer(name=o['name'], email=o['email'], constituency_id=o['cid'])
                off.set_password('Officer@123')
                db.session.add(off)
        db.session.commit()
        print('✓ Officers seeded')

        # ── Voter Registry ─────────────────────────────────────────
        registry_entries = [
            # Chennai North
            dict(voter_id_number='TN00001', full_name='Anbu Selvan',     date_of_birth=date(1990, 5, 15),  constituency_id=cn.id, gender='Male',   address='12 Anna Nagar, Chennai'),
            dict(voter_id_number='TN00002', full_name='Kavitha Rajan',   date_of_birth=date(1985, 8, 22),  constituency_id=cn.id, gender='Female', address='45 T Nagar, Chennai'),
            dict(voter_id_number='TN00003', full_name='Murugan Pillai',  date_of_birth=date(1992, 3, 10),  constituency_id=cn.id, gender='Male',   address='7 Adyar, Chennai'),
            dict(voter_id_number='TN00004', full_name='Deepa Krishnan',  date_of_birth=date(1997, 12, 5),  constituency_id=cn.id, gender='Female', address='23 Velachery, Chennai'),
            dict(voter_id_number='TN00005', full_name='Sathish Kumar',   date_of_birth=date(1983, 6, 18),  constituency_id=cn.id, gender='Male',   address='89 Porur, Chennai'),
            # Mumbai South
            dict(voter_id_number='MH00001', full_name='Rahul Desai',     date_of_birth=date(1988, 11, 30), constituency_id=ms.id, gender='Male',   address='14 Colaba, Mumbai'),
            dict(voter_id_number='MH00002', full_name='Sneha Patil',     date_of_birth=date(1995, 7, 14),  constituency_id=ms.id, gender='Female', address='56 Bandra, Mumbai'),
            dict(voter_id_number='MH00003', full_name='Vikram Joshi',    date_of_birth=date(1980, 4, 2),   constituency_id=ms.id, gender='Male',   address='33 Dadar, Mumbai'),
            dict(voter_id_number='MH00004', full_name='Prachi Nair',     date_of_birth=date(1993, 9, 25),  constituency_id=ms.id, gender='Female', address='78 Worli, Mumbai'),
            dict(voter_id_number='MH00005', full_name='Kiran Shinde',    date_of_birth=date(1991, 1, 8),   constituency_id=ms.id, gender='Male',   address='22 Andheri, Mumbai'),
        ]
        for entry in registry_entries:
            if not VoterRegistry.query.filter_by(voter_id_number=entry['voter_id_number']).first():
                db.session.add(VoterRegistry(**entry))
        db.session.commit()
        print('✓ Voter registry seeded (10 entries)')

        # ── Sample Election (Draft) ────────────────────────────────
        if not Election.query.filter_by(election_name='Chennai North Assembly 2025').first():
            e = Election(
                election_name   = 'Chennai North Assembly 2025',
                election_type   = 'Assembly',
                constituency_id = cn.id,
                start_datetime  = datetime(2025, 12, 1, 8, 0),
                end_datetime    = datetime(2025, 12, 1, 18, 0),
                status          = 'Draft'
            )
            db.session.add(e)
            db.session.commit()
            print('✓ Sample election seeded')

        print('\n✅ Seed complete!')
        print('\n── Login credentials ─────────────────────────────')
        print('  CEO:      admin@election.gov.in     / Admin@123')
        print('  Officer1: officer1@election.gov.in  / Officer@123')
        print('  Officer2: officer2@election.gov.in  / Officer@123')
        print('\n── Voter Registry (register with these) ──────────')
        print('  TN00001  DOB: 1990-05-15  (Chennai North)')
        print('  TN00002  DOB: 1985-08-22  (Chennai North)')
        print('  MH00001  DOB: 1988-11-30  (Mumbai South)')
        print('  MH00002  DOB: 1995-07-14  (Mumbai South)')


if __name__ == '__main__':
    seed()
