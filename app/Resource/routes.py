from flask import Blueprint, request, jsonify, session, render_template
from app.models import db, Resource, Donation, AuditLog, User
from datetime import datetime

from . import resourceBp

ALLOWED_ROLES = {"admin", "super_admin", "donor", "volunteer", "campManager", "victim"}
ADMIN_ROLES = {"admin", "super_admin"}  # can manage all resources

# ---------------- Helpers ----------------
def log_action(user_id, action, details=""):
    audit = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(audit)
    db.session.commit()

def get_current_user():
    user_session = session.get("user")
    if not user_session:
        return None, jsonify({"error": "Unauthorized"}), 401
    role = user_session.get("role", "").lower()
    if role not in ALLOWED_ROLES:
        return None, jsonify({"error": "Forbidden"}), 403
    return user_session, None, None

def serialize_resource(resource: Resource):
    return {
        "id": resource.id,
        "name": resource.name,
        "quantity": resource.quantity,
        "resource_type": resource.resource_type,
        "unit": resource.unit,
        "disaster_id": resource.disaster_id,
        "added_by": resource.added_by,
        "created_at": resource.created_at.isoformat(),
        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
    }

# ---------------- Routes ----------------

# CREATE RESOURCE
@resourceBp.route("/create", methods=["POST"])
def create_resource():
    user_session, resp, status = get_current_user()
    if not user_session:
        return resp, status

    data = request.get_json() or {}
    required = ["name", "quantity", "resource_type"]
    if not all(field in data for field in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400

    try:
        new_resource = Resource(
            name=data["name"],
            quantity=data["quantity"],
            resource_type=data["resource_type"],
            unit=data.get("unit"),
            disaster_id=data.get("disaster_id"),
            added_by=int(user_session["id"]),
        )
        db.session.add(new_resource)
        db.session.commit()
        log_action(new_resource.added_by, "CREATE_RESOURCE", f"Created resource ID {new_resource.id}")
        return jsonify({"message": "Resource created successfully", "id": new_resource.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# GET ALL RESOURCES + DONATIONS
@resourceBp.route("/api", methods=["GET"])
def get_resources():
    user_session, resp, status = get_current_user()
    if not user_session:
        return resp, status

    try:
        # Donations
        donations = Donation.query.order_by(Donation.donated_at.desc()).all()
        donation_data = [{
            "id": f"don-{d.id}",
            "name": d.donor_name,
            "donor_name": d.donor_name,
            "resource_type": "donation",
            "quantity": d.quantity or 0,
            "unit": d.unit or "",
            "amount": d.amount or 0,
            "disaster_id": d.disaster_id or "-",
            "source": "donation",
            "created_at": d.donated_at.isoformat()
        } for d in donations]

        # Resources
        resources = Resource.query.order_by(Resource.created_at.desc()).all()
        resource_data = [serialize_resource(r) | {"source": "resource"} for r in resources]

        return jsonify(donation_data + resource_data), 200
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# GET SINGLE RESOURCE
@resourceBp.route("/resource/<int:resource_id>", methods=["GET"])
def get_resource(resource_id):
    user_session, resp, status = get_current_user()
    if not user_session:
        return resp, status

    r = Resource.query.get_or_404(resource_id)
    return jsonify(serialize_resource(r)), 200

# UPDATE RESOURCE
@resourceBp.route("/resource/<int:resource_id>", methods=["PUT"])
def update_resource(resource_id):
    user_session, resp, status = get_current_user()
    if not user_session:
        return resp, status

    r = Resource.query.get_or_404(resource_id)

    # Only owner or admin can update
    if int(user_session["id"]) != r.added_by and user_session["role"].lower() not in ADMIN_ROLES:
        return jsonify({"error": "You cannot update this resource"}), 403

    data = request.get_json() or {}
    try:
        for field in ["name", "quantity", "resource_type", "unit", "disaster_id"]:
            if field in data:
                setattr(r, field, data[field])
        db.session.commit()
        log_action(int(user_session["id"]), "UPDATE_RESOURCE", f"Updated resource ID {r.id}")
        return jsonify({"message": "Resource updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# DELETE RESOURCE
@resourceBp.route("/resource/<int:resource_id>", methods=["DELETE"])
def delete_resource(resource_id):
    user_session, resp, status = get_current_user()
    if not user_session:
        return resp, status

    r = Resource.query.get_or_404(resource_id)

    # Only owner or admin can delete
    if int(user_session["id"]) != r.added_by and user_session["role"].lower() not in ADMIN_ROLES:
        return jsonify({"error": "You cannot delete this resource"}), 403

    try:
        db.session.delete(r)
        db.session.commit()
        log_action(int(user_session["id"]), "DELETE_RESOURCE", f"Deleted resource ID {r.id}")
        return jsonify({"message": "Resource deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# FRONTEND PAGE
@resourceBp.route("/", methods=["GET"])
def resources_page():
    user_session = session.get("user")
    if not user_session:
        return "Unauthorized", 401
    return render_template("resources.html")
