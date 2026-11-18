from app import db
from datetime import datetime


# ─────────────────────────────────────────────
# USER / AUTH
# ─────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.Enum("patient", "doctor", "admin"), default="patient", nullable=False)
    phone      = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "role":       self.role,
            "phone":      self.phone,
            "created_at": self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────
# HOSPITAL & BEDS
# ─────────────────────────────────────────────

class Hospital(db.Model):
    __tablename__ = "hospitals"

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(150), nullable=False)
    address  = db.Column(db.Text)
    phone    = db.Column(db.String(20))
    city     = db.Column(db.String(80))
    beds     = db.relationship("Bed", backref="hospital", lazy=True)

    def to_dict(self):
        return {
            "id":      self.id,
            "name":    self.name,
            "address": self.address,
            "phone":   self.phone,
            "city":    self.city,
        }


class Bed(db.Model):
    __tablename__ = "beds"

    id          = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    bed_number  = db.Column(db.String(20), nullable=False)
    bed_type    = db.Column(db.Enum("icu", "oxygen", "ward", "general"), nullable=False)
    status      = db.Column(db.Enum("available", "occupied", "critical"), default="available")
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "hospital_id": self.hospital_id,
            "bed_number":  self.bed_number,
            "bed_type":    self.bed_type,
            "status":      self.status,
            "updated_at":  self.updated_at.isoformat(),
        }


# ─────────────────────────────────────────────
# BLOOD BANK
# ─────────────────────────────────────────────

class BloodStock(db.Model):
    __tablename__ = "blood_stock"

    id          = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)   # A+, O-, etc.
    units       = db.Column(db.Integer, default=0)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "hospital_id": self.hospital_id,
            "blood_group": self.blood_group,
            "units":       self.units,
            "updated_at":  self.updated_at.isoformat(),
        }


class BloodDonor(db.Model):
    __tablename__ = "blood_donors"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    phone       = db.Column(db.String(20))
    city        = db.Column(db.String(80))
    last_donated= db.Column(db.Date)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "blood_group":  self.blood_group,
            "phone":        self.phone,
            "city":         self.city,
            "last_donated": self.last_donated.isoformat() if self.last_donated else None,
        }


# ─────────────────────────────────────────────
# AMBULANCE
# ─────────────────────────────────────────────

class Ambulance(db.Model):
    __tablename__ = "ambulances"

    id           = db.Column(db.Integer, primary_key=True)
    hospital_id  = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    vehicle_no   = db.Column(db.String(20), nullable=False)
    driver_name  = db.Column(db.String(120))
    driver_phone = db.Column(db.String(20))
    status       = db.Column(db.Enum("available", "dispatched", "maintenance"), default="available")
    latitude     = db.Column(db.Float)
    longitude    = db.Column(db.Float)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "hospital_id":  self.hospital_id,
            "vehicle_no":   self.vehicle_no,
            "driver_name":  self.driver_name,
            "driver_phone": self.driver_phone,
            "status":       self.status,
            "latitude":     self.latitude,
            "longitude":    self.longitude,
            "updated_at":   self.updated_at.isoformat(),
        }


# ─────────────────────────────────────────────
# MEDICINE / ORDERS
# ─────────────────────────────────────────────

class Medicine(db.Model):
    __tablename__ = "medicines"

    id          = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    name        = db.Column(db.String(150), nullable=False)
    category    = db.Column(db.String(80))
    price       = db.Column(db.Float, nullable=False)
    stock       = db.Column(db.Integer, default=0)
    unit        = db.Column(db.String(30), default="tablet")

    def to_dict(self):
        return {
            "id":          self.id,
            "hospital_id": self.hospital_id,
            "name":        self.name,
            "category":    self.category,
            "price":       self.price,
            "stock":       self.stock,
            "unit":        self.unit,
        }


