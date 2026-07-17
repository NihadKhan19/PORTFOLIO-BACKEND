# Nihad — Portfolio (Flask / Python version)

The same portfolio, rebuilt as a Python Flask app with an **admin panel**.
All content (profile, about, projects, skills, nav links) lives in a
SQLite database and can be edited from a login-protected `/admin`
panel — no code editing required to add a project, change a link, or
update your bio. The "Ask my AI" chat is a real backend endpoint
(`POST /api/chat`) implemented in Python, and it reads from the same
database so it stays in sync with what's on the page.

## Project structure

```
app.py                     Flask app, routes, /api/chat endpoint
db.py                       SQLite schema, seed data, read helpers
admin.py                    Admin panel routes (login + CRUD)
portfolio.db                 created automatically on first run — your content
templates/
  index.html                 public site template
  admin/                      admin panel templates
  icons/                      small inline icon partials used on work cards
static/
  css/style.css               public site styling
  css/admin.css                admin panel styling
  js/main.js                   nav scrollspy, fade-ins, skill bars, AI chat
  files/resume.pdf             your resume — replace via admin or by hand
requirements.txt
```

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** for the site, and
**http://127.0.0.1:5000/admin** for the admin panel.

### First login

```
username: admin
password: changeme123
```

**Change this immediately** from *Change Password* in the sidebar once
you're logged in. To set a different starting password instead, set an
environment variable before the very first run (before `portfolio.db`
exists):

```bash
ADMIN_PASSWORD=your-new-password python app.py
```

## Editing content

Everything is editable from `/admin` — no code changes needed:

- **Profile & Social** — name, role, tagline, email, GitHub, LinkedIn, and resume file upload
- **Nav Links** — add, remove, reorder, or rename top navigation items
- **About** — bio paragraphs and quick facts, add/remove either
- **Projects** — add, edit, remove, and reorder project cards (title, tag, description, stack, link, icon)
- **Skills** — add/remove skill groups and individual skills with a proficiency level

The AI chat widget automatically reflects whatever is currently in the
database (skills, projects, contact info), so you don't need to edit
it separately.

## Data & backups

All content lives in `portfolio.db` (SQLite), created automatically
the first time you run the app. Back it up like any file — copying it
elsewhere preserves all your content. Deleting it resets the site back
to the original seed content on the next run.

## Deploying

This needs a Python host (unlike a static HTML site), for example:
- **Render** or **Railway** — connect the repo, they auto-detect Flask
- **PythonAnywhere** — free tier works well for a small site like this
- Any VPS with `gunicorn app:app` behind nginx

Two things to set in production:
- `SECRET_KEY` env var — a long random string, so login sessions survive restarts
- Make sure `portfolio.db` is on persistent storage (not wiped on redeploy) — most hosts above handle this fine as long as it's in the project directory

Vercel/Netlify don't run persistent Python backends, so they're not a
fit for this version.
