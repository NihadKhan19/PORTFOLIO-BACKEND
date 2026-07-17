"""
Admin panel — login-protected CRUD for everything editable on the site:
nav links, profile/social links, about text, projects, and skills.

Visit /admin, log in, and edit. Nothing here touches app.py or the
templates for the public site again — it's all data in portfolio.db.
"""

import os
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from db import get_db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates/admin")

RESUME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "files")
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "icons")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def available_icons():
    if not os.path.isdir(ICON_DIR):
        return []
    return sorted(f[:-4] for f in os.listdir(ICON_DIR) if f.endswith(".svg"))


def move(table, item_id, direction):
    """Swap sort_order with the neighbouring row, for reordering lists."""
    conn = get_db()
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        return
    if direction == "up":
        neighbor = conn.execute(
            f"SELECT * FROM {table} WHERE sort_order < ? ORDER BY sort_order DESC LIMIT 1",
            (row["sort_order"],),
        ).fetchone()
    else:
        neighbor = conn.execute(
            f"SELECT * FROM {table} WHERE sort_order > ? ORDER BY sort_order ASC LIMIT 1",
            (row["sort_order"],),
        ).fetchone()
    if neighbor is not None:
        conn.execute(f"UPDATE {table} SET sort_order = ? WHERE id = ?", (neighbor["sort_order"], row["id"]))
        conn.execute(f"UPDATE {table} SET sort_order = ? WHERE id = ?", (row["sort_order"], neighbor["id"]))
        conn.commit()
    conn.close()


# ============================================================
# AUTH
# ============================================================

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM admin_user WHERE id = 1").fetchone()
        conn.close()
        if user and username == user["username"] and check_password_hash(user["password_hash"], password):
            session["admin_logged_in"] = True
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        flash("Wrong username or password.")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        current = request.form.get("current", "")
        new = request.form.get("new", "")
        confirm = request.form.get("confirm", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM admin_user WHERE id = 1").fetchone()
        if not check_password_hash(user["password_hash"], current):
            flash("Current password is wrong.")
        elif len(new) < 8:
            flash("New password must be at least 8 characters.")
        elif new != confirm:
            flash("New passwords don't match.")
        else:
            conn.execute(
                "UPDATE admin_user SET password_hash = ? WHERE id = 1",
                (generate_password_hash(new),),
            )
            conn.commit()
            flash("Password updated.")
        conn.close()
    return render_template("admin/password.html")


# ============================================================
# DASHBOARD
# ============================================================

@admin_bp.route("/")
@login_required
def dashboard():
    return render_template("admin/dashboard.html")


# ============================================================
# PROFILE
# ============================================================

@admin_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db()
    if request.method == "POST":
        fields = ("name", "role", "location", "tagline", "email", "github", "linkedin")
        values = [request.form.get(f, "").strip() for f in fields]
        conn.execute(
            f"UPDATE profile SET {', '.join(f + ' = ?' for f in fields)} WHERE id = 1",
            values,
        )
        conn.commit()

        resume = request.files.get("resume")
        if resume and resume.filename:
            os.makedirs(RESUME_DIR, exist_ok=True)
            resume.save(os.path.join(RESUME_DIR, "resume.pdf"))

        flash("Profile updated.")
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return render_template("admin/profile.html", profile=dict(row))


# ============================================================
# NAV LINKS
# ============================================================

@admin_bp.route("/nav")
@login_required
def nav_list():
    conn = get_db()
    links = conn.execute("SELECT * FROM nav_links ORDER BY sort_order, id").fetchall()
    conn.close()
    return render_template("admin/nav.html", links=links)


@admin_bp.route("/nav/add", methods=["POST"])
@login_required
def nav_add():
    label = request.form.get("label", "").strip()
    href = request.form.get("href", "").strip()
    if label and href:
        conn = get_db()
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS m FROM nav_links").fetchone()["m"]
        conn.execute("INSERT INTO nav_links (label, href, sort_order) VALUES (?, ?, ?)", (label, href, max_order + 1))
        conn.commit()
        conn.close()
    return redirect(url_for("admin.nav_list"))


@admin_bp.route("/nav/<int:link_id>/edit", methods=["POST"])
@login_required
def nav_edit(link_id):
    label = request.form.get("label", "").strip()
    href = request.form.get("href", "").strip()
    if label and href:
        conn = get_db()
        conn.execute("UPDATE nav_links SET label = ?, href = ? WHERE id = ?", (label, href, link_id))
        conn.commit()
        conn.close()
    return redirect(url_for("admin.nav_list"))


@admin_bp.route("/nav/<int:link_id>/delete", methods=["POST"])
@login_required
def nav_delete(link_id):
    conn = get_db()
    conn.execute("DELETE FROM nav_links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.nav_list"))


