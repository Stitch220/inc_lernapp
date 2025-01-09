from flask import render_template, request, redirect, url_for, session, flash
import sqlite3
import json
from datetime import datetime
from admin import active_nicknames, release_nickname



CHATS_DB = "chats.db"
USERS_DB = "users.db"


def student_chat():
    if "username" not in session or session.get("role") != "student":
        return redirect(url_for("login"))

    student = session["username"]

    # Liste der Lehrer abrufen
    with sqlite3.connect(USERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'teacher'")
        teachers = [teacher[0] for teacher in cursor.fetchall()]

    # Archivierte Chats abrufen, die den aktuellen Schüler betreffen
    archived_chats = []
    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title FROM archived_chats 
            WHERE student = ?
            ORDER BY timestamp DESC
        """, (student,))
        archived_chats = cursor.fetchall()

    selected_teacher = request.args.get("teacher")
    selected_archived_chat_id = request.args.get("archived_chat")

    chats = []
    archived = False

    if selected_archived_chat_id:
        # Archivierten Chat abrufen und den Chat-Inhalt laden
        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chat_content, teacher FROM archived_chats 
                WHERE id = ? AND student = ?
            """, (selected_archived_chat_id, student))
            result = cursor.fetchone()
            if result:
                chats = json.loads(result[0])  # Chat-Inhalt als Liste laden
                archived_chat_teacher = result[1]
                archived = True
    elif selected_teacher:
        # Aktuellen Chat abrufen
        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message, sender, timestamp 
                FROM chats 
                WHERE student = ? AND teacher = ?
                ORDER BY timestamp ASC
            """, (student, selected_teacher))
            chats = cursor.fetchall()

        # Falls kein aktiver Chat existiert, neuen Chat starten
        if not chats:
            nickname = get_unique_nickname(student)
            flash(f"Starting a new chat with {selected_teacher}. Your nickname is {nickname}.", "info")

    if request.method == "POST" and selected_teacher and not archived:
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
        archived_chats=archived_chats,
        selected_teacher=selected_teacher,
        selected_archived_chat_id=selected_archived_chat_id,
        archived_chat_teacher=archived_chat_teacher if archived else None,
        chats=chats,
        archived=archived
    )





def teacher_chat():
    if "username" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))

    teacher = session["username"]

    # Liste der Schüler mit aktiven Chats abrufen
    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT student FROM chats 
            WHERE teacher = ?
        """, (teacher,))
        students = [student[0] for student in cursor.fetchall()]

    # Archivierte Chats abrufen
    archived_chats = []
    with sqlite3.connect(CHATS_DB) as conn:
        cursor.execute("""
            SELECT id, title FROM archived_chats 
            WHERE teacher = ? 
            ORDER BY timestamp DESC
        """, (teacher,))
        archived_chats = cursor.fetchall()


    selected_student = request.args.get("student")
    selected_archived_chat_id = request.args.get("archived_chat")

    chats = []
    archived = False

    if selected_archived_chat_id:
        # Öffnen des archivierten Chats
        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chat_content FROM archived_chats 
                WHERE id = ?
            """, (selected_archived_chat_id,))
            result = cursor.fetchone()
            if result:
                chats = json.loads(result[0])
                archived = True
    elif selected_student:
        # Aktuellen Chat abrufen
        with sqlite3.connect(CHATS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message, sender, timestamp 
                FROM chats 
                WHERE student = ? AND teacher = ?
                ORDER BY timestamp ASC
            """, (selected_student, teacher))
            chats = cursor.fetchall()

    return render_template(
        "teacher.html",
        teacher=teacher,
        students=students,
        archived_chats=archived_chats,
        selected_student=selected_student,
        selected_archived_chat_id=selected_archived_chat_id,
        chats=chats,
        archived=archived
    )



def end_chat():
    """Archiviert den Chat, speichert ihn in der Datenbank und gibt den Nickname frei."""
    if "username" not in session:
        return redirect(url_for("login"))

    role = session["role"]
    user = session["username"]
    other_user = request.form["other_user"]  # Der andere Chat-Partner (Lehrer oder Schüler)

    # Pop-up für den Titel des Chats
    chat_title = request.form["chat_title"].strip()
    if not chat_title:
        flash("Please enter a title for the chat.", "error")
        return redirect(url_for(f"{role}_chat", teacher=other_user if role == "student" else user))

    # Nickname ermitteln
    if role == "teacher":
        nickname = active_nicknames.get(other_user, "Unknown")
    else:  # role == "student"
        nickname = active_nicknames.get(user, "Unknown")

    with sqlite3.connect(CHATS_DB) as conn:
        cursor = conn.cursor()

        # ID für den neuen archivierten Chat ermitteln
        cursor.execute("SELECT MAX(id) FROM archived_chats")
        next_id = (cursor.fetchone()[0] or 0) + 1

        # Chat-Verlauf abrufen
        cursor.execute("""
            SELECT message, sender, timestamp FROM chats 
            WHERE student = ? AND teacher = ?
            ORDER BY timestamp ASC
        """, (other_user if role == "teacher" else user, user if role == "teacher" else other_user))
        chat_content = cursor.fetchall()

        # Chat-Inhalt als JSON speichern
        chat_json = json.dumps(chat_content)

        # Archivierten Chat speichern
        cursor.execute("""
            INSERT INTO archived_chats (id, student, teacher, title, nickname, chat_content)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (next_id, other_user if role == "teacher" else user, user if role == "teacher" else other_user,
              chat_title, nickname, chat_json))

        # Chat aus der aktiven Chats-Tabelle löschen
        cursor.execute("""
            DELETE FROM chats 
            WHERE student = ? AND teacher = ?
        """, (other_user if role == "teacher" else user, user if role == "teacher" else other_user))

        conn.commit()

    # Nickname freigeben
    release_nickname(other_user if role == "teacher" else user)

    flash("Chat has been archived.", "success")
    return redirect(url_for(f"{role}_chat"))



