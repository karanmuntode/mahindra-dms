from flask import Blueprint, request, jsonify
from models import db, User
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import limiter
import re, random
from utils.email_service import send_otp_email

auth_bp = Blueprint('auth', __name__)

LOCATIONS = [
    "Igatpuri", "Nashik Plant 1", "Nashik Plant 2",
    "Chakan", "Zahirabad", "Haridwar"
]

def validate_username(username):
    return re.match(r"^[a-zA-Z0-9_]{3,20}$", username)

def validate_password(password):
    return len(password) >= 8 and re.search(r'[A-Za-z]', password) and re.search(r'\d', password)

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


# ================= SIGNUP =================
@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("5 per minute")
def signup():
    data = request.json or {}

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip().lower()
    location = data.get('location', '').strip()

    if not all([username, password, email, location]):
        return jsonify({"error": "All fields are required"}), 400

    if not validate_username(username):
        return jsonify({"error": "Username: 3-20 chars, letters/numbers/_ only"}), 400

    if not validate_password(password):
        return jsonify({"error": "Password must be 8+ chars with letters & numbers"}), 400

    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    otp = str(random.randint(100000, 999999))

    user = User(
        username=username,
        password=generate_password_hash(password),
        email=email,
        role="user",
        location=location,
        is_admin=False,
        is_approved=False,
        otp=otp,
        otp_verified=False
    )

    db.session.add(user)
    db.session.commit()

    try:
        send_otp_email(email, otp)
    except Exception as e:
        print("EMAIL ERROR:", e)

    return jsonify({"msg": "Signup successful! OTP sent to email. Wait for admin approval.", "approved": False}), 201


# ================= VERIFY OTP =================
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json or {}
    user = User.query.filter_by(email=data.get("email", "").lower()).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user.otp != data.get("otp"):
        return jsonify({"msg": "Invalid OTP"}), 400

    user.otp_verified = True
    db.session.commit()
    return jsonify({"msg": "Email verified successfully"}), 200


# ================= SEND RESET OTP =================
@auth_bp.route('/send-reset-otp', methods=['POST'])
@limiter.limit("3 per minute")
def send_reset_otp():
    data = request.json or {}
    user = User.query.filter_by(email=data.get("email", "").lower()).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    otp = str(random.randint(100000, 999999))
    user.otp = otp
    db.session.commit()

    try:
        send_otp_email(user.email, otp)
    except Exception as e:
        print("EMAIL ERROR:", e)

    return jsonify({"msg": "OTP sent to email"}), 200


# ================= RESET PASSWORD =================
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json or {}

        email = data.get("email", "").lower()
        otp = str(data.get("otp", "")).strip()
        new_password = data.get("new_password")

        print("USER OTP:", otp)

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"msg": "User not found"}), 404

        print("DB OTP:", user.otp)

        # OTP CHECK
        if str(user.otp).strip() != otp:
            return jsonify({"msg": "Invalid OTP"}), 400

        # UPDATE PASSWORD
        user.password = generate_password_hash(new_password)

        # CLEAR OTP
        user.otp = None

        db.session.commit()

        return jsonify({
            "msg": "Password reset successful"
        }), 200

    except Exception as e:
        print("RESET ERROR:", str(e))

        return jsonify({
            "msg": str(e)
        }), 500
# ================= LOGIN =================
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.json or {}

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.is_approved:
        return jsonify({"error": "Account pending admin approval"}), 403

    access_token = create_access_token(
        identity=user.username,
        additional_claims={
            "role": user.role,
            "location": user.location,
            "is_admin": user.is_admin
        }
    )

    return jsonify({
        "msg": "Login successful",
        "token": access_token,
        "user": user.to_dict()
    }), 200
