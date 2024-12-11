from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database setup
DATABASE = "users.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('teacher', 'student'))
            )
        """)
        conn.commit()

def add_user(username, password, role):
    hashed_password = generate_password_hash(password)
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           (username, hashed_password, role))
            conn.commit()
            print(f"User {username} added successfully.")
        except sqlite3.IntegrityError:
            print(f"Error: Username {username} already exists.")


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        stay_logged_in = request.form.get("stay_logged_in")

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session["username"] = username
                session["role"] = user[3]
                
                # Local Storage script for "stay logged in"
                response = redirect(url_for(user[3]))
                response.set_cookie("username", username if stay_logged_in else "", max_age=60*60*24*30)
                return response
            else:
                flash("Invalid credentials", "error")

    return render_template("index.html")

@app.route("/teacher")
def teacher():
    if "username" in session and session["role"] == "teacher":
        return render_template("teacher.html", username=session["username"])
    return redirect(url_for("login"))

@app.route("/student")
def student():
    if "username" in session and session["role"] == "student":
        return render_template("student.html", username=session["username"])
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
