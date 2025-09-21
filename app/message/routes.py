from flask import request, jsonify
from app.models import db, Message, User, AuditLog
from . import messageBp
from datetime import datetime
from sqlalchemy import or_, and_

# ---------------------------- Helper ----------------------------
def serialize_message(m):
    return {
        "id": m.id,
        "sender_id": m.sender_id,
        "receiver_id": m.receiver_id,
        "content": m.content,
        "sent_at": m.sent_at.isoformat(),
        "is_read": m.is_read
    }

# ---------------------------- Send message ----------------------------
@messageBp.route("/", methods=["POST"])
def send_message():
    data = request.get_json()
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    content = data.get("content", "").strip()

    if not sender_id or not receiver_id or not content:
        return jsonify({"error": "sender_id, receiver_id, and content are required"}), 400

    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)
    if not sender or not receiver:
        return jsonify({"error": "Invalid sender or receiver"}), 404

    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()

    # Audit log
    db.session.add(AuditLog(
        user_id=sender_id,
        action="SEND_MESSAGE",
        details=f"Sent message to User {receiver_id} (Message ID: {message.id})"
    ))
    db.session.commit()

    return jsonify({"message": "Message sent", "data": serialize_message(message)}), 201

# ---------------------------- Get conversation ----------------------------
@messageBp.route("/conversation/<int:user1_id>/<int:user2_id>", methods=["GET"])
def get_conversation(user1_id, user2_id):
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id==user1_id, Message.receiver_id==user2_id),
            and_(Message.sender_id==user2_id, Message.receiver_id==user1_id)
        )
    ).order_by(Message.sent_at.asc()).all()
    return jsonify([serialize_message(m) for m in messages]), 200

# ---------------------------- Poll unread messages ----------------------------
@messageBp.route("/latest/<int:user_id>", methods=["GET"])
def latest_messages(user_id):
    # Get all unread messages for this user
    messages = Message.query.filter_by(receiver_id=user_id, is_read=False)\
                            .order_by(Message.id.asc()).all()

    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.name if m.sender else "Unknown",  # fallback if sender is None
            "receiver_id": m.receiver_id,
            "content": m.content,
            "sent_at": m.sent_at.isoformat(),
            "is_read": m.is_read
        })
    return jsonify(result), 200


# ---------------------------- Mark conversation as read ----------------------------
@messageBp.route("/mark_read/<int:other_user_id>", methods=["POST"])
def mark_conversation_read(other_user_id):
    user_id = request.json.get("current_user_id")
    if not user_id:
        return jsonify({"error": "Missing current_user_id"}), 400

    unread_messages = Message.query.filter_by(
        sender_id=other_user_id, receiver_id=user_id, is_read=False
    ).all()

    for m in unread_messages:
        m.is_read = True
    db.session.commit()

    return jsonify({"success": True, "count": len(unread_messages)}), 200

