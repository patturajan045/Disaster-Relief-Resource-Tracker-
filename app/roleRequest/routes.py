# app/roleRequest/routes.py
from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from app.models import db, User, RoleRequest, PromotionLog

from . import roleRequestBp

# ---------------- Helpers ----------------

def get_current_user():
    """Fetch the logged-in user from session."""
    user_data = session.get("user")
    if not user_data:
        return None
    return User.query.get(int(user_data["id"]))

def is_admin(user):
    return user and user.role == "admin"

def log_role_request_action(user_id, admin_id, old_role, new_role, action):
    """Log role request approval/rejection."""
    db.session.add(PromotionLog(
        user_id=user_id,
        promoted_by=admin_id,
        old_role=old_role,
        new_role=new_role,
        created_at=datetime.utcnow()
    ))
    db.session.commit()

# ---------------- Routes ----------------

# Serve Role Request Page
@roleRequestBp.route("/", methods=["GET"])
def role_page():
    # No need to pass user explicitly; session JS can fetch role via API if needed
    return render_template("rolerequest.html")

# Non-admin: Submit Role Request
@roleRequestBp.route("/request", methods=["POST"])
def submit_role_request():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    if is_admin(user):
        return jsonify({"error": "Admins cannot submit role requests"}), 403

    data = request.get_json() or {}
    requested_role = (data.get("requested_role") or "").strip()
    if not requested_role:
        return jsonify({"error": "requested_role required"}), 400

    # Check for existing pending request
    existing = RoleRequest.query.filter_by(user_id=user.id, status="pending").first()
    if existing:
        return jsonify({"error": "You already have a pending request"}), 400

    role_request = RoleRequest(user_id=user.id, requested_role=requested_role)
    db.session.add(role_request)
    db.session.commit()

    return jsonify({"message": "Role change request submitted", "request_id": role_request.id}), 201

# Admin: Get Pending Requests
@roleRequestBp.route("/requests", methods=["GET"])
def get_pending_requests():
    admin = get_current_user()
    if not is_admin(admin):
        return jsonify({"error": "Only admin can view requests"}), 403

    pending_requests = RoleRequest.query.filter_by(status="pending").all()
    result = [
        {
            "request_id": r.id,
            "user_id": r.user_id,
            "user_name": r.user.name,
            "current_role": r.user.role,
            "requested_role": r.requested_role,
            "created_at": r.created_at.isoformat()
        } for r in pending_requests
    ]
    return jsonify({"pending_requests": result}), 200

# Admin: Approve/Reject Requests
@roleRequestBp.route("/review", methods=["POST"])
def review_role_request():
    admin = get_current_user()
    if not is_admin(admin):
        return jsonify({"error": "Only admin can review requests"}), 403

    data = request.get_json() or {}
    request_id = data.get("request_id")
    action = (data.get("action") or "").lower()

    if not request_id or action not in {"approve", "reject"}:
        return jsonify({"error": "request_id and valid action required"}), 400

    role_request = RoleRequest.query.get(request_id)
    if not role_request or role_request.status != "pending":
        return jsonify({"error": "Request not found or already reviewed"}), 404

    if action == "approve":
        old_role = role_request.user.role
        role_request.user.role = role_request.requested_role
        role_request.status = "approved"
        role_request.admin_id = admin.id
        log_role_request_action(role_request.user.id, admin.id, old_role, role_request.requested_role, action)
    else:
        old_role = role_request.user.role
        role_request.status = "rejected"
        role_request.admin_id = admin.id
        log_role_request_action(role_request.user.id, admin.id, old_role, old_role, action)

    db.session.commit()
    return jsonify({"message": f"Request {action}d successfully"}), 200
