# 🗳️ Online Voting System

A production-style online election platform built with **Python Flask**, **MySQL**, **SQLAlchemy**, and a premium **Bento Grid UI**.

---

## Tech Stack

| Layer      | Technology                  |
|------------|-----------------------------|
| Backend    | Python 3, Flask             |
| Auth       | Flask-Login, Werkzeug        |
| Database   | MySQL + SQLAlchemy ORM      |
| Migrations | Flask-Migrate (Alembic)     |
| Frontend   | HTML5, Vanilla CSS, JS      |
| Security   | Flask-WTF CSRF, bcrypt hash |

---

## Project Structure

```
online_voting_system/
├── app.py          ← All routes
├── models.py       ← All database models
├── extensions.py   ← Flask extension instances
├── config.py       ← Configuration
├── seed_data.py    ← Demo data loader
├── requirements.txt
├── .env            ← Your local environment variables
├── static/
│   ├── style.css   ← Premium CSS design system
│   └── main.js     ← Client-side interactions
└── templates/      ← Jinja2 HTML templates (14 pages)
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.9+
- MySQL 8.0+
- pip

### 2. Clone & install dependencies

```bash
git clone <repo-url>
cd online_voting_system
pip install -r requirements.txt
```

### 3. Create the MySQL database

```sql
CREATE DATABASE voting_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure environment

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/voting_db
```

### 5. Run database migrations

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Load seed data

```bash
python seed_data.py
```

### 7. Start the server

```bash
python app.py
```

Open: **http://localhost:5000**

---

## Default Login Credentials

| Role             | Email                         | Password     |
|------------------|-------------------------------|--------------|
| Chief Elec. Off. | admin@election.gov.in         | Admin@123    |
| Officer (Chennai)| officer1@election.gov.in      | Officer@123  |
| Officer (Mumbai) | officer2@election.gov.in      | Officer@123  |

---

## Voter Registration (Test Flow)

Use these **Voter IDs + DOB** when registering a voter account:

| Voter ID | Date of Birth | Name           | Constituency   |
|----------|---------------|----------------|----------------|
| TN00001  | 1990-05-15    | Anbu Selvan    | Chennai North  |
| TN00002  | 1985-08-22    | Kavitha Rajan  | Chennai North  |
| TN00003  | 1992-03-10    | Murugan Pillai | Chennai North  |
| MH00001  | 1988-11-30    | Rahul Desai    | Mumbai South   |
| MH00002  | 1995-07-14    | Sneha Patil    | Mumbai South   |

---

## User Roles

| Role | Capabilities |
|------|-------------|
| **Voter** | Register, login, view elections, cast vote, view profile |
| **Election Officer** | Approve/reject voter registrations, review candidates |
| **Chief Elec. Off.** | Create elections, manage everything, publish results |

---

## Complete Test Walkthrough

1. **Login as CEO** → Create an election, add candidates
2. **Login as Voter** (register first using a Voter ID above)
3. **Login as Officer** → Approve the voter registration
4. **Login as Voter** → Cast your vote
5. **Login as CEO** → Change election status → Active → Closed → Publish Results
6. **Voter** can now see results

---

## Security

- Passwords hashed with `werkzeug.security.generate_password_hash`
- CSRF protection on all POST forms via `Flask-WTF`
- Role-based access control with custom decorators
- `UniqueConstraint` on `(voter_id, election_id)` prevents double-voting
- Ballot secrecy enforced — no route ever exposes voter → candidate mapping

---

## Git History

```
Phase 1 — Scaffold (config, requirements, extensions)
Phase 2 — Database models (all 10 tables)
Phase 3 — All routes (auth, voter, officer, admin)
Phase 4 — Static assets (CSS design system + JS)
Phase 5 — Templates (14 pages)
Phase 6 — Seed data
Phase 7 — README
```
