from flask import request, jsonify
from app import db
from app.models.models import Medicine, Order, OrderItem


# ─── MEDICINES ──────────────────────────────────────────────────────────────

def get_medicines(hospital_id):
    meds = Medicine.query.filter_by(hospital_id=hospital_id).all()
    return jsonify({"medicines": [m.to_dict() for m in meds]}), 200


def search_medicines():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Search query 'q' is required"}), 400
    meds = Medicine.query.filter(Medicine.name.ilike(f"%{q}%")).all()
    return jsonify({"medicines": [m.to_dict() for m in meds]}), 200


def add_medicine(current_user):
    if current_user["role"] not in ("admin",):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ["hospital_id", "name", "price", "stock"]
    for f in required:
        if data.get(f) is None:
            return jsonify({"error": f"'{f}' is required"}), 400

    med = Medicine(
        hospital_id=data["hospital_id"],
        name=data["name"],
        category=data.get("category", "General"),
        price=float(data["price"]),
        stock=int(data["stock"]),
        unit=data.get("unit", "tablet"),
    )
    db.session.add(med)
    db.session.commit()
    return jsonify({"message": "Medicine added", "medicine": med.to_dict()}), 201


def update_stock(med_id, current_user):
    if current_user["role"] not in ("admin",):
        return jsonify({"error": "Admin access required"}), 403

    med  = Medicine.query.get_or_404(med_id, description="Medicine not found")
    data = request.get_json()
    stock = data.get("stock")
    if stock is None or int(stock) < 0:
        return jsonify({"error": "Valid stock quantity required"}), 400

    med.stock = int(stock)
    db.session.commit()
    return jsonify({"message": "Stock updated", "medicine": med.to_dict()}), 200


# ─── ORDERS ─────────────────────────────────────────────────────────────────

def place_order(current_user):
    data = request.get_json()
    items = data.get("items")  # [{medicine_id, quantity}]
    if not items or not isinstance(items, list):
        return jsonify({"error": "'items' list is required"}), 400

    required = ["payment_method", "address"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required"}), 400

    total = 0.0
    order_items = []

    for item in items:
        med_id = item.get("medicine_id")
        qty    = int(item.get("quantity", 1))

        if not med_id or qty < 1:
            return jsonify({"error": "Each item needs medicine_id and quantity >= 1"}), 400

        med = Medicine.query.get(med_id)
        if not med:
            return jsonify({"error": f"Medicine {med_id} not found"}), 404
        if med.stock < qty:
            return jsonify({"error": f"Insufficient stock for '{med.name}'. Available: {med.stock}"}), 409

        total += med.price * qty
        order_items.append((med, qty))

    # Create order
    order = Order(
        user_id=current_user["id"],
        total_amount=round(total, 2),
        payment_method=data["payment_method"],
        address=data["address"],
        status="pending",
    )
    db.session.add(order)
    db.session.flush()  # get order.id

    for med, qty in order_items:
        oi = OrderItem(order_id=order.id, medicine_id=med.id, quantity=qty, price=med.price)
        db.session.add(oi)
        med.stock -= qty   # deduct stock

    db.session.commit()
    return jsonify({"message": "Order placed successfully", "order": order.to_dict()}), 201


def get_orders(current_user):
    if current_user["role"] == "admin":
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(user_id=current_user["id"]).order_by(Order.created_at.desc()).all()
    return jsonify({"orders": [o.to_dict() for o in orders]}), 200


def get_order(order_id, current_user):
    order = Order.query.get_or_404(order_id, description="Order not found")
    if current_user["role"] != "admin" and order.user_id != current_user["id"]:
        return jsonify({"error": "Access denied"}), 403
    return jsonify({"order": order.to_dict()}), 200


def cancel_order(order_id, current_user):
    order = Order.query.get_or_404(order_id, description="Order not found")
    if current_user["role"] != "admin" and order.user_id != current_user["id"]:
        return jsonify({"error": "Access denied"}), 403
    if order.status not in ("pending",):
        return jsonify({"error": "Only pending orders can be cancelled"}), 400

    # Restore stock
    for oi in order.items:
        med = Medicine.query.get(oi.medicine_id)
        if med:
            med.stock += oi.quantity

    order.status = "cancelled"
    db.session.commit()
    return jsonify({"message": "Order cancelled", "order": order.to_dict()}), 200
