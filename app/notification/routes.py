from flask import request, jsonify, session, render_template
from datetime import datetime
from app.models import db, Notification, AuditLog, User
from . import notificationBp

# ---------------- Helpers ----------------
def get_current_user():
    return session.get("user")

def is_admin_user(user):
    return user and user.get("role", "").strip().lower() in ["admin", "super_admin"]

def log_action(user_id, action, details):
    db.session.add(
        AuditLog(
            user_id=int(user_id) if user_id else None,
            action=action,
            details=details,
            created_at=datetime.utcnow()
        )
    )
    db.session.commit()

# ---------------- Routes ----------------

# Render Notification Page
@notificationBp.route("/", methods=["GET"])
def notification_page():
    user = get_current_user()
    if not user:
        return "Unauthorized", 401

    unread_count = Notification.query.filter_by(user_id=int(user["id"]), is_read=False).count()
    return render_template("notification.html", unread_count=unread_count, user_role=user.get("role"))

# API: Get all notifications
@notificationBp.route("/api", methods=["GET"])
def get_notifications():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    notifications = Notification.query.filter_by(user_id=int(user["id"])).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        "id": n.id,
        "type": n.type,
        "related_id": n.related_id,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat()
    } for n in notifications]), 200

# API: Mark notification as read
@notificationBp.route("/<int:notification_id>/read", methods=["PUT"])
def mark_as_read(notification_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != int(user["id"]):
        return jsonify({"error": "Forbidden"}), 403

    if not notification.is_read:
        notification.is_read = True
        db.session.commit()
        log_action(user["id"], "READ_NOTIFICATION", f"Notification {notification_id} marked as read")

    return jsonify({"message": "Notification marked as read"}), 200

# API: Create new notification (Admin only)
@notificationBp.route("/", methods=["POST"])
def create_notification():
    user = get_current_user()
    if not is_admin_user(user):
        return jsonify({"error": "Unauthorized: only admin/super_admin can create notifications"}), 403

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    message = data.get("message")
    if not user_id or not message:
        return jsonify({"error": "Missing required fields: user_id or message"}), 400

    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({"error": "Target user does not exist"}), 400

    new_notification = Notification(
        user_id=user_id,
        type=data.get("type", "system"),
        related_id=data.get("related_id"),
        message=message
    )
    db.session.add(new_notification)
    db.session.commit()
    log_action(user["id"], "CREATE_NOTIFICATION", f"Notification {new_notification.id} created for user {user_id}")

    return jsonify({"message": "Notification created", "id": new_notification.id}), 201

# API: Delete notification (Owner or Admin)
@notificationBp.route("/<int:notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != int(user["id"]) and not is_admin_user(user):
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(notification)
    db.session.commit()
    log_action(user["id"], "DELETE_NOTIFICATION", f"Notification {notification_id} deleted")
    return jsonify({"message": "Notification deleted"}), 200
