from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app import db
from app.models.models import User


def register():
    data = request.get_json()

    # Validate required fields
    required = ["name", "email", "password"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    name     = data["name"].strip()
    email    = data["email"].strip().lower()
    password = data["password"]
    role     = data.get("role", "patient")
    phone    = data.get("phone", "")

    if role not in ("patient", "doctor", "admin"):
        return jsonify({"error": "Invalid role. Must be patient, doctor, or admin"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 409

    hashed = generate_password_hash(password)
    user = User(name=name, email=email, password=hashed, role=role, phone=phone)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity={"id": user.id, "role": user.role})
    return jsonify({
        "message": "Registration successful",
        "token":   token,
        "user":    user.to_dict()
    }), 201


def login():
    data = request.get_json()

    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity={"id": user.id, "role": user.role})
    return jsonify({
        "message": "Login successful",
        "token":   token,
        "user":    user.to_dict()
    }), 200


def get_profile(current_user):
    user = User.query.get(current_user["id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


def get_all_users(current_user):
    if current_user["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200
