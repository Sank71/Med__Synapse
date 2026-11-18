from flask import request, jsonify
from app import db
from app.models.models import Hospital, Bed
from datetime import datetime


# ─── HOSPITALS ─────────────────────────────────────────────────────────────

def get_hospitals():
    hospitals = Hospital.query.all()
    return jsonify({"hospitals": [h.to_dict() for h in hospitals]}), 200


def get_hospital(hospital_id):
    h = Hospital.query.get_or_404(hospital_id, description="Hospital not found")
    return jsonify({"hospital": h.to_dict()}), 200


def add_hospital(current_user):
    if current_user["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ["name", "address", "phone", "city"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required"}), 400

    h = Hospital(
        name=data["name"],
        address=data["address"],
        phone=data["phone"],
        city=data["city"],
    )
    db.session.add(h)
    db.session.commit()
    return jsonify({"message": "Hospital added", "hospital": h.to_dict()}), 201


# ─── BEDS ───────────────────────────────────────────────────────────────────

def get_beds(hospital_id):
    beds = Bed.query.filter_by(hospital_id=hospital_id).all()
    summary = {
        "total":     len(beds),
        "available": sum(1 for b in beds if b.status == "available"),
        "occupied":  sum(1 for b in beds if b.status == "occupied"),
        "critical":  sum(1 for b in beds if b.status == "critical"),
    }
    return jsonify({"beds": [b.to_dict() for b in beds], "summary": summary}), 200


def get_beds_by_type(hospital_id, bed_type):
    valid_types = ("icu", "oxygen", "ward", "general")
    if bed_type not in valid_types:
        return jsonify({"error": f"Invalid bed type. Valid: {valid_types}"}), 400

    beds = Bed.query.filter_by(hospital_id=hospital_id, bed_type=bed_type).all()
    return jsonify({"beds": [b.to_dict() for b in beds]}), 200


def add_beds(hospital_id, current_user):
    if current_user["role"] not in ("admin", "doctor"):
        return jsonify({"error": "Access denied"}), 403

    Hospital.query.get_or_404(hospital_id, description="Hospital not found")
    data = request.get_json()

    count    = int(data.get("count", 1))
    bed_type = data.get("bed_type", "general")
    prefix   = data.get("prefix", "B")

    if bed_type not in ("icu", "oxygen", "ward", "general"):
        return jsonify({"error": "Invalid bed_type"}), 400

    # Generate beds automatically
    existing_count = Bed.query.filter_by(hospital_id=hospital_id, bed_type=bed_type).count()
    new_beds = []
    for i in range(count):
        bed = Bed(
            hospital_id=hospital_id,
            bed_number=f"{prefix}{existing_count + i + 1:03d}",
            bed_type=bed_type,
            status="available",
        )
        db.session.add(bed)
        new_beds.append(bed)

    db.session.commit()
    return jsonify({"message": f"{count} beds added", "beds": [b.to_dict() for b in new_beds]}), 201


def update_bed_status(bed_id, current_user):
    if current_user["role"] not in ("admin", "doctor"):
        return jsonify({"error": "Access denied"}), 403

    bed  = Bed.query.get_or_404(bed_id, description="Bed not found")
    data = request.get_json()
    status = data.get("status")

    if status not in ("available", "occupied", "critical"):
        return jsonify({"error": "Status must be available, occupied, or critical"}), 400

    bed.status     = status
    bed.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Bed status updated", "bed": bed.to_dict()}), 200
