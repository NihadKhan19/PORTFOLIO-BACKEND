"""
SQLite data layer for the portfolio site.

All editable content (profile, about text, projects, skills, nav links)
lives in portfolio.db instead of being hard-coded in app.py. The admin
panel (admin.py) reads and writes through the helpers below.

On first run, if the database doesn't exist yet, it's created and
seeded with the same content that used to be hard-coded, so the site
looks identical until you start editing it in /admin.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    tagline TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    github TEXT NOT NULL DEFAULT '#',
    linkedin TEXT NOT NULL DEFAULT '#'
);

CREATE TABLE IF NOT EXISTS about_paragraphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS about_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    tag TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    stack TEXT NOT NULL DEFAULT '',
    link TEXT NOT NULL DEFAULT '#',
    icon TEXT NOT NULL DEFAULT 'bar-chart',
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS skill_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES skill_groups(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 50,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS nav_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    href TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admin_user (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if missing, and seed with starter content on first run."""
    is_new = not os.path.exists(DB_PATH)
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()

    if is_new:
        _seed(conn)

    # Make sure there's always exactly one admin user, even if the db
    # already existed without one (e.g. upgrading from an older copy).
    if conn.execute("SELECT 1 FROM admin_user WHERE id = 1").fetchone() is None:
        from werkzeug.security import generate_password_hash
        default_password = os.environ.get("ADMIN_PASSWORD", "changeme123")
        conn.execute(
            "INSERT INTO admin_user (id, username, password_hash) VALUES (1, ?, ?)",
            ("admin", generate_password_hash(default_password)),
        )
        conn.commit()

    conn.close()


def _seed(conn):
    conn.execute(
        """INSERT INTO profile (id, name, role, location, tagline, email, github, linkedin)
           VALUES (1, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "Nihad",
            "Data Analyst Intern",
            "India",
            "I turn raw data into clear insights using SQL, Python and dashboards. Based in India.",
            "hello@nihad.dev",
            "#",
            "#",
        ),
    )

    paragraphs = [
        "I work with data to find patterns that actually matter — cleaning messy "
        "datasets, building dashboards, and turning numbers into decisions people "
        "can act on.",
        "Currently interning as a Data Analyst, learning by working on real "
        "datasets end to end: cleaning, analysis, and reporting.",
    ]
    for i, p in enumerate(paragraphs):
        conn.execute(
            "INSERT INTO about_paragraphs (content, sort_order) VALUES (?, ?)", (p, i)
        )

    facts = [
        ("Focus", "Data analysis & visualization"),
        ("Status", "Data Analyst Intern"),
        ("Experience", "Intern"),
        ("Based in", "India"),
    ]
    for i, (label, value) in enumerate(facts):
        conn.execute(
            "INSERT INTO about_facts (label, value, sort_order) VALUES (?, ?, ?)",
            (label, value, i),
        )

    projects = [
        ("Sales Dashboard", "Power BI",
         "Interactive dashboard tracking monthly sales and regional performance for a retail dataset.",
         "Power BI,SQL", "#", "bar-chart"),
        ("Customer Churn", "Python",
         "Analysis of customer churn patterns using Python, identifying key drop-off factors.",
         "Python,Pandas,Matplotlib", "#", "trend-down"),
        ("Survey Insights", "Excel",
         "Cleaned and analyzed survey data of 2,000+ responses, presented as a summary report.",
         "Excel,Statistics", "#", "clipboard"),
        ("COVID Trends", "Visualization",
         "Public health dataset explored and visualized to show regional case trends over time.",
         "Tableau,SQL", "#", "activity"),
    ]
    for i, (title, tag, desc, stack, link, icon) in enumerate(projects):
        conn.execute(
            """INSERT INTO projects (title, tag, description, stack, link, icon, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, tag, desc, stack, link, icon, i),
        )

    skill_groups = {
        "Languages & Analysis": [
            ("SQL", 85), ("Python (Pandas)", 75), ("Excel", 90), ("Statistical Analysis", 70),
        ],
        "Tools & Visualization": [
            ("Power BI", 80), ("Tableau", 65), ("Jupyter Notebook", 75), ("Git", 60),
        ],
    }
    for gi, (group_name, items) in enumerate(skill_groups.items()):
        cur = conn.execute(
            "INSERT INTO skill_groups (name, sort_order) VALUES (?, ?)", (group_name, gi)
        )
        group_id = cur.lastrowid
        for si, (name, level) in enumerate(items):
            conn.execute(
                "INSERT INTO skills (group_id, name, level, sort_order) VALUES (?, ?, ?, ?)",
                (group_id, name, level, si),
            )

    nav_links = [
        ("Home", "#home"),
        ("About", "#about"),
        ("Work", "#work"),
        ("Resume", "#resume"),
        ("Contact", "#contact"),
    ]
    for i, (label, href) in enumerate(nav_links):
        conn.execute(
            "INSERT INTO nav_links (label, href, sort_order) VALUES (?, ?, ?)",
            (label, href, i),
        )

    conn.commit()


# ============================================================
# Read helpers used by the public site (app.py)
# ============================================================

def get_profile():
    conn = get_db()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def get_about():
    conn = get_db()
    paragraphs = [
        r["content"] for r in
        conn.execute("SELECT content FROM about_paragraphs ORDER BY sort_order, id")
    ]
    facts = [
        (r["label"], r["value"]) for r in
        conn.execute("SELECT label, value FROM about_facts ORDER BY sort_order, id")
    ]
    conn.close()
    return {"paragraphs": paragraphs, "facts": facts}


def get_projects():
    conn = get_db()
    rows = conn.execute("SELECT * FROM projects ORDER BY sort_order, id").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["stack"] = [s.strip() for s in d["stack"].split(",") if s.strip()]
        result.append(d)
    return result


def get_skills():
    conn = get_db()
    groups = conn.execute("SELECT * FROM skill_groups ORDER BY sort_order, id").fetchall()
    out = {}
    for g in groups:
        items = conn.execute(
            "SELECT name, level FROM skills WHERE group_id = ? ORDER BY sort_order, id",
            (g["id"],),
        ).fetchall()
        out[g["name"]] = [{"name": i["name"], "level": i["level"]} for i in items]
    conn.close()
    return out


def get_nav_links():
    conn = get_db()
    rows = conn.execute("SELECT * FROM nav_links ORDER BY sort_order, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]