@admin_bp.route("/nav/<int:link_id>/move/<direction>", methods=["POST"])
@login_required
def nav_move(link_id, direction):
    move("nav_links", link_id, direction)
    return redirect(url_for("admin.nav_list"))


# ============================================================
# ABOUT
# ============================================================

@admin_bp.route("/about")
@login_required
def about_list():
    conn = get_db()
    paragraphs = conn.execute("SELECT * FROM about_paragraphs ORDER BY sort_order, id").fetchall()
    facts = conn.execute("SELECT * FROM about_facts ORDER BY sort_order, id").fetchall()
    conn.close()
    return render_template("admin/about.html", paragraphs=paragraphs, facts=facts)


@admin_bp.route("/about/paragraph/add", methods=["POST"])
@login_required
def paragraph_add():
    content = request.form.get("content", "").strip()
    if content:
        conn = get_db()
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS m FROM about_paragraphs").fetchone()["m"]
        conn.execute("INSERT INTO about_paragraphs (content, sort_order) VALUES (?, ?)", (content, max_order + 1))
        conn.commit()
        conn.close()
    return redirect(url_for("admin.about_list"))


@admin_bp.route("/about/paragraph/<int:pid>/edit", methods=["POST"])
@login_required
def paragraph_edit(pid):
    content = request.form.get("content", "").strip()
    conn = get_db()
    conn.execute("UPDATE about_paragraphs SET content = ? WHERE id = ?", (content, pid))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.about_list"))


@admin_bp.route("/about/paragraph/<int:pid>/delete", methods=["POST"])
@login_required
def paragraph_delete(pid):
    conn = get_db()
    conn.execute("DELETE FROM about_paragraphs WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.about_list"))


@admin_bp.route("/about/fact/add", methods=["POST"])
@login_required
def fact_add():
    label = request.form.get("label", "").strip()
    value = request.form.get("value", "").strip()
    if label and value:
        conn = get_db()
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS m FROM about_facts").fetchone()["m"]
        conn.execute("INSERT INTO about_facts (label, value, sort_order) VALUES (?, ?, ?)", (label, value, max_order + 1))
        conn.commit()
        conn.close()
    return redirect(url_for("admin.about_list"))


@admin_bp.route("/about/fact/<int:fid>/edit", methods=["POST"])
@login_required
def fact_edit(fid):
    label = request.form.get("label", "").strip()
    value = request.form.get("value", "").strip()
    conn = get_db()
    conn.execute("UPDATE about_facts SET label = ?, value = ? WHERE id = ?", (label, value, fid))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.about_list"))


