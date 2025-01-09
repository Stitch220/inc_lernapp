from flask import request, redirect, url_for, session, flash, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json

USERS_DB = "users.db"
CHATS_DB = "chats.db"

active_nicknames = {}


def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session["username"] = username
                session["role"] = user[3]

                if user[3] == "admin":
                    return redirect(url_for("admin"))
                elif user[3] == "teacher":
                    return redirect(url_for("teacher_chat"))
                elif user[3] == "student":
                    return redirect(url_for("student_chat"))
                else:
                    flash("Invalid role", "error")
                    return redirect(url_for("login"))
            else:
                flash("Invalid credentials", "error")

    return render_template("index.html")

def auto_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    with sqlite3.connect(USERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session["username"] = username
            session["role"] = user[3]
            if user[3] == "admin":
                return {"success": True, "redirect_url": url_for("admin")}
            elif user[3] == "teacher":
                return {"success": True, "redirect_url": url_for("teacher_chat")}
            elif user[3] == "student":
                return {"success": True, "redirect_url": url_for("student_chat")}
            return {"success": False}

    return {"success": False}

def admin():
    if "username" in session and session["role"] == "admin":
        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users")
            users = cursor.fetchall()
        return render_template("admin.html", users=users)
    return redirect(url_for("login"))

def add_user():
    if "username" in session and session["role"] == "admin":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        try:
            with sqlite3.connect(USERS_DB) as conn:
                cursor = conn.cursor()
                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                               (username, hashed_password, role))
                conn.commit()
            flash("New user added successfully.", "success")
        except sqlite3.IntegrityError:
            flash("Error: Username already exists.", "error")
    return redirect(url_for("admin"))

def update_user():
    if "username" in session and session["role"] == "admin":
        user_id = request.form["id"]
        new_username = request.form["username"]
        new_password = request.form["password"]
        new_role = request.form["role"]

        with sqlite3.connect(USERS_DB) as conn:
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

def delete_user(user_id):
    if "username" in session and session["role"] == "admin":
        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        flash("User deleted successfully.", "success")
    return redirect(url_for("admin"))

def get_unique_nickname(student):
    if student in active_nicknames:
        return active_nicknames[student]

    with open("nickname.json", "r") as file:
        data = json.load(file)
        available_nicknames = data["nicknames"]

    used_nicknames = set(active_nicknames.values())
    for nickname in available_nicknames:
        if nickname not in used_nicknames:
            active_nicknames[student] = nickname
            return nickname

    return "Unknown"

def release_nickname(student):
    if student in active_nicknames:
        del active_nicknames[student]
