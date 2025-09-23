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
TESTIMONIALS_FILE = "data/testimonials.json"  # New file for reviews
ADMIN_FILE = "data/admin.json"


# --- Initialization ---
def initialize_app():
    """Ensure all necessary directories and data files exist on startup."""
    os.makedirs("data", exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    for file_path in [PROJECTS_FILE, MESSAGES_FILE, TESTIMONIALS_FILE]:
        if not os.path.exists(file_path):
            save_json(file_path, [])

    # Initialize admin user if file doesn't exist
    if not os.path.exists(ADMIN_FILE):
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
        return (
            []
            if any(f in path for f in ["projects", "messages", "testimonials"])
            else {}
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return (
            []
            if any(f in path for f in ["projects", "messages", "testimonials"])
            else {}
        )


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
            print(f"Error deleting file {filename}: {e}")


# --- Frontend Routes ---
@app.route("/")
def home():
    """Render the homepage with projects and testimonials sorted by creation date."""
    projects = sorted(
        load_json(PROJECTS_FILE), key=lambda p: p.get("date_created", ""), reverse=True
    )
    testimonials = sorted(
        load_json(TESTIMONIALS_FILE),
        key=lambda t: t.get("date_created", ""),
        reverse=True,
    )
    return render_template("index.html", projects=projects, testimonials=testimonials)


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
    messages.insert(0, new_message)
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
    return (
        jsonify({"success": True, "project": project})
        if project
        else jsonify({"success": False, "message": "Project not found."})
    ), 404


@app.route("/api/testimonial/<int:tid>")
def get_testimonial_details(tid):
    """API endpoint to get details for a single testimonial."""
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    testimonials = load_json(TESTIMONIALS_FILE)
    testimonial = next((t for t in testimonials if t.get("id") == tid), None)
    return (
        jsonify({"success": True, "testimonial": testimonial})
        if testimonial
        else jsonify({"success": False, "message": "Testimonial not found."})
    ), 404


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
        if username == admin_data.get("username") and check_password_hash(
            admin_data.get("password", ""), password
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
    projects = sorted(
        load_json(PROJECTS_FILE), key=lambda p: p.get("date_created", ""), reverse=True
    )
    messages = sorted(
        load_json(MESSAGES_FILE), key=lambda m: m.get("timestamp", ""), reverse=True
    )
    testimonials = sorted(
        load_json(TESTIMONIALS_FILE),
        key=lambda t: t.get("date_created", ""),
        reverse=True,
    )
    return render_template(
        "admin_dashboard.html",
        projects=projects,
        messages=messages,
        testimonials=testimonials,
        admin=session.get("admin_username"),
    )


# --- Helper for file saving ---
def save_uploaded_file(file_storage):
    if file_storage and file_storage.filename and allowed_file(file_storage.filename):
        safe_filename = secure_filename(file_storage.filename)
        ext = safe_filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        file_storage.save(os.path.join(UPLOAD_FOLDER, filename))
        return filename
    return None


# --- Project CRUD (Admin Only) ---
@app.route("/admin/project/add", methods=["POST"])
def add_project():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    projects = load_json(PROJECTS_FILE)
    filename = save_uploaded_file(request.files.get("image"))
    new_project = {
        "id": get_next_id(projects),
        "title": request.form["title"],
        "description": request.form["description"],
        "category": request.form["category"],
        "status": request.form["status"],
        "image": filename,
        "date_created": datetime.now().strftime("%Y-%m-%d"),
    }
    projects.insert(0, new_project)
    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "project": new_project})


@app.route("/admin/project/edit/<int:pid>", methods=["POST"])
def edit_project(pid):
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    projects = load_json(PROJECTS_FILE)
    project = next((p for p in projects if p.get("id") == pid), None)
    if not project:
        return jsonify({"success": False, "message": "Project not found."}), 404

    project.update(
        {
            "title": request.form.get("title", project["title"]),
            "description": request.form.get("description", project["description"]),
            "category": request.form.get("category", project["category"]),
            "status": request.form.get("status", project["status"]),
        }
    )

    img_file = request.files.get("image")
    if img_file:
        remove_file(project.get("image"))
        project["image"] = save_uploaded_file(img_file)

    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "project": project})


