from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from app.models import db, Disaster, User, AuditLog

from .import disasterBp

# ----------------------------
# Helpers
# ----------------------------
def is_admin(role):
    return role in ["super_admin", "admin", "camp_manager"]

def can_modify_disaster(user, disaster, role):
    return is_admin(role) or (user and disaster.reported_by == user.id)

def serialize_disaster(d):
    return {
        "id": d.id,
        "name": d.name,
        "type": d.type,
        "location": d.location,
        "severity": d.severity,
        "affected_population": d.affected_population,
        "description": d.description,
        "reported_on": d.reported_on.isoformat() if d.reported_on else None,
        "updated_on": d.updated_on.isoformat() if d.updated_on else None,
        "reported_by": d.reported_by,
        "reported_by_name": getattr(d.reporter, "name", "Unknown")
    }

def log_action(user_id, action, details):
    audit = AuditLog(user_id=user_id or None, action=action, details=details, created_at=datetime.utcnow())
    db.session.add(audit)
    db.session.commit()

# ----------------------------
# Routes
# ----------------------------

# --- Create Disaster ---
@disasterBp.route("/create", methods=["POST"])
def create_disaster():
    data = request.get_json() or {}
    user_id = session.get("user_id")
    user = User.query.get(user_id) if user_id else None
    role = request.headers.get("X-Role") or (user.role if user else None)

    required = ["name", "type", "location"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    disaster = Disaster(
        name=data["name"],
        type=data["type"],
        location=data["location"],
        severity=data.get("severity", "Low"),
        affected_population=data.get("affected_population"),
        description=data.get("description"),
        reported_by=user_id,
        reported_on=datetime.utcnow()
    )
    db.session.add(disaster)
    db.session.commit()
    log_action(user_id, "CREATE_DISASTER", f"Created {disaster.name}")

    return jsonify({"message": "Disaster created", "disaster": serialize_disaster(disaster)}), 201

# --- Get All Disasters ---
@disasterBp.route("/disaster", methods=["GET"])
def get_disasters():
    disasters = Disaster.query.all()
    return jsonify([serialize_disaster(d) for d in disasters]), 200

# --- Get Single Disaster ---
@disasterBp.route("/<int:id>", methods=["GET"])
def get_disaster(id):
    disaster = Disaster.query.get_or_404(id)
    return jsonify(serialize_disaster(disaster)), 200

# --- Update Disaster ---
@disasterBp.route("/<int:id>", methods=["PUT"])
def update_disaster(id):
    disaster = Disaster.query.get_or_404(id)
    data = request.get_json() or {}

    user_id = session.get("user_id")
    user = User.query.get(user_id) if user_id else None
    role = (request.headers.get("X-Role") or (user.role if user else "")).lower()

    # Allow admins or the original reporter
    if not can_modify_disaster(user, disaster, role) and not is_admin(role):
        return jsonify({"error": "You are not allowed to update this disaster"}), 403

    # Update fields
    for field in ["name", "type", "location", "severity", "affected_population", "description"]:
        if field in data:
            setattr(disaster, field, data[field])

    disaster.updated_on = datetime.utcnow()
    db.session.commit()
    log_action(user_id, "UPDATE_DISASTER", f"Updated disaster {disaster.id}")

    return jsonify({"message": "Disaster updated", "disaster": serialize_disaster(disaster)}), 200

# --- Delete Disaster ---
@disasterBp.route("/<int:id>", methods=["DELETE"])
def delete_disaster(id):
    disaster = Disaster.query.get_or_404(id)

    user_id = session.get("user_id")
    user = User.query.get(user_id) if user_id else None
    role = (request.headers.get("X-Role") or (user.role if user else "")).lower()

    # Admin bypass
    if not can_modify_disaster(user, disaster, role):
        if not is_admin(role):  # only block non-admins
            return jsonify({"error": "You are not allowed to delete this disaster"}), 403

    db.session.delete(disaster)
    db.session.commit()
    log_action(user_id, "DELETE_DISASTER", f"Deleted {disaster.name}")

    return jsonify({"message": "Disaster deleted"}), 200


# --- Render HTML Page (optional) ---
@disasterBp.route("/", methods=["GET"])
def disaster_page():
    if "user_id" not in session:
        session["user_id"] = None
    return render_template("disaster.html", user_id=session.get("user_id"))
