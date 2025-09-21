from flask import Blueprint, request, jsonify, session, render_template
from functools import wraps
from datetime import datetime
from app.models import db, Organization, AuditLog

from . import organizationBp   # make sure __init__.py registers organizationBp


# ----------------------------
# Role-based access decorator
# ----------------------------
def require_roles(allowed_roles=None):
    if allowed_roles is None:
        # default roles allowed for create/update/delete
        allowed_roles = ["super_admin", "admin", "organization_manager"]

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
    try:
        audit = AuditLog(user_id=user_id, action=action, details=details, created_at=datetime.utcnow())
        db.session.add(audit)
        db.session.commit()
    except Exception:
        db.session.rollback()


# ----------------------------
# Serializer
# ----------------------------
def serialize_org(org, include_relations=False):
    data = {
        "org_id": org.org_id,
        "name": org.name,
        "type": org.type,
        "contact_number": org.contact_number,
        "created_at": org.created_at.isoformat()
    }
    if include_relations:
        # include related counts safely
        data["relief_camps_count"] = len(org.relief_camps or [])
        data["members_count"] = len(org.members or [])
    return data


# ----------------------------
# Create Organization
# ----------------------------
@organizationBp.route("/create", methods=["POST"])
@require_roles(["super_admin", "admin", "organization_manager"])
def create_organization():
    data = request.get_json()
    user_id = session["user"]["id"]

    try:
        org = Organization(
            name=data.get("name"),
            type=data.get("type"),
            contact_number=data.get("contact_number")
        )
        db.session.add(org)
        db.session.commit()

        log_action(user_id, "CREATE_ORGANIZATION", f"Created organization '{org.name}' (ID: {org.org_id})")
        return jsonify({"message": "✅ Organization created successfully!", "org_id": org.org_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ----------------------------
# Get All Organizations
# ----------------------------
@organizationBp.route("/api", methods=["GET"])
def get_organizations():
    orgs = Organization.query.all()
    return jsonify([serialize_org(o, include_relations=True) for o in orgs]), 200


# ----------------------------
# Get Organization by ID
# ----------------------------
@organizationBp.route("/<int:org_id>", methods=["GET"])
def get_organization(org_id):
    org = Organization.query.get_or_404(org_id)
    return jsonify(serialize_org(org, include_relations=True)), 200


# ----------------------------
# Update Organization
# ----------------------------
@organizationBp.route("/<int:org_id>", methods=["PUT", "PATCH"])
@require_roles(["super_admin", "admin", "organization_manager"])
def update_organization(org_id):
    data = request.get_json()
    org = Organization.query.get_or_404(org_id)
    old_data = serialize_org(org)

    org.name = data.get("name", org.name)
    org.type = data.get("type", org.type)
    org.contact_number = data.get("contact_number", org.contact_number)

    db.session.commit()

    log_action(session["user"]["id"], "UPDATE_ORGANIZATION",
               f"Updated org ID {org.org_id}. Old Data: {old_data}, New Data: {serialize_org(org)}")
    return jsonify({"message": "✅ Organization updated successfully!"}), 200


# ----------------------------
# Delete Organization
# ----------------------------
@organizationBp.route("/<int:org_id>", methods=["DELETE"])
@require_roles(["super_admin", "admin"])
def delete_organization(org_id):
    org = Organization.query.get_or_404(org_id)
    org_name = org.name

    db.session.delete(org)
    db.session.commit()

    log_action(session["user"]["id"], "DELETE_ORGANIZATION", f"Deleted organization '{org_name}' (ID: {org_id})")
    return jsonify({"message": "✅ Organization deleted successfully!"}), 200


# ----------------------------
# Frontend Page
# ----------------------------
@organizationBp.route("/", methods=["GET"])
def organization_page():
    # renders templates/organization.html
    return render_template("organization.html")