@app.route("/admin/project/delete/<int:pid>", methods=["POST"])
def delete_project(pid):
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    projects = load_json(PROJECTS_FILE)
    project_to_delete = next((p for p in projects if p.get("id") == pid), None)
    if not project_to_delete:
        return jsonify({"success": False, "message": "Project not found."}), 404

    remove_file(project_to_delete.get("image"))
    projects = [p for p in projects if p.get("id") != pid]
    save_json(PROJECTS_FILE, projects)
    return jsonify({"success": True, "message": "Project deleted."})


# --- Testimonial CRUD (Admin Only) ---
@app.route("/admin/testimonial/add", methods=["POST"])
def add_testimonial():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    testimonials = load_json(TESTIMONIALS_FILE)
    filename = save_uploaded_file(request.files.get("image"))
    new_testimonial = {
        "id": get_next_id(testimonials),
        "name": request.form["name"],
        "company": request.form["company"],
        "text": request.form["text"],
        "rating": int(request.form.get("rating", 5)),
        "image": filename,
        "date_created": datetime.now().strftime("%Y-%m-%d"),
    }
    testimonials.insert(0, new_testimonial)
    save_json(TESTIMONIALS_FILE, testimonials)
    return jsonify({"success": True, "testimonial": new_testimonial})


@app.route("/admin/testimonial/edit/<int:tid>", methods=["POST"])
def edit_testimonial(tid):
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    testimonials = load_json(TESTIMONIALS_FILE)
    testimonial = next((t for t in testimonials if t.get("id") == tid), None)
    if not testimonial:
        return jsonify({"success": False, "message": "Testimonial not found."}), 404

    testimonial.update(
        {
            "name": request.form.get("name", testimonial["name"]),
            "company": request.form.get("company", testimonial["company"]),
            "text": request.form.get("text", testimonial["text"]),
            "rating": int(request.form.get("rating", testimonial["rating"])),
        }
    )

    img_file = request.files.get("image")
    if img_file:
        remove_file(testimonial.get("image"))
        testimonial["image"] = save_uploaded_file(img_file)

    save_json(TESTIMONIALS_FILE, testimonials)
    return jsonify({"success": True, "testimonial": testimonial})


@app.route("/admin/testimonial/delete/<int:tid>", methods=["POST"])
def delete_testimonial(tid):
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    testimonials = load_json(TESTIMONIALS_FILE)
    testimonial_to_delete = next((t for t in testimonials if t.get("id") == tid), None)
    if not testimonial_to_delete:
        return jsonify({"success": False, "message": "Testimonial not found."}), 404

    remove_file(testimonial_to_delete.get("image"))
    testimonials = [t for t in testimonials if t.get("id") != tid]
    save_json(TESTIMONIALS_FILE, testimonials)
    return jsonify({"success": True, "message": "Testimonial deleted."})


# --- Customer Query Management ---
@app.route("/admin/message/status/<int:mid>", methods=["POST"])
def update_message_status(mid):
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    messages = load_json(MESSAGES_FILE)
    message = next((m for m in messages if m.get("id") == mid), None)
    if not message:
        return jsonify({"success": False, "message": "Message not found."}), 404

    message["status"] = request.form.get("status", message["status"])
    save_json(MESSAGES_FILE, messages)
    return jsonify({"success": True, "message": "Status updated."})


@app.route("/admin/message/delete/<int:mid>", methods=["POST"])
def delete_message(mid):
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    messages = load_json(MESSAGES_FILE)
    if not any(m.get("id") == mid for m in messages):
        return jsonify({"success": False, "message": "Message not found."}), 404

    messages = [m for m in messages if m.get("id") != mid]
    save_json(MESSAGES_FILE, messages)
    return jsonify({"success": True, "message": "Message deleted."})


if __name__ == "__main__":
    initialize_app()
    app.run(debug=True, host="0.0.0.0", port=5003)