@admin_bp.route("/about/fact/<int:fid>/delete", methods=["POST"])
@login_required
def fact_delete(fid):
    conn = get_db()
    conn.execute("DELETE FROM about_facts WHERE id = ?", (fid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.about_list"))


# ============================================================
# PROJECTS
# ============================================================

@admin_bp.route("/projects")
@login_required
def projects_list():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY sort_order, id").fetchall()
    conn.close()
    return render_template("admin/projects.html", projects=projects)


@admin_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if request.method == "POST":
        conn = get_db()
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS m FROM projects").fetchone()["m"]
        conn.execute(
            """INSERT INTO projects (title, tag, description, stack, link, icon, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                request.form.get("title", "").strip(),
                request.form.get("tag", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("stack", "").strip(),
                request.form.get("link", "#").strip() or "#",
                request.form.get("icon", "bar-chart"),
                max_order + 1,
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin.projects_list"))
    return render_template("admin/project_form.html", project=None, icons=available_icons())


@admin_bp.route("/projects/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def project_edit(pid):
    conn = get_db()
    if request.method == "POST":
        conn.execute(
            """UPDATE projects SET title=?, tag=?, description=?, stack=?, link=?, icon=? WHERE id=?""",
            (
                request.form.get("title", "").strip(),
                request.form.get("tag", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("stack", "").strip(),
                request.form.get("link", "#").strip() or "#",
                request.form.get("icon", "bar-chart"),
                pid,
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin.projects_list"))
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    conn.close()
    return render_template("admin/project_form.html", project=project, icons=available_icons())


@admin_bp.route("/projects/<int:pid>/delete", methods=["POST"])
@login_required
def project_delete(pid):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.projects_list"))


@admin_bp.route("/projects/<int:pid>/move/<direction>", methods=["POST"])
@login_required
def project_move(pid, direction):
    move("projects", pid, direction)
    return redirect(url_for("admin.projects_list"))


# ============================================================
# SKILLS
# ============================================================

@admin_bp.route("/skills")
@login_required
def skills_list():
    conn = get_db()
    groups = conn.execute("SELECT * FROM skill_groups ORDER BY sort_order, id").fetchall()
    data = []
    for g in groups:
        items = conn.execute(
            "SELECT * FROM skills WHERE group_id = ? ORDER BY sort_order, id", (g["id"],)
        ).fetchall()
        data.append((g, items))
    conn.close()
    return render_template("admin/skills.html", data=data)


@admin_bp.route("/skills/group/add", methods=["POST"])
@login_required
def skill_group_add():
    name = request.form.get("name", "").strip()
    if name:
        conn = get_db()
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS m FROM skill_groups").fetchone()["m"]
        conn.execute("INSERT INTO skill_groups (name, sort_order) VALUES (?, ?)", (name, max_order + 1))
        conn.commit()
        conn.close()
    return redirect(url_for("admin.skills_list"))


@admin_bp.route("/skills/group/<int:gid>/delete", methods=["POST"])
@login_required
def skill_group_delete(gid):
    conn = get_db()
    conn.execute("DELETE FROM skills WHERE group_id = ?", (gid,))
    conn.execute("DELETE FROM skill_groups WHERE id = ?", (gid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.skills_list"))


@admin_bp.route("/skills/<int:gid>/add", methods=["POST"])
@login_required
def skill_add(gid):
    name = request.form.get("name", "").strip()
    level = request.form.get("level", "50")
    try:
        level = max(0, min(100, int(level)))
    except ValueError:
        level = 50
    if name:
        conn = get_db()
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) AS m FROM skills WHERE group_id = ?", (gid,)
        ).fetchone()["m"]
        conn.execute(
            "INSERT INTO skills (group_id, name, level, sort_order) VALUES (?, ?, ?, ?)",
            (gid, name, level, max_order + 1),
        )
        conn.commit()
        conn.close()
    return redirect(url_for("admin.skills_list"))


@admin_bp.route("/skills/item/<int:sid>/edit", methods=["POST"])
@login_required
def skill_edit(sid):
    name = request.form.get("name", "").strip()
    level = request.form.get("level", "50")
    try:
        level = max(0, min(100, int(level)))
    except ValueError:
        level = 50
    conn = get_db()
    conn.execute("UPDATE skills SET name = ?, level = ? WHERE id = ?", (name, level, sid))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.skills_list"))


@admin_bp.route("/skills/item/<int:sid>/delete", methods=["POST"])
@login_required
def skill_delete(sid):
    conn = get_db()
    conn.execute("DELETE FROM skills WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin.skills_list"))
