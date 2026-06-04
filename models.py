"""
models.py — All SQLAlchemy models in one file.

Tables:
  Constituency, Party, VoterRegistry,
  User, ElectionOfficer, ChiefElectionOfficer,
  Election, Candidate, Vote, AuditLog
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# ── Base Model with Custom Init for Linters ───────────────────────────────────

class BaseModel(db.Model):
    __abstract__ = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# ── Constituency ──────────────────────────────────────────────────────────────

class Constituency(BaseModel):
    __tablename__ = 'constituencies'

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(150), nullable=False, unique=True)
    district = db.Column(db.String(100), nullable=False)
    state    = db.Column(db.String(100), nullable=False)

    voter_records = db.relationship('VoterRegistry',   backref='constituency', lazy=True)
    elections     = db.relationship('Election',         backref='constituency', lazy=True)
    officers      = db.relationship('ElectionOfficer',  backref='constituency', lazy=True)

    def __repr__(self):
        return f'<Constituency {self.name}>'


# ── Political Party ───────────────────────────────────────────────────────────

class Party(BaseModel):
    __tablename__ = 'parties'

    id          = db.Column(db.Integer, primary_key=True)
    party_name  = db.Column(db.String(150), nullable=False, unique=True)
    symbol      = db.Column(db.String(100))
    description = db.Column(db.Text)

    candidates  = db.relationship('Candidate', backref='party', lazy=True)

    def __repr__(self):
        return f'<Party {self.party_name}>'


# ── Voter Registry (pre-loaded government list) ───────────────────────────────

class VoterRegistry(BaseModel):
    __tablename__ = 'voter_registry'

    id              = db.Column(db.Integer, primary_key=True)
    voter_id_number = db.Column(db.String(20), nullable=False, unique=True, index=True)
    full_name       = db.Column(db.String(200), nullable=False)
    date_of_birth   = db.Column(db.Date, nullable=False)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=False)
    gender          = db.Column(db.Enum('Male', 'Female', 'Other', name='gender_types'), nullable=False)
    address         = db.Column(db.Text)
    is_active       = db.Column(db.Boolean, default=True)

    user_account    = db.relationship('User', backref='registry', uselist=False)

    def __repr__(self):
        return f'<VoterRegistry {self.voter_id_number}>'


# ── Voter User Account ────────────────────────────────────────────────────────

class User(UserMixin, BaseModel):
    __tablename__ = 'users'

    id                = db.Column(db.Integer, primary_key=True)
    voter_registry_id = db.Column(db.Integer, db.ForeignKey('voter_registry.id'),
                                  nullable=False, unique=True)
    email             = db.Column(db.String(180), nullable=False, unique=True, index=True)
    password_hash     = db.Column(db.String(256), nullable=False)
    account_status    = db.Column(
        db.Enum('pending', 'approved', 'rejected', 'suspended', name='account_status_types'),
        default='pending', nullable=False
    )
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    votes             = db.relationship('Vote', backref='voter', lazy=True)

    # ── helpers ──
    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def full_name(self):
        return self.registry.full_name if self.registry else 'Unknown'

    @property
    def constituency_id(self):
        return self.registry.constituency_id if self.registry else None

    def __repr__(self):
        return f'<User {self.email}>'


# ── Election Officer ──────────────────────────────────────────────────────────

class ElectionOfficer(UserMixin, BaseModel):
    __tablename__ = 'election_officers'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(200), nullable=False)
    email           = db.Column(db.String(180), nullable=False, unique=True, index=True)
    password_hash   = db.Column(db.String(256), nullable=False)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'))

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def __repr__(self):
        return f'<ElectionOfficer {self.email}>'


# ── Chief Election Officer (Super Admin) ──────────────────────────────────────

class ChiefElectionOfficer(UserMixin, BaseModel):
    __tablename__ = 'chief_election_officers'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(200), nullable=False)
    email         = db.Column(db.String(180), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def __repr__(self):
        return f'<CEO {self.email}>'


# ── Election ──────────────────────────────────────────────────────────────────

class Election(BaseModel):
    __tablename__ = 'elections'

    id              = db.Column(db.Integer, primary_key=True)
    election_name   = db.Column(db.String(250), nullable=False)
    election_type   = db.Column(
        db.Enum('Parliamentary', 'Assembly', 'Municipal', 'Panchayat', name='election_types'),
        nullable=False
    )
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=False)
    start_datetime  = db.Column(db.DateTime, nullable=False)
    end_datetime    = db.Column(db.DateTime, nullable=False)
    status          = db.Column(
        db.Enum('Draft', 'Scheduled', 'Active', 'Closed', 'Published', name='election_status_types'),
        default='Draft', nullable=False
    )
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    candidates      = db.relationship('Candidate', backref='election', lazy=True)
    votes           = db.relationship('Vote',      backref='election', lazy=True)

    @property
    def is_currently_active(self):
        now = datetime.utcnow()
        return (self.status == 'Active' and
                self.start_datetime <= now <= self.end_datetime)

    @property
    def total_votes(self):
        return len(self.votes)

    def __repr__(self):
        return f'<Election {self.election_name}>'


# ── Candidate ─────────────────────────────────────────────────────────────────

class Candidate(BaseModel):
    __tablename__ = 'candidates'

    id               = db.Column(db.Integer, primary_key=True)
    full_name        = db.Column(db.String(200), nullable=False)
    party_id         = db.Column(db.Integer, db.ForeignKey('parties.id'))
    constituency_id  = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=False)
    election_id      = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    candidate_status = db.Column(
        db.Enum('Pending', 'Approved', 'Rejected', name='candidate_status_types'),
        default='Pending', nullable=False
    )

    constituency     = db.relationship('Constituency', foreign_keys=[constituency_id])
    votes_received   = db.relationship('Vote', backref='candidate', lazy=True)

    @property
    def vote_count(self):
        return len(self.votes_received)

    def __repr__(self):
        return f'<Candidate {self.full_name}>'


# ── Vote ──────────────────────────────────────────────────────────────────────

class Vote(BaseModel):
    __tablename__  = 'votes'
    __table_args__ = (
        db.UniqueConstraint('voter_id', 'election_id', name='uq_one_vote_per_election'),
    )

    id             = db.Column(db.Integer, primary_key=True)
    election_id    = db.Column(db.Integer, db.ForeignKey('elections.id'),  nullable=False)
    candidate_id   = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    voter_id       = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=False)
    vote_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Vote election={self.election_id}>'


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(BaseModel):
    __tablename__ = 'audit_logs'

    id         = db.Column(db.Integer, primary_key=True)
    actor_type = db.Column(db.String(50))    # 'voter' | 'officer' | 'admin'
    actor_id   = db.Column(db.Integer)
    action     = db.Column(db.String(100))
    details    = db.Column(db.Text)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AuditLog {self.action}>'
