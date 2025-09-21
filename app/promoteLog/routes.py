from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from app.models import db, User, AuditLog

from .import promoteLogBp

# ---------------- Helpers ----------------

def get_current_user():
    """Fetch the logged-in user from session."""
    user_session = session.get("user")
    if not user_session:
        return None
    return User.query.get(int(user_session["id"]))

def is_authorized_promoter(user):
    """Check if user can promote others."""
    return user and user.role in {"admin", "super_admin"}

def log_action(user_id, action, details):
    """Create an audit log entry."""
    db.session.add(AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        created_at=datetime.utcnow()
    ))
    db.session.commit()

def role_hierarchy():
    """Define hierarchy of roles."""
    return {
        "victim": 1,
        "volunteer": 2,
        "donor": 3,
        "organization_manager": 4,
        "camp_manager": 5,
        "admin": 6,
        "super_admin": 7
    }

# ---------------- Routes ----------------

# Serve HTML page
@promoteLogBp.route("/", methods=["GET"])
def promote_page():
    user = get_current_user()
    if not is_authorized_promoter(user):
        return jsonify({"error": "Unauthorized"}), 403
    return render_template("promoteLog.html", name=user.name, email=user.email)

# Promote user
@promoteLogBp.route("/promote", methods=["POST"])
def promote_user():
    admin = get_current_user()
    if not is_authorized_promoter(admin):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    user_email = data.get("user_email", "").strip().lower()
    new_role = (data.get("new_role") or "").strip().lower()

    if not user_email or not new_role:
        return jsonify({"error": "Missing user_email or new_role"}), 400

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    hierarchy = role_hierarchy()

    # Admin cannot promote above their own hierarchy
    if hierarchy.get(new_role, 0) > hierarchy.get(admin.role, 0):
        return jsonify({"error": "Cannot promote above your own role"}), 403

    old_role = user.role
    user.role = new_role
    db.session.commit()

    log_action(admin.id, "PROMOTE_USER", f"Promoted {user.email} from {old_role} → {new_role}")

    return jsonify({"message": f"✅ {user.email} promoted from {old_role} → {new_role} by {admin.email}"}), 200

# Get promotion logs
@promoteLogBp.route("/logs", methods=["GET"])
def get_promotion_logs():
    admin = get_current_user()
    if not is_authorized_promoter(admin):
        return jsonify({"error": "Unauthorized"}), 403

    logs = AuditLog.query.filter(AuditLog.action=="PROMOTE_USER").order_by(AuditLog.created_at.desc()).all()
    result = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "details": log.details,
            "created_at": log.created_at.isoformat()
        } for log in logs
    ]
    return jsonify(result), 200
