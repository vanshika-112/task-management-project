from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task

app = Flask(__name__)

app.secret_key = "taskmanagersecret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "Username already exists!"

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect("/dashboard")

        return "Invalid username or password!"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    tasks = Task.query.filter_by(user_id=session["user_id"]).all()

    total_tasks = len(tasks)
    completed_tasks = len([task for task in tasks if task.status == "Completed"])
    pending_tasks = total_tasks - completed_tasks

    return render_template(
        "dashboard.html",
        username=session["username"],
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )

@app.route("/add_task", methods=["GET", "POST"])
def add_task():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        new_task = Task(
            title=request.form["title"],
            description=request.form["description"],
            due_date=request.form["due_date"],
            priority=request.form["priority"],
            user_id=session["user_id"]
        )

        db.session.add(new_task)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("add_task.html")

@app.route("/delete_task/<int:id>")
def delete_task(id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    if task.user_id != session["user_id"]:
        return "Unauthorized"

    db.session.delete(task)
    db.session.commit()

    return redirect("/dashboard")

@app.route("/complete_task/<int:id>")
def complete_task(id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    if task.user_id != session["user_id"]:
        return "Unauthorized"

    task.status = "Completed"

    db.session.commit()

    return redirect("/dashboard")

@app.route("/edit_task/<int:id>", methods=["GET", "POST"])
def edit_task(id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    if task.user_id != session["user_id"]:
        return "Unauthorized"

    if request.method == "POST":

        task.title = request.form["title"]
        task.description = request.form["description"]
        task.due_date = request.form["due_date"]
        task.priority = request.form["priority"]

        db.session.commit()

        return redirect("/dashboard")

    return render_template("edit_task.html", task=task)

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)