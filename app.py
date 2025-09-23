import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
    jsonify,
)
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# --- Configuration ---
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

app = Flask(__name__)
app.secret_key = "super_secret_key_for_rrr_construction_2025"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# --- Data file paths ---
PROJECTS_FILE = "data/projects.json"
MESSAGES_FILE = "data/messages.json"
ADMIN_FILE = "data/admin.json"

# --- Ensure directories and files exist ---
os.makedirs("data", exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- Utility Functions ---
def allowed_file(filename):
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_json(path):
    """Load JSON data from a file, returning an empty list on error."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_json(path, data):
    """Save data to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def is_admin():
    """Check if an admin is logged in."""
    return session.get("admin_logged_in", False)


def init_data():
    """Initialize data files if they don't exist."""
    if not os.path.exists(PROJECTS_FILE):
        save_json(PROJECTS_FILE, [])
    if not os.path.exists(MESSAGES_FILE):
        save_json(MESSAGES_FILE, [])
    if not os.path.exists(ADMIN_FILE):
        save_json(
            ADMIN_FILE,
            {
                "username": "admin",
                "password": generate_password_hash("rrr2024"),
            },
        )


init_data()


# --- Frontend Routes ---
@app.route("/")
def home():
    """Render the homepage with sorted projects."""
    projects = sorted(
        load_json(PROJECTS_FILE), key=lambda p: p.get("date_created", ""), reverse=True
    )
    return render_template("index.html", projects=projects)


@app.route("/static/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# --- API Routes ---
@app.route("/api/contact", methods=["POST"])
def api_contact():
    """Handle the contact form submission via AJAX."""
    data = request.get_json()
    if not all(k in data for k in ["name", "email", "phone", "service", "message"]):
        return jsonify({"success": False, "message": "Missing required fields."}), 400

    messages = load_json(MESSAGES_FILE)
    new_id = (messages[0]["id"] + 1) if messages else 1

    new_message = {
        "id": new_id,
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "service": data.get("service"),
        "message": data.get("message"),
        "timestamp": datetime.now().isoformat(),
        "status": "New",
    }
    messages.insert(0, new_message)  # Prepend to keep it sorted
    save_json(MESSAGES_FILE, messages)
    return jsonify(
        {"success": True, "message": "Query received! We'll contact you soon."}
    )


# --- Admin Authentication ---
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Handle admin login."""
    if is_admin():
        return redirect(url_for("admin_dashboard"))

    error = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Load admin data from a file that is not publicly served
        admin_data_path = os.path.join(app.root_path, ADMIN_FILE)
        if os.path.exists(admin_data_path):
            admin = load_json(admin_data_path)
        else:
            admin = {}

        if username == admin.get("username") and check_password_hash(
            admin.get("password", ""), password
        ):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    """Log out the admin."""
    session.clear()
    return redirect(url_for("admin_login"))


# --- Admin Dashboard ---
@app.route("/admin/dashboard")
def admin_dashboard():
    """Display the admin dashboard."""
    if not is_admin():
        return redirect(url_for("admin_login"))

    # Load and sort data to show newest first
    projects = sorted(
        load_json(PROJECTS_FILE), key=lambda p: p.get("date_created", ""), reverse=True
    )
    messages = sorted(
        load_json(MESSAGES_FILE), key=lambda m: m.get("timestamp", ""), reverse=True
    )

    return render_template(
        "admin_dashboard.html",
        projects=projects,
        messages=messages,
        admin=session.get("admin_username"),
    )


# --- Project CRUD (Admin Only) ---
@app.route("/admin/project/add", methods=["POST"])
def add_project():
    """Add a new project."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if not all(
        f in request.form for f in ["title", "description", "category", "status"]
    ):
        return (
            jsonify({"success": False, "message": "Missing required form fields."}),
            400,
        )

    projects = load_json(PROJECTS_FILE)
    filename = None
    img_file = request.files.get("image")

    if img_file and img_file.filename:
        if not allowed_file(img_file.filename):
            return jsonify({"success": False, "message": "Invalid file type."}), 400
        filename = (
            f"{int(datetime.now().timestamp())}_{secure_filename(img_file.filename)}"
        )
        img_file.save(os.path.join(UPLOAD_FOLDER, filename))

    new_id = (projects[0]["id"] + 1) if projects else 1
    new_project = {
        "id": new_id,
        "title": request.form["title"],
        "description": request.form["description"],
        "category": request.form["category"],
        "status": request.form["status"],
        "image": filename,
        "date_created": datetime.now().strftime("%Y-%m-%d"),
    }
    projects.insert(0, new_project)  # Prepend for chronological order
    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "message": "Project added successfully."})


@app.route("/admin/project/edit/<int:pid>", methods=["POST"])
def edit_project(pid):
    """Edit an existing project."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    projects = load_json(PROJECTS_FILE)
    project = next((p for p in projects if p["id"] == pid), None)
    if not project:
        return jsonify({"success": False, "message": "Project not found."}), 404

    # Update text fields
    project["title"] = request.form.get("title", project["title"])
    project["description"] = request.form.get("description", project["description"])
    project["category"] = request.form.get("category", project["category"])
    project["status"] = request.form.get("status", project["status"])

    # Handle optional image update
    img_file = request.files.get("image")
    if img_file and img_file.filename:
        if not allowed_file(img_file.filename):
            return jsonify({"success": False, "message": "Invalid file type"}), 400
        filename = (
            f"{int(datetime.now().timestamp())}_{secure_filename(img_file.filename)}"
        )
        img_file.save(os.path.join(UPLOAD_FOLDER, filename))
        # TODO: Optionally delete the old image file from disk
        project["image"] = filename

    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "message": "Project updated successfully."})


@app.route("/admin/project/delete/<int:pid>", methods=["POST"])
def delete_project(pid):
    """Delete a project."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    projects = load_json(PROJECTS_FILE)
    initial_count = len(projects)
    projects = [p for p in projects if p["id"] != pid]

    if len(projects) == initial_count:
        return jsonify({"success": False, "message": "Project not found."}), 404

    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "message": "Project deleted."})


# --- Customer Query Management ---
@app.route("/admin/message/status/<int:mid>", methods=["POST"])
def update_message_status(mid):
    """Update the status of a customer message."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    messages = load_json(MESSAGES_FILE)
    message_found = False
    status = request.form.get("status")

    for m in messages:
        if m["id"] == mid:
            m["status"] = status
            message_found = True
            break

    if not message_found:
        return jsonify({"success": False, "message": "Message not found."}), 404

    save_json(MESSAGES_FILE, messages)
    return jsonify({"success": True, "message": "Status updated."})


@app.route("/admin/message/delete/<int:mid>", methods=["POST"])
def delete_message(mid):
    """Delete a customer message."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    messages = load_json(MESSAGES_FILE)
    initial_count = len(messages)
    messages = [m for m in messages if m["id"] != mid]

    if len(messages) == initial_count:
        return jsonify({"success": False, "message": "Message not found."}), 404

    save_json(MESSAGES_FILE, messages)
    return jsonify({"success": True, "message": "Message deleted."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
