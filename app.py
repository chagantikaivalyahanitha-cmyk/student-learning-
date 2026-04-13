from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret_key"

DB = "database.db"


# ---------------- DATABASE ---------------- #
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        user_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        score INTEGER,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------------- AUTH ---------------- #
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect(url_for("login"))
        except:
            flash("Username already exists")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ---------------- #
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    subjects = conn.execute(
        "SELECT * FROM subjects WHERE user_id=?", (session["user_id"],)
    ).fetchall()

    return render_template("dashboard.html", subjects=subjects)


# ---------------- SUBJECT CRUD ---------------- #
@app.route("/add_subject", methods=["POST"])
def add_subject():
    name = request.form["name"]

    conn = get_db()
    conn.execute(
        "INSERT INTO subjects (name, user_id) VALUES (?, ?)",
        (name, session["user_id"])
    )
    conn.commit()

    return redirect(url_for("dashboard"))


@app.route("/delete_subject/<int:id>")
def delete_subject(id):
    conn = get_db()
    conn.execute("DELETE FROM subjects WHERE id=?", (id,))
    conn.commit()
    return redirect(url_for("dashboard"))


# ---------------- SCORE CRUD ---------------- #
@app.route("/subject/<int:subject_id>", methods=["GET", "POST"])
def subject_detail(subject_id):
    conn = get_db()

    if request.method == "POST":
        score = request.form["score"]
        date = request.form["date"]

        conn.execute(
            "INSERT INTO scores (subject_id, score, date) VALUES (?, ?, ?)",
            (subject_id, score, date)
        )
        conn.commit()

    scores = conn.execute(
        "SELECT * FROM scores WHERE subject_id=?",
        (subject_id,)
    ).fetchall()

    return render_template("subject.html", scores=scores, subject_id=subject_id)


@app.route("/delete_score/<int:id>/<int:subject_id>")
def delete_score(id, subject_id):
    conn = get_db()
    conn.execute("DELETE FROM scores WHERE id=?", (id,))
    conn.commit()
    return redirect(url_for("subject_detail", subject_id=subject_id))


# ---------------- ANALYTICS ---------------- #
@app.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    data = conn.execute("""
    SELECT subjects.name, AVG(scores.score) as avg_score
    FROM scores
    JOIN subjects ON subjects.id = scores.subject_id
    WHERE subjects.user_id=?
    GROUP BY subjects.name
    """, (session["user_id"],)).fetchall()

    return render_template("analytics.html", data=data)


# ---------------- REPORT ---------------- #
@app.route("/report")
def report():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    report_data = conn.execute("""
    SELECT subjects.name, scores.score, scores.date
    FROM scores
    JOIN subjects ON subjects.id = scores.subject_id
    WHERE subjects.user_id=?
    """, (session["user_id"],)).fetchall()

    return render_template("report.html", report_data=report_data)


# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    init_db()
    print("Starting Flask server...")  # ADD THIS
    app.run(debug=True)