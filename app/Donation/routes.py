from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from app.models import db, Donation, Resource, AuditLog, User

from . import donationBp

# ---------------- Helpers ----------------
def get_current_user():
    user_session = session.get("user")
    if not user_session:
        return None
    return User.query.get(int(user_session["id"]))

def is_admin(user):
    return user.role.lower() in {"admin", "super_admin"}

def can_modify_donation(user, donation):
    # Owner or admin can modify
    return user and (is_admin(user) or donation.donated_by == user.id)

def log_action(user_id, action, details):
    audit = AuditLog(user_id=user_id, action=action, details=details, created_at=datetime.utcnow())
    db.session.add(audit)
    db.session.commit()

def update_resource_stock(donation, old_data=None):
    # Rollback old quantity if updating
    if old_data and old_data.get("resource_type"):
        res = Resource.query.filter_by(
            resource_type=old_data["resource_type"],
            disaster_id=old_data["disaster_id"]
        ).first()
        if res:
            res.quantity -= old_data.get("quantity", 0)
            if res.quantity < 0:
                res.quantity = 0

    # Add current donation quantity
    if donation.resource_type:
        res = Resource.query.filter_by(
            resource_type=donation.resource_type,
            disaster_id=donation.disaster_id
        ).first()
        if res:
            res.quantity += donation.quantity or 0
            res.name = donation.donor_name or res.name
        else:
            res = Resource(
                name=donation.donor_name or "Unknown",
                resource_type=donation.resource_type,
                quantity=donation.quantity or 0,
                unit=donation.unit,
                disaster_id=donation.disaster_id
            )
            db.session.add(res)

# ---------------- API ----------------
@donationBp.route("/api", methods=["GET"])
def get_donations():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Admin sees all, normal users and victims see only their own donations
    donations_query = Donation.query.order_by(Donation.donated_at.desc())
    if not is_admin(user):
        donations_query = donations_query.filter_by(donated_by=user.id)
    donations = donations_query.all()

    return jsonify([{
        "id": d.id,
        "donor_name": d.donor_name,
        "resource_type": d.resource_type,
        "quantity": d.quantity,
        "unit": d.unit,
        "amount": d.amount,
        "disaster_id": d.disaster_id,
        "donated_by": d.donated_by,
        "donated_at": d.donated_at.isoformat()
    } for d in donations])

@donationBp.route("/<int:donation_id>", methods=["GET"])
def get_donation(donation_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    d = Donation.query.get_or_404(donation_id)

    # Only owner or admin can view
    if not can_modify_donation(user, d) and not is_admin(user):
        return jsonify({"error": "Forbidden"}), 403

    return jsonify({
        "id": d.id,
        "donor_name": d.donor_name,
        "resource_type": d.resource_type,
        "quantity": d.quantity,
        "unit": d.unit,
        "amount": d.amount,
        "disaster_id": d.disaster_id
    })

@donationBp.route("/create", methods=["POST"])
def create_donation():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    try:
        quantity = int(data.get("quantity") or 0)
        amount = float(data.get("amount") or 0)
        disaster_id = int(data.get("disaster_id")) if data.get("disaster_id") else None
    except ValueError:
        return jsonify({"error": "Quantity, amount, and disaster_id must be numeric"}), 400

    donation = Donation(
        donor_name=data.get("donor_name") or user.name,
        resource_type=data.get("resource_type"),
        quantity=quantity,
        unit=data.get("unit"),
        amount=amount,
        disaster_id=disaster_id,
        donated_by=user.id,
        donated_at=datetime.utcnow()
    )

    try:
        db.session.add(donation)
        db.session.flush()
        update_resource_stock(donation)
        db.session.commit()
        log_action(user.id, "CREATE_DONATION", f"Donation {donation.id} created")
        return jsonify({"message": "Donation created", "id": donation.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Server error: " + str(e)}), 500

@donationBp.route("/<int:donation_id>", methods=["PUT"])
def update_donation(donation_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    d = Donation.query.get_or_404(donation_id)
    if not can_modify_donation(user, d):
        return jsonify({"error": "Forbidden"}), 403

    old_data = {
        "resource_type": d.resource_type,
        "quantity": d.quantity,
        "disaster_id": d.disaster_id
    }

    data = request.get_json() or {}
    try:
        d.donor_name = data.get("donor_name", d.donor_name)
        d.resource_type = data.get("resource_type", d.resource_type)
        d.quantity = int(data.get("quantity") or d.quantity)
        d.unit = data.get("unit", d.unit)
        d.amount = float(data.get("amount") or d.amount)
        d.disaster_id = int(data.get("disaster_id")) if data.get("disaster_id") else d.disaster_id
    except ValueError:
        return jsonify({"error": "Quantity, amount, and disaster_id must be numeric"}), 400

    try:
        update_resource_stock(d, old_data)
        db.session.commit()
        log_action(user.id, "UPDATE_DONATION", f"Donation {d.id} updated")
        return jsonify({"message": "Donation updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Server error: " + str(e)}), 500

@donationBp.route("/<int:donation_id>", methods=["DELETE"])
def delete_donation(donation_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    d = Donation.query.get_or_404(donation_id)
    if not can_modify_donation(user, d):
        return jsonify({"error": "Forbidden"}), 403

    if d.resource_type:
        res = Resource.query.filter_by(resource_type=d.resource_type, disaster_id=d.disaster_id).first()
        if res:
            res.quantity -= d.quantity or 0
            if res.quantity < 0:
                res.quantity = 0

    try:
        db.session.delete(d)
        db.session.commit()
        log_action(user.id, "DELETE_DONATION", f"Donation {d.id} deleted")
        return jsonify({"message": "Donation deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Server error: " + str(e)}), 500

# ---------------- HTML ----------------
@donationBp.route("/", methods=["GET"])
def donation_page():
    return render_template("donation.html")
