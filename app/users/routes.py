from flask import request, jsonify, render_template
from app.models import db, User, AuditLog
from . import user_bp

# ---------------------------- Audit Log Helper ----------------------------
def log_action(user_id, action, details=""):
    audit = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(audit)
    db.session.commit()

def serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": getattr(user, "phone", None),
        "role": getattr(user, "role", "victim")
    }

# ---------------------------- HTML PAGE ----------------------------
@user_bp.route("/adminUser", methods=["GET"])
def admin_user_page():
    """Serve the admin user management HTML page"""
    return render_template("adminUser.html")

# ---------------------------- API: CREATE USER ----------------------------
@user_bp.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or "name" not in data or "email" not in data or "phone" not in data:
        return jsonify({"message": "Invalid request"}), 400

    user = User(name=data['name'], email=data['email'], phone=data['phone'])
    db.session.add(user)
    db.session.commit()

    log_action(user.id, "CREATE_USER", f"User {user.name} ({user.email}) created")

    return jsonify({"message": "User created", "id": user.id})

# ---------------------------- API: READ ALL USERS ----------------------------
@user_bp.route('/api/users', methods=['GET'])
def get_all_users():
    try:
        users = User.query.all()
        return jsonify([serialize_user(u) for u in users])
    except Exception as e:
        print("❌ ERROR in /api/users:", e)
        return jsonify({"error": str(e)}), 500

# ---------------------------- API: UPDATE USER ----------------------------
@user_bp.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    old_data = serialize_user(user)

    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.phone = data.get('phone', user.phone)
    db.session.commit()

    new_data = serialize_user(user)
    log_action(user.id, "UPDATE_USER", f"Updated user from {old_data} → {new_data}")

    return jsonify({"message": "User updated"})

# ---------------------------- API: DELETE USER ----------------------------
@user_bp.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user_info = serialize_user(user)
    db.session.delete(user)
    db.session.commit()

    log_action(id, "DELETE_USER", f"Deleted user {user_info}")

    return jsonify({"message": "User deleted"})