class Order(db.Model):
    __tablename__ = "orders"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount   = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    address        = db.Column(db.Text)
    status         = db.Column(db.Enum("pending", "confirmed", "delivered", "cancelled"), default="pending")
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    items          = db.relationship("OrderItem", backref="order", lazy=True)

    def to_dict(self):
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "total_amount":   self.total_amount,
            "payment_method": self.payment_method,
            "address":        self.address,
            "status":         self.status,
            "created_at":     self.created_at.isoformat(),
            "items":          [i.to_dict() for i in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id          = db.Column(db.Integer, primary_key=True)
    order_id    = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    quantity    = db.Column(db.Integer, nullable=False)
    price       = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id":          self.id,
            "medicine_id": self.medicine_id,
            "quantity":    self.quantity,
            "price":       self.price,
        }


# ─────────────────────────────────────────────
# CONSULTATION / APPOINTMENTS
# ─────────────────────────────────────────────

class Doctor(db.Model):
    __tablename__ = "doctors"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"))
    specialty   = db.Column(db.String(100))
    experience  = db.Column(db.Integer)
    fee         = db.Column(db.Float, default=500.0)
    available   = db.Column(db.Boolean, default=True)

    def to_dict(self):
        user = User.query.get(self.user_id)
        return {
            "id":          self.id,
            "user_id":     self.user_id,
            "name":        user.name if user else "Unknown",
            "hospital_id": self.hospital_id,
            "specialty":   self.specialty,
            "experience":  self.experience,
            "fee":         self.fee,
            "available":   self.available,
        }


class Appointment(db.Model):
    __tablename__ = "appointments"

    id         = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doctor_id  = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    age        = db.Column(db.Integer)
    symptoms   = db.Column(db.Text)
    status     = db.Column(db.Enum("booked", "completed", "cancelled"), default="booked")
    notes      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        doctor = Doctor.query.get(self.doctor_id)
        return {
            "id":         self.id,
            "patient_id": self.patient_id,
            "doctor_id":  self.doctor_id,
            "doctor_name": doctor.to_dict()["name"] if doctor else "Unknown",
            "specialty":  doctor.specialty if doctor else None,
            "date":       self.date.isoformat(),
            "age":        self.age,
            "symptoms":   self.symptoms,
            "status":     self.status,
            "notes":      self.notes,
            "created_at": self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────
# PATIENT ANALYTICS
# ─────────────────────────────────────────────

class PatientVitals(db.Model):
    __tablename__ = "patient_vitals"

    id           = db.Column(db.Integer, primary_key=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bp           = db.Column(db.Integer)    # Systolic BP
    sugar        = db.Column(db.Integer)    # mg/dL
    oxygen       = db.Column(db.Integer)    # SpO2 %
    heart_rate   = db.Column(db.Integer)    # BPM
    risk_level   = db.Column(db.Enum("normal", "moderate", "high", "critical"), default="normal")
    ai_report    = db.Column(db.Text)
    recorded_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "patient_id":  self.patient_id,
            "bp":          self.bp,
            "sugar":       self.sugar,
            "oxygen":      self.oxygen,
            "heart_rate":  self.heart_rate,
            "risk_level":  self.risk_level,
            "ai_report":   self.ai_report,
            "recorded_at": self.recorded_at.isoformat(),
        }


# ─────────────────────────────────────────────
# EMERGENCY SOS
# ─────────────────────────────────────────────

class EmergencyAlert(db.Model):
    __tablename__ = "emergency_alerts"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    name       = db.Column(db.String(120))
    phone      = db.Column(db.String(20))
    latitude   = db.Column(db.Float)
    longitude  = db.Column(db.Float)
    message    = db.Column(db.Text)
    status     = db.Column(db.Enum("pending", "responded", "resolved"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "user_id":    self.user_id,
            "name":       self.name,
            "phone":      self.phone,
            "latitude":   self.latitude,
            "longitude":  self.longitude,
            "message":    self.message,
            "status":     self.status,
            "created_at": self.created_at.isoformat(),
        }
