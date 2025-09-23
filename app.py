import os
import uuid
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
# For production, it's highly recommended to set the secret key via an environment variable
# for better security.
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "a_strong_default_secret_key_for_dev")
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# --- Data file paths ---
PROJECTS_FILE = "data/projects.json"
MESSAGES_FILE = "data/messages.json"
ADMIN_FILE = "data/admin.json"


# --- Initialization ---
def initialize_app():
    """Ensure all necessary directories and data files exist on startup."""
    os.makedirs("data", exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if not os.path.exists(PROJECTS_FILE):
        save_json(PROJECTS_FILE, [])
    if not os.path.exists(MESSAGES_FILE):
        save_json(MESSAGES_FILE, [])
    # Initialize admin user if file doesn't exist
    if not os.path.exists(ADMIN_FILE):
        # In a real-world scenario, the initial admin setup should be handled
        # by a separate script or a first-run setup page.
        save_json(
            ADMIN_FILE,
            {
                "username": "admin",
                "password": generate_password_hash("rrr_admin_2025!"),
            },
        )


# --- Utility Functions ---
def allowed_file(filename):
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_json(path):
    """Load JSON data from a file, returning an empty list/dict on error."""
    if not os.path.exists(path):
        return [] if "projects" in path or "messages" in path else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return [] if "projects" in path or "messages" in path else {}


def save_json(path, data):
    """Save data to a JSON file with proper indentation."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def is_admin():
    """Check if an admin is logged into the session."""
    return session.get("admin_logged_in", False)


def get_next_id(items):
    """Generate a new unique ID, robust against deletions."""
    if not items:
        return 1
    return max(item.get("id", 0) for item in items) + 1


def remove_file(filename):
    """Safely remove a file from the upload folder."""
    if filename:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        except OSError as e:
            # Log this error in a real application
            print(f"Error deleting file {filename}: {e}")


# --- Frontend Routes ---
@app.route("/")
def home():
    """Render the homepage with projects sorted by creation date."""
    projects = sorted(
        load_json(PROJECTS_FILE), key=lambda p: p.get("date_created", ""), reverse=True
    )
    return render_template("index.html", projects=projects)


@app.route("/static/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded files from the UPLOAD_FOLDER."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# --- API Routes ---
@app.route("/api/contact", methods=["POST"])
def api_contact():
    """Handle the contact form submission via AJAX."""
    data = request.get_json()
    if not data or not all(
        k in data for k in ["name", "email", "phone", "service", "message"]
    ):
        return jsonify({"success": False, "message": "Missing required fields."}), 400

    messages = load_json(MESSAGES_FILE)
    new_message = {
        "id": get_next_id(messages),
        "name": data.get("name", "N/A"),
        "email": data.get("email", "N/A"),
        "phone": data.get("phone", "N/A"),
        "service": data.get("service", "N/A"),
        "message": data.get("message", "N/A"),
        "timestamp": datetime.now().isoformat(),
        "status": "New",
    }
    messages.insert(0, new_message)  # Prepend to keep it sorted by time
    save_json(MESSAGES_FILE, messages)
    return jsonify(
        {"success": True, "message": "Query received! We'll contact you soon."}
    )


@app.route("/api/project/<int:pid>")
def get_project_details(pid):
    """API endpoint to get full details for a single project."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    projects = load_json(PROJECTS_FILE)
    project = next((p for p in projects if p.get("id") == pid), None)

    if project:
        return jsonify({"success": True, "project": project})
    return jsonify({"success": False, "message": "Project not found."}), 404


# --- Admin Authentication ---
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Handle admin login."""
    if is_admin():
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin_data = load_json(ADMIN_FILE)

        is_correct_username = username == admin_data.get("username")
        is_correct_password = check_password_hash(
            admin_data.get("password", ""), password
        )

        if is_correct_username and is_correct_password:
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password. Please try again."

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    """Log out the admin by clearing the session."""
    session.clear()
    return redirect(url_for("admin_login"))


# --- Admin Dashboard ---
@app.route("/admin/dashboard")
def admin_dashboard():
    """Display the admin dashboard if logged in."""
    if not is_admin():
        return redirect(url_for("admin_login"))

    # Load and sort data to show the newest entries first
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
    """Add a new project and return the new project data."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if not all(
        f in request.form for f in ["title", "description", "category", "status"]
    ):
        return jsonify({"success": False, "message": "Missing form fields."}), 400

    projects = load_json(PROJECTS_FILE)
    filename = None
    img_file = request.files.get("image")

    if img_file and img_file.filename:
        if not allowed_file(img_file.filename):
            return jsonify({"success": False, "message": "Invalid file type."}), 400
        # Create a unique filename to prevent conflicts
        ext = img_file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        img_file.save(os.path.join(UPLOAD_FOLDER, filename))

    new_project = {
        "id": get_next_id(projects),
        "title": request.form["title"],
        "description": request.form["description"],
        "category": request.form["category"],
        "status": request.form["status"],
        "image": filename,
        "date_created": datetime.now().strftime("%Y-%m-%d"),
    }
    projects.insert(0, new_project)  # Prepend for chronological order
    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "project": new_project})


@app.route("/admin/project/edit/<int:pid>", methods=["POST"])
def edit_project(pid):
    """Edit an existing project."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    projects = load_json(PROJECTS_FILE)
    project = next((p for p in projects if p.get("id") == pid), None)
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

        # Remove old image before saving new one
        remove_file(project.get("image"))

        ext = img_file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        img_file.save(os.path.join(UPLOAD_FOLDER, filename))
        project["image"] = filename

    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "project": project})


@app.route("/admin/project/delete/<int:pid>", methods=["POST"])
def delete_project(pid):
    """Delete a project and its associated image."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    projects = load_json(PROJECTS_FILE)
    project_to_delete = next((p for p in projects if p.get("id") == pid), None)

    if not project_to_delete:
        return jsonify({"success": False, "message": "Project not found."}), 404

    # Remove the image file from storage
    remove_file(project_to_delete.get("image"))

    # Filter out the deleted project
    projects = [p for p in projects if p.get("id") != pid]
    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "message": "Project deleted."})


# --- Customer Query Management ---
@app.route("/admin/message/status/<int:mid>", methods=["POST"])
def update_message_status(mid):
    """Update the status of a customer message."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    messages = load_json(MESSAGES_FILE)
    message = next((m for m in messages if m.get("id") == mid), None)
    status = request.form.get("status")

    if not message:
        return jsonify({"success": False, "message": "Message not found."}), 404

    message["status"] = status
    save_json(MESSAGES_FILE, messages)
    return jsonify({"success": True, "message": "Status updated."})


@app.route("/admin/message/delete/<int:mid>", methods=["POST"])
def delete_message(mid):
    """Delete a customer message."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    messages = load_json(MESSAGES_FILE)
    initial_count = len(messages)
    messages = [m for m in messages if m.get("id") != mid]

    if len(messages) == initial_count:
        return jsonify({"success": False, "message": "Message not found."}), 404

    save_json(MESSAGES_FILE, messages)
    return jsonify({"success": True, "message": "Message deleted."})


if __name__ == "__main__":
    initialize_app()
    app.run(debug=True, host="0.0.0.0", port=5003)
