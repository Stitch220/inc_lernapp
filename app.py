
### Import Modules ###
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

### Setup Database ###
DATABASE = "users.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('teacher', 'student', 'admin'))
            )
        """)
        conn.commit()

        # Create default admin user if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'Admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           ("Admin", generate_password_hash("0000"), "admin"))
            conn.commit()

### Standard Routes for Login Page ###
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session["username"] = username
                session["role"] = user[3]

                if user[3] == "admin":
                    return redirect(url_for("admin"))
                return redirect(url_for(user[3]))
            else:
                flash("Invalid credentials", "error")

    return render_template("index.html")

### Auto Login Route ###
@app.route("/auto_login", methods=["POST"])
def auto_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            # Simulate login
            session["username"] = username
            session["role"] = user[3]

            # Determine redirect URL based on role
            if user[3] == "admin":
                redirect_url = url_for("admin")
            elif user[3] == "teacher":
                redirect_url = url_for("teacher")
            elif user[3] == "student":
                redirect_url = url_for("student")
            else:
                redirect_url = url_for("login")

            return {"success": True, "redirect_url": redirect_url}

    return {"success": False}


### Teacher, Student and Admin Routes ###
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


@app.route("/admin")
def admin():
    if "username" in session and session["role"] == "admin":
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users")
            users = cursor.fetchall()
        return render_template("admin.html", users=users)
    return redirect(url_for("login"))


### CRUD Routes ###
@app.route("/add_user", methods=["POST"])
def add_user():
    if "username" in session and session["role"] == "admin":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                               (username, hashed_password, role))
                conn.commit()
            flash("New user added successfully.", "success")
        except sqlite3.IntegrityError:
            flash("Error: Username already exists.", "error")
    return redirect(url_for("admin"))

@app.route("/update_user", methods=["POST"])
def update_user():
    if "username" in session and session["role"] == "admin":
        user_id = request.form["id"]
        new_username = request.form["username"]
        new_password = request.form["password"]
        new_role = request.form["role"]

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            if new_username:
                cursor.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
            if new_password:
                hashed_password = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
            if new_role:
                cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
            conn.commit()

        flash("User updated successfully.", "success")
    return redirect(url_for("admin"))

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if "username" in session and session["role"] == "admin":
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        flash("User deleted successfully.", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
