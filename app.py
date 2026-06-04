"""
app.py — Online Voting System
Flask application with all routes in one file.

Roles:
  voter        → /voter/*
  officer      → /officer/*
  admin (CEO)  → /admin/*
"""

from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, session
)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps

import config
from extensions import db, login_manager, csrf, migrate
from models import (
    User, ElectionOfficer, ChiefElectionOfficer,
    VoterRegistry, Constituency, Party,
    Election, Candidate, Vote, AuditLog
)

# ─────────────────────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config.from_object(config)

db.init_app(app)
csrf.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


# ─────────────────────────────────────────────────────────────────────────────
# User Loader (multi-role)
# ─────────────────────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    role = session.get('role')
    if role == 'voter':
        return db.session.get(User, int(user_id))
    if role == 'officer':
        return db.session.get(ElectionOfficer, int(user_id))
    if role == 'admin':
        return db.session.get(ChiefElectionOfficer, int(user_id))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Role Decorators
# ─────────────────────────────────────────────────────────────────────────────

def voter_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or session.get('role') != 'voter':
            flash('Voter login required.', 'warning')
            return redirect(url_for('login'))
        if current_user.account_status != 'approved':
            flash(f'Account is {current_user.account_status}. Please wait for approval.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def officer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or session.get('role') != 'officer':
            flash('Election Officer login required.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or session.get('role') != 'admin':
            flash('Admin login required.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Helper — Audit logging
# ─────────────────────────────────────────────────────────────────────────────

def log_action(actor_type, actor_id, action, details=''):
    entry = AuditLog(actor_type=actor_type, actor_id=actor_id,
                     action=action, details=details)
    db.session.add(entry)
    db.session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Root
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))


# ─────────────────────────────────────────────────────────────────────────────
# Auth — Login / Register / Logout
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role     = request.form.get('role', 'voter')
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user_obj = None
        if role == 'voter':
            user_obj = User.query.filter_by(email=email).first()
        elif role == 'officer':
            user_obj = ElectionOfficer.query.filter_by(email=email).first()
        elif role == 'admin':
            user_obj = ChiefElectionOfficer.query.filter_by(email=email).first()

        if user_obj and user_obj.check_password(password):
            # Voters must be approved
            if role == 'voter' and user_obj.account_status != 'approved':
                flash(f'Your account is {user_obj.account_status}. '
                      'Please wait for Election Officer approval.', 'warning')
                return redirect(url_for('login'))

            session['role'] = role
            login_user(user_obj)
            log_action(role, user_obj.id, 'Login', email)

            if role == 'voter':
                return redirect(url_for('voter_dashboard'))
            if role == 'officer':
                return redirect(url_for('officer_dashboard'))
            return redirect(url_for('admin_dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    states_query = db.session.query(Constituency.state).distinct().order_by(Constituency.state).all()
    states = [s[0] for s in states_query]
    constituencies = Constituency.query.order_by(Constituency.name).all()
    
    if request.method == 'POST':
        voter_id = request.form.get('voter_id', '').strip().upper()
        dob_str  = request.form.get('dob', '')
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Retrieve new fields
        full_name = request.form.get('full_name', '').strip()
        gender = request.form.get('gender', 'Male')
        constituency_id = request.form.get('constituency_id', type=int)
        address = request.form.get('address', '').strip()

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', constituencies=constituencies, states=states)

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', constituencies=constituencies, states=states)

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date of birth.', 'danger')
            return render_template('register.html', constituencies=constituencies, states=states)

        # Look up or create registry entry dynamically
        registry = VoterRegistry.query.filter_by(voter_id_number=voter_id).first()
        if not registry:
            registry = VoterRegistry(
                voter_id_number=voter_id,
                full_name=full_name,
                date_of_birth=dob,
                constituency_id=constituency_id,
                gender=gender,
                address=address,
                is_active=True
            )
            db.session.add(registry)
            db.session.flush()

        if registry.user_account:
            flash('This Voter ID is already linked to an account.', 'danger')
            return render_template('register.html', constituencies=constituencies, states=states)

        user = User(voter_registry_id=registry.id, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        log_action('voter', user.id, 'Registration Submitted', voter_id)
        flash('Registration submitted! Please wait for officer approval.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', constituencies=constituencies, states=states)


@app.route('/logout')
@login_required
def logout():
    role = session.get('role', 'voter')
    log_action(role, current_user.id, 'Logout', '')
    session.clear()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────────────────────────────────────
# Voter Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/voter/dashboard')
@login_required
@voter_required
def voter_dashboard():
    elections  = Election.query.filter_by(
        constituency_id=current_user.constituency_id
    ).order_by(Election.created_at.desc()).all()
    voted_ids  = {v.election_id for v in current_user.votes}
    return render_template('voter_dashboard.html',
                           elections=elections, voted_ids=voted_ids)


@app.route('/voter/profile')
@login_required
@voter_required
def voter_profile():
    return render_template('voter_profile.html', user=current_user)


@app.route('/voter/vote/<int:election_id>', methods=['GET', 'POST'])
@login_required
@voter_required
def cast_vote(election_id):
    election = Election.query.get_or_404(election_id)

    if election.constituency_id != current_user.constituency_id:
        flash('You are not registered in this constituency.', 'danger')
        return redirect(url_for('voter_dashboard'))

    if not election.is_currently_active:
        flash('This election is not currently open for voting.', 'warning')
        return redirect(url_for('voter_dashboard'))

    if Vote.query.filter_by(voter_id=current_user.id, election_id=election_id).first():
        flash('You have already voted in this election.', 'warning')
        return redirect(url_for('voter_dashboard'))

    candidates = Candidate.query.filter_by(
        election_id=election_id, candidate_status='Approved'
    ).all()

    if request.method == 'POST':
        candidate_id = request.form.get('candidate_id', type=int)
        if not candidate_id:
            flash('Please select a candidate.', 'danger')
            return render_template('vote.html', election=election, candidates=candidates)

        candidate = db.session.get(Candidate, candidate_id)
        if not candidate or candidate.election_id != election_id:
            flash('Invalid candidate.', 'danger')
            return render_template('vote.html', election=election, candidates=candidates)

        vote = Vote(election_id=election_id, candidate_id=candidate_id, voter_id=current_user.id)
        db.session.add(vote)
        db.session.commit()

        log_action('voter', current_user.id, 'Vote Cast',
                   f'Election ID {election_id}')
        flash('Your vote has been recorded. Thank you!', 'success')
        return redirect(url_for('voter_dashboard'))

    return render_template('vote.html', election=election, candidates=candidates)


@app.route('/results/<int:election_id>')
def election_results(election_id):
    election = Election.query.get_or_404(election_id)
    if election.status != 'Published':
        flash('Results have not been published yet.', 'warning')
        return redirect(url_for('voter_dashboard')
                        if current_user.is_authenticated else url_for('login'))

    candidates = Candidate.query.filter_by(
        election_id=election_id, candidate_status='Approved'
    ).all()

    total = election.total_votes
    results = sorted(
        [{'candidate': c, 'votes': c.vote_count,
          'pct': round(c.vote_count / total * 100, 1) if total else 0}
         for c in candidates],
        key=lambda x: x['votes'], reverse=True
    )
    return render_template('results.html',
                           election=election, results=results, total=total)


# ─────────────────────────────────────────────────────────────────────────────
# Officer Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/officer/dashboard')
@login_required
@officer_required
def officer_dashboard():
    cid = current_user.constituency_id

    base_voters = User.query.join(VoterRegistry)
    base_cands  = Candidate.query.join(Election)

    if cid:
        base_voters = base_voters.filter(VoterRegistry.constituency_id == cid)
        base_cands  = base_cands.filter(Election.constituency_id == cid)

    pending   = base_voters.filter(User.account_status == 'pending').all()
    approved  = base_voters.filter(User.account_status == 'approved').all()
    pend_cands = base_cands.filter(Candidate.candidate_status == 'Pending').all()

    return render_template('officer_dashboard.html',
                           pending=pending, approved=approved,
                           pending_candidates=pend_cands)


@app.route('/officer/voter/<int:user_id>/<action>', methods=['POST'])
@login_required
@officer_required
def review_voter(user_id, action):
    user = User.query.get_or_404(user_id)
    status_map = {'approve': 'approved', 'reject': 'rejected', 'suspend': 'suspended'}
    if action in status_map:
        user.account_status = status_map[action]
        db.session.commit()
        log_action('officer', current_user.id,
                   f'Voter {action.title()}d', f'User ID {user_id}')
        flash(f'{user.full_name} has been {action}d.', 'success')
    return redirect(url_for('officer_dashboard'))


@app.route('/officer/candidate/<int:cid>/<action>', methods=['POST'])
@login_required
@officer_required
def review_candidate(cid, action):
    candidate = Candidate.query.get_or_404(cid)
    if action == 'approve':
        candidate.candidate_status = 'Approved'
    elif action == 'reject':
        candidate.candidate_status = 'Rejected'
    db.session.commit()
    log_action('officer', current_user.id,
               f'Candidate {action.title()}d', f'Candidate ID {cid}')
    flash(f'{candidate.full_name} {action}d.', 'success')
    return redirect(url_for('officer_dashboard'))


# ─────────────────────────────────────────────────────────────────────────────
# Admin (CEO) Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'total_voters':     User.query.filter_by(account_status='approved').count(),
        'pending_voters':   User.query.filter_by(account_status='pending').count(),
        'total_elections':  Election.query.count(),
        'active_elections': Election.query.filter_by(status='Active').count(),
    }
    elections = Election.query.order_by(Election.created_at.desc()).limit(5).all()
    logs      = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    return render_template('admin_dashboard.html',
                           stats=stats, elections=elections, logs=logs)


# ── Elections ─────────────────────────────────────────────────────────────────

@app.route('/admin/elections')
@login_required
@admin_required
def admin_elections():
    elections = Election.query.order_by(Election.created_at.desc()).all()
    return render_template('admin_elections.html', elections=elections)


@app.route('/admin/elections/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_election():
    constituencies = Constituency.query.all()
    if request.method == 'POST':
        e = Election(
            election_name=request.form['election_name'],
            election_type=request.form['election_type'],
            constituency_id=int(request.form['constituency_id']),
            start_datetime=datetime.strptime(request.form['start_datetime'], '%Y-%m-%dT%H:%M'),
            end_datetime=datetime.strptime(request.form['end_datetime'], '%Y-%m-%dT%H:%M'),
            status='Draft'
        )
        db.session.add(e)
        db.session.commit()
        log_action('admin', current_user.id, 'Election Created', e.election_name)
        flash('Election created successfully!', 'success')
        return redirect(url_for('admin_elections'))
    return render_template('election_form.html',
                           constituencies=constituencies, election=None)


@app.route('/admin/elections/<int:eid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_election(eid):
    election       = Election.query.get_or_404(eid)
    constituencies = Constituency.query.all()
    if request.method == 'POST':
        election.election_name   = request.form['election_name']
        election.election_type   = request.form['election_type']
        election.constituency_id = int(request.form['constituency_id'])
        election.start_datetime  = datetime.strptime(request.form['start_datetime'], '%Y-%m-%dT%H:%M')
        election.end_datetime    = datetime.strptime(request.form['end_datetime'],   '%Y-%m-%dT%H:%M')
        election.status          = request.form['status']
        db.session.commit()
        log_action('admin', current_user.id, 'Election Updated', election.election_name)
        flash('Election updated!', 'success')
        return redirect(url_for('admin_elections'))
    return render_template('election_form.html',
                           constituencies=constituencies, election=election)


@app.route('/admin/elections/<int:eid>/status/<status>', methods=['POST'])
@login_required
@admin_required
def set_election_status(eid, status):
    election = Election.query.get_or_404(eid)
    allowed  = ['Draft', 'Scheduled', 'Active', 'Closed', 'Published']
    if status in allowed:
        election.status = status
        db.session.commit()
        log_action('admin', current_user.id,
                   f'Election → {status}', election.election_name)
        flash(f'Election status set to {status}.', 'success')
    return redirect(url_for('admin_elections'))


# ── Candidates ────────────────────────────────────────────────────────────────

@app.route('/admin/elections/<int:eid>/candidates', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_candidates(eid):
    election   = Election.query.get_or_404(eid)
    parties    = Party.query.all()
    candidates = Candidate.query.filter_by(election_id=eid).all()

    if request.method == 'POST':
        c = Candidate(
            full_name=request.form['full_name'],
            party_id=int(request.form['party_id']) if request.form.get('party_id') else None,
            constituency_id=election.constituency_id,
            election_id=eid,
            candidate_status='Approved'
        )
        db.session.add(c)
        db.session.commit()
        log_action('admin', current_user.id, 'Candidate Added', c.full_name)
        flash('Candidate added!', 'success')
        return redirect(url_for('manage_candidates', eid=eid))

    return render_template('candidates.html',
                           election=election, parties=parties, candidates=candidates)


# ── Constituencies ────────────────────────────────────────────────────────────

@app.route('/admin/constituencies', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_constituencies():
    if request.method == 'POST':
        c = Constituency(
            name=request.form['name'],
            district=request.form['district'],
            state=request.form['state']
        )
        db.session.add(c)
        db.session.commit()
        flash('Constituency added!', 'success')
        return redirect(url_for('admin_constituencies'))
    constituencies = Constituency.query.all()
    return render_template('constituencies.html', constituencies=constituencies)


# ── Parties ───────────────────────────────────────────────────────────────────

@app.route('/admin/parties', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_parties():
    if request.method == 'POST':
        p = Party(
            party_name=request.form['party_name'],
            symbol=request.form.get('symbol', ''),
            description=request.form.get('description', '')
        )
        db.session.add(p)
        db.session.commit()
        flash('Party added!', 'success')
        return redirect(url_for('admin_parties'))
    parties = Party.query.all()
    return render_template('parties.html', parties=parties)


# ── Officers ──────────────────────────────────────────────────────────────────

@app.route('/admin/officers', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_officers():
    constituencies = Constituency.query.all()
    if request.method == 'POST':
        o = ElectionOfficer(
            name=request.form['name'],
            email=request.form['email'],
            constituency_id=int(request.form['constituency_id']) if request.form.get('constituency_id') else None
        )
        o.set_password(request.form['password'])
        db.session.add(o)
        db.session.commit()
        log_action('admin', current_user.id, 'Officer Created', o.email)
        flash('Election Officer created!', 'success')
        return redirect(url_for('admin_officers'))
    officers = ElectionOfficer.query.all()
    return render_template('officers.html',
                           officers=officers, constituencies=constituencies)


# ── Audit Logs ────────────────────────────────────────────────────────────────

@app.route('/admin/audit-logs')
@login_required
@admin_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('audit_logs.html', logs=logs)


# ─────────────────────────────────────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('404.html'), 403


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
