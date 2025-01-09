from flask import Flask
from admin import init_db, login, auto_login, admin, add_user, update_user, delete_user
from chat import student_chat, teacher_chat, end_chat, init_chat_db

app = Flask(__name__)
app.secret_key = "your_secret_key"

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
    init_db()
    init_chat_db()
    app.run(debug=True)
