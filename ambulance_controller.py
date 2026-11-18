from flask import request, jsonify
from app import db
from app.models.models import Ambulance
from datetime import datetime


def get_ambulances(hospital_id):
    ambulances = Ambulance.query.filter_by(hospital_id=hospital_id).all()
    return jsonify({"ambulances": [a.to_dict() for a in ambulances]}), 200


def get_available_ambulances():
    ambulances = Ambulance.query.filter_by(status="available").all()
    return jsonify({"ambulances": [a.to_dict() for a in ambulances]}), 200


def add_ambulance(current_user):
    if current_user["role"] not in ("admin",):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ["hospital_id", "vehicle_no", "driver_name", "driver_phone"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required"}), 400

    amb = Ambulance(
        hospital_id=data["hospital_id"],
        vehicle_no=data["vehicle_no"],
        driver_name=data["driver_name"],
        driver_phone=data["driver_phone"],
        status="available",
    )
    db.session.add(amb)
    db.session.commit()
    return jsonify({"message": "Ambulance added", "ambulance": amb.to_dict()}), 201


def update_ambulance_status(amb_id, current_user):
    if current_user["role"] not in ("admin", "doctor"):
        return jsonify({"error": "Access denied"}), 403

    amb  = Ambulance.query.get_or_404(amb_id, description="Ambulance not found")
    data = request.get_json()
    status = data.get("status")

    if status not in ("available", "dispatched", "maintenance"):
        return jsonify({"error": "Invalid status"}), 400

    amb.status     = status
    amb.updated_at = datetime.utcnow()

    # Optionally update GPS
    if "latitude" in data:
        amb.latitude  = data["latitude"]
        amb.longitude = data.get("longitude")

    db.session.commit()
    return jsonify({"message": "Ambulance updated", "ambulance": amb.to_dict()}), 200


def update_location(amb_id, current_user):
    amb  = Ambulance.query.get_or_404(amb_id, description="Ambulance not found")
    data = request.get_json()

    lat = data.get("latitude")
    lng = data.get("longitude")
    if lat is None or lng is None:
        return jsonify({"error": "latitude and longitude required"}), 400

    amb.latitude   = float(lat)
    amb.longitude  = float(lng)
    amb.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Location updated", "ambulance": amb.to_dict()}), 200
