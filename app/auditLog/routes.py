from flask import request, jsonify, session
from datetime import datetime
from app.models import db, AuditLog, User
from . import auditLog

# ----------------------------
# Helpers
# ----------------------------
def get_current_user():
    """Return user object from session, or None."""
    u = session.get("user")
    if not u:
        return None
    return User.query.get(int(u["id"]))


def is_admin_user(user):
    """Check if the user is admin or super_admin."""
    return user and user.role.lower() in ["admin", "super_admin"]


def serialize_log(log):
    user = get_current_user()
    return {
        "id": log.id,
        "user_id": log.user_id,
        "user_name": getattr(log.user, "name", None),
        "action": log.action,
        "details": log.details,
        "created_at": log.created_at.isoformat(),
        "can_delete": is_admin_user(user)
    }


def log_action(user_id, action, details):
    audit = AuditLog(
        user_id=user_id or None,
        action=action,
        details=details,
        created_at=datetime.utcnow()
    )
    db.session.add(audit)
    db.session.commit()


def fetch_logs(query):
    logs = query.order_by(AuditLog.created_at.desc()).all()
    return jsonify([serialize_log(log) for log in logs])


# ----------------------------
# GET Routes
# ----------------------------
@auditLog.route("/", methods=["GET"])
def get_all_audit_logs():
    return fetch_logs(AuditLog.query)


@auditLog.route("/user/<int:user_id>", methods=["GET"])
def get_user_audit_logs(user_id):
    return fetch_logs(AuditLog.query.filter_by(user_id=user_id))


@auditLog.route("/action/<string:action>", methods=["GET"])
def get_logs_by_action(action):
    return fetch_logs(AuditLog.query.filter_by(action=action.upper()))


# ----------------------------
# DELETE Routes (Admin only)
# ----------------------------
@auditLog.route("/<int:log_id>", methods=["DELETE"])
def delete_audit_log(log_id):
    user = get_current_user()

    if not is_admin_user(user):
        return jsonify({"success": False, "error": "Unauthorized: only admin or super_admin can delete logs"}), 403

    log = AuditLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({"success": True, "message": f"Audit log {log_id} deleted"})


@auditLog.route("/clear", methods=["DELETE"])
def clear_audit_logs():
    user = get_current_user()

    if not is_admin_user(user):
        return jsonify({"success": False, "error": "Unauthorized: only admin or super_admin can delete logs"}), 403

    num_rows = db.session.query(AuditLog).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"success": True, "message": f"Deleted {num_rows} audit logs"})
