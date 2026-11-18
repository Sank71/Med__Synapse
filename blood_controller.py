from flask import request, jsonify
from app import db
from app.models.models import BloodStock, BloodDonor

VALID_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


def get_blood_stock(hospital_id):
    stocks = BloodStock.query.filter_by(hospital_id=hospital_id).all()
    return jsonify({"blood_stock": [s.to_dict() for s in stocks]}), 200


def all_blood_stock():
    stocks = BloodStock.query.all()
    return jsonify({"blood_stock": [s.to_dict() for s in stocks]}), 200


def update_blood_stock(hospital_id, current_user):
    if current_user["role"] not in ("admin", "doctor"):
        return jsonify({"error": "Access denied"}), 403

    data  = request.get_json()
    group = data.get("blood_group", "").upper()
    units = data.get("units")

    if group not in VALID_GROUPS:
        return jsonify({"error": f"Invalid blood group. Valid: {VALID_GROUPS}"}), 400
    if units is None or int(units) < 0:
        return jsonify({"error": "units must be a non-negative integer"}), 400

    record = BloodStock.query.filter_by(hospital_id=hospital_id, blood_group=group).first()
    if record:
        record.units = int(units)
    else:
        record = BloodStock(hospital_id=hospital_id, blood_group=group, units=int(units))
        db.session.add(record)

    db.session.commit()
    return jsonify({"message": "Blood stock updated", "blood_stock": record.to_dict()}), 200


def search_blood(blood_group):
    group = blood_group.upper()
    if group not in VALID_GROUPS:
        return jsonify({"error": "Invalid blood group"}), 400

    stocks  = BloodStock.query.filter_by(blood_group=group).filter(BloodStock.units > 0).all()
    donors  = BloodDonor.query.filter_by(blood_group=group).all()
    return jsonify({
        "blood_group": group,
        "hospitals_with_stock": [s.to_dict() for s in stocks],
        "available_donors": [d.to_dict() for d in donors],
    }), 200


# ─── DONORS ─────────────────────────────────────────────────────────────────

def get_donors():
    donors = BloodDonor.query.all()
    return jsonify({"donors": [d.to_dict() for d in donors]}), 200


def add_donor():
    data = request.get_json()
    required = ["name", "blood_group", "phone"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required"}), 400

    group = data["blood_group"].upper()
    if group not in VALID_GROUPS:
        return jsonify({"error": "Invalid blood group"}), 400

    donor = BloodDonor(
        name=data["name"],
        blood_group=group,
        phone=data["phone"],
        city=data.get("city"),
        last_donated=data.get("last_donated"),
    )
    db.session.add(donor)
    db.session.commit()
    return jsonify({"message": "Donor registered", "donor": donor.to_dict()}), 201
