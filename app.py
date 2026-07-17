"""
Nihad's portfolio — Flask version, with an admin panel.

Run with:
    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5000
Admin panel: http://127.0.0.1:5000/admin
  Default login: admin / changeme123  (change this immediately in
  /admin/password, or set the ADMIN_PASSWORD env var before the very
  first run to seed a different default password.)

All editable content (profile, about, projects, skills, nav links)
lives in portfolio.db — see db.py. Nothing here needs to be edited
by hand anymore to change site content.
"""

import os
import secrets

from flask import Flask, render_template, request, jsonify, send_from_directory

import db
from admin import admin_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.register_blueprint(admin_bp)

db.init_db()


# ============================================================
# AI ASSISTANT — simple keyword-matching FAQ bot, running fully
# in Python on the server. The front end calls POST /api/chat.
# No external API key needed. Answers are built from the same
# database-backed content shown on the page, so editing content
# in /admin also updates what the assistant says.
# ============================================================

def build_knowledge_base(profile, skills, projects):
    skills_list = [s["name"] for group in skills.values() for s in group]
    projects_list = [p["title"] for p in projects]
    return [
        {
            "keywords": ["name", "who are you", "who is nihad"],
            "answer": f"I'm {profile['name']}, a {profile['role']} based in "
                      f"{profile['location']}, working with SQL, Python and dashboards "
                      f"to turn raw data into clear insights.",
        },
        {
            "keywords": ["skill", "tech", "stack", "tools", "know"],
            "answer": "Core skills: " + ", ".join(skills_list) + ".",
        },
        {
            "keywords": ["project", "work", "portfolio", "built", "made"],
            "answer": "A few projects: " + ", ".join(projects_list)
                      + ". Scroll to the Work section to see details on each.",
        },
        {
            "keywords": ["resume", "cv", "download"],
            "answer": "You can download the resume from the Resume section — "
                      "I'll scroll you there.",
            "scrollTo": "#resume",
        },
        {
            "keywords": ["contact", "email", "reach", "hire", "linkedin", "github"],
            "answer": f"Best way to reach {profile['name']} is {profile['email']}, "
                      f"or check the Contact section for socials.",
            "scrollTo": "#contact",
        },
        {
            "keywords": ["experience", "background", "about", "intern"],
            "answer": "Currently interning as a Data Analyst — working on real "
                      "datasets end to end: cleaning, analysis, and reporting.",
        },
        {
            "keywords": ["hi", "hello", "hey", "sup"],
            "answer": "Hey! I'm a lightweight AI assistant for this portfolio. Ask me "
                      "about skills, projects, or how to get in touch.",
        },
    ]


FALLBACK = ("I don't have an answer for that yet — try asking about skills, "
            "projects, resume, or contact details.")


def get_answer(text: str) -> dict:
    profile = db.get_profile()
    skills = db.get_skills()
    projects = db.get_projects()
    knowledge_base = build_knowledge_base(profile, skills, projects)

    lower = text.lower()
    best, best_score = None, 0
    for entry in knowledge_base:
        score = sum(1 for kw in entry["keywords"] if kw in lower)
        if score > best_score:
            best_score, best = score, entry
    if best:
        return {"answer": best["answer"], "scrollTo": best.get("scrollTo")}
    return {"answer": FALLBACK, "scrollTo": None}


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template(
        "index.html",
        profile=db.get_profile(),
        about=db.get_about(),
        projects=db.get_projects(),
        skills=db.get_skills(),
        nav_links=db.get_nav_links(),
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"answer": FALLBACK, "scrollTo": None}), 400
    return jsonify(get_answer(message))


@app.route("/resume.pdf")
def resume():
    # Replace the file from the admin panel (Profile page) or by
    # dropping a new one at static/files/resume.pdf.
    return send_from_directory("static/files", "resume.pdf")


if __name__ == "__main__":
    app.run(debug=True)
