from flask import request, jsonify
from app import db
from app.models.models import Doctor, Appointment, User
from datetime import date


def get_doctors():
    doctors = Doctor.query.filter_by(available=True).all()
    return jsonify({"doctors": [d.to_dict() for d in doctors]}), 200


def get_doctor(doctor_id):
    d = Doctor.query.get_or_404(doctor_id, description="Doctor not found")
    return jsonify({"doctor": d.to_dict()}), 200


def add_doctor(current_user):
    if current_user["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ["user_id", "specialty"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    doc = Doctor(
        user_id=data["user_id"],
        hospital_id=data.get("hospital_id"),
        specialty=data["specialty"],
        experience=data.get("experience", 0),
        fee=float(data.get("fee", 500.0)),
        available=True,
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({"message": "Doctor registered", "doctor": doc.to_dict()}), 201


# ─── APPOINTMENTS ────────────────────────────────────────────────────────────

def book_appointment(current_user):
    data = request.get_json()
    required = ["doctor_id", "date"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required"}), 400

    doctor = Doctor.query.get(data["doctor_id"])
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    if not doctor.available:
        return jsonify({"error": "Doctor is not available"}), 409

    try:
        appt_date = date.fromisoformat(data["date"])
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    if appt_date < date.today():
        return jsonify({"error": "Appointment date cannot be in the past"}), 400

    symptoms = data.get("symptoms")
    if isinstance(symptoms, list):
        symptoms = ", ".join(symptoms)

    appt = Appointment(
        patient_id=current_user["id"],
        doctor_id=data["doctor_id"],
        date=appt_date,
        age=data.get("age"),
        symptoms=symptoms,
        status="booked",
    )
    db.session.add(appt)
    db.session.commit()
    return jsonify({"message": "Appointment booked", "appointment": appt.to_dict()}), 201


def get_appointments(current_user):
    if current_user["role"] == "admin":
        appts = Appointment.query.order_by(Appointment.date.desc()).all()
    elif current_user["role"] == "doctor":
        doc = Doctor.query.filter_by(user_id=current_user["id"]).first()
        if not doc:
            return jsonify({"appointments": []}), 200
        appts = Appointment.query.filter_by(doctor_id=doc.id).order_by(Appointment.date.desc()).all()
    else:
        appts = Appointment.query.filter_by(patient_id=current_user["id"]).order_by(Appointment.date.desc()).all()

    return jsonify({"appointments": [a.to_dict() for a in appts]}), 200


def update_appointment(appt_id, current_user):
    appt = Appointment.query.get_or_404(appt_id, description="Appointment not found")
    data = request.get_json()

    if current_user["role"] not in ("admin", "doctor"):
        # Patient can only cancel their own
        if appt.patient_id != current_user["id"]:
            return jsonify({"error": "Access denied"}), 403
        appt.status = "cancelled"
    else:
        if "status" in data:
            if data["status"] not in ("booked", "completed", "cancelled"):
                return jsonify({"error": "Invalid status"}), 400
            appt.status = data["status"]
        if "notes" in data:
            appt.notes = data["notes"]

    db.session.commit()
    return jsonify({"message": "Appointment updated", "appointment": appt.to_dict()}), 200
