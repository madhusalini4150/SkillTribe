# SkillTribe — Full Stack Flask App

A skill-sharing platform where people can teach and learn skills.
Built with **Python Flask + SQLAlchemy + Flask-Login + Flask-Bcrypt**,
production-ready for deployment on **Render** (free tier).

---

## ⚡ Run it locally — 4 commands

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** — the SQLite database is created
automatically and demo data is seeded on first run.

---

## 🌍 Put it live on the internet (free)

See **[DEPLOY.md](DEPLOY.md)** for a full step-by-step guide to deploying
on Render.com with one click — gets you a real URL to put on your resume.

---

## 🔑 Demo Credentials

| Email            | Password  | Role           |
|------------------|-----------|----------------|
| demo@demo.com    | demo1234  | Learner        |
| aiko@demo.com    | demo1234  | Teacher (Free) |
| ravi@demo.com    | demo1234  | Teacher (Paid) |
| priya@demo.com   | demo1234  | Teacher (Free) |
| lucas@demo.com   | demo1234  | Teacher (Paid) |
| meera@demo.com   | demo1234  | Teacher (Free) |

---

## 📁 Project Structure

```
skilltribe/
├── app.py            ← All routes (main Flask application)
├── wsgi.py            ← Production entry point (used by gunicorn)
├── models.py          ← Database models (User, Skill, Message, Review)
├── forms.py            ← WTForms form classes (incl. avatar upload)
├── config.py          ← App configuration (dev + production)
├── requirements.txt  ← Python dependencies
├── Procfile           ← Tells Render/Heroku how to start the app
├── render.yaml         ← One-click Render Blueprint (app + database)
├── runtime.txt         ← Python version pin
├── .env.example        ← Template for local environment variables
├── DEPLOY.md           ← Step-by-step deployment guide
│
├── templates/
│   ├── base.html         ← Shared layout (nav, footer, flash messages)
│   ├── index.html        ← Homepage
│   ├── register.html     ← Sign up
│   ├── login.html        ← Log in
│   ├── search.html       ← Search & browse teachers
│   ├── profile.html      ← Teacher/user profile
│   ├── dashboard.html    ← Logged-in user hub
│   ├── settings.html     ← Edit profile + avatar upload
│   ├── message.html      ← Send message form
│   ├── inbox.html        ← All received messages
│   ├── conversation.html ← Two-way chat thread
│   └── errors/           ← 404 / 403 / 500 pages
│
└── static/
    ├── css/ , js/         ← (optional extra assets)
    └── images/            ← Uploaded profile photos
```

---

## 🔗 All Routes

| Method | URL                          | Description                    |
|--------|------------------------------|---------------------------------|
| GET    | /                            | Homepage with featured teachers |
| GET    | /search                      | Search teachers by skill        |
| GET    | /profile/<id>                 | View user profile               |
| GET/POST | /register                  | Create new account              |
| GET/POST | /login                     | Authenticate user               |
| GET    | /logout                      | Logout current user             |
| GET    | /dashboard                   | User dashboard (auth required)  |
| GET/POST | /settings                  | Edit profile + avatar upload    |
| POST   | /skills/add                  | Add a skill to profile          |
| POST   | /skills/remove/<skill_id>    | Remove a skill                  |
| GET/POST | /message/<user_id>         | Compose & send a message        |
| GET    | /inbox                        | View all received messages      |
| GET    | /conversation/<user_id>      | Two-way chat thread             |
| POST   | /review/<user_id>            | Leave a star review             |
| GET    | /api/skills/autocomplete      | JSON autocomplete (AJAX)        |
| GET    | /api/teachers                 | JSON teacher list (AJAX)        |
| GET    | /healthz                      | Health check (used by Render)   |

---

## 🗄️ Database Models

- **User** — username, email, password (bcrypt hash), bio, location,
  avatar, is_teacher, is_paid, hourly_rate, currency, skills (M2M)
- **Skill** — name, category, slug
- **Message** — sender, receiver, body, is_read, created_at
- **Review** — reviewer, reviewed, rating (1–5), comment, created_at

On Render, the app automatically uses **PostgreSQL** (production-grade);
locally it falls back to **SQLite** automatically — no code changes needed.

---

## 🔐 Security features included

- Passwords hashed with bcrypt (never stored in plain text)
- CSRF protection on every form (Flask-WTF)
- Secure session cookies in production (`SESSION_COOKIE_SECURE`)
- File upload validation (type + 2MB size limit) for avatars
- Environment-based secrets (`.env` — never committed to GitHub)

---

## 🚀 Future features to add

- [ ] Email notifications (Flask-Mail)
- [ ] Stripe payment integration for paid lessons
- [ ] Real-time chat (Flask-SocketIO)
- [ ] Calendar / session booking
- [ ] Cloud storage for avatars (Cloudinary / S3) so they persist on redeploy
- [ ] Admin panel (Flask-Admin)

---
Small documentation improvement by Sridiyva
Built with Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt, WTForms, Gunicorn.
