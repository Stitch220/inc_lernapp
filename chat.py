from flask import render_template, request, redirect, url_for, session
import sqlite3
import json
from datetime import datetime
import random
import os


CHATS_DB = "chats.db"
USERS_DB = "users.db"
NICKNAMES_JSON = "nicknames.json"



def format_chats(chats):
    """Format chats to include date labels and time."""
    formatted_chats = []
    current_date = None
    for message, sender, timestamp in chats:
        # Format: DD.MM.JJJJ
        timestamp = timestamp.split(".")[0] 
        date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
        time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")

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

def load_nicknames():
    """Lädt die Nicknames aus der JSON-Datei."""
    if not os.path.exists(NICKNAMES_JSON):
        raise FileNotFoundError(f"Die Datei {NICKNAMES_JSON} wurde nicht gefunden.")
    
    with open(NICKNAMES_JSON, "r") as file:
        data = json.load(file)
    return data["nicknames"]

def assign_nickname(student):
    """Weist einem Student einen zufälligen, noch nicht vergebenen Nickname zu."""
    used_nicknames = get_used_nicknames()
    available_nicknames = list(set(load_nicknames()) - set(used_nicknames))
    
    if available_nicknames:
        nickname = random.choice(available_nicknames)
    else:
        nickname = "undefined"  
    
    save_nickname(student, nickname)
    return nickname

def get_used_nicknames():
    """Holt die bereits vergebenen Nicknames aus der Datenbank."""
    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT nickname FROM nicknames")
        return [row[0] for row in cursor.fetchall()]

def save_nickname(student, nickname):
    """Speichert den Nickname eines Students in der Datenbank."""
    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO nicknames (student, nickname) VALUES (?, ?)", (student, nickname))
        conn.commit()

def get_nickname(student):
    """Holt den Nickname eines Students aus der Datenbank."""
    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nickname FROM nicknames WHERE student = ?", (student,))
        result = cursor.fetchone()
        return result[0] if result else assign_nickname(student)

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

    # Lists all students with their nicknames
    with sqlite3.connect(USERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'student'")
        raw_students = [student[0] for student in cursor.fetchall()]

    # Get nicknames for each student
    students = [(student, get_nickname(student)) for student in raw_students]

    selected_student = request.args.get("student") or ""
    selected_nickname = get_nickname(selected_student) if selected_student else ""

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
        selected_nickname=selected_nickname,
        chats=chats
    )




def end_chat():
    pass
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



