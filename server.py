"""
SecuExam — Secure Exam Paper Distribution System
Flask Backend Server
"""

import os
import json
import uuid
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO

from flask import (
    Flask, request, jsonify, session, send_file,
    render_template, redirect, url_for
)
import bcrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="secuexam_app",
    template_folder="secuexam_app",
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["SECRET_KEY"] = os.environ.get(
    "SECUEXAM_SECRET_KEY",
    "secuexam-dev-secret-key-change-in-production",
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "secuexam_app", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB limit

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "secuexam.db")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id      TEXT PRIMARY KEY,
        email        TEXT UNIQUE NOT NULL,
        name         TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role         TEXT NOT NULL CHECK(role IN ('setter','receiver','admin')),
        college_code TEXT,
        approved     INTEGER DEFAULT 1,
        created_at   TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS exam_papers (
        paper_id          TEXT PRIMARY KEY,
        setter_id         TEXT NOT NULL REFERENCES users(user_id),
        original_filename TEXT NOT NULL,
        file_path         TEXT NOT NULL,
        file_size_mb      REAL NOT NULL,
        encryption_status INTEGER DEFAULT 0,
        subject           TEXT,
        created_at        TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS exam_schedule (
        schedule_id    TEXT PRIMARY KEY,
        paper_id       TEXT UNIQUE NOT NULL REFERENCES exam_papers(paper_id) ON DELETE CASCADE,
        exam_start_time TEXT NOT NULL,
        duration_min   INTEGER NOT NULL,
        unlock_time    TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS encryption_keys (
        key_id       TEXT PRIMARY KEY,
        paper_id     TEXT NOT NULL REFERENCES exam_papers(paper_id) ON DELETE CASCADE,
        key_fragment TEXT NOT NULL,
        fragment_idx INTEGER NOT NULL,
        owner_id     TEXT REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS download_logs (
        log_id           TEXT PRIMARY KEY,
        paper_id         TEXT REFERENCES exam_papers(paper_id),
        receiver_id      TEXT REFERENCES users(user_id),
        access_timestamp TEXT DEFAULT (datetime('now')),
        ip_address       TEXT,
        status           TEXT CHECK(status IN ('success','time_locked','failed','denied')),
        details          TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_exam_schedule_start_time
        ON exam_schedule(exam_start_time);
    CREATE INDEX IF NOT EXISTS idx_exam_schedule_unlock_time
        ON exam_schedule(unlock_time);
    CREATE INDEX IF NOT EXISTS idx_download_logs_status
        ON download_logs(status);
    CREATE INDEX IF NOT EXISTS idx_download_logs_receiver
        ON download_logs(receiver_id);
    """)

    # Seed default admin if not exists
    admin_exists = conn.execute(
        "SELECT 1 FROM users WHERE role='admin' LIMIT 1"
    ).fetchone()
    if not admin_exists:
        admin_id = str(uuid.uuid4())
        pw_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (user_id, email, name, password_hash, role, approved) "
            "VALUES (?, ?, ?, ?, 'admin', 1)",
            (admin_id, "admin@secuexam.in", "System Administrator", pw_hash),
        )
    # Seed a demo setter
    setter_exists = conn.execute(
        "SELECT 1 FROM users WHERE role='setter' LIMIT 1"
    ).fetchone()
    if not setter_exists:
        setter_id = str(uuid.uuid4())
        pw_hash = bcrypt.hashpw("setter123".encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (user_id, email, name, password_hash, role, approved) "
            "VALUES (?, ?, ?, ?, 'setter', 1)",
            (setter_id, "setter@vit.ac.in", "Dr. Ramanujan", pw_hash),
        )
    # Seed a demo receiver
    receiver_exists = conn.execute(
        "SELECT 1 FROM users WHERE role='receiver' LIMIT 1"
    ).fetchone()
    if not receiver_exists:
        receiver_id = str(uuid.uuid4())
        pw_hash = bcrypt.hashpw("receiver123".encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (user_id, email, name, password_hash, role, approved) "
            "VALUES (?, ?, ?, ?, 'receiver', 1)",
            (receiver_id, "receiver@vit.ac.in", "VIT Exam Center A", pw_hash),
        )
    conn.commit()
    conn.close()


init_db()


def now_local():
    """Use a consistent naive local datetime for browser/server scheduling."""
    return datetime.now().replace(microsecond=0)


def parse_app_datetime(value: str, field_name: str = "datetime") -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field_name}") from exc


def format_app_datetime(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def get_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def redirect_to_role_home():
    role_routes = {
        "setter": "setter_page",
        "receiver": "receiver_page",
        "admin": "admin_page",
    }
    route_name = role_routes.get(session.get("role"))
    return redirect(url_for(route_name)) if route_name else redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Shamir's Secret Sharing  (simplified k-of-n over GF(256))
# ---------------------------------------------------------------------------
_PRIME = 257  # smallest prime > 255


def _eval_poly(coeffs, x, prime=_PRIME):
    """Evaluate polynomial at x over finite field."""
    result = 0
    for coeff in reversed(coeffs):
        result = (result * x + coeff) % prime
    return result


def shamir_split(secret_bytes: bytes, k: int = 3, n: int = 5):
    """Split secret into n shares; any k can reconstruct."""
    shares_list = []
    for byte_val in secret_bytes:
        coeffs = [byte_val] + [secrets.randbelow(_PRIME) for _ in range(k - 1)]
        byte_shares = [(i, _eval_poly(coeffs, i)) for i in range(1, n + 1)]
        shares_list.append(byte_shares)
    # Transpose: list of n shares, each share = list of (x, y) for each byte
    n_shares = []
    for share_idx in range(n):
        share = [(shares_list[byte_idx][share_idx]) for byte_idx in range(len(secret_bytes))]
        n_shares.append(share)
    return n_shares


def _lagrange_interpolate(x, points, prime=_PRIME):
    """Lagrange interpolation at x=0 to recover secret."""
    k = len(points)
    result = 0
    for i in range(k):
        xi, yi = points[i]
        num = yi
        den = 1
        for j in range(k):
            if i != j:
                xj, _ = points[j]
                num = (num * (x - xj)) % prime
                den = (den * (xi - xj)) % prime
        result = (result + num * pow(den, prime - 2, prime)) % prime
    return result


def shamir_reconstruct(shares, k: int = 3):
    """Reconstruct secret from k shares."""
    num_bytes = len(shares[0])
    secret = bytearray()
    for byte_idx in range(num_bytes):
        points = [(s[byte_idx][0], s[byte_idx][1]) for s in shares[:k]]
        val = _lagrange_interpolate(0, points) % 256
        secret.append(val)
    return bytes(secret)


# ---------------------------------------------------------------------------
# AES-256 Encryption / Decryption
# ---------------------------------------------------------------------------
def aes_encrypt(plaintext: bytes, key: bytes) -> tuple:
    """AES-256-CBC encrypt. Returns (iv, ciphertext)."""
    iv = os.urandom(16)
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    return iv, ct


def aes_decrypt(iv: bytes, ciphertext: bytes, key: bytes) -> bytes:
    """AES-256-CBC decrypt."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


# ---------------------------------------------------------------------------
# Watermarking (overlay text on PDF via reportlab)
# ---------------------------------------------------------------------------
def add_watermark(pdf_bytes: bytes, watermark_text: str) -> bytes:
    """Add a watermark footer to every page of a PDF."""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import HexColor

        reader = PdfReader(BytesIO(pdf_bytes))
        writer = PdfWriter()

        for page in reader.pages:
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            # Create watermark overlay
            packet = BytesIO()
            c = canvas.Canvas(packet, pagesize=(page_width, page_height))
            c.setFont("Helvetica", 7)
            c.setFillColor(HexColor("#cc0000"))
            c.drawString(30, 15, f"SECUEXAM WATERMARK | {watermark_text}")
            # Diagonal watermark
            c.saveState()
            c.setFillColor(HexColor("#cccccc"))
            c.setFont("Helvetica-Bold", 40)
            c.translate(page_width / 2, page_height / 2)
            c.rotate(45)
            c.setFillAlpha(0.15)
            c.drawCentredString(0, 0, "SECUEXAM TRACKED")
            c.restoreState()
            c.save()

            packet.seek(0)
            overlay_reader = PdfReader(packet)
            overlay_page = overlay_reader.pages[0]

            page.merge_page(overlay_page)
            writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as e:
        app.logger.error(f"Watermark error: {e}")
        return pdf_bytes  # Return original if watermarking fails


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------
def login_required(roles=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required"}), 401
            if roles and session.get("role") not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Routes — Pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect_to_role_home()
    return render_template("index.html")


@app.route("/setter")
def setter_page():
    if "user_id" not in session:
        return redirect(url_for("index"))
    if session.get("role") != "setter":
        return redirect_to_role_home()
    return render_template("setter.html")


@app.route("/receiver")
def receiver_page():
    if "user_id" not in session:
        return redirect(url_for("index"))
    if session.get("role") != "receiver":
        return redirect_to_role_home()
    return render_template("receiver.html")


@app.route("/admin")
def admin_page():
    if "user_id" not in session:
        return redirect(url_for("index"))
    if session.get("role") != "admin":
        return redirect_to_role_home()
    return render_template("admin.html")


# ---------------------------------------------------------------------------
# Routes — Auth
# ---------------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user["approved"]:
        return jsonify({"error": "Account pending approval"}), 403

    session["user_id"] = user["user_id"]
    session["email"] = user["email"]
    session["name"] = user["name"]
    session["role"] = user["role"]

    return jsonify({
        "message": "Login successful",
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        }
    })


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/logout", methods=["GET"])
def logout_page():
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/me", methods=["GET"])
def api_me():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({
        "user_id": session["user_id"],
        "email": session["email"],
        "name": session["name"],
        "role": session["role"],
    })


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "receiver").strip()
    college = data.get("college_code", "").strip()

    if not email or not name or not password:
        return jsonify({"error": "All fields are required"}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Please enter a valid email address"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if role not in ("setter", "receiver"):
        return jsonify({"error": "Invalid role"}), 400
    if role == "receiver" and not college:
        return jsonify({"error": "College code is required for receivers"}), 400

    conn = get_db()
    existing = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    user_id = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    approved = 0 if role == "receiver" else 1
    conn.execute(
        "INSERT INTO users (user_id, email, name, password_hash, role, college_code, approved) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, email, name, pw_hash, role, college or None, approved),
    )
    conn.commit()
    conn.close()
    message = (
        "Registration successful. Your receiver account is pending admin approval."
        if role == "receiver"
        else "Registration successful"
    )
    return jsonify({
        "message": message,
        "user_id": user_id,
        "approved": bool(approved),
    }), 201


# ---------------------------------------------------------------------------
# Routes — Paper Upload (Setter)
# ---------------------------------------------------------------------------
@app.route("/api/papers/upload", methods=["POST"])
@login_required(roles=["setter"])
def api_upload_paper():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    subject = request.form.get("subject", "General").strip()
    exam_start = request.form.get("exam_start_time", "").strip()

    try:
        duration = int(request.form.get("duration", 180))
    except (TypeError, ValueError):
        return jsonify({"error": "Exam duration must be a valid number"}), 400

    if not exam_start:
        return jsonify({"error": "Exam start time is required"}), 400
    if not subject:
        return jsonify({"error": "Subject / exam name is required"}), 400
    if duration < 30 or duration > 600:
        return jsonify({"error": "Exam duration must be between 30 and 600 minutes"}), 400

    try:
        exam_dt = parse_app_datetime(exam_start, "exam start time")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if exam_dt <= now_local():
        return jsonify({"error": "Exam start time must be in the future"}), 400

    # Read file bytes
    file_bytes = file.read()
    if not file_bytes:
        return jsonify({"error": "Uploaded PDF is empty"}), 400
    file_size_mb = round(len(file_bytes) / (1024 * 1024), 2)
    if file_size_mb > 50:
        return jsonify({"error": "File exceeds 50 MB limit"}), 400

    # Generate AES-256 key and encrypt
    aes_key = os.urandom(32)  # 256-bit key
    iv, ciphertext = aes_encrypt(file_bytes, aes_key)

    paper_id = str(uuid.uuid4())
    enc_filename = f"{paper_id}.enc"
    enc_path = os.path.join(app.config["UPLOAD_FOLDER"], enc_filename)

    # Store IV + ciphertext
    with open(enc_path, "wb") as f:
        f.write(iv + ciphertext)

    # Split key using Shamir's Secret Sharing (3-of-5)
    shares = shamir_split(aes_key, k=3, n=5)

    # Calculate unlock time (30 min before exam)
    unlock_dt = exam_dt - timedelta(minutes=30)

    conn = get_db()
    conn.execute(
        "INSERT INTO exam_papers (paper_id, setter_id, original_filename, file_path, file_size_mb, encryption_status, subject) "
        "VALUES (?, ?, ?, ?, ?, 1, ?)",
        (paper_id, session["user_id"], file.filename, enc_path, file_size_mb, subject),
    )
    conn.execute(
        "INSERT INTO exam_schedule (schedule_id, paper_id, exam_start_time, duration_min, unlock_time) "
        "VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), paper_id, format_app_datetime(exam_dt), duration, format_app_datetime(unlock_dt)),
    )
    # Store key fragments
    for idx, share in enumerate(shares):
        conn.execute(
            "INSERT INTO encryption_keys (key_id, paper_id, key_fragment, fragment_idx, owner_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), paper_id, json.dumps(share), idx, session["user_id"]),
        )
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Paper uploaded, encrypted, and scheduled successfully",
        "paper_id": paper_id,
        "file_size_mb": file_size_mb,
        "encryption": "AES-256-CBC",
        "key_shares": f"5 shares created (3 required to reconstruct)",
        "unlock_time": format_app_datetime(unlock_dt),
    }), 201


# ---------------------------------------------------------------------------
# Routes — Paper Listing & Download (Receiver)
# ---------------------------------------------------------------------------
@app.route("/api/papers", methods=["GET"])
@login_required()
def api_list_papers():
    conn = get_db()
    rows = conn.execute("""
        SELECT ep.paper_id, ep.original_filename, ep.file_size_mb, ep.subject,
               ep.encryption_status, ep.created_at,
               es.exam_start_time, es.duration_min, es.unlock_time,
               u.name as setter_name,
               (SELECT COUNT(*) FROM encryption_keys ek WHERE ek.paper_id = ep.paper_id) AS key_share_count
        FROM exam_papers ep
        JOIN exam_schedule es ON ep.paper_id = es.paper_id
        JOIN users u ON ep.setter_id = u.user_id
        ORDER BY es.exam_start_time ASC
    """).fetchall()
    conn.close()

    now = now_local()
    papers = []
    for r in rows:
        unlock_dt = parse_app_datetime(r["unlock_time"], "unlock time")
        exam_dt = parse_app_datetime(r["exam_start_time"], "exam start time")
        is_unlocked = now >= unlock_dt
        is_expired = now > exam_dt + timedelta(minutes=r["duration_min"])
        papers.append({
            "paper_id": r["paper_id"],
            "filename": r["original_filename"],
            "file_size_mb": r["file_size_mb"],
            "subject": r["subject"],
            "encrypted": bool(r["encryption_status"]),
            "setter_name": r["setter_name"],
            "exam_start_time": r["exam_start_time"],
            "duration_min": r["duration_min"],
            "unlock_time": r["unlock_time"],
            "is_unlocked": is_unlocked,
            "is_expired": is_expired,
            "created_at": r["created_at"],
            "key_share_count": r["key_share_count"],
            "key_threshold": 3,
        })
    return jsonify({"papers": papers})


@app.route("/api/papers/<paper_id>/download", methods=["GET"])
@login_required(roles=["receiver"])
def api_download_paper(paper_id):
    conn = get_db()
    paper = conn.execute(
        "SELECT * FROM exam_papers WHERE paper_id = ?", (paper_id,)
    ).fetchone()
    schedule = conn.execute(
        "SELECT * FROM exam_schedule WHERE paper_id = ?", (paper_id,)
    ).fetchone()

    if not paper or not schedule:
        _log_access(conn, paper_id, "failed", "Paper not found")
        conn.close()
        return jsonify({"error": "Paper not found"}), 404

    # Time-lock check
    now = now_local()
    unlock_dt = parse_app_datetime(schedule["unlock_time"], "unlock time")
    exam_dt = parse_app_datetime(schedule["exam_start_time"], "exam start time")
    exam_end_dt = exam_dt + timedelta(minutes=schedule["duration_min"])
    if now < unlock_dt:
        remaining = (unlock_dt - now).total_seconds()
        _log_access(conn, paper_id, "time_locked", f"Too early by {remaining:.0f}s")
        conn.close()
        return jsonify({
            "error": "Time-lock active — paper not yet accessible",
            "unlock_time": schedule["unlock_time"],
            "remaining_seconds": remaining,
        }), 403
    if now > exam_end_dt:
        _log_access(conn, paper_id, "denied", "Exam window expired")
        conn.close()
        return jsonify({
            "error": "The exam window has expired for this paper",
            "exam_end_time": format_app_datetime(exam_end_dt),
        }), 410

    # Retrieve key fragments and reconstruct
    fragments = conn.execute(
        "SELECT key_fragment, fragment_idx FROM encryption_keys WHERE paper_id = ? ORDER BY fragment_idx LIMIT 3",
        (paper_id,),
    ).fetchall()

    if len(fragments) < 3:
        _log_access(conn, paper_id, "failed", "Insufficient key fragments")
        conn.close()
        return jsonify({"error": "Cannot reconstruct decryption key"}), 500

    shares = [json.loads(f["key_fragment"]) for f in fragments]
    # Convert lists back to tuples
    shares = [[(pt[0], pt[1]) for pt in share] for share in shares]
    aes_key = shamir_reconstruct(shares, k=3)

    # Decrypt file
    if not os.path.exists(paper["file_path"]):
        _log_access(conn, paper_id, "failed", "Encrypted file missing on disk")
        conn.close()
        return jsonify({"error": "Encrypted file is missing"}), 500

    with open(paper["file_path"], "rb") as f:
        raw = f.read()
    iv = raw[:16]
    ciphertext = raw[16:]
    decrypted_pdf = aes_decrypt(iv, ciphertext, aes_key)

    # Apply dynamic watermark
    client_ip = get_client_ip()
    timestamp = now_local().strftime("%Y-%m-%d %H:%M:%S")
    watermark = f"IP: {client_ip} | User: {session['name']} | Time: {timestamp} | ID: {session['user_id'][:8]}"
    watermarked_pdf = add_watermark(decrypted_pdf, watermark)

    # Log successful download
    _log_access(conn, paper_id, "success", f"Downloaded by {session['name']} from {client_ip}")
    conn.close()

    return send_file(
        BytesIO(watermarked_pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SECUEXAM_{paper['original_filename']}",
    )


def _log_access(conn, paper_id, status, details=""):
    conn.execute(
        "INSERT INTO download_logs (log_id, paper_id, receiver_id, ip_address, status, details) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), paper_id, session.get("user_id"), get_client_ip(), status, details),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Routes — Admin
# ---------------------------------------------------------------------------
@app.route("/api/admin/users", methods=["GET"])
@login_required(roles=["admin"])
def api_admin_users():
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id, email, name, role, college_code, approved, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify({"users": [dict(r) for r in rows]})


@app.route("/api/admin/users/<user_id>/approve", methods=["POST"])
@login_required(roles=["admin"])
def api_admin_approve_user(user_id):
    conn = get_db()
    user = conn.execute(
        "SELECT user_id, approved FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    if user["approved"]:
        conn.close()
        return jsonify({"message": "User is already approved"})
    conn.execute("UPDATE users SET approved = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "User approved"})


@app.route("/api/admin/users/<user_id>/delete", methods=["DELETE"])
@login_required(roles=["admin"])
def api_admin_delete_user(user_id):
    if user_id == session.get("user_id"):
        return jsonify({"error": "Cannot delete yourself"}), 400
    conn = get_db()
    user = conn.execute(
        "SELECT user_id, role, name FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    try:
        conn.execute("BEGIN")

        paper_ids = [
            row["paper_id"]
            for row in conn.execute(
                "SELECT paper_id FROM exam_papers WHERE setter_id = ?",
                (user_id,),
            ).fetchall()
        ]
        if paper_ids:
            placeholders = ",".join("?" for _ in paper_ids)
            conn.execute(
                f"DELETE FROM download_logs WHERE paper_id IN ({placeholders})",
                paper_ids,
            )
            conn.execute(
                f"DELETE FROM exam_papers WHERE paper_id IN ({placeholders})",
                paper_ids,
            )

        conn.execute(
            "DELETE FROM download_logs WHERE receiver_id = ?",
            (user_id,),
        )
        conn.execute(
            "UPDATE encryption_keys SET owner_id = NULL WHERE owner_id = ?",
            (user_id,),
        )
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
    except sqlite3.DatabaseError as exc:
        conn.rollback()
        conn.close()
        return jsonify({"error": f"Unable to delete user: {exc}"}), 400

    conn.close()
    return jsonify({"message": f"User '{user['name']}' deleted"})


@app.route("/api/admin/logs", methods=["GET"])
@login_required(roles=["admin"])
def api_admin_logs():
    conn = get_db()
    rows = conn.execute("""
        SELECT dl.log_id, dl.access_timestamp, dl.ip_address, dl.status, dl.details,
               u.name as receiver_name, u.email as receiver_email,
               ep.original_filename, ep.subject
        FROM download_logs dl
        LEFT JOIN users u ON dl.receiver_id = u.user_id
        LEFT JOIN exam_papers ep ON dl.paper_id = ep.paper_id
        ORDER BY dl.access_timestamp DESC
        LIMIT 200
    """).fetchall()
    conn.close()
    return jsonify({"logs": [dict(r) for r in rows]})


@app.route("/api/admin/stats", methods=["GET"])
@login_required(roles=["admin"])
def api_admin_stats():
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_papers = conn.execute("SELECT COUNT(*) as c FROM exam_papers").fetchone()["c"]
    total_downloads = conn.execute("SELECT COUNT(*) as c FROM download_logs WHERE status='success'").fetchone()["c"]
    blocked_attempts = conn.execute("SELECT COUNT(*) as c FROM download_logs WHERE status='time_locked'").fetchone()["c"]
    failed_attempts = conn.execute("SELECT COUNT(*) as c FROM download_logs WHERE status='failed'").fetchone()["c"]
    users_by_role = conn.execute("SELECT role, COUNT(*) as c FROM users GROUP BY role").fetchall()
    recent_logs = conn.execute("""
        SELECT dl.status, COUNT(*) as c
        FROM download_logs dl
        GROUP BY dl.status
    """).fetchall()
    conn.close()

    return jsonify({
        "total_users": total_users,
        "total_papers": total_papers,
        "total_downloads": total_downloads,
        "blocked_attempts": blocked_attempts,
        "failed_attempts": failed_attempts,
        "users_by_role": {r["role"]: r["c"] for r in users_by_role},
        "access_by_status": {r["status"]: r["c"] for r in recent_logs},
    })


@app.route("/api/admin/keys/<paper_id>", methods=["GET"])
@login_required(roles=["admin"])
def api_admin_keys(paper_id):
    conn = get_db()
    keys = conn.execute(
        "SELECT key_id, fragment_idx, owner_id FROM encryption_keys WHERE paper_id = ?",
        (paper_id,),
    ).fetchall()
    conn.close()
    return jsonify({"keys": [dict(k) for k in keys]})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SecuExam — Secure Exam Paper Distribution System")
    print("  Server running at http://localhost:5050")
    print("=" * 60)
    print("\n  Default credentials:")
    print("    Admin   : admin@secuexam.in / admin123")
    print("    Setter  : setter@vit.ac.in / setter123")
    print("    Receiver: receiver@vit.ac.in / receiver123")
    print("=" * 60 + "\n")
    app.run(debug=os.environ.get("SECUEXAM_DEBUG") == "1", host="0.0.0.0", port=5050, use_reloader=False)
