from flask import Flask
from admin import login, auto_login, admin, add_user, update_user, delete_user
from chat import student_chat, teacher_chat, end_chat
import sqlite3
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

USERS_DB = "users.db"
CHATS_DB = "chats.db"

def init_databases():
    """Erstellt die benötigten Tabellen in der Datenbank, falls sie noch nicht existieren."""
    # Initialisiere USERS_DB
    with sqlite3.connect(USERS_DB) as conn:
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
        cursor.execute("SELECT * FROM users WHERE username = 'Admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           ("Admin", generate_password_hash("0000"), "admin"))
            conn.commit()

    # Initialisiere CHATS_DB
    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student TEXT NOT NULL,
                teacher TEXT NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL CHECK (sender IN ('student', 'teacher')),
                nickname TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nicknames (
                student TEXT PRIMARY KEY,
                nickname TEXT UNIQUE
            )
        """)
        conn.commit()

app.add_url_rule("/", "login", login, methods=["GET", "POST"])
app.add_url_rule("/auto_login", "auto_login", auto_login, methods=["POST"])
app.add_url_rule("/admin", "admin", admin)
app.add_url_rule("/add_user", "add_user", add_user, methods=["POST"])
app.add_url_rule("/update_user", "update_user", update_user, methods=["POST"])
app.add_url_rule("/delete_user/<int:user_id>", "delete_user", delete_user)
app.add_url_rule("/student", "student_chat", student_chat, methods=["GET", "POST"])
app.add_url_rule("/teacher", "teacher_chat", teacher_chat, methods=["GET", "POST"])
app.add_url_rule("/end_chat", "end_chat", end_chat, methods=["POST"])

if __name__ == "__main__":
    init_databases()
    app.run(debug=True)
