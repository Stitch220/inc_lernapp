from flask import render_template, request, redirect, url_for, session, flash
import sqlite3
import json
from datetime import datetime
from admin import active_nicknames, release_nickname



CHATS_DB = "chats.db"
USERS_DB = "users.db"


def init_chat_db():
    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student TEXT NOT NULL,
                teacher TEXT NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                nickname TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS archived_chats (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         student TEXT NOT NULL,
        #         teacher TEXT NOT NULL,
        #         title TEXT NOT NULL,
        #         nickname TEXT NOT NULL,
        #         chat_content TEXT NOT NULL,
        #         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        #     )
        # """)
        conn.commit()

def format_chats(chats):
    """Format chats to include date labels and time."""
    formatted_chats = []
    current_date = None
    for message, sender, timestamp in chats:
        # Format: DD.MM.JJJJ
        date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").strftime("%d.%m.%Y")
        time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M")

        if date != current_date:
            formatted_chats.append({"type": "date", "date": date})
            current_date = date

        formatted_chats.append({
            "type": "message",
            "message": message,
            "sender": sender,
            "time": f"{time} Uhr"
        })
    return formatted_chats



def student_chat():
    if "username" not in session or session.get("role") != "student":
        return redirect(url_for("login"))

    student = session["username"]

    # Lists all teachers
    with sqlite3.connect(USERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'teacher'")
        teachers = [teacher[0] for teacher in cursor.fetchall()]

    selected_teacher = request.args.get("teacher") or ""

    chats = []
    if selected_teacher:
        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message, sender, timestamp 
                FROM chats 
                WHERE student = ? AND teacher = ?
                ORDER BY timestamp ASC
            """, (student, selected_teacher))
            raw_chats = cursor.fetchall()
            chats = format_chats(raw_chats)

    if request.method == "POST" and selected_teacher:
        message = request.form["message"]
        if not message.strip():
            return redirect(url_for("student_chat", teacher=selected_teacher))

        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chats (student, teacher, message, sender, timestamp) VALUES (?, ?, ?, ?, ?)",
                (student, selected_teacher, message, "student", datetime.now()),
            )
            conn.commit()
        return redirect(url_for("student_chat", teacher=selected_teacher))

    return render_template(
        "student.html",
        student=student,
        teachers=teachers,
        selected_teacher=selected_teacher,
        chats=chats
    )

def teacher_chat():
    if "username" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))

    teacher = session["username"]

    # Lists all students
    with sqlite3.connect(USERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'student'")
        students = [student[0] for student in cursor.fetchall()]

    selected_student = request.args.get("student") or ""

    chats = []
    if selected_student:
        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message, sender, timestamp 
                FROM chats 
                WHERE student = ? AND teacher = ?
                ORDER BY timestamp ASC
            """, (selected_student, teacher))
            raw_chats = cursor.fetchall()
            chats = format_chats(raw_chats)

    if request.method == "POST" and selected_student:
        message = request.form["message"]
        if not message.strip():
            return redirect(url_for("teacher_chat", student=selected_student))

        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chats (student, teacher, message, sender, timestamp) VALUES (?, ?, ?, ?, ?)",
                (selected_student, teacher, message, "teacher", datetime.now()),
            )
            conn.commit()
        return redirect(url_for("teacher_chat", student=selected_student))

    return render_template(
        "teacher.html",
        teacher=teacher,
        students=students,
        selected_student=selected_student,
        chats=chats
    )


# def end_chat():
#     """Archiviert den Chat, speichert ihn in der Datenbank und gibt den Nickname frei."""
#     if "username" not in session:
#         return redirect(url_for("login"))

#     role = session["role"]
#     user = session["username"]
#     other_user = request.form["other_user"]  

#     # Pop-up für den Titel des Chats
#     chat_title = request.form["chat_title"].strip()
#     if not chat_title:
#         flash("Please enter a title for the chat.", "error")
#         return redirect(url_for(f"{role}_chat", teacher=other_user if role == "student" else user))

#     # Nickname ermitteln
#     if role == "teacher":
#         nickname = active_nicknames.get(other_user, "Unknown")
#     else:  # role == "student"
#         nickname = active_nicknames.get(user, "Unknown")

#     with sqlite3.connect(CHATS_DB) as conn:
#         cursor = conn.cursor()

#         # ID für den neuen archivierten Chat ermitteln
#         cursor.execute("SELECT MAX(id) FROM archived_chats")
#         next_id = (cursor.fetchone()[0] or 0) + 1

#         # Chat-Verlauf abrufen
#         cursor.execute("""
#             SELECT message, sender, timestamp FROM chats 
#             WHERE student = ? AND teacher = ?
#             ORDER BY timestamp ASC
#         """, (other_user if role == "teacher" else user, user if role == "teacher" else other_user))
#         chat_content = cursor.fetchall()

#         # Chat-Inhalt als JSON speichern
#         chat_json = json.dumps(chat_content)

#         # Archivierten Chat speichern
#         cursor.execute("""
#             INSERT INTO archived_chats (id, student, teacher, title, nickname, chat_content)
#             VALUES (?, ?, ?, ?, ?, ?)
#         """, (next_id, other_user if role == "teacher" else user, user if role == "teacher" else other_user,
#               chat_title, nickname, chat_json))

#         # Chat aus der aktiven Chats-Tabelle löschen
#         cursor.execute("""
#             DELETE FROM chats 
#             WHERE student = ? AND teacher = ?
#         """, (other_user if role == "teacher" else user, user if role == "teacher" else other_user))

#         conn.commit()

#     # Nickname freigeben
#     release_nickname(other_user if role == "teacher" else user)

#     flash("Chat has been archived.", "success")
#     return redirect(url_for(f"{role}_chat"))



