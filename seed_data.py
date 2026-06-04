"""
seed_data.py — Populates the database with demo data.

Run:  python seed_data.py

Default credentials created:
  CEO:      admin@election.gov.in / Admin@123
  Officer1: officer1@election.gov.in / Officer@123  (Thiruvananthapuram)
  Officer2: officer2@election.gov.in / Officer@123  (Ernakulam)

Voter registry entries (use these to register voter accounts):
  Voter ID: KL00001  DOB: 1990-05-15  (Thiruvananthapuram)
  Voter ID: KL00002  DOB: 1985-08-22  (Thiruvananthapuram)
  Voter ID: KL00003  DOB: 1992-03-10  (Thiruvananthapuram)
  Voter ID: KL00006  DOB: 1988-11-30  (Ernakulam)
  Voter ID: KL00007  DOB: 1995-07-14  (Ernakulam)
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
            Constituency(name='Thiruvananthapuram', district='Thiruvananthapuram', state='Kerala'),
            Constituency(name='Ernakulam',          district='Ernakulam',          state='Kerala'),
            Constituency(name='Kozhikode',          district='Kozhikode',          state='Kerala'),
            Constituency(name='Wayanad',            district='Wayanad',            state='Kerala'),
            Constituency(name='Thrissur',           district='Thrissur',           state='Kerala'),
        ]
        for c in constituencies:
            if not Constituency.query.filter_by(name=c.name).first():
                db.session.add(c)
        db.session.commit()
        print('✓ Constituencies seeded')

        tvm = Constituency.query.filter_by(name='Thiruvananthapuram').first()
        ekm = Constituency.query.filter_by(name='Ernakulam').first()

        # ── Political Parties ──────────────────────────────────────
        parties = [
            Party(party_name='Communist Party of India (Marxist)', symbol='CPI(M)', description='Left-wing socialist party'),
            Party(party_name='Indian National Congress',           symbol='INC',    description='Centrist party, UDF coalition'),
            Party(party_name='Bharatiya Janata Party',             symbol='BJP',    description='Nationalist party, NDA coalition'),
            Party(party_name='Indian Union Muslim League',          symbol='IUML',   description='Regional party, UDF coalition'),
            Party(party_name='Kerala Congress (M)',                symbol='KC(M)',  description='Regional party, LDF coalition'),
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
            {'name': 'Faisal Rahman',  'email': 'officer1@election.gov.in', 'cid': tvm.id},
            {'name': 'Anjali Nair',     'email': 'officer2@election.gov.in', 'cid': ekm.id},
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
            # Thiruvananthapuram
            dict(voter_id_number='KL00001', full_name='Arjun Nair',        date_of_birth=date(1990, 5, 15),  constituency_id=tvm.id, gender='Male',   address='Flat 4B, Heera Apartments, Kowdiar, Thiruvananthapuram'),
            dict(voter_id_number='KL00002', full_name='Lakshmi Pillai',    date_of_birth=date(1985, 8, 22),  constituency_id=tvm.id, gender='Female', address='Saras, TC 12/342, Pattom, Thiruvananthapuram'),
            dict(voter_id_number='KL00003', full_name='Siddharth Kurup',   date_of_birth=date(1992, 3, 10),  constituency_id=tvm.id, gender='Male',   address='Ganga, TC 5/120, Sasthamangalam, Thiruvananthapuram'),
            dict(voter_id_number='KL00004', full_name='Dhanya Varma',      date_of_birth=date(1997, 12, 5),  constituency_id=tvm.id, gender='Female', address='Nandanam, Kazhakoottam, Thiruvananthapuram'),
            dict(voter_id_number='KL00005', full_name='Madhavan Namboothiri', date_of_birth=date(1983, 6, 18), constituency_id=tvm.id, gender='Male',   address='Illam, Vattiyoorkavu, Thiruvananthapuram'),
            # Ernakulam
            dict(voter_id_number='KL00006', full_name='Mathew Joseph',     date_of_birth=date(1988, 11, 30), constituency_id=ekm.id, gender='Male',   address='24/102 Edappally, Kochi, Ernakulam'),
            dict(voter_id_number='KL00007', full_name='Riya Mary John',    date_of_birth=date(1995, 7, 14),  constituency_id=ekm.id, gender='Female', address='45B Kadavanthra, Kochi, Ernakulam'),
            dict(voter_id_number='KL00008', full_name='Harikrishnan G',    date_of_birth=date(1980, 4, 2),   constituency_id=ekm.id, gender='Male',   address='Pranavam, Tripunithura, Ernakulam'),
            dict(voter_id_number='KL00009', full_name='Sandra K.S.',       date_of_birth=date(1993, 9, 25),  constituency_id=ekm.id, gender='Female', address='Sree Nilayam, Kakkanad, Ernakulam'),
            dict(voter_id_number='KL00010', full_name='Vipin Das',         date_of_birth=date(1991, 1, 8),   constituency_id=ekm.id, gender='Male',   address='12 Marine Drive, Kochi, Ernakulam'),
        ]
        for entry in registry_entries:
            if not VoterRegistry.query.filter_by(voter_id_number=entry['voter_id_number']).first():
                db.session.add(VoterRegistry(**entry))
        db.session.commit()
        print('✓ Voter registry seeded (10 entries)')

        # ── Sample Election (Draft) ────────────────────────────────
        if not Election.query.filter_by(election_name='Thiruvananthapuram Assembly 2026').first():
            e = Election(
                election_name   = 'Thiruvananthapuram Assembly 2026',
                election_type   = 'Assembly',
                constituency_id = tvm.id,
                start_datetime  = datetime(2026, 12, 1, 8, 0),
                end_datetime    = datetime(2026, 12, 1, 18, 0),
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
        print('  KL00001  DOB: 1990-05-15  (Thiruvananthapuram)')
        print('  KL00002  DOB: 1985-08-22  (Thiruvananthapuram)')
        print('  KL00006  DOB: 1988-11-30  (Ernakulam)')
        print('  KL00007  DOB: 1995-07-14  (Ernakulam)')


if __name__ == '__main__':
    seed()
