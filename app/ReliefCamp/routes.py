# app/relief_camp/routes.py
from flask import Blueprint, request, jsonify, session ,render_template
from functools import wraps
from app.models import db, ReliefCamp, AuditLog

from . import reliefCampBp


# ----------------------------
# Role-based access decorator
# ----------------------------
def require_roles(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = ["super_admin", "admin", "campmanager"]

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return jsonify({"error": "Unauthorized - Login required"}), 401
            if session["user"]["role"] not in allowed_roles:
                return jsonify({"error": "Forbidden - Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ----------------------------
# Audit Log Helper
# ----------------------------
def log_action(user_id, action, details=""):
    audit = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(audit)
    db.session.commit()


# ----------------------------
# Serializer
# ----------------------------
def serialize_camp(camp, include_relations=False):
    data = {
        "id": camp.id,
        "name": camp.name,
        "location": camp.location,
        "capacity": camp.capacity,
        "current_occupancy": camp.current_occupancy,
        "created_at": camp.created_at.isoformat(),
    }
    if include_relations:
        data["organization"] = {
            "org_id": camp.organization.org_id,
            "name": camp.organization.name
        } if camp.organization else None
        data["disaster"] = {
            "id": camp.disaster.id,
            "name": camp.disaster.name
        } if camp.disaster else None
    return data


# ----------------------------
# Create Relief Camp
# ----------------------------
@reliefCampBp.route("/create", methods=["POST"])
@require_roles(["super_admin", "admin", "campmanager"])
def create_camp():
    data = request.get_json()
    user_id = session["user"]["id"]

    try:
        camp = ReliefCamp(
            name=data.get("name"),
            location=data.get("location"),
            capacity=data.get("capacity"),
            current_occupancy=data.get("current_occupancy", 0),
            organization_id=data.get("organization_id"),
            disaster_id=data.get("disaster_id")
        )
        db.session.add(camp)
        db.session.commit()

        log_action(user_id, "CREATE_RELIEF_CAMP", f"Created camp '{camp.name}' (ID: {camp.id})")
        return jsonify({"message": "✅ Relief camp created successfully!", "camp_id": camp.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ----------------------------
# Get All Relief Camps
# ----------------------------
@reliefCampBp.route("/api", methods=["GET"])
def get_camps():
    camps = ReliefCamp.query.all()
    return jsonify([serialize_camp(c, include_relations=True) for c in camps]), 200


# ----------------------------
# Get Camp by ID
# ----------------------------
@reliefCampBp.route("/<int:camp_id>", methods=["GET"])
def get_camp(camp_id):
    camp = ReliefCamp.query.get_or_404(camp_id)
    return jsonify(serialize_camp(camp, include_relations=True)), 200


# ----------------------------
# Update Camp
# ----------------------------
@reliefCampBp.route("/<int:camp_id>", methods=["PUT", "PATCH"])
@require_roles(["super_admin", "admin", "campmanager"])
def update_camp(camp_id):
    data = request.get_json()
    camp = ReliefCamp.query.get_or_404(camp_id)
    old_data = serialize_camp(camp)

    camp.name = data.get("name", camp.name)
    camp.location = data.get("location", camp.location)
    camp.capacity = data.get("capacity", camp.capacity)
    camp.current_occupancy = data.get("current_occupancy", camp.current_occupancy)
    camp.organization_id = data.get("organization_id", camp.organization_id)
    camp.disaster_id = data.get("disaster_id", camp.disaster_id)

    db.session.commit()

    log_action(session["user"]["id"], "UPDATE_RELIEF_CAMP",
               f"Updated camp ID {camp.id}. Old Data: {old_data}, New Data: {serialize_camp(camp)}")

    return jsonify({"message": "✅ Relief camp updated successfully!"}), 200


# ----------------------------
# Delete Camp
# ----------------------------
@reliefCampBp.route("/<int:camp_id>", methods=["DELETE"])
@require_roles(["super_admin", "admin"])
def delete_camp(camp_id):
    camp = ReliefCamp.query.get_or_404(camp_id)
    camp_name = camp.name

    db.session.delete(camp)
    db.session.commit()

    log_action(session["user"]["id"], "DELETE_RELIEF_CAMP", f"Deleted camp '{camp_name}' (ID: {camp_id})")
    return jsonify({"message": "✅ Relief camp deleted successfully!"}), 200


@reliefCampBp.route("/", methods=["GET"])
def resources_page():
    return render_template("reliefcamp.html")