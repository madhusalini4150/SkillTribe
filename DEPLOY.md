# 🚀 Deploying SkillTribe — Get a Real Live Link

This guide gets your project live on the internet **for free**, using
[Render.com](https://render.com). At the end you'll have a real URL like:

```
https://skilltribe-xxxx.onrender.com
```

You can put this link on your resume, LinkedIn, or share it with anyone.

---

## Before you start

You need your code on **GitHub** (Render deploys from a GitHub repo).
If you haven't done this yet:

1. Create a free account at [github.com](https://github.com)
2. Create a new repository called `skilltribe`
3. Upload your project folder to it (drag-and-drop on GitHub web works fine,
   or use `git push` if you know Git)

   ⚠️ Make sure `.env` is **not** uploaded — it's already excluded by
   `.gitignore`, just double check it's not in your GitHub repo.

---

## Option A — One-Click Deploy (easiest)

Your project already includes a `render.yaml` file, which means Render can
set up *everything automatically* — the web app AND a free PostgreSQL
database — in one click.

1. Go to **[render.com](https://render.com)** and sign up (free, use your
   GitHub account to sign in — it's faster)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account if asked, then select your `skilltribe` repo
4. Render reads `render.yaml` and shows you a preview: 1 web service +
   1 database. Click **"Apply"**
5. Wait 2–3 minutes while it builds and deploys
6. Once it says "Live", click the URL at the top — that's your real website!

**Done!** Render automatically generated a secure `SECRET_KEY`, connected
the database, and seeded demo data for you.

---

## Option B — Manual Setup (if you want to understand each step)

### 1. Create the database first
- Render dashboard → **New +** → **PostgreSQL**
- Name: `skilltribe-db`, Plan: **Free**
- Click **Create Database**
- Wait until status is "Available", then copy the **Internal Database URL**
  (you'll need it in step 3)

### 2. Create the web service
- Render dashboard → **New +** → **Web Service**
- Connect your GitHub repo → select `skilltribe`
- Settings:
  | Field | Value |
  |---|---|
  | Runtime | Python 3 |
  | Build Command | `pip install -r requirements.txt` |
  | Start Command | `gunicorn wsgi:app` |
  | Plan | Free |

### 3. Add environment variables
In the **Environment** tab of your web service, add:

| Key | Value |
|---|---|
| `SECRET_KEY` | Click "Generate" or run `python -c "import secrets; print(secrets.token_hex(32))"` locally and paste the result |
| `DATABASE_URL` | Paste the Internal Database URL from step 1 |
| `FLASK_ENV` | `production` |
| `SEED_DEMO` | `true` (only for your first deploy — see note below) |

### 4. Deploy
Click **"Create Web Service"**. Render will build and deploy automatically.
After a few minutes you'll get your live URL.

---

## ⚠️ Important: turn off demo seeding after first deploy

`SEED_DEMO=true` creates the sample teachers (Aiko, Ravi, Priya, etc.) the
**first time only** — it checks if the database is empty before adding them.
It's safe to leave it on, but once your real users start signing up, you can
set it to `false` in the Environment tab if you'd rather start with a clean
database with no demo accounts.

---

## Testing your live site

Visit your Render URL and try:
- Register a brand-new account
- Search for a skill ("Python", "Japanese", "Guitar")
- Log in as a demo teacher: `demo@demo.com` / `demo1234`
- Send a message, leave a review, upload a profile photo

---

## Common issues

**"Application failed to respond"**
→ Check the **Logs** tab in Render. Usually means a missing environment
variable or a typo in the start command. It must be exactly: `gunicorn wsgi:app`

**Database connection errors**
→ Make sure `DATABASE_URL` is the **Internal** URL (not External) if your web
service and database are both on Render — internal is faster and free.

**Free tier sleeps after inactivity**
→ Render's free web services "spin down" after 15 minutes of no traffic, and
take ~30 seconds to wake up on the next visit. This is normal for free
hosting — mention it if you demo the link live, or upgrade to a paid plan
($7/mo) for an always-on instance.

**Uploaded avatar images disappear after redeploy**
→ Render's free filesystem is *ephemeral* — files written while the app is
running don't survive a redeploy. For a resume project this is fine to leave
as-is. If you want avatars to persist permanently, the next step is
connecting a cloud storage service like Cloudinary or AWS S3 (a great
"v2" feature to mention you're planning!).

---

## Running locally (for development)

This still works exactly as before — Render doesn't change your local setup:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt
python app.py
```

Local mode automatically uses SQLite (no `DATABASE_URL` needed) and seeds
demo data the first time you run it.

---

## What to put on your resume

> **SkillTribe** — Full-stack skill-sharing platform (Flask, SQLAlchemy,
> PostgreSQL) with user auth, search, messaging, and review system.
> Deployed live on Render. [your-url-here]

Good luck! 🎓
