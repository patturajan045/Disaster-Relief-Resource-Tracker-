from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from app.models import db, ReliefRequest, AuditLog, User

from . import reliefRequestBp

# ---------------- Helpers ----------------
ALLOWED_ROLES = {"admin", "super_admin", "donor", "volunteer", "campManager"}

def get_current_user():
    user_session = session.get("user")
    if not user_session:
        return None
    user = User.query.get(int(user_session["id"]))
    return user

def is_admin(role):
    return role in {"admin", "super_admin"}

def can_modify_request(user, request_obj):
    return is_admin(user.role) or (user and request_obj.user_id == user.id)

def log_action(user_id, action, details):
    audit = AuditLog(user_id=user_id, action=action, details=details, created_at=datetime.utcnow())
    db.session.add(audit)
    db.session.commit()

def serialize_relief_request(r):
    return {
        "id": r.id,
        "user_id": r.user_id,
        "disaster_id": r.disaster_id,
        "resource_needed": r.resource_needed,
        "quantity": r.quantity,
        "status": r.status,
        "created_at": r.created_at.isoformat(),
    }

# ---------------- Routes ----------------

# CREATE
@reliefRequestBp.route("/create", methods=["POST"])
def create_relief_request():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    required = ["disaster_id", "resource_needed", "quantity"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    relief_request = ReliefRequest(
        user_id=user.id,
        disaster_id=data["disaster_id"],
        resource_needed=data["resource_needed"],
        quantity=data["quantity"],
        status=data.get("status", "Pending")
    )
    db.session.add(relief_request)
    db.session.commit()

    log_action(user.id, "CREATE_RELIEF_REQUEST",
               f"Created relief request ID {relief_request.id} for disaster {relief_request.disaster_id}")

    return jsonify({"message": "Relief request created successfully", "id": relief_request.id}), 201

# READ ALL
@reliefRequestBp.route("/api", methods=["GET"])
def get_all_relief_requests():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    requests = ReliefRequest.query.all()
    return jsonify([serialize_relief_request(r) for r in requests]), 200

# READ ONE
@reliefRequestBp.route("/<int:request_id>", methods=["GET"])
def get_relief_request(request_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    r = ReliefRequest.query.get_or_404(request_id)
    return jsonify(serialize_relief_request(r)), 200

# UPDATE
@reliefRequestBp.route("/<int:request_id>", methods=["PUT"])
def update_relief_request(request_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    r = ReliefRequest.query.get_or_404(request_id)
    if not can_modify_request(user, r):
        return jsonify({"error": "Forbidden: You can only edit your own requests"}), 403

    data = request.get_json() or {}
    old_data = {"resource_needed": r.resource_needed, "quantity": r.quantity, "status": r.status}

    # Only admin can update status
    if is_admin(user.role):
        r.status = data.get("status", r.status)

    r.resource_needed = data.get("resource_needed", r.resource_needed)
    r.quantity = data.get("quantity", r.quantity)

    db.session.commit()

    log_action(user.id, "UPDATE_RELIEF_REQUEST",
               f"Updated relief request ID {r.id}. Old: {old_data}, New: "
               f"{{'resource_needed': '{r.resource_needed}', 'quantity': {r.quantity}, 'status': '{r.status}'}}")

    return jsonify({"message": "Relief request updated successfully"}), 200

# DELETE
@reliefRequestBp.route("/<int:request_id>", methods=["DELETE"])
def delete_relief_request(request_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    r = ReliefRequest.query.get_or_404(request_id)
    if not can_modify_request(user, r):
        return jsonify({"error": "Forbidden: You can only delete your own requests"}), 403

    db.session.delete(r)
    db.session.commit()
    log_action(user.id, "DELETE_RELIEF_REQUEST", f"Deleted relief request ID {r.id}")

    return jsonify({"message": "Relief request deleted successfully"}), 200

# RENDER HTML PAGE
@reliefRequestBp.route("/", methods=["GET"])
def resources_page():
    return render_template("reliefrequest.html")
